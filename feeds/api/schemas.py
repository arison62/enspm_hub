# feeds/api/schemas.py
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from ninja import Schema
from pydantic import Field, field_validator
from core.utils.date_formatters import format_linkedin_duration
from users.api.schemas import ProfilBaseOut

MAX_POST_SIZE = 10 * 1024 * 1024

class BaseFeedSchema(Schema):
    """
    Schéma de base pour les posts et les commentaires
    """
    id: UUID
    duree_text : str
    @staticmethod
    def resolve_duree_text(obj):
        """Affiche la durée de l'experience en texte"""
        return format_linkedin_duration(obj.created_at)


class PostCreate(Schema):
    """
    Schéma de création de post
    """
    content: str = Field(
        ...,
        description="Contenu HTML (rich-text) du post",
    )
    
    @field_validator('content')
    def check_size(cls, value):
        # Calcul de la taille en octets (approx)
        size_in_bytes = len(value.encode('utf-8'))
        if size_in_bytes > MAX_POST_SIZE:
            raise ValueError(f"Le contenu du post doit avoir une taille maximale de {MAX_POST_SIZE / (1024*1024)} MB.")
        return value

class PostUpdate(Schema):
    """
    Schéma de mise à jour de post
    """
    content: Optional[str] = Field(
        None,
        description="Contenu HTML (rich-text) du post",
        max_length=10000,
        min_length=1
    )
    is_pinned: Optional[bool] = None
    
class PostOut(BaseFeedSchema):
    """
    Schéma de sortie de post
    """
    author: ProfilBaseOut
    content: str
    content_text: str
    is_pinned: bool
    
    likes_count: int
    comments_count: int
    views_count: int
    
    created_at: datetime
    updated_at: datetime
    
    user_has_liked: Optional[bool] = False
    latest_score: Optional[float] = None
    content_type: Optional[str] = None
    
class PostDetail(PostOut):
    """
    Schéma de sortie de post complet
    """
    recent_comments: List['CommentOut'] = []
    
  
class CommentCreate(Schema):
    content: str = Field(
        ...,
        description="Contenu HTML (rich-text) du commentaire",
        max_length=10000,
        min_length=1
    )
    parent_id: Optional[UUID] = None

class CommentUpdate(Schema):
    content: Optional[str] = Field(
        None,
        description="Contenu HTML (rich-text) du commentaire",
        max_length=10000,
        min_length=1
    )
    
class CommentOut(BaseFeedSchema):
    """
    Schéma de création de commentaire
    """
    post_id: UUID
    author: ProfilBaseOut
    content: str
    content_text: str
    parent_id: Optional[UUID] = None
    
    
    likes_count: Optional[int] = 0
    replies_count: Optional[int] = 0
    
    created_at: datetime
    updated_at: datetime
    
    user_has_liked: Optional[bool] = False

class CommentDetail(CommentOut):
    """
    Schéma de sortie de commentaire complet
    """
    replies: List['CommentOut'] = []


class LikeToggle(Schema):
    post_id: Optional[UUID] = None
    comment_id: Optional[UUID] = None
    
class LikeResponse(Schema):
    created: bool = Field(..., description="True si creer, False si supprimer")
    likes_count: int = Field(..., description="Nombre de likes")

class ViewCreate(Schema):
    post_id: UUID

class ViewResponse(Schema):
    recorded: bool = Field(..., description="True si creer, False si supprimer")
    views_count: int = Field(..., description="Nombre de views")


class ReportCreate(Schema):
    post_id: Optional[UUID] = None
    comment_id: Optional[UUID] = None
    reason: str = Field(..., description="Raison du rapport")
    description: Optional[str] = Field(None, description="Description du rapport")
    
    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v):
        valid_choices = ['spam', 'harassment', 
                         'hate_speech', 'violence', 
                         'false_info', 'inappropriate', 
                         'other']
        if v not in valid_choices:
            raise ValueError(f"la raison doit etre l'une {', '.join(valid_choices)}")
        return v

class ReportOut(Schema):
    id: UUID
    reporter: ProfilBaseOut
    post_id: Optional[UUID] = None
    comment_id: Optional[UUID] = None
    reason: str
    description: Optional[str]
    status: str
    create_at: datetime
    

class ReportUpdate(Schema):
    status: str
    resolution_note: Optional[str] = None
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_choices = ['pending', 'reviewed', 'resolved', 'rejected']
        if v not in valid_choices:
            raise ValueError(f"Status doit être l'un de: {', '.join(valid_choices)}")
        return v

class PostPaginatedResponse(Schema):
    posts: List[PostDetail]
    page: int
    page_size: int
    total_items: Optional[int] = None

class CommentPaginatedResponse(Schema):
    comments: List[CommentOut]
    page: int
    page_size: int
    total_items: Optional[int] = None

class SearchQuery(Schema):
    query: str = Field(
        ...,
        min_length=1,
        description="Requête de recherche"
    )

class PostStats(Schema):
    post_id: str
    likes_count: int
    views_count: int
    comments_count: int
    reports_count: int
    current_score: Optional[float] = None

class ProfileFeedStats(Schema):
    profil_id: UUID
    posts_count: int
    comments_count: int
    total_likes_received: int
    total_views_received: int
    current_score: Optional[float] = None
    

class ProfilStats(Schema):
    """
    Schéma de sortie pour les statistiques d'engagement d'un profil.
    """
    posts_count: int
    posts_count_display: str
    
    comments_send_count: int
    comments_send_count_display: str
    
    comments_received_count: int
    comments_received_count_display: str
    
    likes_received_count: int
    likes_received_count_display: str
    
    shares_count: int
    shares_count_display: str
    
    views_count: int
    views_count_display: str
    
    engagement_rate: float
    engagement_rate_display: str