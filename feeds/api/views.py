# feeds/api/views.py
from typing import List, Optional
from uuid import UUID
from ninja import Router
from django.shortcuts import get_object_or_404
from django.db.models import Exists, OuterRef, Prefetch

from core.api.schemas import PaginationMetaSchema
from core.services.auth_service import jwt_auth
from core.api.exceptions import BadRequestAPIException, PermissionDeniedAPIException
from feeds.models import Post, Comment, Like
from feeds.services.feeds_service import FeedService
from feeds.api.schemas import (
    PostCreate, PostUpdate, PostOut, PostDetail, PostPaginatedResponse,
    CommentCreate, CommentUpdate, CommentOut, CommentDetail, CommentPaginatedResponse,
    LikeToggle, LikeResponse,
    ViewCreate, ViewResponse,
    ReportCreate, ReportOut, ReportUpdate,
    SearchQuery, PostStats, ProfileFeedStats
)

router = Router(tags=["Feeds"])

@router.post("/posts", response=PostOut, auth=jwt_auth)
def create_post(request, payload: PostCreate):
    """
    Créer un nouveau post
    
    Permissions: Utilisateur authentifié
    """
    post = FeedService.create_post(
        author_profil=request.auth,
        content=payload.content
    )
    return post



@router.get("/posts", response=PostPaginatedResponse, auth=jwt_auth)
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


@router.get("/posts/search", response=PostPaginatedResponse, auth=jwt_auth)
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

@router.patch(
    "/posts/{post_id}",
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

@router.delete(
    "/posts/{post_id}",
    auth=jwt_auth
)
def delete_post(request, post_id: UUID):
    """
    Supprimer un post
    
    Permissions: Utilisateur authentifié
    """
    FeedService.delete_post(post_id=post_id, user_profil=request.auth.profil)
    


@router.get("/posts/user/{profil_id}", response=PostPaginatedResponse, auth=True)
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

@router.post("/posts/{post_id}/comments", response=CommentOut, auth=jwt_auth)
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

@router.get("/posts/{post_id}/comments", response=CommentPaginatedResponse, auth=jwt_auth)
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

@router.get("/comments/{comment_id}", response=CommentDetail, auth=jwt_auth)
def get_comment_detail(request, comment_id: UUID):
    """
    Récupérer le detail d'un commentaire
    
    Permissions: Utilisateur authentifié
    """
    comment = FeedService.get_comment_detail(comment_id=comment_id, user_profil=request.auth.profil)
    return comment

@router.delete("/comments/{comment_id}", auth=jwt_auth)
def delete_comment(request, comment_id: UUID):
    """
    Supprimer un commentaire
    
    Permissions: Utilisateur authentifié
    """
    FeedService.delete_comment(comment_id=comment_id, user_profil=request.auth.profil)

@router.post("/views", response=ViewResponse, auth=jwt_auth)
def record_view(
    request,
    payload: ViewCreate
):
    """
    Enregistrer une vue sur un post
    
    Permissions: Utilisateur authentifié
    """
    views_count, created = FeedService.record_view(
        user_profil=request.auth.profil,
        post_id=payload.post_id
    )
 
   
    return {
        "views_count": views_count,
        "recorded": created
    }


@router.post("/reports", response=ReportOut, auth=jwt_auth)
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
    