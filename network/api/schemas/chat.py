from typing import List, Optional
from uuid import UUID
from datetime import datetime
from ninja import Field, ModelSchema, Schema
from pydantic import field_validator, ConfigDict
from core.api.schemas import PaginationMetaSchema
from network.models import (
    Groupe, MembreGroupe, Conversation, ConversationParticipant, Message, MessageMeta, DemandeAccesGroupe
)
from users.api.schemas import ProfilBaseOut

# ============================================
# BASE & UTILITY SCHEMAS
# ============================================

class ProfilMinimalOut(Schema):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    nom_complet: str
    photo_url: Optional[str] = None
    is_online: bool = False

    @staticmethod
    def resolve_photo_url(obj):
        if hasattr(obj, 'photo_profil') and obj.photo_profil:
            return obj.photo_profil.url
        return None

class MediaOut(Schema):
    model_config = ConfigDict(from_attributes=True)
    url: str
    type: str  # MIME type
    nom: str
    taille: int

# ============================================
# MESSAGE SCHEMAS
# ============================================

class MessageOut(ModelSchema):
    """Schéma de sortie détaillé pour un message"""
    model_config = ConfigDict(from_attributes=True)
    client_id: Optional[UUID] = None
    conversation_id: UUID
    expediteur: Optional[ProfilMinimalOut] = None
    media_url: Optional[str] = None
    media_info: Optional[MediaOut] = None
    reponse_a: Optional['MessageOut'] = None
    nombre_reponses: int = 0

    # Métadonnées utilisateur
    est_lu_par_moi: bool = False

    class Meta:
        model = Message
        fields = [
            'id', 'type', 'contenu', 'created_at', 'updated_at',
            'edited_at', 'media_type', 'media_name', 'media_size'
        ]

    @staticmethod
    def resolve_conversation_id(obj: Message) -> UUID:
        return obj.conversation_id

    @staticmethod
    def resolve_media_url(obj: Message) -> Optional[str]:
        return obj.media.url if obj.media else None

    @staticmethod
    def resolve_media_info(obj: Message):
        if not obj.media:
            return None
        return {
            'url': obj.media.url,
            'type': obj.media_type or 'application/octet-stream',
            'nom': obj.media_name or 'file',
            'taille': obj.media_size or 0
        }

    @staticmethod
    def resolve_nombre_reponses(obj: Message) -> int:
        if hasattr(obj, 'nb_reponses'):
            return obj.nb_reponses
        return obj.reponses.filter(deleted=False).count()

class MessageCreateIn(Schema):
    contenu: str
    client_id: Optional[UUID] = None
    media_base64: Optional[str] = None
    reponse_a_id: Optional[UUID] = None

class MessageListResponse(Schema):
    items: List[MessageOut]
    meta: PaginationMetaSchema

# ============================================
# CONVERSATION SCHEMAS
# ============================================

class GroupeMinimalOut(Schema):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    nom: str
    slug: str
    image_url: Optional[str] = None
    conversation_id: Optional[UUID]

    @staticmethod
    def resolve_image_url(obj):
        return obj.image.url if obj.image else None
    
    @staticmethod
    def resolve_conversation_id(obj):
        if hasattr(obj, 'conversation'):
            return obj.conversation.id
        return None

class ConversationOut(ModelSchema):
    """Schéma de sortie pour une conversation"""
    model_config = ConfigDict(from_attributes=True)
    groupe: Optional[GroupeMinimalOut] = None
    contact: Optional[ProfilMinimalOut] = None
    dernier_message: Optional[MessageOut] = None
    messages_non_lus: int = 0
    role: Optional[str] = None
    contact: Optional[ProfilMinimalOut] = None
    est_ferme: bool

    @staticmethod
    def resolve_est_ferme(obj: Conversation):
        if obj.type == Conversation.ConversationType.GROUP and obj.groupe:
            return obj.groupe.est_ferme
        return False
    
    class Meta:
        model = Conversation
        fields = ['id', 'type', 'created_at', 'updated_at']
        
class ConversationListResponse(Schema):
    items: List[ConversationOut]
    meta: PaginationMetaSchema

# ============================================
# GROUPE SCHEMAS
# ============================================

class GroupeOut(ModelSchema):
    model_config = ConfigDict(from_attributes=True)
    createur: Optional[ProfilBaseOut] = None
    nombre_membres: int
    image_url: Optional[str] = None
    is_member: bool = False
    is_admin: bool = False
    pending_request: Optional[int] = None
    has_user_pending_request: bool = False
    conversation_id: Optional[UUID] = None
    est_actif: bool
    

    class Meta:
        model = Groupe
        fields = [
            'id', 'nom', 'slug', 'description', 'type_acces',
            'created_at', 'updated_at', 'status', 'est_ferme'
        ]

    @staticmethod
    def resolve_nombre_membres(obj: Groupe) -> int:
        if hasattr(obj, 'nb_members'):
            return obj.nb_members
        return obj.get_nombre_membres()

    @staticmethod
    def resolve_image_url(obj: Groupe) -> Optional[str]:
        return obj.image.url if obj.image else None

    @staticmethod
    def resolve_conversation_id(obj: Groupe) -> Optional[UUID]:
        if hasattr(obj, 'conversation'):
            return obj.conversation.id
        return None
    
    @staticmethod
    def resolve_est_actif(obj: Groupe) -> bool:
        return obj.status == 'actif'

class GroupeCreate(Schema):
    nom: str
    description: Optional[str] = None
    type_acces: str = 'public'
    image_base64: Optional[str] = None

class GroupeUpdate(Schema):
    nom: Optional[str] = None
    description: Optional[str] = None
    type_acces: Optional[str] = None
    image_base64: Optional[str] = None
    status: Optional[str] = None
    est_ferme: Optional[bool] = None

class GroupeListResponse(Schema):
    items: List[GroupeOut]
    meta: PaginationMetaSchema

class GroupeFilter(Schema):
    query: Optional[str] = None
    type_acces: Optional[str] = None

class MembreGroupeOut(ModelSchema):
    model_config = ConfigDict(from_attributes=True)
    profil: ProfilBaseOut
    est_admin: bool

    class Meta:
        model = MembreGroupe
        fields = ['id', 'role', 'date_membre', 'created_at']

    @staticmethod
    def resolve_est_admin(obj: MembreGroupe) -> bool:
        return obj.role == MembreGroupe.Role.ADMIN

class MembreGroupeCreate(Schema):
    profil_id: UUID
    role: str = 'membre'

class MembreGroupeUpdate(Schema):
    role: str

class MembreGroupeListResponse(Schema):
    items: List[MembreGroupeOut]
    meta: PaginationMetaSchema

class MembreGroupeRequest(ModelSchema):
    model_config = ConfigDict(from_attributes=True)
    demandeur: ProfilBaseOut

    class Meta:
        model = DemandeAccesGroupe
        fields = ['id', 'message', 'status', 'created_at']

class MembreGroupeRequestListResponse(Schema):
    items: List[MembreGroupeRequest]
    meta: PaginationMetaSchema
