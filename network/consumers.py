import json
import logging
from uuid import UUID
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
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

        # Join all active rooms (Groups and DM Conversations)
        await self.join_all_active_rooms()

    async def disconnect(self, close_code):
        if hasattr(self, 'user_room_name'):
            await self.channel_layer.group_discard(
                self.user_room_name,
                self.channel_name
            )
        logger.info(f"WebSocket disconnected: User {self.user.id} (Code: {close_code})")

    async def receive(self, text_data):
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
            room_type = data.get("room_type") # "groupe" or "conv"
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

    async def handle_dm_init(self, destinataire_id):
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
        """Generic handler for group/conversation messages"""
        await self.send(text_data=json.dumps({
            "type": "chat.message",
            "room_type": event.get("room_type"),
            "room_id": event.get("room_id"),
            "message": event["message"]
        }))

    @database_sync_to_async
    def get_user_profil_id(self, user):
        try:
            return user.profil.id
        except ObjectDoesNotExist:
            return None

    @database_sync_to_async
    def get_or_create_conversation_id(self, destinataire_id):
        from network.services.chat import ChatService
        try:
            conv = ChatService.obtenir_ou_creer_conversation(self.user, destinataire_id)
            return conv.id
        except Exception as e:
            logger.error(f"Error in dm.init for user {self.user.id}: {str(e)}")
            return None

    async def join_all_active_rooms(self):
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
        from network.models import MembreGroupe
        return list(MembreGroupe.objects.filter(
            profil_id=self.profil_id,
            deleted=False
        ).values_list('groupe_id', flat=True))

    @database_sync_to_async
    def get_user_conv_ids(self):
        from network.models import Conversation
        return list(Conversation.objects.filter(
            participants__id=self.profil_id,
            deleted=False
        ).values_list('id', flat=True))

    @database_sync_to_async
    def check_room_permission(self, room_type, room_id):
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
