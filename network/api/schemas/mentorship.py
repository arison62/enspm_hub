from datetime import datetime
from typing import List, Optional
from ninja import ModelSchema, Schema
from pydantic import UUID4, field_validator, Field
from network.models import MentorProfile
from core.api.schemas import DomaineOut, FiliereOut
from users.api.schemas import ProfilBaseOut


# ============================================
# SCHÉMAS MENTOR PROFILE
# ============================================

class MentorProfileOut(ModelSchema):
    """Schéma de sortie pour un profil mentor"""
    profil: ProfilBaseOut
    filieres_expertise: Optional[List[FiliereOut]] = None
    domaines_expertise: Optional[List[DomaineOut]] = None
    places_disponibles: int
    
    class Meta:
        model = MentorProfile
        fields = [
            'id', 'biographie', 'disponibilite',
            'nombre_max_mentees', 'est_actif', 'status',
            'nombre_demandes_recues', 'nombre_demandes_acceptees',
            'nombre_mentees_actuels',
            'created_at', 'updated_at'
        ]
    
    @staticmethod
    def resolve_places_disponibles(obj: MentorProfile) -> int:
        return obj.get_nombre_places_disponibles()


class MentorProfileCreate(Schema):
    """Schéma pour créer un profil mentor"""
    biographie: Optional[str] = None
    competences_cles: Optional[str] = None
    disponibilite: str
    nombre_max_mentees: int = 3
    filieres_expertise: Optional[List[UUID4]] = None
    domaines_expertise: Optional[List[UUID4]] = None
    
    @field_validator('nombre_max_mentees')
    @classmethod
    def validate_nombre_max(cls, v: int) -> int:
        if v < 1 or v > 10:
            raise ValueError('Le nombre maximum de mentees doit être entre 1 et 10')
        return v


class MentorProfileUpdate(Schema):
    """Schéma pour mettre à jour un profil mentor"""
    biographie: Optional[str] = None
    competences_cles: Optional[str] = None
    disponibilite: Optional[str] = None
    nombre_max_mentees: Optional[int] = None
    est_actif: Optional[bool] = None
    filieres_expertise: Optional[List[UUID4]] = None
    domaines_expertise: Optional[List[UUID4]] = None
    
    @field_validator('nombre_max_mentees')
    @classmethod
    def validate_nombre_max(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 10):
            raise ValueError('Le nombre maximum de mentees doit être entre 1 et 10')
        return v




class MentorProfileValidationOut(Schema):
    """Schéma de sortie pour une validation de profil mentor"""
    id: UUID4
    status_avant: str
    status_apres: str
    commentaire: str
    valide_par: ProfilBaseOut
    created_at: datetime


class MentorProfileValidationCreate(Schema):
    """Schéma pour valider ou refuser un profil mentor"""
    status: str
    commentaire: Optional[str] = None


# ============================================
# SCHÉMAS FILTRES
# ============================================

class MentorFilter(Schema):
    """Filtres pour la recherche de mentors"""
    filieres: Optional[List[UUID4]] = Field(None, alias="filieres[]")
    domaines: Optional[List[UUID4]] = Field(None, alias="domaines[]")
    disponible_uniquement: bool = True

