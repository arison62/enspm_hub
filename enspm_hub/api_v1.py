from ninja import NinjaAPI
from ninja.throttling import AnonRateThrottle, AuthRateThrottle
from django.http import HttpRequest, JsonResponse
from ninja.errors import ValidationError, HttpError, AuthenticationError, AuthorizationError
from django.http import Http404
from django.conf import settings
import logging

from core.api.auth import auth_router
from core.api.references import references_router
from core.api.notifications import notifications_router
from users.api.users import users_router
from users.api.experiences import experience_router
from feeds.api.views import posts_router
from opportunities.api.views import (
    stages_router,
    emplois_router,
    formations_router
)
from network.api.views import network_router
from core.api.exceptions import BaseAPIException, ErrorCode

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
        "version": "1.0.0 git push --set-upstream origin module_network",
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
api_v1.add_router("/notifications/", notifications_router)
api_v1.add_router("/network/", network_router)
api_v1.add_router("/auth/", auth_router)
api_v1.add_router("/users/", users_router)
api_v1.add_router("internships/", stages_router)
api_v1.add_router("jobs/", emplois_router)
api_v1.add_router("trainings/", formations_router)
api_v1.add_router("posts/", posts_router)

# ------------------------------
# Validation Ninja
# ------------------------------
@api_v1.exception_handler(ValidationError)
def validation_errors(request, exc):
    errors = []

    for error in exc.errors:
        field = ".".join(map(str, error['loc'])) if error['loc'] else 'non_field_error'
        errors.append({
            "field": field,
            "message": error['msg']
        })

    return JsonResponse(
        {
            "detail": "Erreur de validation.",
            "error_code": ErrorCode.VALIDATION_ERROR,
            "error_message": "Les données envoyées sont invalides.",
            "errors": errors
        },
        status=422
    )


# ------------------------------
# Authentification
# ------------------------------
@api_v1.exception_handler(AuthenticationError)
def authentication_error(request, exc):
    return JsonResponse(
        {
            "detail": "Authentification requise.",
            "error_code": ErrorCode.UNAUTHORIZED,
            "error_message": str(exc) or "Identifiants invalides"
        },
        status=401
    )


# ------------------------------
# Autorisation
# ------------------------------
@api_v1.exception_handler(AuthorizationError)
def authorization_error(request, exc):
    return JsonResponse(
        {
            "detail": "Permission refusée.",
            "error_code": ErrorCode.PERMISSION_DENIED,
            "error_message": str(exc) or "Accès interdit"
        },
        status=403
    )


# ------------------------------
# 404 Django
# ------------------------------
@api_v1.exception_handler(Http404)
def not_found(request, exc):
    return JsonResponse(
        {
            "detail": "Ressource introuvable.",
            "error_code": ErrorCode.NOT_FOUND,
            "error_message": str(exc) or "La ressource demandée n'existe pas"
        },
        status=404
    )


# ------------------------------
# HttpError Ninja
# ------------------------------
@api_v1.exception_handler(HttpError)
def http_error(request, exc):
    return JsonResponse(
        {
            "detail": "Erreur HTTP.",
            "error_code": ErrorCode.HTTP_ERROR,
            "error_message": exc.message
        },
        status=exc.status_code
    )


# ------------------------------
# Exceptions métier personnalisées
# ------------------------------
@api_v1.exception_handler(BaseAPIException)
def custom_api_error(request, exc: BaseAPIException):

    return JsonResponse(
        {
            "detail": "Erreur métier.",
            "error_code": exc.code,
            "error_message": exc.message
        },
        status=exc.status_code
    )


# ------------------------------
# Fallback global
# ------------------------------
@api_v1.exception_handler(Exception)
def generic_exception_handler(request, exc):

    logger.error(
        f"Erreur non gérée sur {request.path}: {exc}",
        exc_info=True
    )

    if settings.DEBUG:
        return JsonResponse(
            {
                "detail": "Erreur interne serveur.",
                "error_code": ErrorCode.INTERNAL_ERROR,
                "error_message": str(exc),
                "error_type": type(exc).__name__
            },
            status=500
        )

    return JsonResponse(
        {
            "detail": "Une erreur inattendue est survenue.",
            "error_code": ErrorCode.INTERNAL_ERROR,
            "error_message": "Erreur interne serveur"
        },
        status=500
    )