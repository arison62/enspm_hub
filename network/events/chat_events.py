"""
Définition des événements du système de messagerie
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from .event_bus import Event


# ============================================
# ÉVÉNEMENTS MESSAGES GROUPE
# ============================================

@dataclass
class MessageGroupeCreatedEvent(Event):
    """Événement émis quand un message de groupe est créé"""
    message_id: UUID
    groupe_id: UUID
    expediteur_id: UUID
    contenu: str
    reponse_a_id: Optional[UUID] = None
    piece_jointe_url: Optional[str] = None
    message_data: Optional[Dict[str, Any]] = None  # Données sérialisées du message


@dataclass
class MessageGroupeUpdatedEvent(Event):
    """Événement émis quand un message de groupe est modifié"""
    message_id: UUID
    groupe_id: UUID
    expediteur_id: UUID
    updated_fields: Dict[str, Any]
   


@dataclass
class MessageGroupeDeletedEvent(Event):
    """Événement émis quand un message de groupe est supprimé"""
    message_id: UUID
    groupe_id: UUID
    expediteur_id: UUID
    


@dataclass
class MessageGroupeReadEvent(Event):
    """Événement émis quand un message de groupe est marqué comme lu"""
    message_id: UUID
    groupe_id: UUID
    reader_id: UUID  # ID du profil qui a lu
   


# ============================================
# ÉVÉNEMENTS MESSAGES DM
# ============================================

@dataclass
class MessageDMCreatedEvent(Event):
    """Événement émis quand un message DM est créé"""
    message_id: UUID
    conversation_id: UUID
    expediteur_id: UUID
    contenu: str
    piece_jointe_url: Optional[str] = None
    message_data: Optional[Dict[str, Any]] = None  # Données sérialisées du message
   

@dataclass
class MessageDMUpdatedEvent(Event):
    """Événement émis quand un message DM est modifié"""
    message_id: UUID
    conversation_id: UUID
    expediteur_id: UUID
    updated_fields: Dict[str, Any]
    


@dataclass
class MessageDMDeletedEvent(Event):
    """Événement émis quand un message DM est supprimé"""
    message_id: UUID
    conversation_id: UUID
    expediteur_id: UUID
  

@dataclass
class MessageDMReadEvent(Event):
    """Événement émis quand un message DM est marqué comme lu"""
    message_id: UUID
    conversation_id: UUID
    reader_id: UUID
   


# ============================================
# ÉVÉNEMENTS CONVERSATION
# ============================================

@dataclass
class ConversationCreatedEvent(Event):
    """Événement émis quand une conversation est créée"""
    conversation_id: UUID
    participant_ids: list[UUID]
   
@dataclass
class ConversationReadEvent(Event):
    """Événement émis quand une conversation est marquée comme lue"""
    conversation_id: UUID
    profil_id: UUID
  

# ============================================
# ÉVÉNEMENTS GROUPE
# ============================================

@dataclass
class GroupeCreatedEvent(Event):
    """Événement émis quand un groupe est créé"""
    groupe_id: UUID
    createur_id: UUID
    nom: str
   

@dataclass
class GroupeUpdatedEvent(Event):
    """Événement émis quand un groupe est modifié"""
    groupe_id: UUID
    updated_fields: Dict[str, Any]
    


@dataclass
class GroupeDeletedEvent(Event):
    """Événement émis quand un groupe est supprimé"""
    groupe_id: UUID
    

@dataclass
class MembreGroupeAddedEvent(Event):
    """Événement émis quand un membre rejoint un groupe"""
    groupe_id: UUID
    profil_id: UUID
    role: str
   

@dataclass
class MembreGroupeRemovedEvent(Event):
    """Événement émis quand un membre quitte un groupe"""
    groupe_id: UUID
    profil_id: UUID
    
@dataclass
class GroupeReadEvent(Event):
    """Événement émis quand un groupe est marqué comme lu"""
    groupe_id: UUID
    profil_id: UUID
   

# ============================================
# TYPES D'ÉVÉNEMENTS (constantes)
# ============================================

class EventTypes:
    """Constantes pour les types d'événements"""
    
    # Messages Groupe
    MESSAGE_GROUPE_CREATED = "message.groupe.created"
    MESSAGE_GROUPE_UPDATED = "message.groupe.updated"
    MESSAGE_GROUPE_DELETED = "message.groupe.deleted"
    MESSAGE_GROUPE_READ = "message.groupe.read"
    
    # Messages DM
    MESSAGE_DM_CREATED = "message.dm.created"
    MESSAGE_DM_UPDATED = "message.dm.updated"
    MESSAGE_DM_DELETED = "message.dm.deleted"
    MESSAGE_DM_READ = "message.dm.read"
    
    # Conversations
    CONVERSATION_CREATED = "conversation.created"
    CONVERSATION_READ = "conversation.read"
    
    # Groupes
    GROUPE_CREATED = "groupe.created"
    GROUPE_UPDATED = "groupe.updated"
    GROUPE_DELETED = "groupe.deleted"
    MEMBRE_GROUPE_ADDED = "membre.groupe.added"
    MEMBRE_GROUPE_REMOVED = "membre.groupe.removed"
    GROUPE_READ = "groupe.read"