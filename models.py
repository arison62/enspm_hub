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



# users/models.py
from django.db import models
from core.models import ENSPMHubBaseModel
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

class Profil(ENSPMHubBaseModel):
    STATUT_GLOBAL_CHOICES = [
        ('etudiant', 'Étudiant'),
        ('alumni', 'Alumni'),
        ('enseignant', 'Enseignant'),
        ('personnel_admin', 'Personnel Administratif'),
        ('partenaire', 'Partenaire'),
    ]
    user = models.OneToOneField("core.User", on_delete=models.CASCADE, related_name='profil', db_constraint=True)
    nom_complet = models.CharField(null=True, blank=True, max_length=255, verbose_name=_("Nom complet"))
    matricule = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name=_("Matricule"), db_index=True)
    
    titre = models.ForeignKey(
        'core.TitreHonorifique',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='profils',
        verbose_name=_("Titre")
    )
    
    statut_global = models.CharField(max_length=30, choices=STATUT_GLOBAL_CHOICES, verbose_name=_("Statut global"))
    annee_sortie = models.ForeignKey(
        'core.AnneePromotion',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='profils',
        verbose_name=_("Promotion")
    )
    
    adresse = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Adresse"))
    telephone = models.CharField(max_length=20, null=True, blank=True, verbose_name=_("Téléphone"))
    
    ville = models.CharField(max_length=100, null=True, blank=True, verbose_name=_("Ville"))
    
    pays = CountryField(null=True, blank=True, verbose_name=_("Pays"))
    
    photo_profil = models.ImageField(upload_to='photos_profils/', null=True, blank=True, verbose_name=_("Photo de profil"))
    
    domaine = models.ForeignKey(
        'core.Domaine',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='profils',
        verbose_name=_("Domaine")
    )
    
    bio = models.TextField(null=True, blank=True, verbose_name=_("Bio"))
    slug = models.SlugField(unique=True, null=True, blank=True, verbose_name=_("Slug"), db_index=True)

    class Meta:
        verbose_name = _("Profil")
        db_table = 'users_profiles'

    def __str__(self):
        return self.nom_complet or self.user.email
    
    def est_alumni(self) -> bool:
        return self.statut_global == 'alumni'
    
    def est_etudiant(self) -> bool:
        return self.statut_global == 'etudiant'
    
    def est_enseignant(self) -> bool:
        return self.statut_global == 'enseignant'
    
    def est_personnel_admin(self) -> bool:
        return self.statut_global == 'personnel_admin'
    
    def est_partenaire(self) -> bool:
        return self.statut_global == 'partenaire'
 
class ExperienceProfessionnelle(ENSPMHubBaseModel):
    """
    Représente une étape du parcours professionnel d'un membre.
    """
    profil = models.ForeignKey(
        'users.Profil', 
        on_delete=models.CASCADE, 
        related_name='experiences',
        verbose_name=_("Profil")
    )
    
    # Champs descriptifs libres
    titre_poste = models.CharField(
        max_length=255, 
        verbose_name=_("Titre du poste"),
        help_text=_("Ex: Ingénieur Logiciel, Consultant, Directeur Technique...")
    )
    nom_entreprise = models.CharField(
        max_length=255, 
        verbose_name=_("Entreprise ou Organisation")
    )
    lieu = models.CharField(
        max_length=255, 
        null=True, 
        blank=True, 
        verbose_name=_("Lieu (Ville, Pays ou Distanciel)")
    )
    
    # Chronologie
    date_debut = models.DateField(verbose_name=_("Date de début"))
    date_fin = models.DateField(
        null=True, 
        blank=True, 
        verbose_name=_("Date de fin"),
        help_text=_("Laissez vide si vous occupez toujours ce poste")
    )
    est_poste_actuel = models.BooleanField(
        default=False, 
        verbose_name=_("Poste actuel")
    )
    
    # Contenu riche
    description = models.TextField(
        null=True, 
        blank=True, 
        verbose_name=_("Missions et réalisations")
    )
    

    class Meta:
        verbose_name = _("Expérience Professionnelle")
        db_table = 'users_experience_professionnelle'
        ordering = ['-date_debut']
        indexes = [
            models.Index(fields=['profil', '-date_debut']),
            models.Index(fields=['est_poste_actuel']),
        ]

    def __str__(self):
        return f"{self.titre_poste} @ {self.nom_entreprise}"

    def save(self, *args, **kwargs):
        # Logique métier simple : si date_fin est nulle, c'est probablement un poste actuel
        if not self.date_fin:
            self.est_poste_actuel = True
        super().save(*args, **kwargs) 
    
class LienReseauSocialProfil(ENSPMHubBaseModel):
    profil = models.ForeignKey(Profil, on_delete=models.CASCADE, related_name='liens_reseaux')
    
    reseau = models.ForeignKey(
        'core.ReseauSocial',
        on_delete=models.CASCADE,
        related_name='liens',
        verbose_name=_("Réseau social")
    )
    
    url = models.URLField(verbose_name=_("URL"))
    est_actif = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _("Lien de résseau social")
        db_table = 'users_lien_reseau_social_profil'

    def __str__(self):
        return f"{self.reseau.nom} - {self.profil.nom_complet}"
    
    
# feeds/models/feeds.py
from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.utils.translation import gettext_lazy as _
from django.utils.text import Truncator
from core.mixins import ChatReferenceable
from bs4 import BeautifulSoup

from core.models import ENSPMHubBaseModel


class Post(ENSPMHubBaseModel, ChatReferenceable):
    """Modèle pour les posts du fil d'actualité"""
    
    REFERENCE_TYPE = "post"
    
    author = models.ForeignKey(
        'users.Profil',
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name=_("Auteur")
    )
    
    content = models.TextField(
        verbose_name=_("Contenu"),
        help_text=_("Contenu HTML du post (rich-text)")
    )
    
    # Champ de texte brut pour la recherche et l'indexation
    content_text = models.TextField(
        blank=True,
        verbose_name=_("Contenu texte"),
        help_text=_("Version texte du contenu sans HTML")
    )
    
    # Champ de recherche vectorielle
    search_vector = SearchVectorField(null=True, blank=True)
    
    is_pinned = models.BooleanField(
        default=False,
        verbose_name=_("Épinglé"),
        help_text=_("Post épinglé en haut du fil")
    )
    
    is_archived = models.BooleanField(
        default=False,
        verbose_name=_("Archivé")
    )
    
    # Compteurs dénormalisés pour les performances
    likes_count = models.PositiveIntegerField(default=0, verbose_name=_("Nombre de likes"))
    comments_count = models.PositiveIntegerField(default=0, verbose_name=_("Nombre de commentaires"))
    views_count = models.PositiveIntegerField(default=0, verbose_name=_("Nombre de vues"))
    shares_count = models.PositiveIntegerField(default=0, verbose_name=_("Nombre de partages"))
    
    class Meta:
        verbose_name = _("Post")
        verbose_name_plural = _("Posts")
        db_table = 'feed_posts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['is_pinned', '-created_at']),
            GinIndex(fields=['search_vector']),
        ]
    
    def __str__(self):
        return f"Post by {self.author.nom_complet} - {Truncator(self.content_text).words(10)}"
    
    def save(self, *args, **kwargs):
        """Extraire le texte du HTML pour la recherche"""
        if self.content:
            soup = BeautifulSoup(self.content, 'html.parser')
            self.content_text = soup.get_text(separator=' ', strip=True)
        super().save(*args, **kwargs)
        
        # Mettre à jour le vecteur de recherche
        if self.content_text:
            Post.objects.filter(pk=self.pk).update(
                search_vector=SearchVector('content_text', weight='A')
            )
    
    @property
    def content_type(self):
        """Détermine le type de contenu du post"""
        if not self.content:
            return 'text'
        
        soup = BeautifulSoup(self.content, 'html.parser')
        
        # Vérifier la présence d'images
        if soup.find('img'):
            return 'image'
        
        # Vérifier la présence de liens
        if soup.find('a'):
            return 'link'
        
        return 'text'

    def get_chat_preview(self) -> dict:
        return {
            "id": self.pk,
            "type": self.REFERENCE_TYPE,
            "titre": self.content_text[:100] + "..." if self.content_text else "",
            "sous_titre": self.author.nom_complet,
            "apercu": self.content_text[:100] + "..." if self.content_text else "",
            "url": f"/network/posts/{self.id}",
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class Comment(ENSPMHubBaseModel, ChatReferenceable):
    """Modèle pour les commentaires sur les posts"""
    
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_("Post")
    )
    
    author = models.ForeignKey(
        'users.Profil',
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_("Auteur")
    )
    
    content = models.TextField(
        verbose_name=_("Contenu"),
        help_text=_("Contenu HTML du commentaire (rich-text)")
    )
    
    content_text = models.TextField(
        blank=True,
        verbose_name=_("Contenu texte"),
        help_text=_("Version texte du contenu sans HTML")
    )
    
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies',
        verbose_name=_("Commentaire parent")
    )
    
    # Compteurs dénormalisés
    likes_count = models.PositiveIntegerField(default=0, verbose_name=_("Nombre de likes"))
    replies_count = models.PositiveIntegerField(default=0, verbose_name=_("Nombre de réponses"))
    
    class Meta:
        verbose_name = _("Commentaire")
        verbose_name_plural = _("Commentaires")
        db_table = 'feed_comments'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['parent', 'created_at']),
        ]
    
    def __str__(self):
        return f"Comment by {self.author.nom_complet} on {self.post}"
    
    def save(self, *args, **kwargs):
        """Extraire le texte du HTML"""
        if self.content:
            soup = BeautifulSoup(self.content, 'html.parser')
            self.content_text = soup.get_text(separator=' ', strip=True)
        super().save(*args, **kwargs)
    
    def get_chat_preview(self) -> dict:
        return {
            "id": self.pk,
            "type": self.REFERENCE_TYPE,
            "titre": self.content_text[:100] + "..." if self.content_text else "",
            "sous_titre": self.author.nom_complet,
            "apercu": self.content_text[:100] + "..." if self.content_text else "",
            "url": f"/network/posts/{self.post.id}/comments/{self.id}",
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    


class Like(ENSPMHubBaseModel):
    """Modèle pour les likes sur les posts et commentaires"""
    
    profil = models.ForeignKey(
        'users.Profil',
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name=_("Profil")
    )
    
    post = models.ForeignKey(
        Post,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name=_("Post")
    )
    
    comment = models.ForeignKey(
        Comment,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name=_("Commentaire")
    )
    
    class Meta:
        verbose_name = _("Like")
        verbose_name_plural = _("Likes")
        db_table = 'feed_likes'
        unique_together = [
            ('profil', 'post'),
            ('profil', 'comment'),
        ]
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['comment', 'created_at']),
            models.Index(fields=['profil', '-created_at']),
        ]
    
    def __str__(self):
        target = self.post if self.post else self.comment
        return f"{self.profil.nom_complet} likes {target}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.post and not self.comment:
            raise ValidationError(_("Un like doit être associé à un post ou un commentaire"))
        if self.post and self.comment:
            raise ValidationError(_("Un like ne peut pas être associé à la fois à un post et un commentaire"))


class View(ENSPMHubBaseModel):
    """Modèle pour tracker les vues des posts"""
    
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='views',
        verbose_name=_("Post")
    )
    
    profil = models.ForeignKey(
        'users.Profil',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='post_views',
        verbose_name=_("Profil")
    )
    
    # Pour les vues anonymes
    session_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Session key")
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("Adresse IP")
    )
    
    class Meta:
        verbose_name = _("Vue")
        verbose_name_plural = _("Vues")
        db_table = 'feed_views'
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['profil', '-created_at']),
        ]
    
    def __str__(self):
        viewer = self.profil.nom_complet if self.profil else "Anonymous"
        return f"{viewer} viewed {self.post}"


class Share(ENSPMHubBaseModel):
    """Modèle pour les partages de posts"""
    
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='shares',
        verbose_name=_("Post")
    )
    
    profil = models.ForeignKey(
        'users.Profil',
        on_delete=models.CASCADE,
        related_name='post_shares',
        verbose_name=_("Profil")
    )
    
    platform = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Plateforme"),
        help_text=_("Plateforme de partage (linkedin, twitter, email, etc.)")
    )
    
    class Meta:
        verbose_name = _("Partage")
        verbose_name_plural = _("Partages")
        db_table = 'feed_shares'
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['profil', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.profil.nom_complet} shared {self.post}"



class Report(ENSPMHubBaseModel):
    """Modèle pour les signalements de posts ou commentaires"""
    
    REASON_CHOICES = [
        ('spam', _('Spam')),
        ('harassment', _('Harcèlement')),
        ('hate_speech', _('Discours haineux')),
        ('violence', _('Violence')),
        ('false_info', _('Fausse information')),
        ('inappropriate', _('Contenu inapproprié')),
        ('other', _('Autre')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('reviewed', _('Examiné')),
        ('resolved', _('Résolu')),
        ('rejected', _('Rejeté')),
    ]
    
    reporter = models.ForeignKey(
        'users.Profil',
        on_delete=models.CASCADE,
        related_name='reports_made',
        verbose_name=_("Rapporteur")
    )
    
    post = models.ForeignKey(
        Post,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_("Post")
    )
    
    comment = models.ForeignKey(
        Comment,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_("Commentaire")
    )
    
    reason = models.CharField(
        max_length=50,
        choices=REASON_CHOICES,
        verbose_name=_("Raison")
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Description détaillée du signalement")
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_("Statut")
    )
    
    reviewed_by = models.ForeignKey(
        'users.Profil',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reports_reviewed',
        verbose_name=_("Examiné par")
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'examen")
    )
    
    resolution_note = models.TextField(
        blank=True,
        verbose_name=_("Note de résolution")
    )
    
    class Meta:
        verbose_name = _("Signalement")
        verbose_name_plural = _("Signalements")
        db_table = 'feed_reports'
        unique_together = [
            ('reporter', 'post'),
            ('reporter', 'comment'),
        ]
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['post', 'status']),
            models.Index(fields=['comment', 'status']),
        ]
    
    def __str__(self):
        target = self.post if self.post else self.comment
        return f"Report by {self.reporter.nom_complet} - {target}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.post and not self.comment:
            raise ValidationError(_("Un signalement doit être associé à un post ou un commentaire"))
        if self.post and self.comment:
            raise ValidationError(_("Un signalement ne peut pas être associé à la fois à un post et un commentaire"))


from django.db import models
from django.utils import timezone

from core.models import ENSPMHubBaseModel


class FeedScoreConfig(ENSPMHubBaseModel):
    """
    Configuration des scores
    """
    
    # Configuration des score utilisateur
    profil_base_score = models.FloatField(default=1.0, help_text="Score de base pour les utilisateur")
    profil_activity_coeff = models.FloatField(default=1.0, help_text="Coefficient les activites de l'utilisateur")
    profil_report_penalty_per_report = models.FloatField(default=1.0, help_text="Penalite par signalement de l'utilisateur")
    profil_report_threshold = models.IntegerField(default=10, help_text="Seuil de signalement de l'utilisateur")
    
    
    # Configuration des score posts
    post_base_score = models.FloatField(default=10.0, help_text="Score de base pour les posts")
    post_penality_per_report = models.FloatField(default=10.0, help_text="Penalite par signalement de post")
    post_report_threshold = models.IntegerField(default=10, help_text="Seuil de signalement de post")
    time_decay_factor = models.FloatField(default=12.0, help_text="Facteur de diminution du score par temps")
    boost_new_posts = models.BooleanField(default=True, help_text="Boost les nouveaux posts ")
    new_posts_boost_factor = models.FloatField(default=2.0, help_text="Facteur de boost des nouveaux posts")
    boost_new_posts_threshold = models.IntegerField(default=8, help_text="Duree de boost des nouveaux posts")
    content_multipliers = models.JSONField(
        default=dict,
        help_text='''JSON : {
            "image": 2.0,
            "video: 1.5,
            "pooll: 1.2,
            "link": 1.1,
            "text": 1.0
            "
        }'''
    )
    engagement_coefficients = models.JSONField(
        default=dict,
        help_text='''JSON:{
            comment: 3.0,
            "like": 2.0,
            "view: 0.1,
            "share": 1.5
        }'''
    )
    
    is_active = models.BooleanField(default=False, help_text="Configuration actuellement utilisée")
    
    class Meta:
        verbose_name = "Configuration de score"
        verbose_name_plural = "Configurations des scores"
        ordering = ["-is_active", "updated_at"]
    
    def __str__(self):
        return f"Config {'Actif' if self.is_active else 'Inactif'} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        """S'assurer qu'une seule configuration est active"""
        if self.is_active:
            FeedScoreConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        
        # Valeur par defaut pour les JSON
        if not self.content_multipliers:
            self.content_multipliers = {
                "image": 2.0,
                "video": 1.5,
                "poll": 1.2,
                "link": 1.1,
                "text": 1.0
            }
        
        if not self.engagement_coefficients:
            self.engagement_coefficients = {
                "comment": 3.0,
                "like": 2.0,
                "view": 0.1,
                "share": 1.5
            }
        super().save(*args, **kwargs)
    

class ProfilScoreRecord(ENSPMHubBaseModel):
    """Historique des poids utilisateurs"""
    profil = models.ForeignKey('users.Profil', on_delete=models.CASCADE, related_name='score_records')
    calculated_score = models.FloatField()
    config = models.ForeignKey(FeedScoreConfig, on_delete=models.SET_NULL, null=True, blank=True)
    calculation_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Historique des poids utilisateurs"
        verbose_name_plural = "Historique des poids utilisateurs"
        indexes = [
            models.Index(fields=['profil', '-calculation_time']),
        ]
        ordering = ["-calculation_time"]
        

class PostScoreRecord(ENSPMHubBaseModel):
    """Historique des poids des posts"""
    post = models.ForeignKey('feeds.Post', on_delete=models.CASCADE, related_name='score_records')
    calculated_score = models.FloatField()
    config = models.ForeignKey(FeedScoreConfig, on_delete=models.SET_NULL, null=True, blank=True)
    calculation_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Historique des poids des posts"
        verbose_name_plural = "Historique des poids des posts"
        indexes = [
            models.Index(fields=['post', '-calculation_time']),
        ]
        ordering = ["-calculation_time"]
    
            
     

# opportunities/models.py
from bs4 import BeautifulSoup
from django.db import models
from core.models import ENSPMHubBaseModel
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from core.mixins import ChatReferenceable


class Stage(ENSPMHubBaseModel, ChatReferenceable):
    """Modèle pour les offres de stage"""
    REFERENCE_TYPE = "stage"
    
    TYPE_STAGE_CHOICES = [
        ('ouvrier', 'Ouvrier'),
        ('academique', 'Académique'),
        ('professionnel', 'Professionnel')
    ]
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente de validation'),
        ('active', 'Active'),
        ('expiree', 'Expirée'),
        ('pourvue', 'Pourvue'),
        ('rejetee', 'Rejetée')
    ]

    # Relations
    createur_profil = models.ForeignKey(
        'users.Profil',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='stages_crees',
        verbose_name=_("Créateur")
    )
    organisation = models.ForeignKey(
        'network.Organisation',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='stages',
        verbose_name=_("Organisation")
    )
    
    # Informations principales
    titre = models.CharField(max_length=255, verbose_name=_("Titre du stage"))
    slug = models.SlugField(
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("Slug"),
        help_text=_("Identifiant unique pour les URLs")
    )
    nom_structure = models.CharField(max_length=255, verbose_name=_("Nom de la structure"))
    description = models.TextField(verbose_name=_("Description HTML (rich-text)"))
    description_text = models.TextField(null=True, blank=True, verbose_name=_("Description texte"))
    type_stage = models.CharField(max_length=20, choices=TYPE_STAGE_CHOICES, verbose_name=_("Type de stage"))
    
    # Localisation
    adresse = models.CharField(max_length=150, verbose_name=_("Lieu"))
    ville = models.CharField(max_length=100, null=True, blank=True, verbose_name=_("Ville"))
    pays = CountryField(null=True, blank=True, verbose_name=_("Pays"))
    
    # Contact
    email_contact = models.EmailField(null=True, blank=True, verbose_name=_("Email de contact"))
    telephone_contact = models.CharField(max_length=20, null=True, blank=True, verbose_name=_("Téléphone"))
    
    # Liens
    lien_offre_original = models.URLField(null=True, blank=True, verbose_name=_("Lien offre originale"))
    lien_candidature = models.URLField(null=True, blank=True, verbose_name=_("Lien candidature"))
    
    # Champs de recherche vectorielle
    search_vector = SearchVectorField(null=True, blank=True)
    
    # secteurs
    domaines = models.ManyToManyField(
        'core.Domaine',
        related_name='stages',
        verbose_name=_("Domaine")
    )
    filieres = models.ManyToManyField(
        'core.Filiere',
        related_name='stages',
        verbose_name=_("Filière")
    )
    secteurs = models.ManyToManyField(
        'core.SecteurActivite',
        related_name='stages',
        verbose_name=_("Secteur")
    )
    
    # Dates
    date_debut = models.DateField(null=True, blank=True, verbose_name=_("Date de début"))
    date_fin = models.DateField(null=True, blank=True, verbose_name=_("Date de fin"))
    date_publication = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de publication"))
    
    # Statut et validation
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente', verbose_name=_("Statut"))
    est_valide = models.BooleanField(default=False, verbose_name=_("Validé"))
    validateur_profil = models.ForeignKey(
        'users.Profil',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='stages_valides',
        verbose_name=_("Validateur")
    )
    date_validation = models.DateTimeField(null=True, blank=True, verbose_name=_("Date de validation"))
    commentaire_validation = models.TextField(null=True, blank=True, verbose_name=_("Commentaire de validation"))

    class Meta:
        verbose_name = _("Stage")
        verbose_name_plural = _("Stages")
        db_table = 'opportunities_stages'
        ordering = ['-date_publication']
        indexes = [
            models.Index(fields=['statut', '-date_publication']),
            models.Index(fields=['ville', 'pays']),
            models.Index(fields=['type_stage', 'statut']),
            GinIndex(fields=['search_vector']),
        ]

    def __str__(self):
        return self.titre
    
    def save(self, *args, **kwargs):
        """Extraire le texte du HTML"""
        if self.description:
            soup = BeautifulSoup(self.description, 'html.parser')
            self.description_text = soup.get_text(separator=' ', strip=True)
        super().save(*args, **kwargs)
        
        #  Mettre à jour le vecteur de recherche
        if self.description_text:
            Stage.objects.filter(pk=self.pk).update(
                search_vector=SearchVector('titre', weight='A') + SearchVector('description_text', weight='B')
            )

    def get_chat_preview(self) -> dict:
        return {
            "id": self.id,
            "type": self.REFERENCE_TYPE,
            "titre": "Stage",
            "sous_titre": self.titre,
            "apercu": self.description_text[:100] + "..." if self.description_text else "",
            "url": "/internships/" + self.slug, # type: ignore
            "create_at": self.created_at,
            "update_at": self.updated_at
        }


class Emploi(ENSPMHubBaseModel, ChatReferenceable):
    REFERENCE_TYPE = "emploi"
    """Modèle pour les offres d'emploi"""
    TYPE_EMPLOI_CHOICES = [
        ('temps_plein_terrain', 'Temps plein terrain'),
        ('temps_partiel_terrain', 'Temps partiel terrain'),
        ('temps_plein_ligne', 'Temps plein en ligne'),
        ('temps_partiel_ligne', 'Temps partiel en ligne'),
        ('freelance', 'Freelance'),
        ('contrat', 'Contrat')
    ]
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente de validation'),
        ('active', 'Active'),
        ('expiree', 'Expirée'),
        ('pourvue', 'Pourvue'),
        ('rejetee', 'Rejetée')
    ]

    # Relations
    createur_profil = models.ForeignKey(
        'users.Profil',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='emplois_crees',
        verbose_name=_("Créateur")
    )
    organisation = models.ForeignKey(
        'network.Organisation',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='emplois',
        verbose_name=_("Organisation")
    )
    
    # Informations principales
    titre = models.CharField(max_length=255, verbose_name=_("Titre du poste"))
    slug = models.SlugField(
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("Slug")
    )
    nom_structure = models.CharField(max_length=255, verbose_name=_("Nom de la structure"))
    description = models.TextField(verbose_name=_("Description HTML(rich-text)"))
    description_text = models.TextField(null=True, blank=True, verbose_name=_("Description textuelle"))
    type_emploi = models.CharField(
        max_length=40,
        choices=TYPE_EMPLOI_CHOICES,
        null=True,
        blank=True,
        verbose_name=_("Type d'emploi")
    )
    
    # Localisation
    adresse = models.CharField(max_length=150, verbose_name=_("Lieu"))
    ville = models.CharField(max_length=100, null=True, blank=True, verbose_name=_("Ville"))
    pays = CountryField(null=True, blank=True, verbose_name=_("Pays"))

    
    # Contact
    email_contact = models.EmailField(null=True, blank=True, verbose_name=_("Email de contact"))
    telephone_contact = models.CharField(max_length=20, null=True, blank=True, verbose_name=_("Téléphone"))
    
    # Liens
    lien_offre_original = models.URLField(null=True, blank=True, verbose_name=_("Lien offre originale"))
    lien_candidature = models.URLField(null=True, blank=True, verbose_name=_("Lien candidature"))
    
    # Dates
    date_publication = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de publication"))
    date_expiration = models.DateField(null=True, blank=True, verbose_name=_("Date d'expiration"))
    
    # Salaire
    salaire_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salaire_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Search vector
    search_vector = SearchVectorField(null=True, blank=True)
    
    devise = models.ForeignKey(
        'core.Devise',
        on_delete=models.PROTECT,
        related_name='emplois',
        verbose_name=_("Devise")
    )
    # Statut et validation
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente', verbose_name=_("Statut"))
    est_valide = models.BooleanField(default=False, verbose_name=_("Validé"))
    validateur_profil = models.ForeignKey(
        'users.Profil',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='emplois_valides',
        verbose_name=_("Validateur")
    )
    date_validation = models.DateTimeField(null=True, blank=True, verbose_name=_("Date de validation"))
    commentaire_validation = models.TextField(null=True, blank=True, verbose_name=_("Commentaire de validation"))

    class Meta:
        verbose_name = _("Emploi")
        verbose_name_plural = _("Emplois")
        db_table = 'opportunities_emplois'
        ordering = ['-date_publication']
        indexes = [
            models.Index(fields=['statut', 'est_valide'], name='emploi_statut_est_valide'),
            models.Index(fields=['date_publication'], name='emploi_date_publication'),   
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validation des salaires
        if self.salaire_min and self.salaire_max:
            if self.salaire_min > self.salaire_max:
                raise ValidationError({
                    'salaire_max': _("Le salaire maximum doit être supérieur au minimum")
                })
        
        # Validation de la devise si salaire présent
        if (self.salaire_min or self.salaire_max) and not self.devise:
            raise ValidationError({
                'devise': _("La devise est obligatoire si un salaire est spécifié")
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        soup = BeautifulSoup(self.description, 'html.parser')
        self.description_text = soup.get_text(separator=' ', strip=True)
        super().save(*args, **kwargs)
        
        # Mettre à jour le vecteur de recherche
        if self.description_text:
            Emploi.objects.filter(pk=self.pk).update(
                search_vector=SearchVector('description_text', weight='B') + SearchVector('titre', weight='A')
            )
    def __str__(self):
        return self.titre
    
    def get_chat_preview(self) -> dict:
        return {
            'id': self.pk,
            'type': self.REFERENCE_TYPE,
            "titre": "Emploi",
            "sous_titre": self.titre,
            "apercu": self.description_text[:100] + "..." if self.description_text else "",
            "url": "/jobs/" + self.slug, # type: ignore
            "created_at": self.date_publication,
            "updated_at": self.updated_at
        }


class Formation(ENSPMHubBaseModel, ChatReferenceable):
    REFERENCE_TYPE = 'formation'
    """Modèle pour les formations"""
    TYPE_FORMATION_CHOICES = [
        ('en_ligne', 'En ligne'),
        ('presentiel', 'Présentiel'),
        ('hybride', 'Hybride')
    ]
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente de validation'),
        ('active', 'Active'),
        ('expiree', 'Expirée'),
        ('annulee', 'Annulée'),
        ('rejetee', 'Rejetée')
    ]

    # Relations
    createur_profil = models.ForeignKey(
        'users.Profil',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='formations_creees',
        verbose_name=_("Créateur")
    )
    organisation = models.ForeignKey(
        'network.Organisation',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='formations',
        verbose_name=_("Organisation")
    )
    
    # Informations principales
    titre = models.CharField(max_length=255, verbose_name=_("Titre de la formation"))
    slug = models.SlugField(
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("Slug")
    )
    nom_structure = models.CharField(max_length=255, verbose_name=_("Nom de la structure"))
    description = models.TextField(verbose_name=_("Description HTML (rich text)"))
    description_text = models.TextField(null=True, blank=True, verbose_name=_("Description textuelle"))
    type_formation = models.CharField(
        max_length=20,
        choices=TYPE_FORMATION_CHOICES,
        verbose_name=_("Type de formation")
    )
    
    # Localisation
    adresse = models.CharField(max_length=150, null=True, blank=True, verbose_name=_("Lieu"))
    ville = models.CharField(max_length=100, null=True, blank=True, verbose_name=_("Ville"))
    pays = CountryField(null=True, blank=True, verbose_name=_("Pays"))
    
    # Contact
    email_contact = models.EmailField(null=True, blank=True, verbose_name=_("Email de contact"))
    telephone_contact = models.CharField(max_length=20, null=True, blank=True, verbose_name=_("Téléphone"))
    
    # Liens
    lien_formation = models.URLField(null=True, blank=True, verbose_name=_("Lien de la formation"))
    lien_inscription = models.URLField(null=True, blank=True, verbose_name=_("Lien d'inscription"))
    
    # Dates
    date_debut = models.DateField(null=True, blank=True, verbose_name=_("Date de début"))
    date_fin = models.DateField(null=True, blank=True, verbose_name=_("Date de fin"))
    date_publication = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de publication"))
    
    # Prix
    est_payante = models.BooleanField(default=False, verbose_name=_("Formation payante"))
    prix = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Search vector
    search_vector = SearchVectorField(null=True, blank=True)
    
    # Devise
    devise = models.ForeignKey(
        'core.Devise',
        on_delete=models.SET_NULL,
        related_name='formations',
        verbose_name=_("Devise"),
        help_text=_("Devise de la formation (si payante)"),
        null=True,
        blank=True
    )
    
    # Durée
    duree_heures = models.IntegerField(null=True, blank=True, verbose_name=_("Durée en heures"))
    
    # Statut et validation
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente', verbose_name=_("Statut"))
    est_valide = models.BooleanField(default=False, verbose_name=_("Validé"))
    validateur_profil = models.ForeignKey(
        'users.Profil',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='formations_validees',
        verbose_name=_("Validateur")
    )
    date_validation = models.DateTimeField(null=True, blank=True, verbose_name=_("Date de validation"))
    commentaire_validation = models.TextField(null=True, blank=True, verbose_name=_("Commentaire de validation"))

    class Meta:
        verbose_name = _("Formation")
        verbose_name_plural = _("Formations")
        db_table = 'opportunities_formations'
        ordering = ['-date_publication']

    def __str__(self):
        return self.titre
    
    def save(self, *args, **kwargs):
        """Extraire le texte du HTML"""
        if self.description:
            soup = BeautifulSoup(self.description, 'html.parser')
            self.description_text = soup.get_text(separator=' ', strip=True)
        super().save(*args, **kwargs)
        
        # Mettre à jour le vecteur de recherche
        if self.description_text:
            Formation.objects.filter(pk=self.pk).update(
                search_vector=SearchVector('titre', weight='A') + SearchVector('description_text', weight='B')
            )
    
    def get_chat_preview(self) -> dict:
        return {
            "id": self.id,
            "type": self.REFERENCE_TYPE,
            "titre": "Formation",
            "sous_titre": self.titre,
            "apercu": self.description_text[:100] + "..." if self.description_text else "",
            "url": "/trainings/" + self.slug, # type: ignore
            "create_at": self.date_publication,
            "update_at": self.updated_at
        }
 
    
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from core.mixins import ChatReferenceable
from core.models import ENSPMHubBaseModel
from django.core.validators import FileExtensionValidator


class Groupe(ENSPMHubBaseModel):
    class TypeAcces(models.TextChoices):
        PUBLIC = 'public', _('Public')
        PRIVE = 'prive', _('Privé')
    class Status(models.TextChoices):
        ACTIF = 'actif', _('Actif')
        INACTIF = 'inactif', _('Inactif')
        
    class Meta:
        db_table = 'network_groupe'
        ordering = ['-created_at']
        verbose_name = _('groupe')
        verbose_name_plural = _('groupes')
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['type_acces']),
        ]
    
    nom = models.CharField(max_length=255, verbose_name=_('nom'))
    slug = models.SlugField(unique=True, verbose_name=_('slug'))
    description = models.TextField(blank=True, verbose_name=_('description'))
    image = models.ImageField(upload_to='network/groups/', null=True, blank=True, verbose_name=_('image'))
    type_acces = models.CharField(
        max_length=10,
        choices=TypeAcces.choices,
        default=TypeAcces.PUBLIC,
        verbose_name=_('type d\'accès')
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.INACTIF,
        verbose_name=_('status')
    )
    est_ferme = models.BooleanField(default=False, verbose_name=_('fermé'))
    createur = models.ForeignKey(
        'users.Profil',
        on_delete=models.SET_NULL,
        null=True,
        related_name='groupes_crees',
        verbose_name=_('créateur')
    )

    def __str__(self):
        return self.nom
    
    def is_active(self):
        """Vérifie si le groupe est actif"""
        return self.status == self.Status.ACTIF
    
    def get_nombre_membres(self):
        """Retourne le nombre de membres actifs"""
        return self.membres.filter(deleted=False).count()
    
    def est_membre(self, profil):
        """Vérifie si un profil est membre du groupe"""
        return self.membres.filter(profil=profil, deleted=False).exists()
    
    def est_admin(self, profil):
        """Vérifie si un profil est administrateur du groupe"""
        return self.membres.filter(
            profil=profil,
            role=MembreGroupe.Role.ADMIN,
            deleted=False
        ).exists()

class MembreGroupe(ENSPMHubBaseModel):
    class Role(models.TextChoices):
        MEMBRE = 'membre', _('Membre')
        ADMIN = 'admin', _('Administrateur')
    
    class Meta:
        db_table = 'network_membre_groupe'
        verbose_name = _('membre du groupe')
        verbose_name_plural = _('membres du groupe')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['groupe', 'role']),
        ]
    
    groupe = models.ForeignKey(
        Groupe,
        on_delete=models.CASCADE,
        related_name='membres',
        verbose_name=_('groupe')
    )
    profil = models.ForeignKey(
        'users.Profil',
        on_delete=models.CASCADE,
        related_name='membre_groupes',
        verbose_name=_('profil')
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBRE,
        verbose_name=_('rôle')
    )

    date_membre = models.DateTimeField(auto_now_add=True, verbose_name=_('date de membre'))

    # Nouveaux champs pour la refactorisation
    derniere_lecture = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('dernière lecture'),
        help_text=_('Dernière date de lecture des messages du groupe')
    )
    messages_non_lus = models.PositiveIntegerField(
        default=0,
        verbose_name=_('messages non lus')
    )
    premiere_visite_messages = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('première visite des messages')
    )
    
    def __str__(self):
        return f"{self.profil} - {self.groupe} ({self.get_role_display()})"

    @property
    def est_admin(self):
        return self.role == self.Role.ADMIN
    
    def marquer_lu(self):
        self.derniere_lecture = timezone.now()
        self.messages_non_lus = 0
        self.save(update_fields=['derniere_lecture', 'messages_non_lus'])

def validate_file_size(value):
    """Limite la taille des fichiers à 10 Mo"""
    max_size = 25 * 1024 * 1024  # 10 Mo
    if value.size > max_size:
        raise ValidationError(f'La taille du fichier ne doit pas dépasser 10 Mo.')

def validate_file_extension(value):
    """Autorise uniquement certains types de fichiers"""
    allowed_extensions = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif', 'mp4', 'mp3']
    return FileExtensionValidator(allowed_extensions=allowed_extensions)(value)

# ============================================
# DEMANDES D'ACCÈS AUX GROUPES
# ============================================
class DemandeAccesGroupe(ENSPMHubBaseModel):
    class Status(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente')
        APPROUVE = 'approuve', _('Approuvé')
        REFUSE = 'refuse', _('Refusé')

    class Meta:
        db_table = 'network_demande_acces_groupe'
        verbose_name = _('demande d\'accès au groupe')
        verbose_name_plural = _('demandes d\'accès aux groupes')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['groupe', 'status']),
            models.Index(fields=['demandeur', 'status']),
        ]

    groupe = models.ForeignKey(
        'network.Groupe',
        on_delete=models.CASCADE,
        related_name='demandes_acces',
        verbose_name=_('groupe')
    )
    demandeur = models.ForeignKey(
        'users.Profil',
        on_delete=models.CASCADE,
        related_name='demandes_acces_groupes',
        verbose_name=_('demandeur')
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.EN_ATTENTE,
        verbose_name=_('status')
    )
    message = models.TextField(
        blank=True,
        verbose_name=_('message de demande'),
        help_text=_('Message optionnel expliquant la demande')
    )
    date_traitement = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('date de traitement')
    )
    traite_par = models.ForeignKey(
        'users.Profil',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demandes_traitees',
        verbose_name=_('traité par')
    )

    def __str__(self):
        return f"Demande de {self.demandeur} pour {self.groupe} ({self.get_status_display()})"

    def clean(self):
        if self.groupe.type_acces != self.groupe.TypeAcces.PRIVE:
            raise ValidationError(_("Les demandes d'accès ne sont possibles que pour les groupes privés."))
        if self.groupe.est_membre(self.demandeur):
            raise ValidationError(_("Le demandeur est déjà membre du groupe."))
        if self.status == self.Status.EN_ATTENTE and DemandeAccesGroupe.objects.filter(
            groupe=self.groupe,
            demandeur=self.demandeur,
            status=self.Status.EN_ATTENTE,
            deleted=False
        ).exclude(pk=self.pk).exists():
            raise ValidationError(_("Une demande en attente existe déjà pour ce groupe."))
        super().clean()
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def approuver(self, admin):
        if self.status != self.Status.EN_ATTENTE:
            raise ValidationError(_("Seules les demandes en attente peuvent être approuvées."))
        if not self.groupe.est_admin(admin):
            raise ValidationError(_("Seul un administrateur du groupe peut approuver les demandes."))
        self.status = self.Status.APPROUVE
        self.date_traitement = timezone.now() 
        self.traite_par = admin
        self.save(update_fields=['status', 'date_traitement', 'traite_par', 'updated_at'])
        MembreGroupe.objects.create(groupe=self.groupe, profil=self.demandeur)

    def refuser(self, admin):
        if self.status != self.Status.EN_ATTENTE:
            raise ValidationError(_("Seules les demandes en attente peuvent être refusées."))
        if not self.groupe.est_admin(admin):
            raise ValidationError(_("Seul un administrateur du groupe peut refuser les demandes."))
        self.status = self.Status.REFUSE
        self.date_traitement = timezone.now() 
        self.traite_par = admin
        self.save(update_fields=['status', 'date_traitement', 'traite_par', 'updated_at'])

# ============================================
# UNIFIED CHAT MODELS
# ============================================



class Conversation(ENSPMHubBaseModel):
    """Représente une conversation unifiée (DM ou Groupe)"""
    
    class ConversationType(models.TextChoices):
        DM = 'dm', _('Direct Message')
        GROUP = 'group', _('Groupe')
    type = models.CharField(max_length=10, choices=ConversationType.choices, default=ConversationType.DM)
    groupe = models.OneToOneField(
        'network.Groupe',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='conversation'
    )
    participants = models.ManyToManyField(
        'users.Profil',
        through='ConversationParticipant',
        related_name='conversations',
        verbose_name=_('participants')
    )

    class Meta:
        db_table = 'network_conversation'
        verbose_name = _('conversation')
        verbose_name_plural = _('conversations')
        ordering = ['-updated_at']

    def __str__(self):
        if self.type == self.ConversationType.GROUP and self.groupe:
            return f"Conversation Groupe: {self.groupe.nom}"
        return f"Conversation DM: {self.id}"

class ConversationParticipant(ENSPMHubBaseModel):
    """Table intermédiaire pour les participants d'une conversation"""
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='conversation_participants'
    )
    profil = models.ForeignKey(
        'users.Profil',
        on_delete=models.CASCADE,
        related_name='conversation_participations'
    )
    last_read_at = models.DateTimeField(null=True, blank=True, verbose_name=_('dernière lecture'))
    role = models.CharField(max_length=20, null=True, blank=True, verbose_name=_('rôle'))
    messages_non_lus = models.PositiveIntegerField(default=0, verbose_name=_('messages non lus'))
    joined_at = models.DateTimeField(default=timezone.now, verbose_name=_('date d\'ajout'))

    class Meta:
        db_table = 'network_conversation_participant'
        unique_together = ('conversation', 'profil')
        verbose_name = _('participant à la conversation')
        verbose_name_plural = _('participants à la conversation')

    def __str__(self):
        return f"{self.profil} dans {self.conversation}"

class MessageType(models.TextChoices):
    USER = 'user', _('Utilisateur')
    SYSTEM = 'system', _('Système')

class Message(ENSPMHubBaseModel, ChatReferenceable):
    """Modèle unique pour tous les messages (DM, Groupe, Système)"""
    REFERENCE_TYPE = "message"
    client_id = models.UUIDField(null=True, blank=True, verbose_name=_('ID client'))  # Généré par frontend (optimistic UI)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('conversation')
    )
    type = models.CharField(
        max_length=10,
        choices=MessageType.choices,
        default=MessageType.USER,
        verbose_name=_('type')
    )
    expediteur = models.ForeignKey(
        'users.Profil',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='messages_envoyes',
        verbose_name=_('expéditeur')
    )
    contenu = models.TextField(verbose_name=_('contenu'))

    # Média avec MIME type
    media = models.FileField(upload_to='chat/media/%Y/%m/', null=True, verbose_name=_('média'))
    media_type = models.CharField(max_length=100, null=True, verbose_name=_('type média'))  # image/jpeg, etc.
    media_name = models.CharField(max_length=255, null=True, verbose_name=_('nom média'))
    media_size = models.PositiveIntegerField(null=True, verbose_name=_('taille média'))

    # Reference generique
    reference_content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_('type de contenu')
    )
    reference_object_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_("l'id de la reference")
    )
    reference = GenericForeignKey('reference_content_type', 'reference_object_id')
    reference_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_('type de reference (cache)')
    )
    # Édition
    edited_at = models.DateTimeField(null=True, blank=True, verbose_name=_('date d\'édition'))
    edited_by = models.ForeignKey(
        'users.Profil',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='messages_edites',
        verbose_name=_('édité par')
    )

    class Meta:
        db_table = 'network_message'
        ordering = ['created_at']
        verbose_name = _('message')
        verbose_name_plural = _('messages')
        indexes = [
            models.Index(fields=['conversation', '-created_at']),
            models.Index(fields=['client_id']),
            models.Index(fields=['type', 'conversation']),
            models.Index(fields=['reference_content_type', 'reference_object_id']),
        ]

    def save(self, *args, **kwargs):
        # Auto-renseigner le reference_type depuis le ContentType
        if self.reference_content_type:
            ct = self.reference_content_type
            self.reference_type = ct.model
        super().save(*args, **kwargs)
        
    
    def get_chat_preview(self) -> dict:
        return {
            "id": str(self.pk),
            "type": self.type,
            "titre": self.expediteur.nom_complet if self.expediteur else "Système",
            "apercu": self.contenu,
            "media_type": self.media_type,
            "media_name": self.media_name,
            "media_size": self.media_size,
            "media_url": self.media.url if self.media else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    
    def __str__(self):
        sender = self.expediteur.nom_complet if self.expediteur else "Système"
        return f"[{sender}] {self.contenu[:50]}"

class MessageMeta(ENSPMHubBaseModel):
    """Métadonnées d'un message par utilisateur (ex: lecture)"""
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='metas',
        verbose_name=_('message')
    )
    profil = models.ForeignKey(
        'users.Profil',
        on_delete=models.CASCADE,
        related_name='message_metas',
        verbose_name=_('profil')
    )
    date_lecture = models.DateTimeField(null=True, blank=True, verbose_name=_('date de lecture'))

    class Meta:
        db_table = 'network_message_meta'
        unique_together = ('message', 'profil')
        verbose_name = _('métadonnée de message')
        verbose_name_plural = _('métadonnées de messages')
        indexes = [
            models.Index(fields=['profil', 'date_lecture'])
        ]

    def clean(self):
        if self.media == '':
            self.media = None
            
    def __str__(self):
        return f"Meta for {self.profil} on message {self.message.id}"




from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import ENSPMHubBaseModel, Domaine, Filiere
from core.mixins import ChatReferenceable


# ============================================
# PROFIL MENTOR
# ============================================

class MentorProfile(ENSPMHubBaseModel, ChatReferenceable):
    """
    Profil de mentor créé par un alumni
    Déclare ses expertises (filières + domaines) et disponibilité
    """
    REFERENCE_TYPE = "mentor_profile"

    class Status(models.TextChoices):
        EN_ATTENTE = 'EN_ATTENTE', _('En attente')
        VALIDE = 'VALIDE', _('Validé')
        REFUSE = 'REFUSE', _('Refusé')

    class Disponibilite(models.IntegerChoices):
        INDISPONIBLE = 0, _("Indisponible")
        FAIBLE = 25, _("Faible disponibilité")
        MODEREE = 50, _("Disponibilité modérée")
        ELEVEE = 75, _("Très disponible")
        MAXIMALE = 100, _("Disponibilité maximale")

    profil = models.OneToOneField(
        'users.Profil',
        on_delete=models.CASCADE,
        related_name='mentor_profile',
        help_text="Alumni qui devient mentor"
    )

    filieres_expertise = models.ManyToManyField(
        Filiere,
        related_name='mentors'
    )

    domaines_expertise = models.ManyToManyField(
        Domaine,
        related_name='mentors'
    )

    disponibilite = models.PositiveSmallIntegerField(
        choices=Disponibilite.choices,
        default=Disponibilite.MODEREE,
        help_text="Niveau de disponibilité pour le mentoring"
    )

    biographie = models.TextField(blank=True)

    est_actif = models.BooleanField(
        default=True,
        help_text="Reçoit des notifications de nouvelles demandes"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.EN_ATTENTE
    )

    nombre_demandes_recues = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'network_mentor_profile'
        ordering = ['-created_at']
        verbose_name = _('Profil Mentor')
        verbose_name_plural = _('Profils Mentors')
    
    def __str__(self):
        return f"{self.profil.nom_complet} - Mentor"

    def get_expertises_texte(self):
        """Retourne une chaîne lisible des expertises"""
        filieres = ", ".join([f.nom for f in self.filieres_expertise.all()[:3]])
        domaines = ", ".join([d.nom for d in self.domaines_expertise.all()[:3]])
        return f"{filieres} | {domaines}"
    
    def get_chat_preview(self) -> dict:
        return {
            "id": str(self.pk),
            "type": self.REFERENCE_TYPE,
            "titre": "Mentoring",
            "sous_titre": self.get_expertises_texte(),
            "apercu": self.biographie[:100] + "..." if self.biographie else "",
            "url": f"/profile/{self.profil.slug}",
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }



class MentorProfileValidation(ENSPMHubBaseModel):
    """
    Historique de validation d'un profil mentor
    """
    mentor_profile = models.ForeignKey(
        MentorProfile,
        on_delete=models.CASCADE,
        related_name='validations',
        verbose_name=_('profil mentor')
    )
    status_avant = models.CharField(max_length=20, choices=MentorProfile.Status.choices)
    status_apres = models.CharField(max_length=20, choices=MentorProfile.Status.choices)
    commentaire = models.TextField(blank=True, verbose_name=_('commentaire'))
    valide_par = models.ForeignKey(
        'users.Profil',
        on_delete=models.SET_NULL,
        null=True,
        related_name='validations_mentors_effectuees',
        verbose_name=_('validé par')
    )

    class Meta:
        db_table = 'network_mentor_profile_validation'
        ordering = ['-created_at']
        verbose_name = _('Validation de profil mentor')
        verbose_name_plural = _('Validations de profils mentors')

    def __str__(self):
        return f"Validation {self.mentor_profile} : {self.status_avant} -> {self.status_apres}"
    