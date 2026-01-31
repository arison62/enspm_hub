from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import ENSPMHubBaseModel, Domaine, Filiere


# ============================================
# PROFIL MENTOR
# ============================================

class MentorProfile(ENSPMHubBaseModel):
    """
    Profil de mentor créé par un alumni
    Déclare ses expertises (filières + domaines) et disponibilité
    """
    profil = models.OneToOneField(
        'users.Profil', 
        on_delete=models.CASCADE, 
        related_name='mentor_profile',
        help_text="Alumni qui devient mentor"
    )
    
    # Expertises déclarées
    filieres_expertise = models.ManyToManyField(
        Filiere, 
        related_name='mentors',
        help_text="Filières dans lesquelles je peux mentorer"
    )
    domaines_expertise = models.ManyToManyField(
        Domaine, 
        related_name='mentors',
        help_text="Domaines dans lesquels j'ai de l'expérience"
    )
    
    # Disponibilité et préférences
    disponibilite = models.CharField(
        max_length=200,
        blank=True,
        help_text="Ex: 2h/semaine, Soirées, Week-ends"
    )
    biographie = models.TextField(
        blank=True,
        help_text="Présentez-vous et votre expérience de mentorat"
    )

    
    # Capacité
    nombre_max_mentees = models.PositiveSmallIntegerField(
        default=3,
        help_text="Nombre maximum de mentorés simultanés"
    )
    est_actif = models.BooleanField(
        default=True,
        help_text="Reçoit des notifications de nouvelles demandes"
    )
    
    # Statistiques (mises à jour automatiquement)
    nombre_demandes_recues = models.PositiveIntegerField(default=0)
    nombre_demandes_acceptees = models.PositiveIntegerField(default=0)
    nombre_mentees_actuels = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'network_mentor_profile'
        ordering = ['-created_at']
        verbose_name = _('Profil Mentor')
        verbose_name_plural = _('Profils Mentors')
    
    def __str__(self):
        return f"{self.profil.nom_complet} - Mentor"
    
    def get_nombre_places_disponibles(self):
        """Nombre de places encore disponibles"""
        return self.nombre_max_mentees - self.nombre_mentees_actuels
    
    def a_de_la_place(self):
        """Vérifie si le mentor peut prendre un nouveau mentee"""
        return self.est_actif and self.get_nombre_places_disponibles() > 0
    
    def get_expertises_texte(self):
        """Retourne une chaîne lisible des expertises"""
        filieres = ", ".join([f.nom for f in self.filieres_expertise.all()[:3]])
        domaines = ", ".join([d.nom for d in self.domaines_expertise.all()[:3]])
        return f"Filières: {filieres} | Domaines: {domaines}"
    
    def est_compatible_avec_demande(self, demande):
        """
        Vérifie si une demande correspond au profil du mentor
        Basé sur filières et/ou domaines
        """
        # Si la demande cible spécifiquement ce mentor, c'est compatible
        if demande.mentor_cible == self:
            return True
        
        # Sinon, vérifier les correspondances filières/domaines
        correspondance_filiere = False
        correspondance_domaine = False
        
        if demande.filieres.exists():
            correspondance_filiere = self.filieres_expertise.filter(
                id__in=demande.filieres.values_list('id', flat=True)
            ).exists()
        
        if demande.domaines.exists():
            correspondance_domaine = self.domaines_expertise.filter(
                id__in=demande.domaines.values_list('id', flat=True)
            ).exists()
        
        # Compatible si au moins une filière OU un domaine correspond
        return correspondance_filiere or correspondance_domaine
    



class DemandeMentoring(ENSPMHubBaseModel):
    """
    Demande de mentoring créée par un étudiant
    
    Deux modes :
    1. DEMANDE GÉNÉRALE : Spécifie filières + domaines → Système notifie mentors compatibles
    2. DEMANDE DIRECTE : Cible un alumni spécifique → Seul cet alumni reçoit la demande
    """
    STATUS_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('ACCEPTEE', 'Acceptée'),
        ('REFUSEE', 'Refusée'),
        ('ANNULEE', 'Annulée'),
        ('EXPIREE', 'Expirée'),
    ]
    
    # Qui fait la demande ?
    mentee = models.ForeignKey(
        'users.Profil',
        on_delete=models.CASCADE,
        related_name='demandes_mentoring',
        help_text="Étudiant qui demande le mentorat"
    )
    
    # Mode 1 : DEMANDE DIRECTE
    mentor_cible = models.ForeignKey(
        MentorProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demandes_directes',
        help_text="Alumni ciblé spécifiquement (si demande directe)"
    )
    
    # Mode 2 : DEMANDE GÉNÉRALE (filières + domaines)
    filieres = models.ManyToManyField(
        Filiere,
        blank=True,
        help_text="Filières souhaitées pour le mentorat"
    )
    domaines = models.ManyToManyField(
        Domaine,
        blank=True,
        help_text="Domaines souhaités pour le mentorat"
    )
    
    # Contenu de la demande
    message = models.TextField(
        help_text="Message d'introduction à destination du/des mentor(s)"
    )
    objectifs = models.TextField(
        blank=True,
        help_text="Quels sont vos objectifs de mentorat ?"
    )
    attentes = models.TextField(
        blank=True,
        help_text="Qu'attendez-vous de cette relation de mentorat ?"
    )
    
    # Modalités proposées
    disponibilite_souhaitee = models.CharField(
        max_length=200,
        blank=True,
        help_text="Ex: 1h/semaine, Appels mensuels, etc."
    )
    format_prefere = models.CharField(
        max_length=100,
        blank=True,
        help_text="Ex: Visio, Téléphone, Email, En personne"
    )
    
    # Statut et traitement
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='EN_ATTENTE'
    )
    date_expiration = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date limite de réponse (7 jours par défaut)"
    )
    
    # Réponse du mentor
    mentor_repondant = models.ForeignKey(
        MentorProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demandes_traitees',
        help_text="Mentor qui a répondu à la demande"
    )
    reponse_message = models.TextField(
        blank=True,
        help_text="Message de réponse du mentor"
    )
    reponse_date = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Métadonnées
    mentors_notifies = models.ManyToManyField(
        MentorProfile,
        blank=True,
        related_name='demandes_recues',
        help_text="Mentors qui ont été notifiés de cette demande"
    )

    class Meta:
        db_table = 'network_demande_mentoring'
        ordering = ['-created_at']
        verbose_name = _('Demande de Mentoring')
        verbose_name_plural = _('Demandes de Mentoring')
        indexes = [
            models.Index(fields=['mentee', 'status']),
            models.Index(fields=['mentor_cible', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        cible = self.mentor_cible.profil.nom_complet if self.mentor_cible else "Générale"
        return f"Demande {self.mentee.nom_complet} → {cible}"
    
    def est_demande_directe(self):
        """Vérifie si c'est une demande directe à un mentor spécifique"""
        return self.mentor_cible is not None
    
    def est_demande_generale(self):
        """Vérifie si c'est une demande générale (par filières/domaines)"""
        return self.mentor_cible is None and (self.filieres.exists() or self.domaines.exists())
    
    def est_expiree(self):
        """Vérifie si la demande est expirée"""
        if self.date_expiration:
            return timezone.now() > self.date_expiration
        return False
    
    def est_annulee(self):
        """Vérifie si la demande est annulée"""
        return self.status == 'ANNULEE'


# ============================================
# RELATION DE MENTORAT
# ============================================

class RelationMentorat(ENSPMHubBaseModel):
    """
    Relation active de mentorat créée après acceptation d'une demande
    """
    STATUT_CHOICES = [
        ('ACTIVE', 'Active'),
        ('EN_PAUSE', 'En pause'),
        ('TERMINEE', 'Terminée'),
        ('ANNULEE', 'Annulée'),
    ]
    
    mentor = models.ForeignKey(
        MentorProfile,
        on_delete=models.CASCADE,
        related_name='relations_actives'
    )
    mentee = models.ForeignKey(
        'users.Profil',
        on_delete=models.CASCADE,
        related_name='relations_mentorat'
    )
    
    # Origine
    demande_origine = models.ForeignKey(
        DemandeMentoring,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='relations_crees'
    )
    
    # Détails
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='ACTIVE')
    objectifs = models.TextField(blank=True)
    date_debut = models.DateField(auto_now_add=True)
    date_fin_prevue = models.DateField(null=True, blank=True)
    date_fin_reelle = models.DateField(null=True, blank=True)
    
    # Suivi
    nombre_sessions = models.PositiveIntegerField(default=0)
    derniere_session = models.DateTimeField(null=True, blank=True)
    notes_privees_mentor = models.TextField(blank=True)
    notes_privees_mentee = models.TextField(blank=True)

    class Meta:
        db_table = 'network_relation_mentorat'
        ordering = ['-date_debut']
        verbose_name = _('Relation de Mentorat')
        verbose_name_plural = _('Relations de Mentorat')
    
    def __str__(self):
        return f"{self.mentor.profil.nom_complet} ↔ {self.mentee.nom_complet}"
    
    def terminer(self, raison=""):
        """Termine la relation de mentorat"""
        from django.utils import timezone
        
        self.statut = 'TERMINÉE'
        self.date_fin_reelle = timezone.now().date()
        self.save()
        
        # Mettre à jour le mentor
        self.mentor.nombre_mentees_actuels -= 1
        self.mentor.save()
    
    def mettre_en_pause(self):
        """Met la relation en pause"""
        self.statut = 'EN_PAUSE'
        self.save()
    
    def reprendre(self):
        """Reprend la relation après pause"""
        self.statut = 'ACTIVE'
        self.save()
    
    def annuler(self, raison=""):
        """Annule la relation"""
        self.statut = 'ANNULÉE'
        self.date_fin_reelle = timezone.now().date()
        self.save()
        
        self.mentor.nombre_mentees_actuels -= 1
        self.mentor.save()


# ============================================
# SESSIONS DE MENTORAT
# ============================================

class SessionMentorat(ENSPMHubBaseModel):
    """
    Session individuelle de mentorat
    Permet de suivre les échanges entre mentor et mentee
    """
    TYPE_CHOICES = [
        ('VIDEO', 'Visioconférence'),
        ('TELEPHONE', 'Appel téléphonique'),
        ('CHAT', 'Chat/Email'),
        ('PHYSIQUE', 'En personne'),
    ]
    
    STATUT_CHOICES = [
        ('PLANIFIEE', 'Planifiée'),
        ('REALISEE', 'Réalisée'),
        ('ANNULEE', 'Annulée'),
        ('MANQUEE', 'Manquée'),
    ]
    
    relation = models.ForeignKey(
        RelationMentorat,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    
    # Planification
    date_prevue = models.DateTimeField()
    duree_minutes = models.PositiveSmallIntegerField(default=60)
    type_session = models.CharField(max_length=20, choices=TYPE_CHOICES, default='VIDEO')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='PLANIFIEE')
    
    # Lieu/Lien
    lieu_ou_lien = models.CharField(max_length=500, blank=True)
    
    # Contenu
    theme = models.CharField(max_length=255, blank=True)
    objectifs_session = models.TextField(blank=True)
    
    # Compte-rendu
    date_reelle = models.DateTimeField(null=True, blank=True)
    duree_reelle_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    actions_suivantes = models.TextField(blank=True)
    presence_mentee = models.BooleanField(default=True)

    class Meta:
        db_table = 'network_session_mentorat'
        ordering = ['-date_prevue']
        verbose_name = _('Session de Mentorat')
        verbose_name_plural = _('Sessions de Mentorat')
    
    def __str__(self):
        return f"Session {self.date_prevue.strftime('%d/%m/%Y %H:%M')} - {self.relation}"
    
    def marquer_realisee(self, notes="", actions=""):
        """Marque la session comme réalisée"""
        from django.utils import timezone
        
        self.statut = 'REALISEE'
        self.date_reelle = timezone.now()
        self.notes = notes
        self.actions_suivantes = actions
        self.save()
        
        # Mettre à jour la relation
        relation = self.relation
        relation.nombre_sessions += 1
        relation.derniere_session = timezone.now()
        relation.save()


# ============================================
# FEEDBACK
# ============================================

class FeedbackMentorat(ENSPMHubBaseModel):
    """
    Feedback sur une relation de mentorat terminée
    """
    relation = models.ForeignKey(
        RelationMentorat,
        on_delete=models.CASCADE,
        related_name='feedbacks'
    )
    auteur = models.ForeignKey(
        'users.Profil',
        on_delete=models.CASCADE,
        related_name='feedbacks_mentorat'
    )
    
    note = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    commentaires = models.TextField(blank=True)
    recommanderait = models.BooleanField(default=True)

    class Meta:
        db_table = 'network_feedback_mentorat'
        ordering = ['-created_at']
        verbose_name = _('Feedback de Mentorat')
        verbose_name_plural = _('Feedbacks de Mentorat')
    
    def __str__(self):
        return f"Feedback {self.auteur.nom_complet} - {self.relation}"
    