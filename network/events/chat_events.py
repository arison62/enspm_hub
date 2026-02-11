from .base import BaseEvent
from uuid import UUID
from typing import Dict, Any, Optional, List
from datetime import datetime

class ChatEvents:
    @staticmethod
    def message_envoye(
        message_id: UUID,
        conversation_id: UUID,
        message_data: Dict[str, Any]
    ) -> BaseEvent:
        return BaseEvent.create(
            event_type='MessageEnvoye',
            aggregate_id=conversation_id,
            payload={
                'message_id': str(message_id),
                'conversation_id': str(conversation_id),
                'data': message_data
            }
        )
    
    @staticmethod
    def message_lu(message_id: UUID, conversation_id: UUID, profil_id: UUID, data: Dict[str, Any]) -> BaseEvent:
        return BaseEvent.create(
            event_type='MessageLu',
            aggregate_id=conversation_id,
            payload={
                'message_id': str(message_id),
                'conversation_id': str(conversation_id),
                'profil_id': str(profil_id),
                'data': data
            }
        )
    
    @staticmethod
    def conversation_creee(conversation_id: UUID, data: Dict[str, Any]) -> BaseEvent:
        return BaseEvent.create(
            event_type='ConversationCreee',
            aggregate_id=conversation_id,
            payload={
                'conversation_id': str(conversation_id),
                'data': data
            }
        )

    # On simplifie les signatures pour qu'elles acceptent 'data'
    @staticmethod
    def message_modifie(message_id: UUID, conversation_id: UUID, data: Dict[str, Any]) -> BaseEvent:
        return BaseEvent.create(
            event_type='MessageModifie',
            aggregate_id=conversation_id,
            payload={
                'message_id': str(message_id),
                'conversation_id': str(conversation_id),
                'data': data
            }
        )
    
    @staticmethod
    def message_supprime(message_id: UUID, conversation_id: UUID, data: Dict[str, Any]) -> BaseEvent:
        return BaseEvent.create(
            event_type='MessageSupprime',
            aggregate_id=conversation_id,
            payload={
                'message_id': str(message_id),
                'conversation_id': str(conversation_id),
                'data': data
            }
        )
