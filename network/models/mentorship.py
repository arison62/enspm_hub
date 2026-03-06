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

    est_actif = models.BooleanField(
        default=True,
        help_text="Reçoit des notifications de nouvelles demandes"
    )
    
    # Statut de validation
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.EN_ATTENTE,
        verbose_name=_('statut')
    )

    # Statistiques (mises à jour automatiquement)
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
            "url": f"/network/mentors/{self.id}",
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
    