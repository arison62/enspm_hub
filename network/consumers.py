"""
WebSocket Consumer refactorisé avec EventBus
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
)

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket qui:
    1. Gère les connexions WebSocket
    2. Écoute les événements de l'EventBus
    3. Diffuse les messages via WebSocket
    """
    
    async def connect(self):
        """Connexion WebSocket initiale"""
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            logger.warning(f"WebSocket connection rejected: User not authenticated")
            await self.close()
            return

        self.profil_id = await self.get_user_profil_id(self.user)
        if not self.profil_id:
            logger.warning(f"WebSocket connection rejected: User {self.user.id} has no profile")
            await self.close()
            return

        # Personal notification channel
        self.user_room_name = f"user_{self.profil_id}"
        await self.channel_layer.group_add(
            self.user_room_name,
            self.channel_name
        )

        await self.accept()
        
        logger.info(f"WebSocket connected: User {self.user.id} (Profil {self.profil_id})")

        # IMPORTANT: S'abonner aux événements après connexion
        await self.subscribe_to_events()

        # Join all active rooms (Groups and DM Conversations)
        await self.join_all_active_rooms()

    async def disconnect(self, close_code):
        """Déconnexion WebSocket"""
        if hasattr(self, 'user_room_name'):
            await self.channel_layer.group_discard(
                self.user_room_name,
                self.channel_name
            )
        
        # Désabonnement des événements
        await self.unsubscribe_from_events()
        
        logger.info(f"WebSocket disconnected: User {self.user.id} (Code: {close_code})")

    async def receive(self, text_data):
        """Réception de messages depuis le client WebSocket"""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        message_type = data.get("type")
        
        if message_type == "dm.init":
            destinataire_id = data.get("destinataire_id")
            if destinataire_id:
                await self.handle_dm_init(destinataire_id)

        elif message_type == "room.join":
            room_type = data.get("room_type")  # "groupe" or "conv"
            room_id = data.get("room_id")
            if room_type in ["groupe", "conv"] and room_id:
                # Permission check before joining
                has_permission = await self.check_room_permission(room_type, room_id)
                if has_permission:
                    await self.channel_layer.group_add(
                        f"{room_type}_{room_id}",
                        self.channel_name
                    )
                    logger.info(f"User {self.user.id} joined room {room_type}_{room_id}")
                else:
                    logger.warning(f"User {self.user.id} denied access to room {room_type}_{room_id}")

    # ============================================
    # GESTION DES ÉVÉNEMENTS EVENTBUS
    # ============================================
    
    async def subscribe_to_events(self):
        """S'abonne aux événements EventBus"""
        await database_sync_to_async(self._sync_subscribe_to_events)()
    
    def _sync_subscribe_to_events(self):
        """Version synchrone de la souscription aux événements"""
        # S'abonner aux événements de messages groupe
        event_bus.subscribe(
            EventTypes.MESSAGE_GROUPE_CREATED,
            self.on_message_groupe_created
        )
        
        # S'abonner aux événements de messages DM
        event_bus.subscribe(
            EventTypes.MESSAGE_DM_CREATED,
            self.on_message_dm_created
        )
        
        # S'abonner aux événements de conversation
        event_bus.subscribe(
            EventTypes.CONVERSATION_CREATED,
            self.on_conversation_created
        )
        
        logger.debug(f"User {self.user.id} subscribed to EventBus events")
    
    async def unsubscribe_from_events(self):
        """Se désabonne des événements EventBus"""
        await database_sync_to_async(self._sync_unsubscribe_from_events)()
    
    def _sync_unsubscribe_from_events(self):
        """Version synchrone de la désinscription aux événements"""
        event_bus.unsubscribe(
            EventTypes.MESSAGE_GROUPE_CREATED,
            self.on_message_groupe_created
        )
        
        event_bus.unsubscribe(
            EventTypes.MESSAGE_DM_CREATED,
            self.on_message_dm_created
        )
        
        event_bus.unsubscribe(
            EventTypes.CONVERSATION_CREATED,
            self.on_conversation_created
        )
        
        logger.debug(f"User {self.user.id} unsubscribed from EventBus events")
    
    # ============================================
    # HANDLERS D'ÉVÉNEMENTS
    # ============================================
    
    def on_message_groupe_created(self, event: MessageGroupeCreatedEvent):
        """
        Handler appelé quand un message de groupe est créé
        Diffuse le message à tous les membres du groupe
        """
        logger.info(f"Event received: MessageGroupeCreated - Groupe: {event.groupe_id}, Message: {event.message_id}")
        
        # Diffuser via WebSocket à tous les membres du groupe
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"groupe_{event.groupe_id}",
            {
                "type": "chat.message",
                "room_type": "groupe",
                "room_id": str(event.groupe_id),
                "message": event.message_data or {
                    "id": str(event.message_id),
                    "contenu": event.contenu,
                    "expediteur_id": str(event.expediteur_id),
                    "piece_jointe_url": event.piece_jointe_url,
                    "reponse_a_id": str(event.reponse_a_id) if event.reponse_a_id else None,
                }
            }
        )
    
    def on_message_dm_created(self, event: MessageDMCreatedEvent):
        """
        Handler appelé quand un message DM est créé
        Diffuse le message à tous les participants de la conversation
        """
        logger.info(f"Event received: MessageDMCreated - Conv: {event.conversation_id}, Message: {event.message_id}")
        
        # Diffuser via WebSocket à tous les participants
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"conv_{event.conversation_id}",
            {
                "type": "chat.message",
                "room_type": "conv",
                "room_id": str(event.conversation_id),
                "message": event.message_data or {
                    "id": str(event.message_id),
                    "contenu": event.contenu,
                    "expediteur_id": str(event.expediteur_id),
                    "piece_jointe_url": event.piece_jointe_url,
                }
            }
        )
    
    def on_conversation_created(self, event: ConversationCreatedEvent):
        """
        Handler appelé quand une conversation est créée
        Notifie les participants
        """
        logger.info(f"Event received: ConversationCreated - {event.conversation_id}")
        
        # Notifier chaque participant
        channel_layer = get_channel_layer()
        for participant_id in event.participant_ids:
            async_to_sync(channel_layer.group_send)(
                f"user_{participant_id}",
                {
                    "type": "conversation.created",
                    "conversation_id": str(event.conversation_id),
                    "participant_ids": [str(pid) for pid in event.participant_ids]
                }
            )

    # ============================================
    # HANDLERS POUR MESSAGES CHANNEL LAYER
    # ============================================

    async def handle_dm_init(self, destinataire_id):
        """Initialise une conversation DM"""
        conv_id = await self.get_or_create_conversation_id(destinataire_id)
        if conv_id:
            # Join the newly created/retrieved conversation room
            await self.channel_layer.group_add(f"conv_{conv_id}", self.channel_name)

            # Notify the recipient via their personal channel
            await self.channel_layer.group_send(
                f"user_{destinataire_id}",
                {
                    "type": "dm_init_notification",
                    "conversation_id": str(conv_id),
                    "from_profil_id": str(self.profil_id)
                }
            )

            # Send success back to the initiator
            await self.send(text_data=json.dumps({
                "type": "dm.init_success",
                "conversation_id": str(conv_id)
            }))

    async def dm_init_notification(self, event):
        """Handle 'dm.init' notification sent to a personal user channel"""
        await self.send(text_data=json.dumps({
            "type": "dm.init_notification",
            "conversation_id": event["conversation_id"],
            "from_profil_id": event["from_profil_id"]
        }))

    async def chat_message(self, event):
        """
        Handler générique pour les messages de chat
        Appelé par le channel layer quand un message est diffusé
        """
        await self.send(text_data=json.dumps({
            "type": "chat.message",
            "room_type": event.get("room_type"),
            "room_id": event.get("room_id"),
            "message": event["message"]
        }))
    
    async def conversation_created(self, event):
        """Handler pour la création de conversation"""
        await self.send(text_data=json.dumps({
            "type": "conversation.created",
            "conversation_id": event["conversation_id"],
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

    @database_sync_to_async
    def get_or_create_conversation_id(self, destinataire_id):
        """Obtient ou crée une conversation"""
        from network.services.chat import ChatService
        try:
            conv = ChatService.obtenir_ou_creer_conversation(self.user, destinataire_id)
            return conv.id
        except Exception as e:
            logger.error(f"Error in dm.init for user {self.user.id}: {str(e)}")
            return None

    async def join_all_active_rooms(self):
        """Rejoint automatiquement toutes les rooms actives de l'utilisateur"""
        # Groups
        group_ids = await self.get_user_group_ids()
        for gid in group_ids:
            await self.channel_layer.group_add(f"groupe_{gid}", self.channel_name)
            logger.debug(f"Joined group room: groupe_{gid}")

        # DM Conversations
        conv_ids = await self.get_user_conv_ids()
        for cid in conv_ids:
            await self.channel_layer.group_add(f"conv_{cid}", self.channel_name)
            logger.debug(f"Joined conv room: conv_{cid}")

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

    @database_sync_to_async
    def check_room_permission(self, room_type, room_id):
        """Vérifie les permissions pour une room"""
        from network.models import MembreGroupe, Conversation
        try:
            if room_type == "groupe":
                return MembreGroupe.objects.filter(
                    groupe_id=room_id,
                    profil_id=self.profil_id,
                    deleted=False
                ).exists()
            elif room_type == "conv":
                return Conversation.objects.filter(
                    id=room_id,
                    participants__id=self.profil_id,
                    deleted=False
                ).exists()
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
        return False