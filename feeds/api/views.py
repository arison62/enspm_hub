# feeds/api/views.py
from uuid import UUID
from ninja import Router

from core.api.schemas import ErrorAPIResponse
from core.services.auth_service import jwt_auth
from feeds.services.feeds_service import FeedService
from feeds.api.schemas import (
    PostCreate, PostUpdate, PostOut, PostPaginatedResponse,
    CommentCreate, CommentOut, CommentDetail, CommentPaginatedResponse, ProfilStats,
    ViewResponse,
    ReportCreate, ReportOut
)

posts_router = Router(tags=["Feeds"])

@posts_router.post("/", response=PostOut, auth=jwt_auth)
def create_post(request, payload: PostCreate):
    """
    Créer un nouveau post
    
    Permissions: Utilisateur authentifié
    """
    post = FeedService.create_post(
        author_profil=request.auth.profil,
        content=payload.content
    )
    return post



@posts_router.get("/", response=PostPaginatedResponse, auth=jwt_auth)
def get_feed(
    request,
    page: int = 1,
    page_size: int = 20
):
    """
    Récupérer le fil d'actualité personnalisé
    
    Permissions: Utilisateur authentifié
    """
    posts, total = FeedService.get_feed(
        user_profil=request.auth.profil,
        page=page,
        page_size=page_size
    )
    
    return {
        "posts": posts,
        "page": page,
        "page_size": page_size,
        "total_items": total
    }


@posts_router.get("search", response=PostPaginatedResponse, auth=jwt_auth)
def search_posts(
    request,
    query: str,
    page: int = 1,
    page_size: int = 20
):
    """
    Recherche de posts par texte
    
    Permissions: Utilisateur authentifié
    """
    posts, total = FeedService.search_posts(
        query=query,
        user_profil=request.auth.profil,
        page=page,
        page_size=page_size
    )
    
    return {
        "posts": posts,
        "page": page,
        "page_size": page_size,
        "total_items": total
    }

@posts_router.patch(
    "/{post_id}",
    response=PostOut,
    auth=jwt_auth
)
def update_post(request, post_id: UUID, payload: PostUpdate):
    """
    Mettre a jour un post existant
    
    Permissions: Utilisateur authentifié
    """
    post = FeedService.update_post(
        post_id=post_id,
        user_profil=request.auth.profil,
        content=payload.content,
        is_pinned=payload.is_pinned
    )
    return post

@posts_router.post(
    "/{post_id}/like",
    auth=jwt_auth,
    response={201: None, 401: ErrorAPIResponse, 403: ErrorAPIResponse},
)
def toggle_like(request, post_id: UUID):
    """
    Like ou unlike un post
    
    Permissions: Utilisateur authentifié
    """
    FeedService.toggle_like(
        user_profil=request.auth.profil,
        post_id=post_id
    )

    return 201, None

@posts_router.delete(
    "/{post_id}",
    auth=jwt_auth
)
def delete_post(request, post_id: UUID):
    """
    Supprimer un post
    
    Permissions: Utilisateur authentifié
    """
    FeedService.delete_post(post_id=post_id, user_profil=request.auth.profil)
    


@posts_router.get("/user/{profil_id}", response=PostPaginatedResponse, auth=True)
def get_user_posts(
    request,
    profil_id: UUID,
    page: int = 1,
    page_size: int = 20
):
    """
    Récupérer les posts d'un utilisateur spécifique
    
    Permissions: Utilisateur authentifié
    """
    posts, total = FeedService.get_user_posts(
        profil_id=profil_id,
        page=page,
        page_size=page_size
    )
    
    return {
        "posts": posts,
        "page": page,
        "page_size": page_size,
        "total_items": total
    }



# Comments

@posts_router.post("/{post_id}/comments", response=CommentOut, auth=jwt_auth)
def create_comment(request, post_id: UUID, payload: CommentCreate):
    """
    Créer un nouveau commentaire
    
    Permissions: Utilisateur authentifié
    """
    comment = FeedService.create_comment(
        post_id=post_id,
        author_profil=request.auth.profil,
        content=payload.content
    )
    return comment

@posts_router.get("/{post_id}/comments", response=CommentPaginatedResponse, auth=jwt_auth)
def get_post_comments(request, post_id: UUID, page: int = 1, page_size: int = 20):
    """
    Récupérer les commentaires d'un post
    
    Permissions: Utilisateur authentifié
    """
    comments, total = FeedService.get_post_comments(
        user_profil=request.auth.profil,
        post_id=post_id,
        page=page,
        page_size=page_size
    )
    
    return {
        "comments": comments,
        "page": page,
        "page_size": page_size,
        "total_items": total
    }

@posts_router.get("/comments/{comment_id}", response=CommentDetail, auth=jwt_auth)
def get_comment_detail(request, comment_id: UUID):
    """
    Récupérer le detail d'un commentaire
    
    Permissions: Utilisateur authentifié
    """
    comment = FeedService.get_comment_detail(comment_id=comment_id, user_profil=request.auth.profil)
    return comment

@posts_router.delete("/comments/{comment_id}", auth=jwt_auth)
def delete_comment(request, comment_id: UUID):
    """
    Supprimer un commentaire
    
    Permissions: Utilisateur authentifié
    """
    FeedService.delete_comment(comment_id=comment_id, user_profil=request.auth.profil)

@posts_router.post("/{post_id}/views", response=ViewResponse, auth=jwt_auth)
def record_view(
    request,
    post_id: UUID
):
    """
    Enregistrer une vue sur un post
    
    Permissions: Utilisateur authentifié
    """
    views_count, created = FeedService.record_view(
        user_profil=request.auth.profil,
        post_id=post_id
    )
 
   
    return {
        "views_count": views_count,
        "recorded": created
    }


@posts_router.post("/reports", response=ReportOut, auth=jwt_auth)
def create_report(request, payload: ReportCreate):
    """
    Signaler un post ou commentaire
    
    Permissions: Utilisateur authentifié
    """
    report = FeedService.create_report(
        user_profil=request.auth.profil,
        reason=payload.reason,
        post_id=payload.post_id,
        comment_id=payload.comment_id,
        description=payload.description or ""
    )

    return report

@posts_router.get("/profil/{profil_id}/stats", response={
     200: ProfilStats, 401: ErrorAPIResponse
    }, auth=jwt_auth )
def get_profil_stats(request, profil_id: UUID):
    """
    Récupérer les statistiques d'un profil
    
    Permissions: Utilisateur authentifié
    """
    stats = FeedService.get_profil_stats(profil_id=profil_id)
    return 200, stats