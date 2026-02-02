# network/api/schemas/chat.py
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from ninja import ModelSchema, Schema
from pydantic import field_validator, HttpUrl
from network.models import Groupe, MembreGroupe, MessageGroupe, MessageDirect
from users.api.schemas import ProfilBaseOut


# ============================================
# SCHÉMAS GROUPE
# ============================================

class GroupeOut(ModelSchema):
    """Schéma de sortie pour un groupe"""
    createur: Optional[ProfilBaseOut] = None
    nombre_membres: int
    image_url: Optional[str] = None
    
    class Meta:
        model = Groupe
        fields = [
            'id', 'nom', 'slug', 'description', 'type_acces',
            'created_at', 'updated_at'
        ]
    
    @staticmethod
    def resolve_nombre_membres(obj: Groupe) -> int:
        return obj.get_nombre_membres()
    
    @staticmethod
    def resolve_image_url(obj: Groupe) -> Optional[str]:
        return obj.image.url if obj.image else None


class GroupeCreate(Schema):
    """Schéma pour créer un groupe"""
    nom: str
    description: Optional[str] = None
    type_acces: str = 'public'
    image_base64: Optional[str] = None
    
    @field_validator('type_acces')
    @classmethod
    def validate_type_acces(cls, v: str) -> str:
        valid_types = ['public', 'prive']
        if v not in valid_types:
            raise ValueError(f'Type d\'accès invalide. Choix: {", ".join(valid_types)}')
        return v
    
    @field_validator('nom')
    @classmethod
    def validate_nom(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError('Le nom doit contenir au moins 3 caractères')
        if len(v) > 255:
            raise ValueError('Le nom ne doit pas dépasser 255 caractères')
        return v


class GroupeUpdate(Schema):
    """Schéma pour mettre à jour un groupe"""
    nom: Optional[str] = None
    description: Optional[str] = None
    type_acces: Optional[str] = None
    image_base64: Optional[str] = None
    
    @field_validator('type_acces')
    @classmethod
    def validate_type_acces(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_types = ['public', 'prive']
            if v not in valid_types:
                raise ValueError(f'Type d\'accès invalide. Choix: {", ".join(valid_types)}')
        return v

class GroupeFilter(Schema):
    """Filtres pour la recherche de groupes"""
    query: Optional[str] = None
    type_acces: Optional[str] = None


# ============================================
# SCHÉMAS MEMBRE GROUPE
# ============================================

class MembreGroupeOut(ModelSchema):
    """Schéma de sortie pour un membre de groupe"""
    profil: ProfilBaseOut
    groupe: GroupeOut
    est_admin: bool
    
    class Meta:
        model = MembreGroupe
        fields = ['id', 'role', 'date_membre', 'created_at', 'updated_at']
    
    @staticmethod
    def resolve_est_admin(obj: MembreGroupe) -> bool:
        return obj.est_admin


class MembreGroupeCreate(Schema):
    """Schéma pour ajouter un membre à un groupe"""
    groupe_id: UUID
    profil_id: UUID
    role: str = 'membre'
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = ['membre', 'admin']
        if v not in valid_roles:
            raise ValueError(f'Rôle invalide. Choix: {", ".join(valid_roles)}')
        return v


class MembreGroupeUpdate(Schema):
    """Schéma pour mettre à jour le rôle d'un membre"""
    role: str
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = ['membre', 'admin']
        if v not in valid_roles:
            raise ValueError(f'Rôle invalide. Choix: {", ".join(valid_roles)}')
        return v


# ============================================
# SCHÉMAS MESSAGE GROUPE
# ============================================

class MessageGroupeOut(ModelSchema):
    """Schéma de sortie pour un message de groupe"""
    expediteur: ProfilBaseOut
    groupe: GroupeOut
    reponse_a: Optional['MessageGroupeOut'] = None
    piece_jointe_url: Optional[str] = None
    nombre_reponses: int
    
    class Meta:
        model = MessageGroupe
        fields = [
            'id', 'contenu', 'est_lu', 'reponse_a',
            'created_at', 'updated_at'
        ]
    
    @staticmethod
    def resolve_piece_jointe_url(obj: MessageGroupe) -> Optional[str]:
        return obj.piece_jointe.url if obj.piece_jointe else None
    
    @staticmethod
    def resolve_nombre_reponses(obj: MessageGroupe) -> int:
        return obj.get_nombre_reponses()


class MessageGroupeCreate(Schema):
    """Schéma pour créer un message de groupe"""
    groupe_id: UUID
    contenu: str
    reponse_a_id: Optional[UUID] = None
    piece_jointe_base64: Optional[str] = None
    
    @field_validator('contenu')
    @classmethod
    def validate_contenu(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Le contenu ne peut pas être vide')
        if len(v) > 10000:
            raise ValueError('Le contenu ne doit pas dépasser 10000 caractères')
        return v


class MessageGroupeUpdate(Schema):
    """Schéma pour mettre à jour un message de groupe"""
    contenu: Optional[str] = None
    est_lu: Optional[bool] = None
    
    @field_validator('contenu')
    @classmethod
    def validate_contenu(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 10000:
            raise ValueError('Le contenu ne doit pas dépasser 10000 caractères')
        return v


# ============================================
# SCHÉMAS MESSAGE DIRECT
# ============================================

class MessageDirectOut(ModelSchema):
    """Schéma de sortie pour un message direct"""
    expediteur: ProfilBaseOut
    destinataire: ProfilBaseOut
    piece_jointe_url: Optional[str] = None
    
    class Meta:
        model = MessageDirect
        fields = [
            'id', 'contenu', 'est_lu',
            'created_at', 'updated_at'
        ]
    
    @staticmethod
    def resolve_piece_jointe_url(obj: MessageDirect) -> Optional[str]:
        return obj.piece_jointe.url if obj.piece_jointe else None


class MessageDirectCreate(Schema):
    """Schéma pour créer un message direct"""
    destinataire_id: UUID
    contenu: str
    piece_jointe_base64: Optional[str] = None
    
    @field_validator('contenu')
    @classmethod
    def validate_contenu(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Le contenu ne peut pas être vide')
        if len(v) > 10000:
            raise ValueError('Le contenu ne doit pas dépasser 10000 caractères')
        return v


class MessageDirectUpdate(Schema):
    """Schéma pour mettre à jour un message direct"""
    contenu: Optional[str] = None
    est_lu: Optional[bool] = None
    
    @field_validator('contenu')
    @classmethod
    def validate_contenu(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 10000:
            raise ValueError('Le contenu ne doit pas dépasser 10000 caractères')
        return v


