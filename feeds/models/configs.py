from django.db import models
from django.utils import timezone

from core.models import ENSPMHubBaseModel


class FeedScoreConfig(ENSPMHubBaseModel):
    """
    Configuration des scores
    """
    
    # Configuration des score utilisateur
    profil_base_score = models.FloatField(default=1.0, help_text="Score de base pour les utilisateur")
    profil_activity_coeff = models.FloatField(default=1.0, help_text="Coefficient les activites de l'utilisateur")
    profil_report_penalty_per_report = models.FloatField(default=1.0, help_text="Penalite par signalement de l'utilisateur")
    profil_report_threshold = models.IntegerField(default=10, help_text="Seuil de signalement de l'utilisateur")
    
    
    # Configuration des score posts
    post_base_score = models.FloatField(default=10.0, help_text="Score de base pour les posts")
    post_penality_per_report = models.FloatField(default=10.0, help_text="Penalite par signalement de post")
    post_report_threshold = models.IntegerField(default=10, help_text="Seuil de signalement de post")
    time_decay_factor = models.FloatField(default=12.0, help_text="Facteur de diminution du score par temps")
    boost_new_posts = models.BooleanField(default=True, help_text="Boost les nouveaux posts ")
    new_posts_boost_factor = models.FloatField(default=2.0, help_text="Facteur de boost des nouveaux posts")
    boost_new_posts_threshold = models.IntegerField(default=8, help_text="Duree de boost des nouveaux posts")
    content_multipliers = models.JSONField(
        default=dict,
        help_text='''JSON : {
            "image": 2.0,
            "video: 1.5,
            "pooll: 1.2,
            "link": 1.1,
            "text": 1.0
            "
        }'''
    )
    engagement_coefficients = models.JSONField(
        default=dict,
        help_text='''JSON:{
            comment: 3.0,
            "like": 2.0,
            "view: 0.1,
            "share": 1.5
        }'''
    )
    
    is_active = models.BooleanField(default=False, help_text="Configuration actuellement utilisée")
    
    class Meta:
        verbose_name = "Configuration de score"
        verbose_name_plural = "Configurations des scores"
        ordering = ["-is_active", "updated_at"]
    
    def __str__(self):
        return f"Config {'Actif' if self.is_active else 'Inactif'} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        """S'assurer qu'une seule configuration est active"""
        if self.is_active:
            FeedScoreConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        
        # Valeur par defaut pour les JSON
        if not self.content_multipliers:
            self.content_multipliers = {
                "image": 2.0,
                "video": 1.5,
                "poll": 1.2,
                "link": 1.1,
                "text": 1.0
            }
        
        if not self.engagement_coefficients:
            self.engagement_coefficients = {
                "comment": 3.0,
                "like": 2.0,
                "view": 0.1,
                "share": 1.5
            }
        super().save(*args, **kwargs)
    

class ProfilScoreRecord(ENSPMHubBaseModel):
    """Historique des poids utilisateurs"""
    profil = models.ForeignKey('users.Profil', on_delete=models.CASCADE, related_name='score_records')
    calculated_score = models.FloatField()
    config = models.ForeignKey(FeedScoreConfig, on_delete=models.SET_NULL, null=True, blank=True)
    calculation_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Historique des poids utilisateurs"
        verbose_name_plural = "Historique des poids utilisateurs"
        indexes = [
            models.Index(fields=['profil', '-calculation_time']),
        ]
        ordering = ["-calculation_time"]
        

class PostScoreRecord(ENSPMHubBaseModel):
    """Historique des poids des posts"""
    post = models.ForeignKey('feeds.Post', on_delete=models.CASCADE, related_name='score_records')
    calculated_score = models.FloatField()
    config = models.ForeignKey(FeedScoreConfig, on_delete=models.SET_NULL, null=True, blank=True)
    calculation_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Historique des poids des posts"
        verbose_name_plural = "Historique des poids des posts"
        indexes = [
            models.Index(fields=['post', '-calculation_time']),
        ]
        ordering = ["-calculation_time"]
    
    