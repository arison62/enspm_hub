import uuid
from django.db import models
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from core.models import ENSPMHubBaseModel
from django.core.validators import FileExtensionValidator
import os

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
    max_size = 5 * 1024 * 1024  # 10 Mo
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

class ConversationType(models.TextChoices):
    DM = 'dm', _('Direct Message')
    GROUP = 'group', _('Groupe')

class Conversation(ENSPMHubBaseModel):
    """Représente une conversation unifiée (DM ou Groupe)"""
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
        if self.type == ConversationType.GROUP and self.groupe:
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

class Message(ENSPMHubBaseModel):
    """Modèle unique pour tous les messages (DM, Groupe, Système)"""
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
    media = models.FileField(upload_to='chat/media/%Y/%m/', null=True, blank=True, verbose_name=_('média'))
    media_type = models.CharField(max_length=100, null=True, blank=True, verbose_name=_('type média'))  # image/jpeg, etc.
    media_name = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('nom média'))
    media_size = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('taille média'))

    # Threads
    reponse_a = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reponses',
        verbose_name=_('réponse à')
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
        ]

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

    def __str__(self):
        return f"Meta for {self.profil} on message {self.message.id}"
