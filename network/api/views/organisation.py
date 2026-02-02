from typing import List
from uuid import UUID
from ninja import Router, Query
from core.api.auth import django_auth
from network.services.organisation import OrganisationService
from network.api.schemas.organisation import (
    OrganisationOut, OrganisationCreate, OrganisationUpdate, OrganisationFilter,
    MembreOrganisationOut, MembreOrganisationCreate, MembreOrganisationUpdate,
    AbonnementOrganisationOut
)

organisation_router = Router(tags=["Organisations"])

# ============================================
# GESTION DES ORGANISATIONS
# ============================================

@organisation_router.post("/", response={201: OrganisationOut}, auth=django_auth)
def create_organisation(request, payload: OrganisationCreate):
    organisation = OrganisationService.creer_organisation(
        acting_user=request.user,
        **payload.dict()
    )
    return 201, organisation

@organisation_router.patch("/{organisation_id}/", response=OrganisationOut, auth=django_auth)
def update_organisation(request, organisation_id: UUID, payload: OrganisationUpdate):
    organisation = OrganisationService.modifier_organisation(
        acting_user=request.user,
        organisation_id=organisation_id,
        **payload.dict(exclude_unset=True)
    )
    return organisation

@organisation_router.delete("/{organisation_id}/", response={204: None}, auth=django_auth)
def delete_organisation(request, organisation_id: UUID):
    OrganisationService.supprimer_organisation(
        acting_user=request.user,
        organisation_id=organisation_id
    )
    return 204, None

@organisation_router.get("/", response=List[OrganisationOut], auth=django_auth)
def search_organisations(request, filters: Query[OrganisationFilter]):
    return OrganisationService.rechercher_organisations(
        acting_user=request.user,
        **filters.dict(exclude_none=True)
    )

@organisation_router.get("/{organisation_id}/stats/", auth=django_auth)
def get_organisation_stats(request, organisation_id: UUID):
    return OrganisationService.obtenir_statistiques_organisation(
        acting_user=request.user,
        organisation_id=organisation_id
    )

# ============================================
# GESTION DES MEMBRES
# ============================================

@organisation_router.post("/{organisation_id}/membres/", response={201: MembreOrganisationOut}, auth=django_auth)
def add_member(request, organisation_id: UUID, payload: MembreOrganisationCreate):
    membre = OrganisationService.ajouter_membre_organisation(
        acting_user=request.user,
        organisation_id=organisation_id,
        **payload.dict()
    )
    return 201, membre

@organisation_router.patch("/membres/{membre_id}/", response=MembreOrganisationOut, auth=django_auth)
def update_member_access(request, membre_id: UUID, payload: MembreOrganisationUpdate):
    return OrganisationService.modifier_acces_membre(
        acting_user=request.user,
        membre_id=membre_id,
        **payload.dict()
    )

@organisation_router.delete("/membres/{membre_id}/", response={204: None}, auth=django_auth)
def remove_member(request, membre_id: UUID):
    OrganisationService.retirer_membre_organisation(
        acting_user=request.user,
        membre_id=membre_id
    )
    return 204, None

@organisation_router.get("/{organisation_id}/membres/", response=List[MembreOrganisationOut], auth=django_auth)
def list_members(request, organisation_id: UUID, acces: str = None):
    return OrganisationService.obtenir_membres_organisation(
        acting_user=request.user,
        organisation_id=organisation_id,
        acces=acces
    )

# ============================================
# GESTION DES ABONNEMENTS (FOLLOWERS)
# ============================================

@organisation_router.post("/{organisation_id}/s-abonner/", response={201: AbonnementOrganisationOut}, auth=django_auth)
def follow_organisation(request, organisation_id: UUID):
    abonnement = OrganisationService.s_abonner_organisation(
        acting_user=request.user,
        organisation_id=organisation_id
    )
    return 201, abonnement

@organisation_router.post("/{organisation_id}/se-desabonner/", response={204: None}, auth=django_auth)
def unfollow_organisation(request, organisation_id: UUID):
    OrganisationService.se_desabonner_organisation(
        acting_user=request.user,
        organisation_id=organisation_id
    )
    return 204, None

@organisation_router.get("/{organisation_id}/abonnes/", response=List[AbonnementOrganisationOut], auth=django_auth)
def list_followers(request, organisation_id: UUID):
    return OrganisationService.obtenir_abonnes_organisation(
        acting_user=request.user,
        organisation_id=organisation_id
    )
