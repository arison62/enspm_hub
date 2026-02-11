# chat/events.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from network.api.schemas.chat import MessageDMOut, MessageGroupeOut

class EventBus:
    
    @staticmethod
    def message_groupe_created(message):
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        async_to_sync(channel_layer.group_send)(
            f"groupe_{message.conversation.id}",
            {
                'type': 'chat.message.groupe.created',
                'message': MessageGroupeOut.from_orm(message)
            }
        )
        
    @staticmethod
    def message_dm_created(message):
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        async_to_sync(channel_layer.group_send)(
            f"conv_{message.conversation.id}",
            {
                'type': 'chat.message.dm.created',
                'message': MessageDMOut.from_orm(message)
            }
        )
        
    
    @staticmethod
    def conversation_created(conversation):
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        async_to_sync(channel_layer.group_send)(
            f"conv_{conversation.id}",
            {
                'type': 'chat.conversation.created',
                'conversation': conversation
            }
        )