from django.db import models
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from core.models import ENSPMHubBaseModel
from django.core.validators import FileExtensionValidator

class Groupe(ENSPMHubBaseModel):
    class TypeAcces(models.TextChoices):
        PUBLIC = 'public', _('Public')
        PRIVE = 'prive', _('Privé')
    
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
    createur = models.ForeignKey(
        'users.Profil',
        on_delete=models.SET_NULL,
        null=True,
        related_name='groupes_crees',
        verbose_name=_('créateur')
    )

    def __str__(self):
        return self.nom
    
    
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
        unique_together = ('groupe', 'profil')
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

    




def validate_file_size(value):
    """Limite la taille des fichiers à 10 Mo"""
    max_size = 10 * 1024 * 1024  # 10 Mo
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


