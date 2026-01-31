from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import ENSPMHubBaseModel
from django_countries.fields import CountryField



class Organisation(ENSPMHubBaseModel):
    """Représente les structures partenaires (Entreprises, Startups, etc.)"""
    TYPE_CHOICES = [
        ('entreprise', 'Entreprise'), ('ong', 'ONG'), ('startup', 'Startup'),
        ('institution_publique', 'Institution publique'), ('universite', 'Université'),
        ('association', 'Association'), ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [('active', 'Active'), ('inactive', 'Inactive'), ('en_attente', 'En attente')]

    nom_organisation = models.CharField(max_length=255, verbose_name=_("Nom"))
    slug = models.SlugField(unique=True, db_index=True)
    type_organisation = models.CharField(max_length=30, choices=TYPE_CHOICES)
    secteur_activites = models.ManyToManyField('core.SecteurActivite')
    
    logo = models.ImageField(upload_to='network/orgs/logos/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    site_web = models.URLField(null=True, blank=True)
    
    ville = models.CharField(max_length=100, null=True, blank=True)
    pays = CountryField(null=True, blank=True)
    adresse = models.CharField(max_length=255, null=True, blank=True)
    
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')

    class Meta:
        db_table = 'network_organisation'
        verbose_name = _("Organisation")

    def __str__(self):
        return self.nom_organisation


class MembreOrganisation(ENSPMHubBaseModel):
    """Utilisateurs qui sont membres d'une organisation"""
    ACCES_CHOICES = [
        ('admin', 'Administrateur'), 
        ('membre', 'Membre')
    ]
    
    profil = models.ForeignKey('users.Profil', on_delete=models.CASCADE, related_name='membres_orgs')
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='membres')
    date_membre = models.DateTimeField(auto_now_add=True)
    acces = models.CharField(max_length=20, choices=ACCES_CHOICES, default='membre')

    class Meta:
        db_table = 'network_membre_organisation'
        unique_together = ('profil', 'organisation')


class AbonnementOrganisation(ENSPMHubBaseModel):
    """Utilisateurs qui suivent une page organisation (Followers)"""
    profil = models.ForeignKey('users.Profil', on_delete=models.CASCADE, related_name='abonnements_orgs')
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='abonnes')
    date_abonnement = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'network_abonnement_organisation'
        unique_together = ('profil', 'organisation')