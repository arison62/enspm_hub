# feeds/services/feeds_service.py
from typing import Optional, List
from uuid import UUID
from django.db import transaction
from django.db.models import Q, F, Count, Prefetch, Exists, OuterRef, Subquery
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.core.exceptions import ValidationError
from django.db.models import Sum, FloatField, ExpressionWrapper, Value
from django.db.models.functions import Coalesce
from core.api.exceptions import BadRequestAPIException, BaseAPIException, PermissionDeniedAPIException
from users.models import Profil
from feeds.models import Post, Comment, Like, View, Report, PostScoreRecord
from feeds.services.score_service import ScoreCalculator

from logging import getLogger
logger = getLogger('app')


class FeedService:
    """Service pour la gestion du fil d'actualite"""
    
    @staticmethod
    @transaction.atomic
    def create_post(author_profil, content: str) -> Post:
        """
        Cree un nouveau post
        
        Args:
            author_profil: Profil de l'auteur du post
            content: Contenu HTML (rich-text) du post
        
        Returns:
            Post: Post cree
        """
        if not content.strip():
            raise BadRequestAPIException(_("Le contenu du post est vide"))
        try:
            post = Post.objects.create(author=author_profil, content=content)
            logger.info(f"Creation du post {post.id} par {author_profil.id}")
            
            # Calculer le score initial du post
            ScoreCalculator.calculate_post_score(post)
            
            return post
        except ValidationError as e:
            
            logger.error(
                f"Erreur lors de la creation du post: {str(e)}",
                exc_info=True
                )
            raise BadRequestAPIException(str(e))
    
        except Exception as e:
            logger.error(
                f"Erreur lors de la creation du post: {str(e)}",
                exc_info=True
                )
            raise BaseAPIException(str(e))
        
    
    @staticmethod
    @transaction.atomic
    def update_post(
        post_id: UUID, 
        user_profil, 
        content: Optional[str] = None,
        is_pinned: Optional[bool] = None
        ) -> Post:
        """
        Mettre a jour un post existant
        
        Args:
            post_id: ID du post a mettre a jour
            user_profil: Profil de l'utilisateur qui effectue la mise a jour
            content: Nouveau contenu HTML (rich-text) du post
            is_pinned: Indique si le post doit etre epingle
        
        Returns:
            Post: Post mis a jour
        """
        try:
            post = Post.objects.get(pk=post_id)
            if post.author != user_profil:
                raise PermissionDeniedAPIException(_("Vous n'avez pas les droits pour mettre a jour ce post"))
            if content is not None:
                post.content = content
            if is_pinned is not None and FeedService._is_site_admin(user_profil):
                post.is_pinned = is_pinned
                
            post.save()
            if content is not None:
                ScoreCalculator.calculate_post_score(post)
            logger.info(f"Mise a jour du post {post.id} par {user_profil.id}")
            return post
        except Post.DoesNotExist:
            raise BadRequestAPIException(_("Le post n'existe pas"))
        except ValidationError as e:
            logger.error(
                f"Erreur lors de la mise a jour du post: {str(e)}",
                exc_info=True
                )
            raise BadRequestAPIException(str(e))
        except Exception as e:
            logger.error(
                f"Erreur lors de la mise a jour du post: {str(e)}",
                exc_info=True
                )
            raise BaseAPIException(str(e))
        
    @staticmethod
    @transaction.atomic    
    def delete_post(post_id: UUID, user_profil):
        try:
            post = Post.objects.get(pk=post_id)
            if post.author != user_profil and not FeedService._is_site_admin(user_profil):
                raise PermissionDeniedAPIException(_("Vous n'avez pas les droits pour supprimer ce post"))
            post.delete()
            logger.info(f"Suppression du post {post_id} par {user_profil.id}")
        except Post.DoesNotExist:
            raise BadRequestAPIException(_("Le post n'existe pas"))
        except Exception as e:
            logger.error(
                f"Erreur lors de la suppression du post: {str(e)}",
                exc_info=True
                )
            raise BaseAPIException(str(e))
     
     
    @staticmethod
    @transaction.atomic
    def create_comment(
         post_id: UUID,
         author_profil,
         content: str,
         parent_comment_id: Optional[UUID] = None
     ) -> Comment:
         if not content.strip():
            raise BadRequestAPIException(_("Le contenu du commentaire est vide"))
         try:
             comment = Comment.objects.create(
                 post_id=post_id,
                 author=author_profil,
                 content=content,
                 parent_id=parent_comment_id
             )
             # Incrementer le compteur de commentaires
             Post.objects.filter(pk=post_id).update(comments_count=F('comments_count') + 1)
             
             # Incrementer le compteur de reponse du commentaire
             if parent_comment_id:
                 Comment.objects.filter(pk=parent_comment_id).update(replies_count=F('replies_count') + 1)
            
             # Calculer le score initial du commentaire
             ScoreCalculator.calculate_post_score(Post.objects.get(pk=post_id))
             
             logger.info(f"Creation du commentaire {comment.id} par {author_profil.id}")
             return comment
         except ValidationError as e:
             logger.error(
                 f"Erreur lors de la creation du commentaire: {str(e)}",
                 exc_info=True
                 )
             raise BadRequestAPIException(str(e))
         except Exception as e:
             logger.error(
                 f"Erreur lors de la creation du commentaire: {str(e)}",
                 exc_info=True
                 )
             raise BaseAPIException(str(e))
    
    
    @staticmethod
    def get_comment_detail(
        comment_id: UUID,
        user_profil,
        ) -> Comment:

        try:
            return Comment.objects.select_related(
                'author',
            ).prefetch_related(
                Prefetch(
                    'replies',
                    queryset=Comment.objects.select_related('author').order_by('-created_at')
                )
            ).annotate(
                user_has_liked=Exists(
                    Like.objects.filter(comment=OuterRef('pk'), profil=user_profil)
                )
            ).get(pk=comment_id)
            
        except Comment.DoesNotExist:
            raise BadRequestAPIException(_("Le commentaire n'existe pas"))
        except Exception as e:
            logger.error(
                f"Erreur lors de la recuperation du commentaire: {str(e)}",
                exc_info=True
                )
            raise BaseAPIException(str(e))
        
        
        
    @staticmethod
    @transaction.atomic
    def delete_comment(comment_id: UUID, user_profil):
        try:
            comment = Comment.objects.get(pk=comment_id)
            if comment.author != user_profil and not FeedService._is_site_admin(user_profil):
                raise PermissionDeniedAPIException(_("Vous n'avez pas les droits pour supprimer ce commentaire"))
            comment.delete()
            logger.info(f"Suppression du commentaire {comment.id} par {user_profil.id}")
        except Comment.DoesNotExist:
            raise BadRequestAPIException(_("Le commentaire n'existe pas"))
        except Exception as e:
            logger.error(
                f"Erreur lors de la suppression du commentaire: {str(e)}",
                exc_info=True
                )
            raise BaseAPIException(str(e))
     
     
    @staticmethod
    @transaction.atomic
    def toggle_like(
        user_profil,
        post_id: Optional[UUID] = None,
        comment_id: Optional[UUID] = None,
        ) -> tuple[bool, Like]:
        """
        Returns:
            Tuple (created: bool, Like instance):
        """
        if not post_id and not comment_id:
            raise BadRequestAPIException(_("Aucun post ou commentaire n'a ete fourni"))
        if post_id and comment_id:
            raise BadRequestAPIException(_("Un like ne peut pas etre associe a la fois a un post et un commentaire"))
        try:
            if post_id:
                like, created = Like.objects.get_or_create(profil=user_profil, post_id=post_id)
                if created:
                    # Incrementer le compteur de likes
                    Post.objects.filter(pk=post_id).update(likes_count=F('likes_count') + 1)
                else:
                    like.delete()
                    # Decrementer le compteur de likes
                    Post.objects.filter(pk=post_id).update(likes_count=F('likes_count') - 1)
                ScoreCalculator.calculate_post_score(Post.objects.get(pk=post_id))
                
            elif comment_id:
                like, created = Like.objects.get_or_create(profil=user_profil, comment_id=comment_id)
                if created:
                    # Incrementer le compteur de likes
                    Comment.objects.filter(pk=comment_id).update(likes_count=F('likes_count') + 1)
                else:
                    like.delete()
                    # Decrementer le compteur de likes
                    Comment.objects.filter(pk=comment_id).update(likes_count=F('likes_count') - 1)
                    
            return created, like
        except Exception as e:
            logger.error(
                f"Erreur lors du like: {str(e)}",
                exc_info=True
                )
            raise BaseAPIException(str(e))
     
    @staticmethod
    @transaction.atomic
    def record_view(
        post_id: UUID, 
        user_profil=None,
        session_key: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> tuple[int, bool]:
        try:
            View.objects.get(
                post_id=post_id,
                profil = user_profil
            )

            return Post.objects.get(pk=post_id).views_count, False
            
        except View.DoesNotExist:
            View.objects.create(
                post_id=post_id,
                profil = user_profil,
                session_key = session_key,
                ip_address = ip_address
            )
            Post.objects.filter(pk=post_id).update(views_count=F('views_count') + 1)
            ScoreCalculator.calculate_post_score(Post.objects.get(pk=post_id))
            return Post.objects.get(pk=post_id).views_count, True
        except Exception as e:
            logger.error(
                f"Erreur lors de l'enregistrement de la vue: {str(e)}",
                exc_info=True
                )
            raise BaseAPIException(str(e))
     
    
    @staticmethod
    @transaction.atomic
    def create_report(
        user_profil,
        reason: str,
        post_id: Optional[UUID] = None,
        comment_id: Optional[UUID] = None,
        description : str = ""
        ):
        if not post_id and not comment_id:
            raise BadRequestAPIException(_("Aucun post ou commentaire n'a ete fourni"))
        if post_id and comment_id:
            raise BadRequestAPIException(_("Un rapport ne peut pas etre associe a la fois a un post et un commentaire"))
        try:
            if Report.objects.filter(
                post_id=post_id, 
                comment_id=comment_id,
                reporter=user_profil,
                ).exists():
                raise BadRequestAPIException(_("Vous avez deja signale ce contenu"))
            
            report = Report.objects.create(
                post_id=post_id,
                comment_id=comment_id,
                reporter=user_profil,
                reason=reason,
                description=description
            )
            if post_id:
                ScoreCalculator.calculate_post_score(Post.objects.get(pk=post_id))
            elif comment_id:
                ScoreCalculator.calculate_post_score(Comment.objects.get(pk=comment_id).post)
            return report
            
        except Exception as e:
            logger.error(
                f"Erreur lors de la creation du rapport: {str(e)}",
                exc_info=True
                )
            raise BaseAPIException(str(e))
    

    
    @staticmethod
    def get_feed(user_profil, page: int = 1, page_size: int = 20) -> tuple[List[Post], int]:
        """
        Récupère le fil d'actualité personnalisé pour un utilisateur
        
        Args:
            user_profil: Profil de l'utilisateur
            page: Numéro de page
            page_size: Taille de la page
        
        Returns:
            Tuple[List[Post], int]: Liste de posts et nombre total
        """
        
        
        # Subquery pour récupérer le dernier score calculé
        latest_score_subquery = PostScoreRecord.objects.filter(
            post=OuterRef('pk')
        ).order_by('-calculation_time').values('calculated_score')[:1]
        
        # Sous-requête pour récupérer seulement les 3 derniers commentaires par post
        recent_comments_subquery = Comment.objects.filter(
            post=OuterRef('pk'),
            parent__isnull=True  # Seulement les commentaires directs, pas les réponses
        ).order_by('-created_at').values('id')[:3]
        
        # Construire le queryset de base
        queryset = Post.objects.filter(is_archived=False).select_related(
            'author',
            'author__user'
        ).prefetch_related(
            'likes',
            'views',
            'shares',
            # Prefetch optimisé avec limite SQL
            Prefetch(
                'comments',
                queryset=Comment.objects.filter(
                    id__in=recent_comments_subquery,
                    parent__isnull=True
                ).select_related('author').order_by('-created_at'),
                to_attr='recent_comments'
            )
        ).annotate(
            user_has_liked=Exists(
                Like.objects.filter(post=OuterRef('pk'), profil=user_profil)
            ),
            latest_score=Subquery(latest_score_subquery),
            # Annotation pour le nombre total de commentaires (pas seulement les 3 affichés)
            total_comments=Count('comments', filter=Q(comments__parent__isnull=True))
        ).order_by('-is_pinned', '-latest_score', '-created_at')
        
        # Obtenir le total AVANT la pagination
        total_count = queryset.count()
        
        # Appliquer la pagination
        start = (page - 1) * page_size
        end = start + page_size
        
        # Évaluer le queryset une seule fois
        posts = list(queryset[start:end])
        
        return posts, total_count
    
    
    @staticmethod
    def search_posts(query: str, user_profil, page: int = 1, page_size: int = 20) -> tuple[List[Post], int]:
        """
        Recherche de posts par texte
        
        Args:
            query: Requête de recherche
            user_profil: Profil de l'utilisateur
            page: Numéro de page
            page_size: Taille de la page
        
        Returns:
            Liste de posts correspondants
        """
        search_query = SearchQuery(query, search_type='websearch')
        
        queryset = Post.objects.select_related(
            'author'
        ).annotate(
            rank=SearchRank(F('search_vector'), search_query)
        ).filter(
            search_vector=search_query,
            is_archived=False
        )
        
      
        
        queryset = queryset.order_by('-rank', '-created_at')
        
        total_count = queryset.count()
        
        # Pagination
        start = (page - 1) * page_size
        end = start + page_size
        
        return list(queryset[start:end]), total_count  


    
    @staticmethod
    def get_user_posts(profil_id, page: int = 1, page_size: int = 20) -> tuple[List[Post], int]:
        """
        Récupère les posts d'un utilisateur spécifique
        
        Args:
            profil_id: ID de l'utilisateur
            page: Numéro de page
            page_size: Taille de la page
        
        Returns:
            Liste de posts
        """
        queryset = Post.objects.filter(
            author__id=profil_id,
            is_archived=False
        ).select_related('author').prefetch_related('likes', 'comments')
        

        
        queryset = queryset.order_by('-created_at')
        total_count = queryset.count()
        # Pagination
        start = (page - 1) * page_size
        end = start + page_size
        
        return list(queryset[start:end]), total_count

    @staticmethod
    def get_post_comments(
        user_profil,
        post_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Comment], int]:
        """
        Récupérer les commentaires d'un post
        
        Args:
            post_id: ID du post
            page: Numéro de page
            page_size: Taille de la page
        
        Returns:
            Liste de commentaires
        """
        queryset = Comment.objects.filter(
            post__id=post_id,
            parent__isnull=True
        ).select_related('author').annotate(
            user_has_liked=Exists(
                Like.objects.filter(comment=OuterRef('pk'), profil=user_profil)
            )
        )
        
        queryset = queryset.order_by('-created_at')
        total_count = queryset.count()
        # Pagination
        start = (page - 1) * page_size
        end = start + page_size
        
        return list(queryset[start:end]), total_count
    
    
    @staticmethod
    def get_profil_stats(profil_id):
        """
        Calcule les statistiques clés d'un utilisateur à partir des données du fil d'actualité
        
        Args:
            profil_id (str): ID du profil utilisateur
        
        Returns:
            dict: Dictionnaire contenant les statistiques:
                - posts_count: Nombre total de posts créés
                - comments_send_count: Nombre de commentaires envoyés
                - comments_received_count: Nombre de commentaires reçus sur ses posts
                - likes_received_count: Nombre total de likes reçus (posts + commentaires)
                - shares_count: Nombre de partages de ses posts
                - views_count: Nombre total de vues sur ses posts
                - engagement_rate: Taux d'engagement calculé
        """
        try:
            stats = Profil.objects.filter(id=profil_id).aggregate(
                # Nombre de posts créés
                posts_count=Count('posts', filter=Q(posts__is_archived=False)),
                
                # Nombre de commentaires envoyés
                comments_send_count=Count('comments', distinct=True),
                
                # Nombre de commentaires reçus sur ses posts
                comments_received_count=Count(
                    'posts__comments', 
                    filter=Q(posts__is_archived=False),
                    distinct=True
                ),
                
                # Likes reçus sur les posts
                post_likes_count=Coalesce(
                    Sum('posts__likes_count', filter=Q(posts__is_archived=False)),
                    Value(0)
                ),
                
                # Likes reçus sur les commentaires
                comment_likes_count=Coalesce(
                    Sum('comments__likes_count'),
                    Value(0)
                ),
                
                # Partages de ses posts
                shares_count=Coalesce(
                    Sum('posts__shares_count', filter=Q(posts__is_archived=False)),
                    Value(0)
                ),
                
                # Vues sur ses posts
                views_count=Coalesce(
                    Sum('posts__views_count', filter=Q(posts__is_archived=False)),
                    Value(0)
                )
            )
            
            # Calculer le nombre total de likes reçus
            likes_received_count = stats['post_likes_count'] + stats['comment_likes_count']
            
            # Calculer le taux d'engagement (simplifié)
            # Engagement = (likes + commentaires + partages) / vues * 100
            total_interactions = (
                likes_received_count + 
                stats['comments_received_count'] + 
                stats['shares_count']
            )
            
            engagement_rate = 0.0
            if stats['views_count'] > 0 and total_interactions > 0:
                engagement_rate = round((total_interactions / stats['views_count']) * 100, 2)
            
            # Formater les nombres avec des séparateurs de milliers pour l'affichage
            def format_number(num):
                if num >= 1000000:
                    return f"{num/1000000:.1f}M"
                elif num >= 1000:
                    return f"{num/1000:.1f}k"
                return str(num)
            
            return {
                'posts_count': stats['posts_count'],
                'posts_count_display': format_number(stats['posts_count']),
                
                'comments_send_count': stats['comments_send_count'],
                'comments_send_count_display': format_number(stats['comments_send_count']),
                
                'comments_received_count': stats['comments_received_count'],
                'comments_received_count_display': format_number(stats['comments_received_count']),
                
                'likes_received_count': likes_received_count,
                'likes_received_count_display': format_number(likes_received_count),
                
                'shares_count': stats['shares_count'],
                'shares_count_display': format_number(stats['shares_count']),
                
                'views_count': stats['views_count'],
                'views_count_display': format_number(stats['views_count']),
                
                'engagement_rate': engagement_rate,
                'engagement_rate_display': f"{engagement_rate:.1f}%",
            }
        except Exception as e:
            logger.error(
                f"Erreur lors de la recherche des statistiques de l'utilisateur {profil_id} : {str(e)}",
                exc_info=True
                )
            raise BaseAPIException(str(e))
    

    @staticmethod   
    def _is_site_admin(user_profil):
        return user_profil.role_systeme in ['admin_site', 'super_admin']
        
    
    
        
    
    
        
