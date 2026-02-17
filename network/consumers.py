import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from network.models.chat import ConversationParticipant

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket passif.
    Reçoit des messages du Channel Layer et les diffuse au client.
    Le client n'envoie JAMAIS de messages métier via WebSocket.
    """
    
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.profil = await self._get_user_profil()
        if not self.profil:
            await self.close()
            return

        # Rejoindre son propre canal pour les notifications personnelles
        self.user_group_name = f"user_{self.profil.id}"
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)

        # Rejoindre les groupes de toutes ses conversations
        await self._join_all_conversations()

        await self.accept()
        logger.info(f"WebSocket connected for user {self.user.id}")

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(self.user_group_name, self.channel_name)
        
        # En théorie, on devrait aussi quitter tous les groupes de conversation
        # mais Channels le fait automatiquement à la déconnexion si on ne le fait pas.
        logger.info(f"WebSocket disconnected for user {self.user.id} (code: {close_code})")

    async def receive(self, text_data):
        """
        ZÉRO logique métier ici.
        On peut éventuellement gérer des pings ou des commandes de présence.
        """
        try:
            data = json.loads(text_data)
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except Exception:
            pass

    # ============================================
    # HANDLERS CHANNEL LAYER
    # ============================================

    async def chat_message(self, event):
        """
        Reçoit un message du Channel Layer et l'envoie au client via WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': event.get('event_type'),
            'payload': event.get('payload'),
            'timestamp': event.get('timestamp')
        }))

    async def join_room(self, event):
        """
        Commande interne pour rejoindre un nouveau groupe sans reconnexion.
        Utile quand l'utilisateur est ajouté à un nouveau groupe/conversation.
        """
        room_name = event.get('room_name')
        if room_name:
            await self.channel_layer.group_add(room_name, self.channel_name)
            logger.info(f"User {self.user.id} joined room {room_name} via internal command")

    # ============================================
    # MÉTHODES UTILITAIRES
    # ============================================

    @database_sync_to_async
    def _get_user_profil(self):
        try:
            return self.user.profil
        except Exception:
            return None

    @database_sync_to_async
    def _join_all_conversations(self):
        conv_ids = ConversationParticipant.objects.filter(
            profil=self.profil,
            deleted=False
        ).values_list('conversation_id', flat=True)
        return list(conv_ids)

    async def _join_all_conversations(self):
        conv_ids = await self._get_conv_ids()
        for cid in conv_ids:
            group_name = f"conv_{cid}"
            await self.channel_layer.group_add(group_name, self.channel_name)

    @database_sync_to_async
    def _get_conv_ids(self):
        return list(ConversationParticipant.objects.filter(
            profil=self.profil,
            deleted=False
        ).values_list('conversation_id', flat=True))
