from datetime import datetime
from typing import List, Optional
from ninja import ModelSchema, Schema
from pydantic import UUID4, field_validator, Field
from network.models import MentorProfile
from core.api.schemas import DomaineOut, FiliereOut, PaginationMetaSchema
from users.api.schemas import ProfilBaseOut


# ============================================
# SCHÉMAS MENTOR PROFILE
# ============================================

class MentorProfileOut(ModelSchema):
    """Schéma de sortie pour un profil mentor"""
    profil: ProfilBaseOut
    filieres_expertise: Optional[List[FiliereOut]] = None
    domaines_expertise: Optional[List[DomaineOut]] = None
    est_valide: bool
    
    class Meta:
        model = MentorProfile
        fields = [
            'id', 'biographie', 'disponibilite',
            'est_actif', 'status', 'nombre_demandes_recues',
            'created_at', 'updated_at'
        ]
    
    @staticmethod
    def resolve_est_valide(root: MentorProfile) -> bool:
        return root.status == MentorProfile.Status.VALIDE
    


class MentorProfileCreate(Schema):
    """Schéma pour créer un profil mentor"""
    biographie: Optional[str] = None
    disponibilite: Optional[int] = None
    filieres_expertise: Optional[List[UUID4]] = None
    domaines_expertise: Optional[List[UUID4]] = None
    

class MentorProfileUpdate(Schema):
    """Schéma pour mettre à jour un profil mentor"""
    biographie: Optional[str] = None
    disponibilite: Optional[int] = None
    est_actif: Optional[bool] = None
    filieres_expertise: Optional[List[UUID4]] = None
    domaines_expertise: Optional[List[UUID4]] = None
    



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

class MentorProfileListResponse(Schema):
    """Schéma de sortie pour la liste des mentors"""
    items: List[MentorProfileOut]
    meta: PaginationMetaSchema


# ============================================
# SCHÉMAS FILTRES
# ============================================

class MentorFilter(Schema):
    """Filtres pour la recherche de mentors"""
    filieres: Optional[List[UUID4]] = Field(None, alias="filieres[]")
    domaines: Optional[List[UUID4]] = Field(None, alias="domaines[]")
    search: Optional[str] = None

