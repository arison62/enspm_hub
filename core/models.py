# core/models.py
import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from core.utils.encoder import CountriesEncoder
from datetime import datetime, timedelta

from django.apps import apps

# ==========================================
# 1. MANAGERS
# ==========================================
class SoftDeleteManager(models.Manager):
    """Manager qui filtre par défaut les objets supprimés (Soft Delete)"""
    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)


class AllObjectsManager(models.Manager):
    """Manager pour accéder à tous les objets, y compris supprimés (Admin/Audit)"""
    def get_queryset(self):
        return super().get_queryset()
    
class CustomUserManager(BaseUserManager):
    """Manager personnalisé pour la gestion des utilisateurs"""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('L\'adresse email est obligatoire'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('est_actif', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role_systeme', 'super_admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        user = self.create_user(email, password, **extra_fields)
        Profil = apps.get_model('users', 'Profil')
        Profil.objects.create(user=user)
        return user
       
class UserSoftDeleteManager(CustomUserManager, SoftDeleteManager):
    
    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)
    
    def create_user(self, email, password=None, **extra_fields):
        return super().create_user(email, password, **extra_fields)
    
    def create_superuser(self, email, password=None, **extra_fields):
        return super().create_superuser(email, password, **extra_fields)

# ==========================================
# 2. MODÈLE DE BASE (Abstract)
# ==========================================
class ENSPMHubBaseModel(models.Model):
    """
    Modèle de base pour tous les modèles du projet.
    Intègre UUID, Timestamps et Soft Delete.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))

    # Soft Delete
    deleted = models.BooleanField(default=False, verbose_name=_("Supprimé"))
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Date de suppression"))

    # Managers
    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def soft_delete(self):
        self.deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted', 'deleted_at'])

    def restore(self):
        self.deleted = False
        self.deleted_at = None
        self.save(update_fields=['deleted', 'deleted_at'])

# ==========================================
# 1. RÉFÉRENCES ACADÉMIQUES
# ==========================================

class AnneePromotion(ENSPMHubBaseModel):
    """
    Années de sortie valides pour les alumni.
    Permet un contrôle strict et facilite les statistiques par promotion.
    """
    annee = models.SmallIntegerField(
        unique=True,
        validators=[MinValueValidator(1950), MaxValueValidator(2100)],
        verbose_name=_("Année")
    )
    libelle = models.CharField(
        max_length=50,
        verbose_name=_("Libellé"),
        help_text=_("Ex: Promotion 2020, Promo 2020, etc.")
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Informations supplémentaires sur cette promotion")
    )
    est_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Permet de désactiver temporairement une année")
    )
    ordre_affichage = models.IntegerField(
        default=0,
        verbose_name=_("Ordre d'affichage"),
        help_text=_("Plus petit = affiché en premier")
    )

    class Meta:
        verbose_name = _("Année de promotion")
        verbose_name_plural = _("Années de promotion")
        db_table = 'cores_annee_promotions'
        ordering = ['-annee']

    def __str__(self):
        return f"{self.libelle} ({self.annee})"


class Domaine(ENSPMHubBaseModel):
    """
    Domaines d'études et de spécialisation.
    Ex: Génie Civil, Génie Informatique, Génie Mécanique, etc.
    """
    nom = models.CharField(
        max_length=150,
        unique=True,
        verbose_name=_("Nom"),
        help_text=_("Nom complet du domaine")
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Code"),
        help_text=_("Code court: GCI, GIM, GEL, etc.")
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Présentation du domaine, débouchés, compétences")
    )
    categorie = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Catégorie"),
        help_text=_("Ex: Génie, Santé, Sciences Sociales")
    )
    est_actif = models.BooleanField(
        default=True,
        verbose_name=_("Actif")
    )
    ordre_affichage = models.IntegerField(
        default=0,
        verbose_name=_("Ordre d'affichage")
    )

    class Meta:
        verbose_name = _("Domaine")
        verbose_name_plural = _("Domaines")
        db_table = 'core_domaines'
        ordering = ['ordre_affichage', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.code})"


class Filiere(ENSPMHubBaseModel):
    """
    Filières spécifiques au sein des domaines.
    Ex: Domaine "Génie Informatique" → Filières: IA, Cybersécurité, etc.
    """
    NIVEAU_CHOICES = [
        ('licence', 'Licence'),
        ('ingenieur', 'Ingénieur'),
        ('master', 'Master'),
        ('doctorat', 'Doctorat'),
        ('autre', 'Autre'),
    ]

    domaine = models.ForeignKey(
        Domaine,
        on_delete=models.CASCADE,
        related_name='filieres',
        verbose_name=_("Domaine")
    )
    nom = models.CharField(
        max_length=150,
        verbose_name=_("Nom de la filière")
    )
    code = models.CharField(
        max_length=20,
        verbose_name=_("Code")
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Description")
    )
    niveau = models.CharField(
        max_length=50,
        choices=NIVEAU_CHOICES,
        verbose_name=_("Niveau")
    )
    duree_annees = models.SmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Durée (années)")
    )
    est_actif = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )
    ordre_affichage = models.IntegerField(
        default=0,
        verbose_name=_("Ordre d'affichage")
    )

    class Meta:
        verbose_name = _("Filière")
        verbose_name_plural = _("Filières")
        db_table = 'core_filieres'
        unique_together = ('domaine', 'code')
        ordering = ['domaine', 'ordre_affichage', 'nom']

    def __str__(self):
        return f"{self.domaine.code} - {self.nom}"


# ==========================================
# 2. RÉFÉRENCES PROFESSIONNELLES
# ==========================================

class SecteurActivite(ENSPMHubBaseModel):
    """
    Secteurs d'activité économique pour les organisations.
    Supporte une hiérarchie (secteur parent → sous-secteurs).
    """
    nom = models.CharField(
        max_length=150,
        unique=True,
        verbose_name=_("Nom du secteur")
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Code"),
        help_text=_("Ex: TECH, BTP, SANTE, FINANCE")
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Description")
    )
    categorie_parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='sous_secteurs',
        verbose_name=_("Secteur parent"),
        help_text=_("Permet une hiérarchie: Technologie > Informatique > IA")
    )
    icone = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Icône")
    )
    est_actif = models.BooleanField(
        default=True,
        verbose_name=_("Actif")
    )
    ordre_affichage = models.IntegerField(
        default=0,
        verbose_name=_("Ordre d'affichage")
    )

    class Meta:
        verbose_name = _("Secteur d'activité")
        verbose_name_plural = _("Secteurs d'activité")
        db_table = 'core_secteur_activites'
        ordering = ['ordre_affichage', 'nom']

    def __str__(self):
        if self.categorie_parent:
            return f"{self.categorie_parent.nom} > {self.nom}"
        return self.nom

    @property
    def nom_complet(self):
        """Retourne le chemin complet dans la hiérarchie"""
        if self.categorie_parent:
            return f"{self.categorie_parent.nom_complet} > {self.nom}"
        return self.nom


# ==========================================
# 3. RÉFÉRENCES FINANCIÈRES
# ==========================================

class Devise(ENSPMHubBaseModel):
    """
    Devises monétaires pour les salaires et prix de formation.
    Permet la conversion et l'affichage cohérent.
    """
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_("Code"),
        help_text=_("Code ISO 4217: XAF, EUR, USD")
    )
    nom = models.CharField(
        max_length=100,
        verbose_name=_("Nom complet")
    )
    symbole = models.CharField(
        max_length=10,
        verbose_name=_("Symbole"),
        help_text=_("FCFA, €, $")
    )
    taux_change_usd = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_("Taux de change USD"),
        help_text=_("1 USD = X devise (mis à jour régulièrement)")
    )
    date_mise_a_jour_taux = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date mise à jour du taux")
    )
    est_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )
    ordre_affichage = models.IntegerField(
        default=0,
        verbose_name=_("Ordre d'affichage"),
        help_text=_("XAF en premier pour le Cameroun")
    )

    class Meta:
        verbose_name = _("Devise")
        verbose_name_plural = _("Devises")
        db_table = 'core_devises'
        ordering = ['ordre_affichage', 'nom']

    def __str__(self):
        return f"{self.code} ({self.symbole})"


# ==========================================
# 4. RÉFÉRENCES TITRES & HONORIFIQUES
# ==========================================

class TitreHonorifique(ENSPMHubBaseModel):
    """
    Titres honorifiques et académiques.
    Ex: Dr., Prof., Ing., M., Mme
    """
    TYPE_TITRE_CHOICES = [
        ('academique', 'Académique'),
        ('professionnel', 'Professionnel'),
        ('honorifique', 'Honorifique'),
        ('civilite', 'Civilité'),
    ]

    titre = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Titre"),
        help_text=_("Abréviation: Dr., Prof., Ing.")
    )
    nom_complet = models.CharField(
        max_length=100,
        verbose_name=_("Nom complet"),
        help_text=_("Docteur, Professeur, Ingénieur")
    )
    type_titre = models.CharField(
        max_length=20,
        choices=TYPE_TITRE_CHOICES,
        verbose_name=_("Type de titre")
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Explication du titre, conditions d'obtention")
    )
    est_actif = models.BooleanField(
        default=True,
        verbose_name=_("Actif")
    )
    ordre_affichage = models.IntegerField(
        default=0,
        verbose_name=_("Ordre d'affichage")
    )

    class Meta:
        verbose_name = _("Titre honorifique")
        verbose_name_plural = _("Titres honorifiques")
        db_table = 'core_titre_honorifiques'
        ordering = ['ordre_affichage', 'titre']

    def __str__(self):
        return f"{self.titre} ({self.nom_complet})"


# ==========================================
# 5. RÉFÉRENCES RÉSEAUX SOCIAUX
# ==========================================

class ReseauSocial(ENSPMHubBaseModel):
    """
    Réseaux sociaux et plateformes professionnelles.
    Plus flexible que des choices hardcodés.
    """
    TYPE_RESEAU_CHOICES = [
        ('professionnel', 'Professionnel'),
        ('social', 'Social'),
        ('academique', 'Académique'),
        ('technique', 'Technique'),
        ('portfolio', 'Portfolio'),
    ]

    nom = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Nom"),
        help_text=_("LinkedIn, Facebook, GitHub, etc.")
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Code"),
        help_text=_("linkedin, facebook, github (minuscules, sans espaces)")
    )
    url_base = models.URLField(
        verbose_name=_("URL de base"),
        help_text=_("https://linkedin.com/in/, https://github.com/")
    )
    type_reseau = models.CharField(
        max_length=20,
        choices=TYPE_RESEAU_CHOICES,
        verbose_name=_("Type de réseau")
    )
    pattern_validation = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Pattern de validation"),
        help_text=_("Expression régulière pour valider l'URL")
    )
    placeholder_exemple = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Exemple de placeholder"),
        help_text=_("Ex: votre-nom ou username")
    )
    est_actif = models.BooleanField(
        default=True,
        verbose_name=_("Actif")
    )
    ordre_affichage = models.IntegerField(
        default=0,
        verbose_name=_("Ordre d'affichage")
    )

    class Meta:
        verbose_name = _("Réseau social")
        verbose_name_plural = _("Réseaux sociaux")
        db_table = 'core_reseau_sociaux'
        ordering = ['ordre_affichage', 'nom']

    def __str__(self):
        return self.nom



# ==========================================
# 3. AUTHENTIFICATION : USER
# ==========================================
class User(AbstractBaseUser, PermissionsMixin, ENSPMHubBaseModel):
    """Modèle d'authentification minimal"""
    ROLE_SYSTEME_CHOICES = [
        ('user', 'Utilisateur'),
        ('admin_site', 'Administrateur site'),
        ('super_admin', 'Super Administrateur'),
    ]

    email = models.EmailField(
        unique=True, 
        null=True,
        blank=True,
        verbose_name=_("Adresse email")
    )
    telephone = PhoneNumberField(
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("Numéro de téléphone")
    )
    mot_de_passe = models.CharField(max_length=255, editable=False, null=True, blank=True)  # Django gère déjà le hash
    role_systeme = models.CharField(max_length=20, choices=ROLE_SYSTEME_CHOICES, default='user',
                                    verbose_name=_("Rôle système"))
    last_login = models.DateTimeField(null=True, blank=True, verbose_name=_("Dernière connexion"))
    est_actif = models.BooleanField(default=True, verbose_name=_("Compte actif"))
    is_staff = models.BooleanField(default=False, verbose_name=_("Accès admin Django"))

    # Permissions Django
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        related_name="ensp_user_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        related_name="ensp_user_set",
        related_query_name="user",
    )

    objects = UserSoftDeleteManager()
    all_objects = AllObjectsManager()
   

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("Utilisateur")
        verbose_name_plural = _("Utilisateurs")
        db_table = 'core_users'

    def __str__(self):
        return self.email or str(self.telephone) or f"Utilisateur {self.id}"
    
    @property
    def is_active(self):
        return self.est_actif and not self.deleted
    
    def clean(self):
        super().clean()
        if not self.email and not self.telephone:
            raise ValueError(_('L\'utilisateur doit avoir une adresse email ou un numéro de téléphone.'))
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Valide avant de sauvegarder
        super().save(*args, **kwargs)


    def is_admin_user(self) -> bool:
        """Vérifie si l'utilisateur est un administrateur du site"""
        return self.is_superuser or self.is_staff or self.role_systeme in ('admin_site', 'super_admin')

def get_password_reset_token_expiry():
    """Retourne la date d'expiration par défaut pour les tokens de réinitialisation"""
    return timezone.now() + timedelta(hours=1)

class PasswordResetToken(ENSPMHubBaseModel):
    """Modèle pour gérer les tokens de réinitialisation de mot de passe."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
        verbose_name=_("Utilisateur")
    )
    token = models.CharField(max_length=6, unique=True, verbose_name=_("Token"))
    expires_at = models.DateTimeField(default=get_password_reset_token_expiry, verbose_name=_("Date d'expiration"))
    is_used = models.BooleanField(default=False, verbose_name=_("Utilisé"))

    class Meta:
        verbose_name = _("Token de réinitialisation de mot de passe")
        verbose_name_plural = _("Tokens de réinitialisation de mot de passe")
        db_table = 'core_password_reset_tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Password reset token for {self.user.email}"



class AuditLog(ENSPMHubBaseModel):
    """Journal d'audit pour la traçabilité complète des actions."""

    class AuditAction(models.TextChoices):
        CREATE = 'CREATE', _('Create')
        UPDATE = 'UPDATE', _('Update')
        DELETE = 'DELETE', _('Delete')
        VIEW = 'VIEW', _('View')
        ACCESS_DENIED = 'ACCESS_DENIED', _('Access denied')

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name=_("Utilisateur")
    )
    action = models.CharField(
        max_length=20,
        choices=AuditAction.choices,
        verbose_name=_('Action'),
        db_index=True
    )

    # Informations sur l'entité concernée
    entity_type = models.CharField(
        max_length=100,
        verbose_name=_('Type d\'entité'),
        db_index=True
    )
    entity_id = models.UUIDField(verbose_name=_('ID de l\'entité'), db_index=True)

    # Détails des changements
    old_values = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Anciennes valeurs'),
        encoder=CountriesEncoder
    )
    new_values = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Nouvelles valeurs'),
        encoder=CountriesEncoder
    )

    # Informations de connexion
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('Adresse IP')
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User agent')
    )

    class Meta:
        verbose_name = _("Journal d'audit")
        verbose_name_plural = _("Journaux d'audit")
        db_table = 'core_audit_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.action} on {self.entity_type} "


class Notification(ENSPMHubBaseModel):
    """Modèle centralisé pour les notifications"""

    class Category(models.TextChoices):
        SYSTEM = 'SYSTEM', _('Système')
        CHAT = 'CHAT', _('Chat')
        NETWORK = 'NETWORK', _('Réseau')
        OPPORTUNITY = 'OPPORTUNITY', _('Opportunité')
        ADMIN = 'ADMIN', _('Administration')

    destinataire = models.ForeignKey(
        'users.Profil',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('destinataire')
    )

    # Reference generique vers la source
    source_content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_('type de source')
    )
    source_object_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_("id de la source")
    )
    source = GenericForeignKey('source_content_type', 'source_object_id')
    source_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_('type de source (cache)')
    )

    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.SYSTEM,
        verbose_name=_('catégorie')
    )
    action_type = models.CharField(
        max_length=50,
        verbose_name=_('type d\'action')
    ) # ex: 'MENTOR_VALIDATED'

    # Données statiques pour affichage rapide
    title = models.CharField(max_length=255, verbose_name=_('titre'))
    content = models.TextField(verbose_name=_('contenu'))
    link = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('lien'))
    icon = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('icône'))

    # État
    is_read = models.BooleanField(default=False, verbose_name=_('lu'))
    read_at = models.DateTimeField(null=True, blank=True, verbose_name=_('lu le'))

    class Meta:
        db_table = 'core_notifications'
        ordering = ['-created_at']
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        indexes = [
            models.Index(fields=['destinataire', 'is_read', '-created_at']),
            models.Index(fields=['source_content_type', 'source_object_id']),
        ]

    def save(self, *args, **kwargs):
        if self.source_content_type:
            self.source_type = self.source_content_type.model
        super().save(*args, **kwargs)

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def __str__(self):
        return f"Notification {self.action_type} pour {self.destinataire}"
