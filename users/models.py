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
        db_table = 'profil'

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
        db_table = 'experience_professionnelle'
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
        db_table = 'lien_reseau_social_profil'

    def __str__(self):
        return f"{self.reseau.nom} - {self.profil.nom_complet}"
