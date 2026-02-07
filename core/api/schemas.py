# core/api/schemas.py
from ninja import Field, ModelSchema, Schema
from typing import Dict, Optional, List, Literal
from pydantic import EmailStr, field_validator
from phonenumber_field.phonenumber import PhoneNumber
from uuid import UUID
from datetime import datetime
from core.models import (
    User, AuditLog,
    AnneePromotion, Domaine, Filiere, SecteurActivite,
    Devise, TitreHonorifique, ReseauSocial
)


# ==========================================
# 1. Schémas d'authentification
# ==========================================


class LoginSchema(Schema):
    """Schéma d'entrée pour l'authentification (email uniquement)"""
    email: str = Field(..., description="Adresse email de l'utilisateur")
    password: str = Field(..., description="Mot de passe")


class TokenSchema(Schema):
    """Schéma de sortie après connexion réussie"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    user: "UserOut"


class RefreshTokenSchema(Schema):
    """Schéma pour rafraîchir le token"""
    refresh: str

class PasswordResetRequest(Schema):
    """Schéma pour la demande de réinitialisation de mot de passe"""
    user_id: str = Field(..., description="Email ou numéro de téléphone de l'utilisateur")
    method: Literal["email", "sms"] = Field("email", description="Méthode d'envoi du token (email ou sms)")

class PasswordResetConfirm(Schema):
    user_id: str = Field(..., description="Email ou numéro de téléphone de l'utilisateur")
    token: str = Field(..., description="Token de réinitialisation reçu")
    new_password: str = Field(..., description="Nouveau mot de passe souhaité")


class PaginationMetaSchema(Schema):
    """Métadonnées de pagination"""
    page: int
    page_size: int
    total_items: int
    total_pages: int

# ==========================================
# SCHÉMAS POUR User
# ==========================================

class UserOut(ModelSchema):
    telephone: Optional[str] = None
    class Meta:
        model = User
        fields = ['id', 'email', 'role_systeme', 
                  'last_login', 'est_actif', 'telephone', 
                  'is_staff', 'created_at', 
                  'updated_at', 'deleted', 'deleted_at'
                ]
        # Excluded sensitive fields like mot_de_passe, groups, user_permissions

    @staticmethod
    def resolve_telephone(obj):
        return str(obj.telephone) if obj.telephone else None
    
class UserCreate(Schema):
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    password: Optional[str] = None  # For create_user with or without password
    role_systeme: str = 'user'
    est_actif: bool = True
    is_staff: bool = False

    @field_validator('role_systeme')
    def validate_role(cls, v):
        if v not in [choice[0] for choice in User.ROLE_SYSTEME_CHOICES]:
            raise ValueError('Invalid role')
        return v
    
    @field_validator('telephone')
    def validate_telephone(cls, v):
        if v:
            phone = PhoneNumber.from_string(v, region='CM')  # 'CM' pour Cameroun
            if not phone.is_valid():
                raise ValueError("Numéro de téléphone invalide")
            return str(phone)
        return v
        

class UserUpdate(ModelSchema):
    class Meta:
        model = User
        fields = ['email', 'role_systeme', 'est_actif', 'is_staff']
        fields_optional = '__all__'
        # Password update should be handled separately, not included here for security

# ==========================================
# SCHÉMAS POUR AuditLog
# ==========================================

class AuditLogOut(ModelSchema):
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'entity_type', 'entity_id', 'old_values', 'new_values', 'ip_address', 'user_agent', 'created_at', 'updated_at']
        # AuditLog is typically read-only, no create/update schemas needed for API exposure


# ==========================================
# SCHÉMAS DE BASE (Sans relations)
# ==========================================

class AnneePromotionOut(ModelSchema):
    """Schéma de sortie pour AnneePromotion"""
    class Meta:
        model = AnneePromotion
        fields = ['id', 'annee', 'libelle', 'description', 'est_active', 'ordre_affichage']


class DomaineOut(ModelSchema):
    """Schéma de sortie pour Domaine"""
    class Meta:
        model = Domaine
        fields = ['id', 'nom', 'code', 'description', 'categorie', 'est_actif', 'ordre_affichage']


class FiliereOut(ModelSchema):
    """Schéma de sortie pour Filiere (sans domaine complet)"""
    domaine_id: UUID
    domaine_nom: str
    domaine_code: str
    
    class Meta:
        model = Filiere
        fields = ['id', 'nom', 'code', 'description', 'niveau', 'duree_annees', 'est_actif', 'ordre_affichage']
    
    @staticmethod
    def resolve_domaine_id(obj):
        return obj.domaine.id
    
    @staticmethod
    def resolve_domaine_nom(obj):
        return obj.domaine.nom
    
    @staticmethod
    def resolve_domaine_code(obj):
        return obj.domaine.code


class SecteurActiviteOut(ModelSchema):
    """Schéma de sortie pour SecteurActivite"""
    parent_id: Optional[UUID] = None
    parent_nom: Optional[str] = None
    nom_complet: str
    
    class Meta:
        model = SecteurActivite
        fields = ['id', 'nom', 'code', 'description', 'icone', 'est_actif', 'ordre_affichage']
    
    @staticmethod
    def resolve_parent_id(obj):
        return obj.categorie_parent.id if obj.categorie_parent else None
    
    @staticmethod
    def resolve_parent_nom(obj):
        return obj.categorie_parent.nom if obj.categorie_parent else None
    
    @staticmethod
    def resolve_nom_complet(obj):
        return obj.nom_complet




class DeviseOut(ModelSchema):
    """Schéma de sortie pour Devise"""
    class Meta:
        model = Devise
        fields = ['id', 'code', 'nom', 'symbole', 'taux_change_usd', 'date_mise_a_jour_taux', 'est_active', 'ordre_affichage']


class TitreHonorifiqueOut(ModelSchema):
    """Schéma de sortie pour TitreHonorifique"""
    class Meta:
        model = TitreHonorifique
        fields = ['id', 'titre', 'nom_complet', 'type_titre', 'description', 'est_actif', 'ordre_affichage']


class ReseauSocialOut(ModelSchema):
    """Schéma de sortie pour ReseauSocial"""
    class Meta:
        model = ReseauSocial
        fields = [
            'id', 'nom', 'code', 'url_base', 'type_reseau',
            'pattern_validation', 'placeholder_exemple', 'est_actif', 'ordre_affichage'
        ]


# ==========================================
# SCHÉMAS SIMPLIFIÉS (Pour intégration dans d'autres schémas)
# ==========================================

class AnneePromotionSimple(Schema):
    """Version simplifiée pour intégration dans ProfilOut"""
    id: UUID
    annee: int
    libelle: str


class DomaineSimple(Schema):
    """Version simplifiée pour intégration dans ProfilOut"""
    id: UUID
    nom: str
    code: str


class FiliereSimple(Schema):
    """Version simplifiée"""
    id: UUID
    nom: str
    code: str
    niveau: str


class SecteurActiviteSimple(Schema):
    """Version simplifiée pour intégration dans OrganisationOut"""
    id: UUID
    nom: str
    code: str





class DeviseSimple(Schema):
    """Version simplifiée pour intégration dans EmploiOut/FormationOut"""
    id: UUID
    code: str
    symbole: str


class TitreHonorifiqueSimple(Schema):
    """Version simplifiée pour intégration dans ProfilOut"""
    id: UUID
    titre: str
    nom_complet: str


class ReseauSocialSimple(Schema):
    """Version simplifiée pour intégration dans LienReseauSocialOut"""
    id: UUID
    nom: str
    code: str
    url_base: str


# ==========================================
# SCHÉMAS COMPLETS (Avec relations)
# ==========================================

class DomaineComplete(ModelSchema):
    """Domaine avec ses filières"""
    filieres: List[FiliereOut]
    
    class Meta:
        model = Domaine
        fields = ['id', 'nom', 'code', 'description', 'categorie', 'est_actif']
    
    @staticmethod
    def resolve_filieres(obj):
        return list(obj.filieres.filter(est_actif=True).order_by('ordre_affichage'))


class SecteurActiviteComplete(ModelSchema):
    """Secteur avec ses sous-secteurs"""
    sous_secteurs: List[SecteurActiviteOut]
    
    class Meta:
        model = SecteurActivite
        fields = ['id', 'nom', 'code', 'description', 'est_actif']
    
    @staticmethod
    def resolve_sous_secteurs(obj):
        return list(obj.sous_secteurs.filter(est_actif=True).order_by('ordre_affichage'))


# ==========================================
# SCHÉMAS DE RÉPONSE GROUPÉS
# ==========================================

class ReferencesAcademiquesOut(Schema):
    """Toutes les références académiques en un seul appel"""
    annees_promotion: List[AnneePromotionOut]
    domaines: List[DomaineOut]
    titres: List[TitreHonorifiqueOut]


class ReferencesProfessionnellesOut(Schema):
    """Toutes les références professionnelles en un seul appel"""
    secteurs: List[SecteurActiviteOut]


class ReferencesFinancieresOut(Schema):
    """Toutes les références financières"""
    devises: List[DeviseOut]


class ReferencesReseauxOut(Schema):
    """Tous les réseaux sociaux"""
    reseaux: List[ReseauSocialOut]

class CountrieOut(Schema):
    name: str
    code: str

class AllReferencesOut(Schema):
    """TOUTES les références en un seul appel"""
    annees_promotion: List[AnneePromotionOut]
    domaines: List[DomaineOut]
    filieres: List[FiliereOut]
    secteurs: List[SecteurActiviteOut]
    devises: List[DeviseOut]
    titres: List[TitreHonorifiqueOut]
    reseaux: List[ReseauSocialOut]
    pays: List[CountrieOut]


class ErrorAPIResponse(Schema):
    """Schéma de réponse standard pour les erreurs API"""
    detail: str
    error_code: str
    error_message: str
    errors: Optional[List[Dict[str, str]]]