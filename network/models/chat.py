import uuid
from django.db import models
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
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
    
    def __str__(self):
        return f"{self.profil} - {self.groupe} ({self.get_role_display()})"

    @property
    def est_admin(self):
        return self.role == self.Role.ADMIN


# ============================================
# DEMANDES D'ACCÈS AUX GROUPES
# ============================================
class DemandeAccesGroupe(ENSPMHubBaseModel):
    """
    Modèle pour gérer les demandes d'accès à un groupe privé.
    """
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
        """Validations supplémentaires"""
        # Vérifier que le groupe est privé
        if self.groupe.type_acces != self.groupe.TypeAcces.PRIVE:
            raise ValidationError(_("Les demandes d'accès ne sont possibles que pour les groupes privés."))

        # Vérifier que le demandeur n'est pas déjà membre
        if self.groupe.est_membre(self.demandeur):
            raise ValidationError(_("Le demandeur est déjà membre du groupe."))

        # Vérifier qu'il n'y a pas déjà une demande en attente pour ce demandeur et ce groupe
        if self.status == self.Status.EN_ATTENTE and DemandeAccesGroupe.objects.filter(  # ✅ CORRECT
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
        """Approuve la demande et ajoute le demandeur comme membre"""
        if self.status != self.Status.EN_ATTENTE:
            raise ValidationError(_("Seules les demandes en attente peuvent être approuvées."))

        if not self.groupe.est_admin(admin):
            raise ValidationError(_("Seul un administrateur du groupe peut approuver les demandes."))

        self.status = self.Status.APPROUVE
        self.date_traitement = timezone.now() 
        self.traite_par = admin
        self.save(update_fields=['status', 'date_traitement', 'traite_par', 'updated_at'])

        # Ajouter le demandeur comme membre
        MembreGroupe.objects.create(groupe=self.groupe, profil=self.demandeur)


    def refuser(self, admin):
        """Refuse la demande"""
        if self.status != self.Status.EN_ATTENTE:
            raise ValidationError(_("Seules les demandes en attente peuvent être refusées."))

        if not self.groupe.est_admin(admin):
            raise ValidationError(_("Seul un administrateur du groupe peut refuser les demandes."))

        self.status = self.Status.REFUSE
        self.date_traitement = timezone.now() 
        self.traite_par = admin
        self.save(update_fields=['status', 'date_traitement', 'traite_par', 'updated_at'])


    @classmethod
    def get_demandes_en_attente(cls, groupe):
        """Retourne les demandes en attente pour un groupe"""
        return cls.objects.filter(groupe=groupe, status=cls.Status.EN_ATTENTE, deleted=False)
    
    @classmethod
    def demande_existe(cls, groupe, demandeur):
        """Vérifie si une demande en attente existe déjà pour ce groupe et ce demandeur"""
        return cls.objects.filter(
            groupe=groupe,
            demandeur=demandeur,
            status=cls.Status.EN_ATTENTE,
            deleted=False
        ).exists()
    




def validate_file_size(value):
    """Limite la taille des fichiers à 10 Mo"""
    max_size = 5 * 1024 * 1024  # 10 Mo
    if value.size > max_size:
        raise ValidationError(f'La taille du fichier ne doit pas dépasser 10 Mo.')

def validate_file_extension(value):
    """Autorise uniquement certains types de fichiers"""
    allowed_extensions = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif', 'mp4', 'mp3']
    return FileExtensionValidator(allowed_extensions=allowed_extensions)(value)



class MessageBase(ENSPMHubBaseModel):
    """Classe abstraite contenant les champs communs aux messages"""
    
    class Meta:
        abstract = True
    
    expediteur = models.ForeignKey(
        'users.Profil',
        on_delete=models.CASCADE,
        verbose_name=_('expéditeur')
    )
    contenu = models.TextField(verbose_name=_('contenu'))
    piece_jointe = models.FileField(
        upload_to='network/chat/files/',
        null=True,
        blank=True,
        verbose_name=_('pièce jointe'),
        validators=[validate_file_size, validate_file_extension]
    )
    est_lu = models.BooleanField(default=False, verbose_name=_('lu'))

    def marquer_comme_lu(self):
        """Marque le message comme lu"""
        if not self.est_lu:
            self.est_lu = True
            self.save(update_fields=['est_lu', 'updated_at'])


# ============================================
# MESSAGES DE GROUPE
# ============================================

class MessageGroupe(MessageBase):
    """Message dans un chat de groupe"""
    
    class Meta:
        db_table = 'network_message_groupe'
        ordering = ['created_at']
        verbose_name = _('message de groupe')
        verbose_name_plural = _('messages de groupe')
        indexes = [
            models.Index(fields=['groupe', '-created_at']),
            models.Index(fields=['groupe', 'est_lu']),
            models.Index(fields=['expediteur', '-created_at']),
        ]
    
    groupe = models.ForeignKey(
        Groupe,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('groupe')
    )
    reponse_a = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reponses',
        verbose_name=_('réponse à'),
        help_text=_('Message original auquel ce message répond')
    )



    def __str__(self):
        prefix = f"↪️ Réponse à [{self.reponse_a.expediteur}]" if self.reponse_a else ""
        return f"[{self.groupe}] {self.expediteur}: {self.contenu[:50]} {prefix}".strip()
    
    def clean(self):
        """Validation : l'expéditeur doit être membre du groupe et éviter les boucles"""
        if not self.groupe.est_membre(self.expediteur):
            raise ValidationError(
                _("L'expéditeur doit être membre du groupe pour poster un message.")
            )
        
        # Éviter les boucles infinies (un message ne peut pas se répondre à lui-même)
        if self.reponse_a and self.reponse_a == self:
            raise ValidationError(_("Un message ne peut pas être une réponse à lui-même."))
        
        # Limiter la profondeur des réponses (max 3 niveaux pour éviter les threads trop profonds)
        if self.reponse_a:
            profondeur = self._calculer_profondeur()
            if profondeur > 3:
                raise ValidationError(_("La profondeur maximale des réponses est de 3 niveaux."))
        
        # Vérifier que le message auquel on répond appartient au même groupe
        if self.reponse_a and self.reponse_a.groupe != self.groupe:
            raise ValidationError(_("Vous ne pouvez répondre qu'à un message du même groupe."))
        
        super().clean()
    
    def _calculer_profondeur(self):
        """Calcule la profondeur de la chaîne de réponses (récursif avec limite)"""
        profondeur = 0
        msg = self.reponse_a
        while msg and profondeur < 10:  # Limite de sécurité
            profondeur += 1
            msg = msg.reponse_a
        return profondeur
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def est_reponse(self):
        """Indique si ce message est une réponse"""
        return self.reponse_a is not None
    
    @property
    def message_original(self):
        """Retourne le message racine du thread (le premier message non-réponse)"""
        msg = self
        while msg.reponse_a:
            msg = msg.reponse_a
        return msg
    
    @classmethod
    def get_messages_groupe(cls, groupe, limit=None):
        """Retourne les messages d'un groupe, optionnellement limités"""
        queryset = cls.objects.filter(groupe=groupe).select_related('expediteur', 'reponse_a__expediteur')
        if limit:
            queryset = queryset[:limit]
        return queryset
    
    @classmethod
    def get_thread(cls, message_racine):
        """
        Retourne tous les messages d'un thread de conversation (message racine + réponses)
        """
        return cls.objects.filter(
            models.Q(id=message_racine.id) | models.Q(reponse_a=message_racine)
        ).select_related('expediteur', 'reponse_a__expediteur').order_by('created_at')
    
    def get_nombre_reponses(self):
        """Retourne le nombre de réponses directes à ce message"""
        return self.reponses.filter(deleted=False).count()


# ============================================
# MESSAGES DIRECTS (DM)
# ============================================

class MessageDirect(MessageBase):
    """Message direct entre deux utilisateurs"""
    
    class Meta:
        db_table = 'network_message_direct'
        ordering = ['created_at']
        verbose_name = _('message direct')
        verbose_name_plural = _('messages directs')
        indexes = [
            models.Index(fields=['expediteur', '-created_at']),
            models.Index(fields=['destinataire', '-created_at']),
            models.Index(fields=['destinataire', 'est_lu', '-created_at']),
            models.Index(fields=['expediteur', 'destinataire', '-created_at']),
        ]
        constraints = [
            # L'expéditeur ne peut pas être le destinataire
            models.CheckConstraint(
                condition=~models.Q(expediteur=models.F('destinataire')),
                name='expediteur_different_destinataire_dm'
            ),
        ]
    
    destinataire = models.ForeignKey(
        'users.Profil',
        on_delete=models.CASCADE,
        related_name='received_messages',
        verbose_name=_('destinataire')
    )


    def __str__(self):
        return f"{self.expediteur} → {self.destinataire}: {self.contenu[:50]}"
    
    def clean(self):
        """Validation supplémentaire"""
        # L'expéditeur ne peut pas s'envoyer un message à lui-même
        if self.expediteur == self.destinataire:
            raise ValidationError(_("Vous ne pouvez pas vous envoyer un message à vous-même."))
        
        super().clean()
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_conversation(cls, profil1, profil2):
        """
        Retourne tous les messages entre deux profils (bidirectionnel)
        """
        return cls.objects.filter(
            models.Q(expediteur=profil1, destinataire=profil2) |
            models.Q(expediteur=profil2, destinataire=profil1)
        ).select_related('expediteur', 'destinataire').order_by('created_at')
    
    @classmethod
    def get_conversations_recentes(cls, profil):
        """
        Retourne les conversations récentes d'un profil (dernier message avec chaque contact)
        """
        # Sous-requête pour obtenir le dernier message avec chaque contact
        from django.db.models import Max, Q
        
        # Messages envoyés ou reçus par le profil
        messages = cls.objects.filter(
            Q(expediteur=profil) | Q(destinataire=profil)
        ).values('expediteur', 'destinataire').annotate(
            last_message_time=Max('created_at')
        ).order_by('-last_message_time')
        
        # Récupérer les IDs des profils avec qui le profil a discuté
        contact_ids = set()
        for msg in messages:
            if msg['expediteur'] == profil.pk:
                contact_ids.add(msg['destinataire'])
            else:
                contact_ids.add(msg['expediteur'])
        
        return contact_ids
    
    @classmethod
    def get_non_lus_count(cls, destinataire):
        """Compte les messages directs non lus pour un destinataire"""
        return cls.objects.filter(destinataire=destinataire, est_lu=False).count()
    
    @classmethod
    def marquer_conversation_comme_lue(cls, expediteur, destinataire):
        """Marque tous les messages d'une conversation comme lus pour le destinataire"""
        cls.objects.filter(
            expediteur=expediteur,
            destinataire=destinataire,
            est_lu=False
        ).update(est_lu=True)


