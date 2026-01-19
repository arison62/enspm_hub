# opportunities/api/schemas.py
from ninja.schema import Schema
from ninja import Field, ModelSchema
from typing import Optional, List
from datetime import date
from decimal import Decimal
from pydantic import UUID4

from core.api.schemas import DeviseSimple
from users.api.schemas import ProfilBaseOut, PaginationMetaSchema
from organizations.api.schemas import OrganisationOut
from opportunities.models import Stage, Emploi, Formation


# ==========================================
# SCHÉMAS PARTAGÉS / UTILS
# ==========================================

class BaseOpportunityOut(Schema):
    """Mixins pour les champs résolus communs (Pays)"""
    pays: Optional[str] = None
    pays_nom: Optional[str] = None

    @staticmethod
    def resolve_pays(obj):
        return obj.pays.code if obj.pays else None
    
    @staticmethod
    def resolve_pays_nom(obj):
        return obj.pays.name if obj.pays else None


# ==========================================
# SCHÉMAS STAGE
# ==========================================

class StageOut(ModelSchema, BaseOpportunityOut):
    createur_profil: Optional[ProfilBaseOut] = None
    organisation: Optional[OrganisationOut] = None
    validateur_profil: Optional[ProfilBaseOut] = None

    class Meta:
        model = Stage
        fields = [
            'id', 'titre', 'slug', 'nom_structure', 'description', 'type_stage',
            'adresse', 'ville', 'email_contact', 'telephone_contact',
            'lien_offre_original', 'lien_candidature', 'date_debut', 'date_fin',
            'date_publication', 'statut', 'est_valide', 'date_validation',
            'commentaire_validation', 'created_at', 'updated_at'
        ]


class StageCreate(Schema):
    titre: str
    nom_structure: str
    description: str
    type_stage: str # 'ouvrier', 'academique', 'professionnel'
    adresse: str
    ville: Optional[str] = None
    pays: Optional[str] = None # Code pays ISO
    email_contact: Optional[str] = None
    telephone_contact: Optional[str] = None
    lien_offre_original: Optional[str] = None
    lien_candidature: Optional[str] = None
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None


class StageUpdate(Schema):
    titre: Optional[str] = None
    nom_structure: Optional[str] = None
    description: Optional[str] = None
    type_stage: Optional[str] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    pays: Optional[str] = None
    email_contact: Optional[str] = None
    telephone_contact: Optional[str] = None
    lien_offre_original: Optional[str] = None
    lien_candidature: Optional[str] = None
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None

    slug: Optional[str] = None


class StageFilter(Schema):
    """Filtres pour recherche de stages"""
    search: Optional[str] = None
    type_stage: Optional[List[str]] = Field(None, description="Type de stage")
    lieu: Optional[str] = None
    statut: Optional[str] | Optional[List[str]] = None 


class StageListResponse(Schema):
    """Réponse paginée pour liste de stages"""
    items: List[StageOut]
    meta: PaginationMetaSchema


class StageValidation(Schema):
    """Schéma pour validation d'un stage"""
    approved: bool
    commentaire: Optional[str] = None


class StageStatusUpdate(Schema):
    """Schéma pour mise à jour du statut"""
    statut: str


class StageStats(Schema):
    """Statistiques des stages"""
    total_stages: int
    active_stages: int
    pending_stages: int
    expired_stages: int
    pourvue_stages: int
    by_type: dict

# ==========================================
# SCHÉMAS EMPLOI
# ==========================================

class EmploiOut(ModelSchema, BaseOpportunityOut):
    createur_profil: Optional[ProfilBaseOut] = None
    organisation: Optional[OrganisationOut] = None
    validateur_profil: Optional[ProfilBaseOut] = None
    devise: Optional[DeviseSimple] = None

    class Meta:
        model = Emploi
        fields = [
            'id', 'titre', 'slug', 'nom_structure', 'description', 'type_emploi',
            'adresse', 'ville', 'email_contact', 'telephone_contact',
            'lien_offre_original', 'lien_candidature', 'date_publication',
            'date_expiration', 'salaire_min', 'salaire_max',
            'statut', 'est_valide', 'date_validation', 'commentaire_validation',
            'created_at', 'updated_at'
        ]


class EmploiCreate(Schema):
    titre: str
    nom_structure: str
    description: str
    type_emploi: str
    adresse: str
    ville: Optional[str] = None
    pays: Optional[str] = None
    email_contact: Optional[str] = None
    telephone_contact: Optional[str] = None
    lien_offre_original: Optional[str] = None
    lien_candidature: Optional[str] = None
    date_expiration: Optional[date] = None
    salaire_min: Optional[Decimal] = None
    salaire_max: Optional[Decimal] = None
    devise_id: Optional[UUID4] = None # Liaison via ID


class EmploiUpdate(Schema):
    titre: Optional[str] = None
    nom_structure: Optional[str] = None
    description: Optional[str] = None
    type_emploi: Optional[str] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    pays: Optional[str] = None
    email_contact: Optional[str] = None
    telephone_contact: Optional[str] = None
    lien_offre_original: Optional[str] = None
    lien_candidature: Optional[str] = None
    date_expiration: Optional[date] = None
    salaire_min: Optional[Decimal] = None
    salaire_max: Optional[Decimal] = None
    devise_id: Optional[UUID4] = None

class EmploiFilter(Schema):
    """Filtres pour recherche d'emplois"""
    search: Optional[str] = None
    lieu: Optional[str] = None
    type_emploi: Optional[List[str]] = Field(None, description="Type d'emploi")
    pays: Optional[str] = None
    statut: Optional[str] | Optional[List[str]] = None 



class EmploiListResponse(Schema):
    """Réponse paginée pour liste d'emplois"""
    items: List[EmploiOut]
    meta: PaginationMetaSchema


class EmploiValidation(Schema):
    """Schéma pour validation d'un emploi"""
    approved: bool
    commentaire: Optional[str] = None


class EmploiStatusUpdate(Schema):
    """Schéma pour mise à jour du statut"""
    statut: str


class EmploiStats(Schema):
    """Statistiques des emplois"""
    total_emplois: int
    active_emplois: int
    pending_emplois: int
    by_type: dict

# ==========================================
# SCHÉMAS FORMATION
# ==========================================

class FormationOut(ModelSchema, BaseOpportunityOut):
    createur_profil: Optional[ProfilBaseOut] = None
    organisation: Optional[OrganisationOut] = None
    validateur_profil: Optional[ProfilBaseOut] = None
    devise: Optional[DeviseSimple] = None

    class Meta:
        model = Formation
        fields = [
            'id', 'titre', 'slug', 'nom_structure', 'description', 'type_formation',
            'adresse', 'ville', 'email_contact', 'telephone_contact',
            'lien_formation', 'lien_inscription', 'date_debut', 'date_fin',
            'date_publication', 'est_payante', 'prix', 'duree_heures',
            'statut', 'est_valide', 'date_validation', 'commentaire_validation',
            'created_at', 'updated_at'
        ]


class FormationCreate(Schema):
    titre: str
    nom_structure: str
    description: str
    type_formation: str # 'en_ligne', 'presentiel', 'hybride'
    adresse: Optional[str] = None
    ville: Optional[str] = None
    pays: Optional[str] = None
    email_contact: Optional[str] = None
    telephone_contact: Optional[str] = None
    lien_formation: Optional[str] = None
    lien_inscription: Optional[str] = None
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    est_payante: bool = False
    prix: Optional[Decimal] = None
    devise_id: Optional[UUID4] = None
    duree_heures: Optional[int] = None


class FormationUpdate(Schema):
    titre: Optional[str] = None
    nom_structure: Optional[str] = None
    description: Optional[str] = None
    type_formation: Optional[str] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    pays: Optional[str] = None
    email_contact: Optional[str] = None
    telephone_contact: Optional[str] = None
    lien_formation: Optional[str] = None
    lien_inscription: Optional[str] = None
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    est_payante: Optional[bool] = None
    prix: Optional[Decimal] = None
    devise_id: Optional[UUID4] = None
    duree_heures: Optional[int] = None

class FormationFilter(Schema):
    """Filtres pour recherche de formations"""
    search: Optional[str] = None
    lieu: Optional[str] = None
    type_formation: Optional[List[str]] = Field(None, description="Type de formation")
    est_payante: Optional[List[bool]] = Field(None, description="Est payante")
    statut: Optional[str] | Optional[List[str]] = None  



class FormationListResponse(Schema):
    """Réponse paginée pour liste de formations"""
    items: List[FormationOut]
    meta: PaginationMetaSchema


class FormationValidation(Schema):
    """Schéma pour validation d'une formation"""
    approved: bool
    commentaire: Optional[str] = None


class FormationStatusUpdate(Schema):
    """Schéma pour mise à jour du statut"""
    statut: str


class FormationStats(Schema):
    """Statistiques des formations"""
    total_formations: int
    active_formations: int
    pending_formations: int
    by_type: dict
    gratuites: int
    payantes: int