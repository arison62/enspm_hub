"""
Module de gestion des événements
"""
from .event_bus import Event, EventBus, event_bus
from .chat_events import (
    # Events
    MessageGroupeCreatedEvent,
    MessageGroupeUpdatedEvent,
    MessageGroupeDeletedEvent,
    MessageGroupeReadEvent,
    MessageDMCreatedEvent,
    MessageDMUpdatedEvent,
    MessageDMDeletedEvent,
    MessageDMReadEvent,
    ConversationCreatedEvent,
    ConversationReadEvent,
    GroupeCreatedEvent,
    GroupeUpdatedEvent,
    GroupeDeletedEvent,
    MembreGroupeAddedEvent,
    MembreGroupeRemovedEvent,
    GroupeReadEvent,
    # Types
    EventTypes,
)

__all__ = [
    # Core
    'Event',
    'EventBus',
    'event_bus',
    
    # Message Groupe Events
    'MessageGroupeCreatedEvent',
    'MessageGroupeUpdatedEvent',
    'MessageGroupeDeletedEvent',
    'MessageGroupeReadEvent',
    
    # Message DM Events
    'MessageDMCreatedEvent',
    'MessageDMUpdatedEvent',
    'MessageDMDeletedEvent',
    'MessageDMReadEvent',
    
    # Conversation Events
    'ConversationCreatedEvent',
    'ConversationReadEvent',
    
    # Groupe Events
    'GroupeCreatedEvent',
    'GroupeUpdatedEvent',
    'GroupeDeletedEvent',
    'MembreGroupeAddedEvent',
    'MembreGroupeRemovedEvent',
    'GroupeReadEvent',
    
    # Types
    'EventTypes',
]