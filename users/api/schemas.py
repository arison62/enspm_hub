# users/api/schemas.py
from typing import Annotated, Dict, Literal, Optional, List
from ninja import Schema, Field, ModelSchema
from phonenumber_field.phonenumber import PhoneNumber
from pydantic import UUID4, EmailStr, field_validator, model_validator
from datetime import datetime
from core.models import User
from core.utils.date_formatters import format_linkedin_duration
from users.models import ExperienceProfessionnelle, Profil, LienReseauSocialProfil
from core.api.schemas import PaginationMetaSchema
from core.api.schemas import (
    AnneePromotionSimple, DomaineSimple, TitreHonorifiqueSimple,
    ReseauSocialSimple
)

# ==========================================
# SCHÉMAS EXPÉRIENCE PROFESSIONNELLE
# ==========================================

class ExperienceProfessionnelleOut(ModelSchema):
    """Schéma de sortie pour une expérience professionnelle"""
    duree_texte: Optional[str] = None

    
    class Meta:
        model = ExperienceProfessionnelle
        fields = [
            'id', 'titre_poste', 'nom_entreprise', 'lieu', 
            'date_debut', 'date_fin', 'est_poste_actuel', 
            'description', 'created_at'
        ]

    @staticmethod
    def resolve_duree_text(obj):
        """Affiche la durée de l'experience en texte"""
        return format_linkedin_duration(obj.date_debut, obj.date_fin)
    
class ExperienceProfessionnelleCreate(Schema):
    """Schéma pour ajouter une expérience"""
    titre_poste: str = Field(..., max_length=255)
    nom_entreprise: str = Field(..., max_length=255)
    lieu: Optional[str] = None
    date_debut: datetime
    date_fin: Optional[datetime] = None
    est_poste_actuel: bool = False
    description: Optional[str] = None

class ExperienceProfessionnelleUpdate(Schema):
    """Schéma pour modifier une expérience (tout est optionnel)"""
    titre_poste: Optional[str] = None
    nom_entreprise: Optional[str] = None
    lieu: Optional[str] = None
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None
    est_poste_actuel: Optional[bool] = None
    description: Optional[str] = None


# ==========================================
# MISES À JOUR DES SCHÉMAS EXISTANTS
# ==========================================



class ProfilBaseOut(ModelSchema):
    """Schéma de base pour Profil (sans réseaux sociaux)"""
    photo_profil: Optional[str] = None
    titre : Optional[TitreHonorifiqueSimple] = None
    domaine : Optional[DomaineSimple] = None
    pays : Optional[str]
    pays_nom : Optional[str]
    annee_sortie : Optional[AnneePromotionSimple] = None
    est_en_poste : bool = False

    class Meta:
        model = Profil
        fields = [
            'id', 'nom_complet', 'matricule', 'titre', 'statut_global',
            'annee_sortie', 'adresse', 'telephone', 'ville', 'pays', 'domaine', 'bio',
            'slug', 'created_at', 'updated_at'
        ]

    @staticmethod
    def resolve_photo_profil(obj):
        return obj.photo_profil.url if obj.photo_profil else None
    
    @staticmethod
    def resolve_titre(obj):
        """Retourne l'objet TitreHonorifique complet"""
        if obj.titre:
            return {
                "id": obj.titre.id,
                "titre": obj.titre.titre,
                "nom_complet": obj.titre.nom_complet
            }
        return None
    
    @staticmethod
    def resolve_domaine(obj):
        """Retourne l'objet Domaine complet"""
        if obj.domaine:
            return {
                "id": obj.domaine.id,
                "nom": obj.domaine.nom,
                "code": obj.domaine.code
            }
        return None
    
    @staticmethod
    def resolve_annee_sortie(obj):
        """Retourne l'objet AnneePromotion complet"""
        if obj.annee_sortie:
            return {
                "id": obj.annee_sortie.id,
                "annee": obj.annee_sortie.annee,
                "libelle": obj.annee_sortie.libelle
            }
        return None
    
    @staticmethod
    def resolve_pays(obj):
        """Retourne le code ISO du pays"""
        return obj.pays.code if obj.pays else None
    
    @staticmethod
    def resolve_pays_nom(obj):
        """Retourne le nom du pays"""
        return obj.pays.name if obj.pays else None
    
    @staticmethod
    def resolve_est_en_poste(obj):
        """Déduit si l'utilisateur travaille actuellement"""
        return obj.experiences.filter(est_poste_actuel=True).exists()


class ProfilCompleteOut(ProfilBaseOut):
    """Schéma complet enrichi avec réseaux sociaux ET expériences"""
    liens_reseaux: List['LienReseauSocialOut'] = []
    experiences: List[ExperienceProfessionnelleOut] = []
    est_en_poste: bool = False

    @staticmethod
    def resolve_liens_reseaux(obj):
        return list(obj.liens_reseaux.filter(est_actif=True).select_related('reseau'))

    @staticmethod
    def resolve_experiences(obj):
        """Retourne les expériences triées par date de début décroissante"""
        return list(obj.experiences.all().order_by('-date_debut'))



# ==========================================
# SCHÉMAS CRÉATION/MISE À JOUR PROFIL
# ==========================================
# Pas de redondance: Un pour create (requis), un pour update (optionnel).

class ProfilCreate(Schema):
    """Schéma pour création Profil (champs requis/minimaux)"""
    nom_complet: Optional[str] = Field(None, description="Nom complet")
    matricule: Optional[str] = None
    titre_id: Optional[UUID4] = None  # FK vers TitreHonorifique
    statut_global: str = 'etudiant'
    annee_sortie_id: Optional[UUID4] = None  # FK vers AnneePromotion
    adresse: Optional[str] = Field(None, description="Adresse", max_length=255)
    telephone: Optional[str] = Field(None, description="N° de tél.", max_length=20)
    ville: Optional[str] = Field(None, description="Ville", max_length=100)
    pays: Optional[str] = None  # Code pays ISO
    domaine_id: Optional[UUID4] = None  # FK vers Domaine
    bio: Optional[str] = None

    @field_validator('statut_global')
    def validate_statut(cls, v):
        if v not in [choice[0] for choice in Profil.STATUT_GLOBAL_CHOICES]:
            raise ValueError('Statut global invalide')
        return v

class ProfilUpdate(ModelSchema):
    """Schéma pour mise à jour partielle Profil"""
    titre_id: Optional[str] = None  # FK vers TitreHonorifique
    annee_sortie_id: Optional[str] = None  # FK vers AnneePromotion
    domaine_id:Optional[str] = None
    class Meta:
        model = Profil
        fields = [
            'nom_complet', 'matricule', 'statut_global',
             'adresse', 'telephone', 'ville', 'pays', 'bio'
        ]
        fields_optional = '__all__'

    @field_validator('statut_global', check_fields=False)
    def validate_statut(cls, v):
        if v not in [choice[0] for choice in Profil.STATUT_GLOBAL_CHOICES]:
            raise ValueError('Statut global invalide')
        return v


# ==========================================
# SCHÉMAS POUR LIEN RÉSEAU SOCIAL
# ==========================================

class LienReseauSocialOut(ModelSchema):
    """Schéma sortie pour LienReseauSocialProfil"""
    reseau: ReseauSocialSimple
    class Meta:
        model = LienReseauSocialProfil
        fields = ['id', 'reseau', 'url', 'est_actif', 'created_at', 'updated_at']

    @staticmethod
    def resolve_reseau(obj):
        """Retourne l'objet ReseauSocial complet"""
        return {
            "id": obj.reseau.id,
            "nom": obj.reseau.nom,
            "code": obj.reseau.code,
            "url_base": obj.reseau.url_base
        }
class LienReseauSocialCreate(Schema):
    """Schéma création lien réseau social"""
    reseau_id: UUID4
    url: str

class LienReseauSocialUpdate(Schema):
    """Schéma mise à jour lien réseau social"""
    url: Optional[str] = None
    est_actif: Optional[bool] = None


# ==========================================
# SCHÉMAS UTILISATEUR
# ==========================================
# Consolidation: UserBaseOut pour infos basiques, étendu pour détail/complet.

class UserBaseOut(ModelSchema):
    """Schéma base pour User (sans profil)"""
    telephone: Optional[str] = None
    class Meta:
        model = User
        fields = ['id', 'email', 'role_systeme', 'est_actif', 'last_login', 'created_at', 'updated_at']
        # Exclusion sensible: mot_de_passe, groups, user_permissions
    @staticmethod
    def resolve_telephone(obj):
        return str(obj.telephone) if obj.telephone else None
    
class UserDetailOut(UserBaseOut):
    """Schéma détail User avec profil base"""
    profil: Optional[ProfilBaseOut] = None

class UserCompleteOut(UserBaseOut):
    """Schéma complet User avec profil étendu (inclut réseaux sociaux)"""
    profil: Optional[ProfilCompleteOut] = None



# ==========================================
# SCHÉMAS CRÉATION/MISE À JOUR UTILISATEUR
# ==========================================

class UserCreate(Schema):
    """Schéma création User (public/self-register)"""
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    password: Annotated[int, Field(..., min_length=8, description="Mot de passe (min. 8 caractères)")]
    profil: ProfilCreate
    
    @model_validator(mode='before')
    def check_contact_info(cls, values):
        email = values.get('email')
        telephone = values.get('telephone')
        if not email and not telephone:
            raise ValueError("Au moins un des champs 'email' ou 'telephone' doit être fourni.")
        return values

    

class UserCreateAdmin(Schema):
    """Schéma création User par admin (password optionnel)"""
    email: Optional[EmailStr] = Field(None, description="Adresse email de l'utilisateur")
    telephone: Optional[str] = Field(None, description="Numéro de téléphone de l'utilisateur")
    password: Optional[str] = Field(None, min_length=8, description="Mot de passe (min. 8 caractères)")
    role_systeme: str = 'user'
    est_actif: bool = True
    profil: Optional[ProfilCreate] = None

    @field_validator('role_systeme')
    def validate_role(cls, v):
        if v not in [choice[0] for choice in User.ROLE_SYSTEME_CHOICES]:
            raise ValueError('Rôle système invalide')
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
    """Schéma mise à jour User (self ou admin)"""
    profil: Optional[ProfilUpdate] = None
    class Meta:
        model = User
        fields = ['email', 'role_systeme', 'est_actif']
        fields_optional = '__all__'


    

# ==========================================
# SCHÉMAS MOT DE PASSE
# ==========================================

class ChangePassword(Schema):
    """Changement mot de passe par user"""
    old_password: str
    new_password: str = Field(..., min_length=8)

class ResetPassword(Schema):
    """Réinitialisation mot de passe par admin"""
    new_password: Optional[str] = None  # Généré si None

class PasswordResponse(Schema):
    """Réponse après reset/changement"""
    message: str
    temporary_password: Optional[str] = None

# ==========================================
# SCHÉMAS PHOTO PROFIL
# ==========================================

class PhotoUploadResponse(Schema):
    message: str = "Photo mise à jour"
    photo_url: Optional[str] = None

class PhotoDeleteResponse(Schema):
    message: str = "Photo supprimée"

# ==========================================
# SCHÉMAS POUR BULK CREATE USERS
# ==========================================

class BulkUserCreate(Schema):
    """Schéma pour la création en bulk d'utilisateurs par admin"""
    users: List[UserCreateAdmin]
    mode: Literal['strict', 'skip'] = Field('strict', description="Mode d'exécution: 'strict' (arrête sur erreur) ou 'ignore_errors' (continue malgré erreurs)")
    batch_size: Optional[int] = Field(100, ge=1, le=1000, description="Taille des batches pour la création en bulk")

class BulkCreateError(Schema):
    """Schéma pour les erreurs lors de la création en bulk"""
    index: int
    error: str

class BulkCreateResponse(Schema):
    """Schéma de réponse pour la création en bulk"""
    created_users: List[UserCompleteOut]
    errors: List[BulkCreateError]




# ==========================================
# SCHÉMAS LISTE
# ==========================================
# Cohérent: Meta générique, utilisé pour listes paginées.

class UserCompleteListResponse(Schema):
    """Liste paginée Users (utilise UserCompleteOut pour détail)"""
    items: List[UserCompleteOut]
    meta: PaginationMetaSchema

class UserListResponse(Schema):
    """Liste paginée Users (utilise UserDetailOut pour détail)"""
    items: List[UserDetailOut]
    meta: PaginationMetaSchema

# ==========================================
# SCHÉMAS FILTRES ET STATISTIQUES
# ==========================================


class UserFilter(Schema):
    search: Optional[str] = None
    role_systeme: Optional[List[str]] = Field(None, description="Rôle système")
    statut_global: Optional[List[str]] = Field(None, description="Statut global")
    est_actif: Optional[List[bool]] = Field(None, description="Est actif")


class UserStatistics(Schema):
    total_users: int
    active_users: int
    inactive_users: int
    deleted_users: int
    by_role: Dict[str, int]
    by_status: Dict[str, int]

# ==========================================
# SCHÉMAS GESTION COMPTE
# ==========================================

class ToggleStatus(Schema):
    est_actif: bool

# ==========================================
# SCHÉMAS ERREURS (STANDARDISÉS)
# ==========================================

class FieldError(Schema):
    field: str
    message: str

class ValidationErrorResponse(Schema):
    detail: str = "Erreur de validation"
    errors: List[FieldError]

class MessageResponse(Schema):
    detail: str
