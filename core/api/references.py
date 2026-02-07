"""
core/api/references.py
Endpoints API pour les données de référence
"""

from ninja import Router
from typing import List, Optional
from uuid import UUID
from django.http import HttpRequest
from pydantic import UUID4

from .schemas import (
    AnneePromotionOut, CountrieOut, DomaineOut, DomaineComplete, FiliereOut,
    SecteurActiviteOut, SecteurActiviteComplete,
    DeviseOut, TitreHonorifiqueOut, ReseauSocialOut,
    ReferencesAcademiquesOut, ReferencesProfessionnellesOut,
    ReferencesFinancieresOut, ReferencesReseauxOut,
    AllReferencesOut, ErrorAPIResponse
)
from core.services.reference_service import reference_service

# Router pour les endpoints de référence (PUBLIC - pas d'auth requise)
references_router = Router(tags=["Références"])


# ==========================================
# ENDPOINTS INDIVIDUELS
# ==========================================

@references_router.get(
    "/annees-promotion",
    response={200: List[AnneePromotionOut]},
    summary="Liste des années de promotion",
    description="Récupère toutes les années de promotion actives pour les menus déroulants"
)
def get_annees_promotion(request: HttpRequest):
    """
    Récupère la liste des années de promotion.
    Utilisé dans les formulaires d'inscription/profil.
    """
    
    annees = reference_service.get_all_annees_promotion(actives_only=True)
    return 200, annees


@references_router.get(
    "/domaines",
    response={200: List[DomaineOut]},
    summary="Liste des domaines d'études",
    description="Récupère tous les domaines actifs"
)
def get_domaines(request: HttpRequest):
    """
    Récupère la liste des domaines d'études.
    Utilisé dans les formulaires de profil.
    """
    domaines = reference_service.get_all_domaines(actifs_only=True)
    return 200, domaines


@references_router.get(
    "/domaines/{domaine_id}",
    response={200: DomaineComplete, 404: ErrorAPIResponse},
    summary="Détails d'un domaine avec ses filières",
    description="Récupère un domaine spécifique avec toutes ses filières"
)
def get_domaine_detail(request: HttpRequest, domaine_id: UUID4):
    """
    Récupère les détails complets d'un domaine incluant ses filières.
    """
    domaine = reference_service.get_domaine_by_id(domaine_id, include_filieres=True)
    if not domaine:
        return 404, {"detail": "Domaine non trouvé"}
    return 200, domaine


@references_router.get(
    "/filieres",
    response={200: List[FiliereOut]},
    summary="Liste de toutes les filières",
    description="Récupère toutes les filières actives"
)
def get_filieres(request: HttpRequest):
    """
    Récupère toutes les filières.
    """
    filieres = reference_service.get_all_filieres(actives_only=True)
    return 200, filieres


@references_router.get(
    "/filieres/domaine/{domaine_id}",
    response={200: List[FiliereOut], 404: ErrorAPIResponse},
    summary="Filières par domaine",
    description="Récupère les filières d'un domaine spécifique"
)
def get_filieres_by_domaine(request: HttpRequest, domaine_id: UUID4):
    """
    Récupère les filières d'un domaine spécifique.
    Utilisé pour le menu déroulant dépendant du domaine sélectionné.
    """
    filieres = reference_service.get_filieres_by_domaine(domaine_id, actives_only=True)
    if not filieres:
        return 404, {"detail": "Aucune filière trouvée pour ce domaine"}
    return 200, filieres


@references_router.get(
    "/secteurs",
    response={200: List[SecteurActiviteOut]},
    summary="Liste des secteurs d'activité",
    description="Récupère tous les secteurs d'activité actifs"
)
def get_secteurs(request: HttpRequest, parents_only: bool = False):
    """
    Récupère la liste des secteurs d'activité.
    
    Params:
        parents_only: Si True, ne retourne que les secteurs parents (pas les sous-secteurs)
    
    Utilisé dans les formulaires d'organisation.
    """
    secteurs = reference_service.get_all_secteurs(actifs_only=True, parents_only=parents_only)
    return 200, secteurs


@references_router.get(
    "/secteurs/{secteur_id}",
    response={200: SecteurActiviteComplete, 404: ErrorAPIResponse},
    summary="Détails d'un secteur avec ses sous-secteurs",
    description="Récupère un secteur spécifique avec tous ses sous-secteurs"
)
def get_secteur_detail(request: HttpRequest, secteur_id: UUID4):
    """
    Récupère les détails complets d'un secteur incluant ses sous-secteurs.
    """
    secteur = reference_service.get_secteur_by_id(secteur_id, include_children=True)
    if not secteur:
        return 404, {"detail": "Secteur non trouvé"}
    return 200, secteur


@references_router.get(
    "/devises",
    response={200: List[DeviseOut]},
    summary="Liste des devises",
    description="Récupère toutes les devises actives"
)
def get_devises(request: HttpRequest):
    """
    Récupère la liste des devises.
    Utilisé dans les formulaires d'emploi et de formation.
    """
    devises = reference_service.get_all_devises(actives_only=True)
    return 200, devises


@references_router.get(
    "/titres",
    response={200: List[TitreHonorifiqueOut]},
    summary="Liste des titres honorifiques",
    description="Récupère tous les titres honorifiques actifs"
)
def get_titres(request: HttpRequest, type_titre: Optional[str] = None):
    """
    Récupère la liste des titres honorifiques.
    
    Params:
        type_titre: Filtre optionnel par type (academique, professionnel, civilite, honorifique)
    
    Utilisé dans les formulaires de profil.
    """
    if type_titre:
        titres = reference_service.get_titres_by_type(type_titre, actifs_only=True)
    else:
        titres = reference_service.get_all_titres(actifs_only=True)
    return 200, titres


@references_router.get(
    "/reseaux-sociaux",
    response={200: List[ReseauSocialOut]},
    summary="Liste des réseaux sociaux",
    description="Récupère tous les réseaux sociaux actifs"
)
def get_reseaux_sociaux(request: HttpRequest, type_reseau: Optional[str] = None):
    """
    Récupère la liste des réseaux sociaux.
    
    Params:
        type_reseau: Filtre optionnel par type (professionnel, social, academique, technique, portfolio)
    
    Utilisé dans les formulaires de liens réseaux sociaux.
    """
    if type_reseau:
        reseaux = reference_service.get_reseaux_by_type(type_reseau, actifs_only=True)
    else:
        reseaux = reference_service.get_all_reseaux(actifs_only=True)
    return 200, reseaux


# ==========================================
# ENDPOINTS GROUPÉS (Pour optimiser les appels)
# ==========================================

@references_router.get(
    "/academiques",
    response={200: ReferencesAcademiquesOut},
    summary="Toutes les références académiques",
    description="Récupère années, domaines et titres en un seul appel"
)
def get_references_academiques(request: HttpRequest):
    """
    Récupère toutes les références académiques en un seul appel.
    Optimisé pour charger un formulaire de profil complet.
    """
    return 200, {
        "annees_promotion": reference_service.get_all_annees_promotion(actives_only=True),
        "domaines": reference_service.get_all_domaines(actifs_only=True),
        "titres": reference_service.get_all_titres(actifs_only=True),
    }


@references_router.get(
    "/professionnelles",
    response={200: ReferencesProfessionnellesOut},
    summary="Toutes les références professionnelles",
    description="Récupère secteurs et postes en un seul appel"
)
def get_references_professionnelles(request: HttpRequest):
    """
    Récupère toutes les références professionnelles en un seul appel.
    Optimisé pour charger un formulaire d'organisation/emploi.
    """
    return 200, {
        "secteurs": reference_service.get_all_secteurs(actifs_only=True),
    }


@references_router.get(
    "/financieres",
    response={200: ReferencesFinancieresOut},
    summary="Toutes les références financières",
    description="Récupère toutes les devises"
)
def get_references_financieres(request: HttpRequest):
    """
    Récupère toutes les références financières.
    """
    return 200, {
        "devises": reference_service.get_all_devises(actives_only=True),
    }


@references_router.get(
    "/reseaux",
    response={200: ReferencesReseauxOut},
    summary="Tous les réseaux sociaux",
    description="Récupère tous les réseaux sociaux"
)
def get_references_reseaux(request: HttpRequest):
    """
    Récupère tous les réseaux sociaux.
    """
    return 200, reference_service.get_all_reseaux(actifs_only=True),
    

@references_router.get(
    "/pays",
    response={200: List[CountrieOut]},
    summary="Tous les pays",
    description="Récupère tous les pays"
)
def get_references_countries(request: HttpRequest):
    return 200, reference_service.get_all_pays(),
    


@references_router.get(
    "/all",
    response={200: AllReferencesOut},
    summary="TOUTES les références",
    description="Récupère toutes les données de référence en un seul appel (utilisé au chargement de l'app)"
)
def get_all_references(request: HttpRequest):
    """
    Récupère TOUTES les données de référence en un seul appel.
    
    ⚠️ Cet endpoint retourne beaucoup de données.
    À utiliser uniquement au chargement initial de l'application pour pré-remplir
    tous les menus déroulants d'un coup.
    
    Pour des cas d'usage spécifiques, préférez les endpoints individuels.
    """
    return 200, {
        "annees_promotion": reference_service.get_all_annees_promotion(actives_only=True),
        "domaines": reference_service.get_all_domaines(actifs_only=True),
        "filieres": reference_service.get_all_filieres(actives_only=True),
        "secteurs": reference_service.get_all_secteurs(actifs_only=True),
        "devises": reference_service.get_all_devises(actives_only=True),
        "titres": reference_service.get_all_titres(actifs_only=True),
        "reseaux": reference_service.get_all_reseaux(actifs_only=True),
    }