from typing import List, Optional
from ninja import ModelSchema, Schema
from pydantic import UUID4, field_validator, Field
from network.models import Organisation, MembreOrganisation, AbonnementOrganisation
from core.api.schemas import SecteurActiviteOut
from users.api.schemas import ProfilBaseOut

class OrganisationOut(ModelSchema):
    secteur_activites : Optional[List[SecteurActiviteOut]] = None
    logo_url : Optional[str] = None
    class Meta:
        model = Organisation
        fields = [
            'id',
            'nom_organisation',
            'slug',
            'type_organisation',
            'site_web',
            'description',
            'ville',
            'adresse',
            'statut',
            'created_at',
            'updated_at',
        ]
    
    @staticmethod
    def resolve_logo_url(obj):
        return obj.logo.url if obj.logo else None
        

class OrganisationCreate(Schema):
    nom_organisation : str
    description : str
    type_organisation : str
    site_web : Optional[str] = None
    adresse : Optional[str] = None
    ville : Optional[str] = None
    pays : Optional[str] = None
    secteur_activites : Optional[List[UUID4]] = None
    
    @field_validator('type_organisation')
    def validate_nom_organisation(cls, value):
        if value not in [choice[0] for choice in Organisation.TYPE_CHOICES]:
            raise ValueError('Type d\'organisation invalide')
        return value

class OrganisationUpdate(Schema):
    nom_organisation : Optional[str] = None
    description : Optional[str] = None
    type_organisation : Optional[str] = None
    site_web : Optional[str] = None
    adresse : Optional[str] = None
    ville : Optional[str] = None
    pays : Optional[str] = None
    statut : Optional[str] = None
    
    @field_validator('type_organisation')
    def validate_nom_organisation(cls, value):
        if value not in [choice[0] for choice in Organisation.TYPE_CHOICES]:
            raise ValueError('Type d\'organisation invalide')
        return value
    
    @field_validator('statut')
    def validate_statut(cls, value):
        if value is not None and value not in [choice[0] for choice in Organisation.STATUT_CHOICES]:
            raise ValueError('Statut d\'organisation invalide')
        return value

class MembreOrganisationOut(ModelSchema):
    profil: ProfilBaseOut
    class Meta:
        model = MembreOrganisation
        fields = ['id', 'date_membre', 'acces', 'created_at']

class MembreOrganisationCreate(Schema):
    profil_id: UUID4
    acces: str = 'membre'

    @field_validator('acces')
    def validate_acces(cls, value):
        if value not in [choice[0] for choice in MembreOrganisation.ACCES_CHOICES]:
            raise ValueError('Accès invalide')
        return value

class MembreOrganisationUpdate(Schema):
    acces: str

    @field_validator('acces')
    def validate_acces(cls, value):
        if value not in [choice[0] for choice in MembreOrganisation.ACCES_CHOICES]:
            raise ValueError('Accès invalide')
        return value

class AbonnementOrganisationOut(ModelSchema):
    profil: ProfilBaseOut
    class Meta:
        model = AbonnementOrganisation
        fields = ['id', 'date_abonnement', 'created_at']

class OrganisationFilter(Schema):
    query: Optional[str] = None
    type_organisation: Optional[str] = None
    secteur_activites: Optional[List[UUID4]] = Field(None, alias="secteur_activites[]")
    ville: Optional[str] = None
    pays: Optional[str] = None
    statut: Optional[str] = None
