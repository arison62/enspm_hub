# opportunities/models.py
from bs4 import BeautifulSoup
from django.db import models
from core.models import ENSPMHubBaseModel
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField


class Stage(ENSPMHubBaseModel):
    """Modèle pour les offres de stage"""
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
        'organizations.Organisation',
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
        db_table = 'stage'
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


class Emploi(ENSPMHubBaseModel):
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
        'organizations.Organisation',
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
        db_table = 'emploi'
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


class Formation(ENSPMHubBaseModel):
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
        'organizations.Organisation',
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
        db_table = 'formation'
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
    
 
    
