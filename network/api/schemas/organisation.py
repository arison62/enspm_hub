from typing import List, Optional
from ninja import ModelSchema, Schema
from pydantic import UUID4, field_validator
from network.models import Organisation
from core.api.schemas import SecteurActiviteOut

class OrganisationOut(ModelSchema):
    secteur_activites : Optional[List[SecteurActiviteOut]] = None
    log_url : Optional[str] = None
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
    def resolve_log_url(obj):
        return obj.log.url
        

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
        if value not in [choice[0] for choice in Organisation.STATUT_CHOICES]:
            raise ValueError('Statut d\'organisation invalide')
        return value

