import logging
from typing import List, Optional
from ninja import Router, Query, File, UploadedFile
from django.http import HttpRequest
from pydantic import UUID4
from core.models import User
from users.api.schemas import (
    BulkCreateResponse,
    BulkUserCreate,
    ChangePassword, 
    LienReseauSocialCreate, 
    LienReseauSocialOut, 
    LienReseauSocialUpdate, 
    MessageResponse, 
    PasswordResponse, 
    PhotoUploadResponse,
    ResetPassword, 
    ToggleStatus, 
    UserCompleteOut, 
    UserCreateAdmin,
    UserDetailOut, 
    UserFilter, 
    UserListResponse, 
    UserStatistics, 
    UserUpdate, 
    ValidationErrorResponse)
from users.models import LienReseauSocialProfil
from users.services.user_service import user_service
from core.utils.pagination import build_pagination_response
from core.services.auth_service import jwt_auth

logger = logging.getLogger("app")

users_router = Router(tags=["Utilisateurs"])


# ==========================================
# Permissions
# ==========================================
def is_admin(request: HttpRequest) -> bool:
    """Vérifie si l'utilisateur a le rôle 'admin_site' ou 'super_admin'."""
    user = request.auth # type: ignore
    return user.role_systeme in ['admin_site', 'super_admin']

def is_owner_or_admin(request: HttpRequest, user_id: str) -> bool:
    """Vérifie si l'utilisateur est le propriétaire ou un admin."""
    return str(request.auth.id) == user_id or is_admin(request) # type: ignore

# ==========================================
# CRUD Utilisateurs
# ==========================================
@users_router.post(
    "/",
    response={201: UserDetailOut, 400: MessageResponse, 401: MessageResponse, 403: MessageResponse, 422: ValidationErrorResponse},
    auth=[jwt_auth],
    summary="Crée un nouvel utilisateur",
    description="Création d'un utilisateur avec profil. Réservé aux administrateurs."
)
def create_user_endpoint(request: HttpRequest, payload: UserCreateAdmin):
    """
    Crée un nouvel utilisateur avec son profil associé.
    Un mot de passe temporaire est généré automatiquement.
    
    **Permissions requises :** admin_site ou super_admin
    """
    if not is_admin(request):
        return 403, {"detail": "Action non autorisée. Rôle administrateur requis."}
    
    try:
        new_user = user_service.create_user(
            acting_user=request.auth, # type: ignore
            user_data=payload.dict(),
            request=request
        )
        return 201, new_user
    except ValueError as e:
        logger.error(f"Erreur création utilisateur : {str(e)}")
        return 400, {"detail": str(e)}
    except Exception as e:
        logger.exception("Erreur inattendue lors de la création d'utilisateur")
        return 400, {"detail": "Une erreur est survenue lors de la création."}

@users_router.post(
    "/bulk",
    response={201: BulkCreateResponse, 400: MessageResponse, 401: MessageResponse, 403: MessageResponse, 422: ValidationErrorResponse},
    auth=jwt_auth,
    summary="Crée plusieurs utilisateurs en bulk",
    description="Création en bulk d'utilisateurs avec profils. Réservé aux administrateurs. Supporte mode 'strict' ou 'skip'."
)
def bulk_create_users_endpoint(request: HttpRequest, payload: BulkUserCreate):
    """
    Crée plusieurs utilisateurs avec leurs profils associés en batch.
    Des mots de passe temporaires sont générés automatiquement.
    Permissions requises : admin_site ou super_admin
    """
    if not is_admin(request):
        return 403, {"detail": "Action non autorisée. Rôle administrateur requis."}
    try:
        result = user_service.bulk_create_users(
        acting_user=request.auth,  # type: ignore
        users_data=[user.dict() for user in payload.users],
        mode=payload.mode,
        batch_size=payload.batch_size, # type: ignore
        request=request
    )
        return 201, result
    except ValueError as e:
        logger.error(f"Erreur création bulk utilisateurs : {str(e)}")
        return 400, {"detail": str(e)}
    except Exception as e:
        logger.exception("Erreur inattendue lors de la création bulk d'utilisateurs")
        return 400, {"detail": "Une erreur est survenue lors de la création bulk."}


@users_router.get(
    "/",
    response={200: UserListResponse, 401: MessageResponse},
    auth=jwt_auth,
    summary="Liste tous les utilisateurs"
)
def list_users_endpoint(
    request: HttpRequest,
    filters: Query[UserFilter],
    page: int = Query(1, ge=1), # type: ignore
    page_size: int = Query(20, ge=1, le=100) # type: ignore
):
    users_list, total_count = user_service.list_users(
        filters=filters.dict(exclude_unset=True),
        page=page,
        page_size=page_size
    )
    
    # Utilisation du helper
    return 200, build_pagination_response(users_list, total_count, page, page_size) # type: ignore

@users_router.get(
    "/statistics",
    response={200: UserStatistics, 401: MessageResponse, 403: MessageResponse},
    auth=jwt_auth,
    summary="Statistiques des utilisateurs",
    description="Récupère les statistiques globales. Réservé aux administrateurs."
)
def get_statistics_endpoint(request: HttpRequest):
    """
    Retourne les statistiques globales des utilisateurs.
    
    **Permissions requises :** admin_site ou super_admin
    """
    if not is_admin(request):
        return 403, {"detail": "Action non autorisée. Rôle administrateur requis."}
    
    try:
        stats = user_service.get_user_statistics()
        return 200, stats
    except Exception as e:
        logger.exception("Erreur lors de la récupération des statistiques")
        return 400, {"detail": "Impossible de récupérer les statistiques."}

@users_router.get(
    "/slug/{slug}",
    response={200: UserCompleteOut, 401: MessageResponse, 404: MessageResponse},
    auth=jwt_auth,
    summary="Récupère un utilisateur par son slug",
    description="Récupération publique via slug du profil (ex: john-doe-x7r2p9)"
)
def get_user_by_slug_endpoint(request: HttpRequest, slug: str):
    """
    Récupère un utilisateur via le slug de son profil.
    Utile pour les profils publics et les URLs propres.
    
    **Exemple :** `/users/slug/aminatou-seidou-x7r2p9`
    """
    user = user_service.get_user_by_slug(slug)
    if not user:
        return 404, {"detail": f"Aucun utilisateur trouvé avec le slug '{slug}'."}
    return 200, user

@users_router.get(
    "/{user_id}",
    response={200: UserCompleteOut, 401: MessageResponse, 404: MessageResponse},
    auth=jwt_auth,
    summary="Récupère un utilisateur par son ID",
    description="Récupération complète avec profil et réseaux sociaux"
)
def get_user_endpoint(request: HttpRequest, user_id: UUID4):
    """
    Récupère les informations complètes d'un utilisateur.
    Inclut le profil et tous les liens réseaux sociaux actifs.
    """
    user = user_service.get_user_by_id(str(user_id), include_relations=True)
    if not user:
        return 404, {"detail": "Utilisateur introuvable."}
    return 200, user

@users_router.put(
    "/{user_id}",
    response={200: UserCompleteOut, 400: MessageResponse, 401: MessageResponse, 403: MessageResponse, 404: MessageResponse, 422: ValidationErrorResponse},
    auth=jwt_auth,
    summary="Met à jour un utilisateur",
    description="Mise à jour des informations utilisateur et profil"
)
def update_user_endpoint(request: HttpRequest, user_id: UUID4, payload: UserUpdate):
    """
    Met à jour les informations d'un utilisateur.
    
    **Permissions :**
    - Propriétaire : peut modifier ses propres informations (sauf role_systeme)
    - Administrateur : peut tout modifier
    """
    if not is_owner_or_admin(request, str(user_id)):
        return 403, {"detail": "Action non autorisée."}

    user_to_update = user_service.get_user_by_id(str(user_id), include_relations=False)
    if not user_to_update:
        return 404, {"detail": "Utilisateur introuvable."}

    # Vérification spécifique pour le changement de rôle
    payload_dict = payload.dict(exclude_unset=True)
    if 'role_systeme' in payload_dict and not is_admin(request):
        return 403, {"detail": "Seuls les administrateurs peuvent modifier le rôle système."}
    print("data", payload_dict)
    try:
        updated_user = user_service.update_user(
            acting_user=request.auth, # type: ignore
            user_to_update=user_to_update,
            data_update=payload_dict,
            request=request
        )
        return 200, updated_user
    except ValueError as e:
        logger.error(f"Erreur mise à jour utilisateur {user_id}: {str(e)}")
        return 400, {"detail": str(e)}
    except Exception as e:
        logger.exception(f"Erreur inattendue mise à jour utilisateur {user_id}")
        return 400, {"detail": "Une erreur est survenue lors de la mise à jour."}

@users_router.delete(
    "/{user_id}",
    response={204: None, 401: MessageResponse, 403: MessageResponse, 404: MessageResponse},
    auth=jwt_auth,
    summary="Supprime un utilisateur (soft delete)",
    description="Désactivation logique - l'utilisateur peut être restauré"
)
def delete_user_endpoint(request: HttpRequest, user_id: UUID4):
    """
    Effectue une suppression logique (soft delete) de l'utilisateur.
    Les données sont conservées mais l'utilisateur ne peut plus se connecter.
    
    **Permissions :** Propriétaire ou administrateur
    """
    if not is_owner_or_admin(request, str(user_id)):
        return 403, {"detail": "Action non autorisée."}

    user_to_delete = user_service.get_user_by_id(str(user_id))
    if not user_to_delete:
        return 404, {"detail": "Utilisateur introuvable."}
    
    try:
        user_service.soft_delete_user(
            acting_user=request.auth, # type: ignore
            user_to_delete=user_to_delete,
            request=request
        )
        return 204, None
    except Exception as e:
        logger.exception(f"Erreur suppression utilisateur {user_id}")
        return 400, {"detail": "Erreur lors de la suppression."}

@users_router.post(
    "/{user_id}/restore",
    response={200: UserCompleteOut, 401: MessageResponse, 403: MessageResponse, 404: MessageResponse},
    auth=jwt_auth,
    summary="Restaure un utilisateur supprimé",
    description="Annule la suppression logique. Réservé aux administrateurs."
)
def restore_user_endpoint(request: HttpRequest, user_id: UUID4):
    """
    Restaure un utilisateur précédemment supprimé (soft delete).
    
    **Permissions requises :** admin_site ou super_admin
    """
    if not is_admin(request):
        return 403, {"detail": "Action non autorisée. Rôle administrateur requis."}

    try:
        # Récupération avec all_objects pour inclure les supprimés
        user_to_restore = User.all_objects.get(id=user_id, deleted=True)
    except User.DoesNotExist:
        return 404, {"detail": "Utilisateur supprimé introuvable."}

    try:
        restored_user = user_service.restore_user(
            acting_user=request.auth, # type: ignore
            user_to_restore=user_to_restore,
            request=request
        )
        return 200, restored_user
    except Exception as e:
        logger.exception(f"Erreur restauration utilisateur {user_id}")
        return 400, {"detail": "Erreur lors de la restauration."}

# ==========================================
# Gestion du compte
# ==========================================
@users_router.post(
    "/{user_id}/toggle-status",
    response={200: UserCompleteOut, 401: MessageResponse, 403: MessageResponse, 404: MessageResponse},
    auth=jwt_auth,
    summary="Active/Désactive un compte",
    description="Permet de bloquer/débloquer un compte. Réservé aux administrateurs."
)
def toggle_user_status_endpoint(request: HttpRequest, user_id: UUID4, payload: ToggleStatus):
    """
    Active ou désactive un compte utilisateur.
    
    **Permissions requises :** admin_site ou super_admin
    
    **Différence avec la suppression :**
    - Désactivation : Temporaire, rapide à réactiver
    - Suppression : Logique, nécessite restauration
    """
    if not is_admin(request):
        return 403, {"detail": "Action non autorisée. Rôle administrateur requis."}

    user_to_toggle = user_service.get_user_by_id(str(user_id))
    if not user_to_toggle:
        return 404, {"detail": "Utilisateur introuvable."}

    try:
        toggled_user = user_service.toggle_user_status(
            acting_user=request.auth, # type: ignore
            user_to_toggle=user_to_toggle,
            est_actif=payload.est_actif,
            request=request
        )
        return 200, toggled_user
    except Exception as e:
        logger.exception(f"Erreur toggle status utilisateur {user_id}")
        return 400, {"detail": "Erreur lors du changement de statut."}

# ==========================================
# Photo de profil
# ==========================================
@users_router.post(
    "/{user_id}/photo",
    response={200: PhotoUploadResponse, 400: MessageResponse, 401: MessageResponse, 403: MessageResponse, 404: MessageResponse},
    auth=jwt_auth,
    summary="Upload la photo de profil",
    description="Upload/remplace la photo. Optimisation et redimensionnement automatiques."
)
def upload_profile_photo_endpoint(
    request: HttpRequest, 
    user_id: UUID4, 
    file: File[UploadedFile]
):
    """
    Upload ou remplace la photo de profil d'un utilisateur.
    
    **Formats acceptés :** JPG, JPEG, PNG, WEBP  
    **Taille max :** 5 MB  
    **Optimisation :** Conversion automatique en WebP, redimensionnement à 800x800px
    
    **Permissions :** Propriétaire ou administrateur
    """
    if not is_owner_or_admin(request, str(user_id)):
        return 403, {"detail": "Action non autorisée."}

    user = user_service.get_user_by_id(str(user_id))
    if not user:
        return 404, {"detail": "Utilisateur introuvable."}

    try:
        updated_user = user_service.upload_profile_photo(
            acting_user=request.auth, # type: ignore
            user=user,
            photo_file=file,
            request=request
        )
        
        return 200, {
            "message": "Photo de profil mise à jour avec succès",
            "photo_profil": updated_user.profil.photo_profil.url if updated_user.profil.photo_profil else None # type: ignore
        }
    except ValueError as e:
        logger.error(f"Erreur validation photo utilisateur {user_id}: {str(e)}")
        return 400, {"detail": str(e)}
    except Exception as e:
        logger.exception(f"Erreur upload photo utilisateur {user_id}")
        return 400, {"detail": "Erreur lors de l'upload de la photo."}

@users_router.delete(
    "/{user_id}/photo",
    response={204: None, 400: MessageResponse, 401: MessageResponse, 403: MessageResponse, 404: MessageResponse },
    auth=jwt_auth,
    summary="Supprime la photo de profil"
)
def delete_profile_photo_endpoint(request: HttpRequest, user_id: UUID4):
    """
    Supprime la photo de profil d'un utilisateur.
    
    **Permissions :** Propriétaire ou administrateur
    """
    if not is_owner_or_admin(request, str(user_id)):
        return 403, {"detail": "Action non autorisée."}

    user = user_service.get_user_by_id(str(user_id))
    if not user:
        return 404, {"detail": "Utilisateur introuvable."}

    try:
        user_service.delete_profile_photo(
            acting_user=request.auth, # type: ignore
            user=user,
            request=request
        )
        return 204, None
    except Exception as e:
        logger.exception(f"Erreur suppression photo utilisateur {user_id}")
        return 400, {"detail": "Erreur lors de la suppression de la photo."}

# ==========================================
# Réseaux sociaux
# ==========================================
@users_router.get(
    "/{user_id}/social-links",
    response={200: List[LienReseauSocialOut], 401: MessageResponse, 404: MessageResponse},
    auth=jwt_auth,
    summary="Liste les liens réseaux sociaux"
)
def list_social_links_endpoint(request: HttpRequest, user_id: UUID4):
    """
    Récupère tous les liens réseaux sociaux actifs d'un utilisateur.
    """
    user = user_service.get_user_by_id(str(user_id))
    if not user:
        return 404, {"detail": "Utilisateur introuvable."}
    
    links = user_service.get_social_links(user)
    return 200, links

@users_router.post(
    "/{user_id}/social-links",
    response={201: LienReseauSocialOut, 400: MessageResponse, 401: MessageResponse, 403: MessageResponse, 404: MessageResponse},
    auth=jwt_auth,
    summary="Ajoute un lien réseau social"
)
def add_social_link_endpoint(
    request: HttpRequest, 
    user_id: UUID4, 
    payload: LienReseauSocialCreate
):
    """
    Ajoute un nouveau lien vers un réseau social.
    
    **Réseaux disponibles :** LinkedIn, Facebook, Twitter, Instagram, 
    GitHub, ResearchGate, Google Scholar, Site Web, Portfolio
    
    **Permissions :** Propriétaire ou administrateur
    """
    if not is_owner_or_admin(request, str(user_id)):
        return 403, {"detail": "Action non autorisée."}

    user = user_service.get_user_by_id(str(user_id))
    if not user:
        return 404, {"detail": "Utilisateur introuvable."}

    try:
        social_link = user_service.add_social_link(
            acting_user=request.auth, # type: ignore
            user=user,
            reseau_id=payload.reseau_id, # type: ignore
            url=payload.url,
            request=request
        )
        return 201, social_link
    except ValueError as e:
        logger.error(f"Erreur ajout lien social utilisateur {user_id}: {str(e)}")
        return 400, {"detail": str(e)}
    except Exception as e:
        logger.exception(f"Erreur inattendue ajout lien social utilisateur {user_id}")
        return 400, {"detail": "Erreur lors de l'ajout du lien."}

@users_router.put(
    "/{user_id}/social-links/{link_id}",
    response={200: LienReseauSocialOut, 400: MessageResponse, 401: MessageResponse, 403: MessageResponse, 404: MessageResponse},
    auth=jwt_auth,
    summary="Met à jour un lien réseau social"
)
def update_social_link_endpoint(
    request: HttpRequest,
    user_id: UUID4,
    link_id: UUID4,
    payload: LienReseauSocialUpdate
):
    """
    Met à jour l'URL ou le statut d'un lien réseau social.
    
    **Permissions :** Propriétaire ou administrateur
    """
    if not is_owner_or_admin(request, str(user_id)):
        return 403, {"detail": "Action non autorisée."}

    try:
        updated_link = user_service.update_social_link(
            acting_user=request.auth, # type: ignore
            link_id=str(link_id),
            url=payload.url,
            est_actif=payload.est_actif,
            request=request
        )
        return 200, updated_link
    except ValueError as e:
        logger.error(f"Erreur MAJ lien social {link_id}: {str(e)}")
        return 400, {"detail": str(e)}
    except LienReseauSocialProfil.DoesNotExist:
        return 404, {"detail": "Lien réseau social introuvable."}
    except Exception as e:
        logger.exception(f"Erreur inattendue MAJ lien social {link_id}")
        return 400, {"detail": "Erreur lors de la mise à jour du lien."}

@users_router.delete(
    "/{user_id}/social-links/{link_id}",
    response={204: None, 401: MessageResponse, 403: MessageResponse, 404: MessageResponse},
    auth=jwt_auth,
    summary="Supprime un lien réseau social"
)
def delete_social_link_endpoint(
    request: HttpRequest,
    user_id: UUID4,
    link_id: UUID4
):
    """
    Supprime (soft delete) un lien réseau social.
    
    **Permissions :** Propriétaire ou administrateur
    """
    if not is_owner_or_admin(request, str(user_id)):
        return 403, {"detail": "Action non autorisée."}

    try:
        user_service.delete_social_link(
            acting_user=request.auth, # type: ignore
            link_id=str(link_id),
            request=request
        )
        return 204, None
    except ValueError as e:
        return 404, {"detail": str(e)}
    except Exception as e:
        logger.exception(f"Erreur suppression lien social {link_id}")
        return 400, {"detail": "Erreur lors de la suppression du lien."}

# ==========================================
# Gestion des mots de passe
# ==========================================
@users_router.post(
    "/{user_id}/change-password",
    response={200: MessageResponse, 400: MessageResponse, 401: MessageResponse, 403: MessageResponse, 404: MessageResponse},
    auth=jwt_auth,
    summary="Change le mot de passe",
    description="Permet à un utilisateur de changer son propre mot de passe"
)
def change_password_endpoint(
    request: HttpRequest,
    user_id: UUID4,
    payload: ChangePassword
):
    """
    Change le mot de passe de l'utilisateur connecté.
    Nécessite l'ancien mot de passe pour validation.
    
    **Permissions :** Propriétaire uniquement (pas admin)
    """
    # Seul le propriétaire peut changer son propre mot de passe
    if str(request.auth.id) != str(user_id): # type: ignore
        return 403, {"detail": "Vous ne pouvez changer que votre propre mot de passe."}

    user = user_service.get_user_by_id(str(user_id))
    if not user:
        return 404, {"detail": "Utilisateur introuvable."}

    try:
        user_service.change_password(
            user=user,
            old_password=payload.old_password,
            new_password=payload.new_password,
            request=request
        )
        return 200, {"detail": "Mot de passe modifié avec succès."}
    except ValueError as e:
        logger.warning(f"Tentative changement mot de passe échouée pour {user_id}: {str(e)}")
        return 400, {"detail": str(e)}
    except Exception as e:
        logger.exception(f"Erreur changement mot de passe utilisateur {user_id}")
        return 400, {"detail": "Erreur lors du changement de mot de passe."}

@users_router.post(
    "/{user_id}/reset-password",
    response={200: PasswordResponse, 401: MessageResponse, 403: MessageResponse, 404: MessageResponse},
    auth=jwt_auth,
    summary="Réinitialise le mot de passe",
    description="Réinitialisation admin avec génération de mot de passe temporaire"
)
def reset_password_endpoint(
    request: HttpRequest,
    user_id: UUID4,
    payload: Optional[ResetPassword] = None
):
    """
    Réinitialise le mot de passe d'un utilisateur.
    Génère un mot de passe temporaire qui doit être communiqué à l'utilisateur.
    
    **Permissions requises :** admin_site ou super_admin
    
    **Note :** Le mot de passe temporaire n'est retourné qu'une seule fois.
    """
    if not is_admin(request):
        return 403, {"detail": "Action non autorisée. Rôle administrateur requis."}

    user_to_reset = user_service.get_user_by_id(str(user_id))
    if not user_to_reset:
        return 404, {"detail": "Utilisateur introuvable."}

    try:
        new_password = user_service.reset_password(
            acting_user=request.auth, # type: ignore
            user_to_reset=user_to_reset,
            new_password=payload.new_password if payload else None,
            request=request
        )
        
        return 200, {
            "message": "Mot de passe réinitialisé avec succès.",
            "temporary_password": new_password
        }
    except Exception as e:
        logger.exception(f"Erreur réinitialisation mot de passe utilisateur {user_id}")
        return 400, {"detail": "Erreur lors de la réinitialisation du mot de passe."}