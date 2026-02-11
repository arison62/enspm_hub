"""
WebSocket Consumer REFACTORISÉ - Version propre
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from network.events import (
    event_bus,
    EventTypes,
    MessageGroupeCreatedEvent,
    MessageDMCreatedEvent,
    ConversationCreatedEvent,
    MembreGroupeAddedEvent,
)

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket REFACTORISÉ
    
    Responsabilités :
    1. Gérer la connexion WebSocket
    2. Écouter les événements EventBus
    3. Diffuser vers le client via WebSocket
    
    CE QUE CE CONSUMER NE FAIT PAS :
    - ❌ Logique métier
    - ❌ Appel direct aux Services
    - ❌ Gestion manuelle de room.join (sauf auto-join)
    """
    
    async def connect(self):
        """Connexion WebSocket - Minimal"""
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            logger.warning("WebSocket rejected: User not authenticated")
            await self.close()
            return

        self.profil_id = await self.get_user_profil_id(self.user)
        if not self.profil_id:
            logger.warning(f"WebSocket rejected: User {self.user.id} has no profile")
            await self.close()
            return

        # ✅ JOIN uniquement le canal personnel
        self.user_room_name = f"user_{self.profil_id}"
        await self.channel_layer.group_add(
            self.user_room_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket connected: User {self.user.id} (Profil {self.profil_id})")

        # ✅ S'abonner aux événements EventBus
        await self.subscribe_to_events()
        
        # ✅ Charger les rooms existantes (une seule fois)
        await self.load_existing_rooms()

    async def disconnect(self, close_code):
        """Déconnexion WebSocket"""
        if hasattr(self, 'user_room_name'):
            await self.channel_layer.group_discard(
                self.user_room_name,
                self.channel_name
            )
        
        await self.unsubscribe_from_events()
        logger.info(f"WebSocket disconnected: User {self.user.id} (Code: {close_code})")

    async def receive(self, text_data):
        """
        ✅ REFACTORISÉ : WebSocket unidirectionnel
        
        Le client NE DOIT PAS envoyer de commandes métier ici.
        Uniquement des commandes de contrôle (ping, heartbeat, etc.)
        """
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        message_type = data.get("type")
        
        # ✅ Seules les commandes de contrôle sont autorisées
        if message_type == "ping":
            await self.send(json.dumps({"type": "pong"}))
        
        # ❌ SUPPRIMÉ : dm.init (utiliser POST /api/direct/init/{profil_id}/)
        # ❌ SUPPRIMÉ : room.join (auto-join via événements)
        
        else:
            logger.warning(f"Unknown WebSocket command: {message_type}")

    # ============================================
    # GESTION DES ÉVÉNEMENTS EVENTBUS
    # ============================================
    
    async def subscribe_to_events(self):
        """S'abonne aux événements EventBus"""
        await database_sync_to_async(self._sync_subscribe_to_events)()
    
    def _sync_subscribe_to_events(self):
        """Souscription synchrone aux événements"""
        # Messages
        event_bus.subscribe(EventTypes.MESSAGE_GROUPE_CREATED, self.on_message_groupe_created)
        event_bus.subscribe(EventTypes.MESSAGE_DM_CREATED, self.on_message_dm_created)
        
        # Conversations
        event_bus.subscribe(EventTypes.CONVERSATION_CREATED, self.on_conversation_created)
        
        # ✅ NOUVEAU : Auto-join sur ajout à un groupe
        event_bus.subscribe(EventTypes.MEMBRE_GROUPE_ADDED, self.on_membre_groupe_added)
        
        logger.debug(f"User {self.user.id} subscribed to EventBus events")
    
    async def unsubscribe_from_events(self):
        """Désinscription des événements"""
        await database_sync_to_async(self._sync_unsubscribe_from_events)()
    
    def _sync_unsubscribe_from_events(self):
        """Désinscription synchrone"""
        event_bus.unsubscribe(EventTypes.MESSAGE_GROUPE_CREATED, self.on_message_groupe_created)
        event_bus.unsubscribe(EventTypes.MESSAGE_DM_CREATED, self.on_message_dm_created)
        event_bus.unsubscribe(EventTypes.CONVERSATION_CREATED, self.on_conversation_created)
        event_bus.unsubscribe(EventTypes.MEMBRE_GROUPE_ADDED, self.on_membre_groupe_added)
        logger.debug(f"User {self.user.id} unsubscribed from EventBus events")
    
    # ============================================
    # HANDLERS D'ÉVÉNEMENTS - REFACTORISÉS
    # ============================================
    
    def on_message_groupe_created(self, event: MessageGroupeCreatedEvent):
        """
        ✅ SIMPLIFIÉ : Juste diffuser, pas de logique
        """
        logger.info(f"Event: MessageGroupeCreated - Groupe: {event.groupe_id}")
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"groupe_{event.groupe_id}",
            {
                "type": "chat.message",
                "room_type": "groupe",
                "room_id": str(event.groupe_id),
                "message": event.message_data or self._build_message_data(event)
            }
        )
    
    def on_message_dm_created(self, event: MessageDMCreatedEvent):
        """✅ SIMPLIFIÉ : Juste diffuser"""
        logger.info(f"Event: MessageDMCreated - Conv: {event.conversation_id}")
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"conv_{event.conversation_id}",
            {
                "type": "chat.message",
                "room_type": "conv",
                "room_id": str(event.conversation_id),
                "message": event.message_data or self._build_dm_data(event)
            }
        )
    
    def on_conversation_created(self, event: ConversationCreatedEvent):
        """
        ✅ NOUVEAU : Auto-join + notification
        
        Quand une conversation est créée, les participants :
        1. Rejoignent automatiquement la room
        2. Reçoivent une notification
        """
        logger.info(f"Event: ConversationCreated - {event.conversation_id}")
        
        channel_layer = get_channel_layer()
        
        # ✅ AUTO-JOIN : Les participants rejoignent la room
        for participant_id in event.participant_ids:
            # Notifier le participant
            async_to_sync(channel_layer.group_send)(
                f"user_{participant_id}",
                {
                    "type": "conversation.created",
                    "conversation_id": str(event.conversation_id),
                    "participant_ids": [str(pid) for pid in event.participant_ids]
                }
            )
    
    def on_membre_groupe_added(self, event: MembreGroupeAddedEvent):
        """
        ✅ NOUVEAU : Auto-join lors de l'ajout à un groupe
        """
        logger.info(f"Event: MembreGroupeAdded - Groupe: {event.groupe_id}, Membre: {event.profil_id}")
        
        # ✅ AUTO-JOIN : Le nouveau membre rejoint automatiquement
        if event.profil_id == self.profil_id:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_add)(
                f"groupe_{event.groupe_id}",
                self.channel_name
            )
            logger.info(f"User {self.profil_id} auto-joined groupe_{event.groupe_id}")

    # ============================================
    # HANDLERS CHANNEL LAYER
    # ============================================

    async def chat_message(self, event):
        """Handler générique pour les messages de chat"""
        await self.send(text_data=json.dumps({
            "type": "chat.message",
            "room_type": event.get("room_type"),
            "room_id": event.get("room_id"),
            "message": event["message"]
        }))
    
    async def conversation_created(self, event):
        """
        Handler pour la notification de création de conversation
        
        Appelé quand on reçoit un message sur le canal user_{profil_id}
        """
        conversation_id = event["conversation_id"]
        
        # ✅ AUTO-JOIN : Rejoindre la nouvelle conversation
        await self.channel_layer.group_add(
            f"conv_{conversation_id}",
            self.channel_name
        )
        logger.info(f"User {self.profil_id} auto-joined conv_{conversation_id}")
        
        # Notifier le client
        await self.send(text_data=json.dumps({
            "type": "conversation.created",
            "conversation_id": conversation_id,
            "participant_ids": event["participant_ids"]
        }))

    # ============================================
    # MÉTHODES UTILITAIRES
    # ============================================

    @database_sync_to_async
    def get_user_profil_id(self, user):
        """Récupère l'ID du profil de l'utilisateur"""
        try:
            return user.profil.id
        except ObjectDoesNotExist:
            return None

    async def load_existing_rooms(self):
        """
        ✅ REFACTORISÉ : Charger les rooms existantes une seule fois
        
        Appelé uniquement à la connexion pour rejoindre les rooms
        des groupes et conversations existants.
        """
        # Groupes
        group_ids = await self.get_user_group_ids()
        for gid in group_ids:
            await self.channel_layer.group_add(f"groupe_{gid}", self.channel_name)
            logger.debug(f"Loaded group room: groupe_{gid}")

        # Conversations DM
        conv_ids = await self.get_user_conv_ids()
        for cid in conv_ids:
            await self.channel_layer.group_add(f"conv_{cid}", self.channel_name)
            logger.debug(f"Loaded conv room: conv_{cid}")

    @database_sync_to_async
    def get_user_group_ids(self):
        """Récupère les IDs des groupes de l'utilisateur"""
        from network.models import MembreGroupe
        return list(MembreGroupe.objects.filter(
            profil_id=self.profil_id,
            deleted=False
        ).values_list('groupe_id', flat=True))

    @database_sync_to_async
    def get_user_conv_ids(self):
        """Récupère les IDs des conversations de l'utilisateur"""
        from network.models import Conversation
        return list(Conversation.objects.filter(
            participants__id=self.profil_id,
            deleted=False
        ).values_list('id', flat=True))
    
    def _build_message_data(self, event: MessageGroupeCreatedEvent):
        """Construit les données du message groupe depuis l'événement"""
        return {
            "id": str(event.message_id),
            "contenu": event.contenu,
            "expediteur_id": str(event.expediteur_id),
            "piece_jointe_url": event.piece_jointe_url,
            "reponse_a_id": str(event.reponse_a_id) if event.reponse_a_id else None,
        }
    
    def _build_dm_data(self, event: MessageDMCreatedEvent):
        """Construit les données du message DM depuis l'événement"""
        return {
            "id": str(event.message_id),
            "contenu": event.contenu,
            "expediteur_id": str(event.expediteur_id),
            "piece_jointe_url": event.piece_jointe_url,
        }