# feeds/services/score_service.py
import math
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q

from feeds.models import FeedScoreConfig
from feeds.models.configs import PostScoreRecord, ProfilScoreRecord


class ScoreCalculator:
    """Calculateur de score pour les posts et profils"""

    @staticmethod
    def get_active_config():
        """Récupère la configuration active ou crée une par défaut"""
        try:
            return FeedScoreConfig.objects.get(is_active=True)
        except FeedScoreConfig.DoesNotExist:
            default_config = FeedScoreConfig.objects.create(
                is_active=True,
            )
            return default_config

    @staticmethod
    def calculate_profil_score(profil):
        """
        Calcule le score d'autorité d'un profil utilisateur.
        
        Args:
            profil: Instance de Profil
        
        Returns:
            float: Score calculé
            
        ### Formule de Calcul
        ```python
        total_score = base_score + activity_score - penalty
        
        # Détails :
        activity_score = (posts_count + comments_count) * activity_coeff
        penalty = report_count * penalty_per_report
        
        # Si le seuil de signalement est dépassé :
        penalty = penalty * 2
        ```
        """
        config = ScoreCalculator.get_active_config()
        
        # Statistiques de l'utilisateur
        stats = {
            "posts_count": profil.posts.filter(deleted=False).count(),
            "comments_count": profil.comments.filter(deleted=False).count(),
            "report_count": profil.user.reports_received.filter(
                status='pending'
            ).count() if hasattr(profil.user, 'reports_received') else 0,
        }

        # Calcul du score d'activité
        activity_score = (
            stats['comments_count'] + stats['posts_count']
        ) * config.profil_activity_coeff
        
        # Calcul de la pénalité de signalement
        report_penalty = stats['report_count'] * config.profil_report_penalty_per_report
        
        # Si le seuil de signalement est atteint
        if stats['report_count'] >= config.profil_report_threshold:
            report_penalty *= 2  # Double pénalité

        # Score total
        total_score = config.profil_base_score + activity_score - report_penalty
        total_score = max(0.1, total_score)  # Score minimum de 0.1
        
        # Enregistrer le score
        with transaction.atomic():
            ProfilScoreRecord.objects.create(
                profil=profil,
                calculated_score=total_score,
                config=config
            )

        return total_score
    
    @staticmethod
    def calculate_post_score(post):
        """
        Calcule le score de pertinence d'un post.
        
        Args:
            post: Instance de Post
        
        Returns:
            float: Score calculé
            
        ### Formule de Calcul
        ```python
        final_score = (base_score + engagement - penalty) * time_decay
        
        # 1. Base Score
        base_score = author_score * config_base * content_type_multiplier
        
        # 2. Engagement Score
        engagement = (likes * 2.0) + (comments * 3.0) + (views * 0.1) + (shares * 1.5)
        
        # 3. Time Decay (Décroissance temporelle)
        time_decay = exp(-hours_since_posted / decay_factor)
        if new_post: time_decay *= boost_factor
        ```
        """
        config = ScoreCalculator.get_active_config()
        now = timezone.now()
        
        # Récupérer le score de l'auteur
        try:
            author_score_record = post.author.score_records.filter(
                deleted=False
            ).order_by('-calculation_time').first()
            
            if author_score_record:
                author_score = author_score_record.calculated_score
            else:
                author_score = ScoreCalculator.calculate_profil_score(post.author)
        except Exception:
            author_score = ScoreCalculator.calculate_profil_score(post.author)
        
        # Calcul du temps écoulé en heures
        hours_since_posted = (now - post.created_at).total_seconds() / 3600

        # Statistiques du post
        stats = {
            "likes_count": post.likes_count,
            "comments_count": post.comments_count,
            "views_count": post.views_count,
            "shares_count": post.shares_count,
            "report_count": post.reports.filter(status='pending').count(),
            "content_type": getattr(post, 'content_type', 'text'),
        }
        
        # Multiplicateur de type de contenu
        content_multiplier = config.content_multipliers.get(
            stats['content_type'],
            1.0
        )
        
        # Score d'engagement
        engagement_score = (
            stats['likes_count'] * config.engagement_coefficients.get('like', 2.0) +
            stats['comments_count'] * config.engagement_coefficients.get('comment', 3.0) +
            stats['views_count'] * config.engagement_coefficients.get('view', 0.1) +
            stats['shares_count'] * config.engagement_coefficients.get('share', 1.5)
        )
        
        # Décroissance temporelle exponentielle
        time_decay = math.exp(-hours_since_posted / config.time_decay_factor)
        
        # Bonus pour les nouveaux posts
        if config.boost_new_posts and hours_since_posted < config.boost_new_posts_threshold:
            time_decay *= config.new_posts_boost_factor

        # Score de base avec score utilisateur et type de contenu
        base_score = author_score * config.post_base_score * content_multiplier
        
        # Pénalité de signalements
        penalty = stats['report_count'] * config.post_penality_per_report
        
        # Score final
        final_score = (base_score + engagement_score - penalty) * time_decay
        
        # Gestion du seuil de signalement (masquage du post)
        if stats['report_count'] >= config.post_report_threshold:
            final_score = 0.1  # Score minimal pour les posts signalés

        final_score = max(0.1, final_score)
        
        # Enregistrer le score
        with transaction.atomic():
            PostScoreRecord.objects.create(
                post=post,
                calculated_score=final_score,
                config=config
            )

        return final_score
    
    @classmethod
    def batch_update_scores(cls, hours_back=24):
        """
        Met à jour les scores en lot pour les profils et posts actifs.
        
        Args:
            hours_back: Nombre d'heures à remonter pour considérer l'activité
        
        Returns:
            dict: Statistiques de mise à jour {'profils_updated': int, 'posts_updated': int}
        """
        from feeds.models import Post
        from users.models import Profil
        
        now = timezone.now()
        cutoff_time = now - timedelta(hours=hours_back)
        
        # Profils actifs (avec posts ou commentaires récents)
        active_profils = Profil.objects.filter(
            Q(posts__created_at__gte=cutoff_time) |
            Q(comments__created_at__gte=cutoff_time),
            deleted=False
        ).distinct()
        
        # Posts récents
        recent_posts = Post.objects.filter(
            created_at__gte=cutoff_time,
            deleted=False
        )
        
        results = {
            'profils_updated': 0,
            'posts_updated': 0
        }
        
        # Mettre à jour les scores des profils
        for profil in active_profils:
            cls.calculate_profil_score(profil)
            results['profils_updated'] += 1
        
        # Mettre à jour les scores des posts
        for post in recent_posts:
            cls.calculate_post_score(post)
            results['posts_updated'] += 1
        
        return results
    
    @classmethod
    def recalculate_all_scores(cls):
        """
        Recalcule tous les scores de la base de données.
        
        ⚠️ **Attention** : Opération lourde à utiliser uniquement pour la maintenance
        ou l'initialisation.
        
        Returns:
            dict: Statistiques de recalcul
        """
        from feeds.models import Post
        from users.models import Profil
        
        results = {
            'profils_updated': 0,
            'posts_updated': 0
        }
        
        # Recalculer tous les profils
        for profil in Profil.objects.filter(deleted=False):
            cls.calculate_profil_score(profil)
            results['profils_updated'] += 1
        
        # Recalculer tous les posts
        for post in Post.objects.filter(deleted=False):
            cls.calculate_post_score(post)
            results['posts_updated'] += 1
        
        return results