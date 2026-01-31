from ninja import NinjaAPI
from ninja.throttling import AnonRateThrottle, AuthRateThrottle
from django.http import HttpRequest, JsonResponse
from ninja.errors import ValidationError, HttpError, AuthenticationError, AuthorizationError
from django.http import Http404
from django.conf import settings
import logging

from core.api.auth import auth_router
from core.api.references import references_router
from users.api.users import users_router
from users.api.experiences import experience_router
from feeds.api.views import posts_router
from opportunities.api.views import (
    stages_router,
    emplois_router,
    formations_router
)
from core.api.exceptions import BaseAPIException

logger = logging.getLogger(__name__)

api_v1 = NinjaAPI(
    title="ENSPM Hub API V1",
    version="1.0.0",
    description="API V1 for ENSPM Hub",
    throttle=[
        AnonRateThrottle('10/s'),
        AuthRateThrottle('100/s')
    ]
)


@api_v1.get("/", tags=["Général"])
def root(request: HttpRequest):
    """Endpoint racine de l'API."""
    return {
        "message": "Bienvenue sur l'API ENSPM Hub",
        "version": "1.0.0",
        "documentation": "/api/v1/docs",
        "modules": {
            "users": "/api/v1/users/",
            "network": "/api/v1/network/",
            "stages": "/api/v1/internships/",
            "emplois": "/api/v1/jobs/",
            "formations": "/api/v1/trainings/"
        }
    }

users_router.add_router("/experiences/", experience_router)

# Inclusion des routers
api_v1.add_router("/references/", references_router)
api_v1.add_router("/auth/", auth_router)
api_v1.add_router("/users/", users_router)
api_v1.add_router("internships/", stages_router)
api_v1.add_router("jobs/", emplois_router)
api_v1.add_router("trainings/", formations_router)
api_v1.add_router("posts/", posts_router)

# Gestionnaires d'exceptions globaux
@api_v1.exception_handler(ValidationError)
def validation_errors(request, exc):
    """Handler pour les erreurs de validation des schémas Ninja."""
    # Extrait et formate les erreurs pour une meilleure lisibilité
    errors = []
    for error in exc.errors:
        field = ".".join(map(str, error['loc'])) if error['loc'] else 'non_field_error'
        errors.append({
            "field": field,
            "message": error['msg']
        })
    return JsonResponse({"detail": "Erreur de validation.", "errors": errors}, status=422)

@api_v1.exception_handler(AuthenticationError)
def authentication_error(request, exc):
    """Handler pour les erreurs d'authentification (401)."""
    return JsonResponse({"detail": "Authentification requise. Veuillez fournir des identifiants valides."}, status=401)

@api_v1.exception_handler(AuthorizationError)
def authorization_error(request, exc):
    """Handler pour les erreurs de permission (403)."""
    return JsonResponse({"detail": "Permission refusée. Vous n'avez pas les droits nécessaires pour effectuer cette action."}, status=403)

@api_v1.exception_handler(Http404)
def not_found(request, exc):
    """Handler pour les erreurs 404 (ressource non trouvée)."""
    return JsonResponse({"detail": "La ressource demandée n'a pas été trouvée."}, status=404)

@api_v1.exception_handler(HttpError)
def http_error(request, exc):
    """Handler pour les erreurs HTTP génériques levées manuellement."""
    return JsonResponse({"detail": exc.message}, status=exc.status_code)

@api_v1.exception_handler(BaseAPIException)
def custom_api_error(request, exc):
    """Handler pour les exceptions personnalisées de l'API."""
    return JsonResponse({"detail": exc.detail}, status=exc.status_code)

@api_v1.exception_handler(Exception)
def generic_exception_handler(request, exc):
    """Handler pour toutes les autres exceptions non gérées."""
    # Log de l'erreur pour le débogage
    logger.error(f"Erreur non gérée sur {request.path}: {exc}", exc_info=True)

    # Réponse générique pour le client
    if settings.DEBUG:
        # En mode DEBUG, fournir plus de détails
        return JsonResponse({
            "detail": "Une erreur interne est survenue.",
            "error_type": type(exc).__name__,
            "error_message": str(exc)
        }, status=500)
    else:
        # En production, message vague pour la sécurité
        return JsonResponse({"detail": "Une erreur inattendue est survenue. L'équipe technique a été notifiée."}, status=500)
