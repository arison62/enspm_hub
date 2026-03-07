# feeds/models/feeds.py
from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.utils.translation import gettext_lazy as _
from django.utils.text import Truncator
from core.mixins import ChatReferenceable
from bs4 import BeautifulSoup

from core.models import ENSPMHubBaseModel


class Post(ENSPMHubBaseModel, ChatReferenceable):
    """Modèle pour les posts du fil d'actualité"""
    
    REFERENCE_TYPE = "post"
    
    author = models.ForeignKey(
        'users.Profil',
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name=_("Auteur")
    )
    
    content = models.TextField(
        verbose_name=_("Contenu"),
        help_text=_("Contenu HTML du post (rich-text)")
    )
    
    # Champ de texte brut pour la recherche et l'indexation
    content_text = models.TextField(
        blank=True,
        verbose_name=_("Contenu texte"),
        help_text=_("Version texte du contenu sans HTML")
    )
    
    # Champ de recherche vectorielle
    search_vector = SearchVectorField(null=True, blank=True)
    
    is_pinned = models.BooleanField(
        default=False,
        verbose_name=_("Épinglé"),
        help_text=_("Post épinglé en haut du fil")
    )
    
    is_archived = models.BooleanField(
        default=False,
        verbose_name=_("Archivé")
    )
    
    # Compteurs dénormalisés pour les performances
    likes_count = models.PositiveIntegerField(default=0, verbose_name=_("Nombre de likes"))
    comments_count = models.PositiveIntegerField(default=0, verbose_name=_("Nombre de commentaires"))
    views_count = models.PositiveIntegerField(default=0, verbose_name=_("Nombre de vues"))
    shares_count = models.PositiveIntegerField(default=0, verbose_name=_("Nombre de partages"))
    
    class Meta:
        verbose_name = _("Post")
        verbose_name_plural = _("Posts")
        db_table = 'feed_posts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['is_pinned', '-created_at']),
            GinIndex(fields=['search_vector']),
        ]
    
    def __str__(self):
        return f"Post by {self.author.nom_complet} - {Truncator(self.content_text).words(10)}"
    
    def save(self, *args, **kwargs):
        """Extraire le texte du HTML pour la recherche"""
        if self.content:
            soup = BeautifulSoup(self.content, 'html.parser')
            self.content_text = soup.get_text(separator=' ', strip=True)
        super().save(*args, **kwargs)
        
        # Mettre à jour le vecteur de recherche
        if self.content_text:
            Post.objects.filter(pk=self.pk).update(
                search_vector=SearchVector('content_text', weight='A')
            )
    
    @property
    def content_type(self):
        """Détermine le type de contenu du post"""
        if not self.content:
            return 'text'
        
        soup = BeautifulSoup(self.content, 'html.parser')
        
        # Vérifier la présence d'images
        if soup.find('img'):
            return 'image'
        
        # Vérifier la présence de liens
        if soup.find('a'):
            return 'link'
        
        return 'text'

    def get_chat_preview(self) -> dict:
        return {
            "id": self.pk,
            "type": self.REFERENCE_TYPE,
            "titre": self.content_text[:100] + "..." if self.content_text else "",
            "sous_titre": self.author.nom_complet,
            "apercu": self.content_text[:100] + "..." if self.content_text else "",
            "url": f"/network/posts/{self.id}",
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class Comment(ENSPMHubBaseModel, ChatReferenceable):
    """Modèle pour les commentaires sur les posts"""
    
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_("Post")
    )
    
    author = models.ForeignKey(
        'users.Profil',
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_("Auteur")
    )
    
    content = models.TextField(
        verbose_name=_("Contenu"),
        help_text=_("Contenu HTML du commentaire (rich-text)")
    )
    
    content_text = models.TextField(
        blank=True,
        verbose_name=_("Contenu texte"),
        help_text=_("Version texte du contenu sans HTML")
    )
    
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies',
        verbose_name=_("Commentaire parent")
    )
    
    # Compteurs dénormalisés
    likes_count = models.PositiveIntegerField(default=0, verbose_name=_("Nombre de likes"))
    replies_count = models.PositiveIntegerField(default=0, verbose_name=_("Nombre de réponses"))
    
    class Meta:
        verbose_name = _("Commentaire")
        verbose_name_plural = _("Commentaires")
        db_table = 'feed_comments'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['parent', 'created_at']),
        ]
    
    def __str__(self):
        return f"Comment by {self.author.nom_complet} on {self.post}"
    
    def save(self, *args, **kwargs):
        """Extraire le texte du HTML"""
        if self.content:
            soup = BeautifulSoup(self.content, 'html.parser')
            self.content_text = soup.get_text(separator=' ', strip=True)
        super().save(*args, **kwargs)
    
    def get_chat_preview(self) -> dict:
        return {
            "id": self.pk,
            "type": self.REFERENCE_TYPE,
            "titre": self.content_text[:100] + "..." if self.content_text else "",
            "sous_titre": self.author.nom_complet,
            "apercu": self.content_text[:100] + "..." if self.content_text else "",
            "url": f"/network/posts/{self.post.id}/comments/{self.id}",
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    


class Like(ENSPMHubBaseModel):
    """Modèle pour les likes sur les posts et commentaires"""
    
    profil = models.ForeignKey(
        'users.Profil',
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name=_("Profil")
    )
    
    post = models.ForeignKey(
        Post,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name=_("Post")
    )
    
    comment = models.ForeignKey(
        Comment,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name=_("Commentaire")
    )
    
    class Meta:
        verbose_name = _("Like")
        verbose_name_plural = _("Likes")
        db_table = 'feed_likes'
        unique_together = [
            ('profil', 'post'),
            ('profil', 'comment'),
        ]
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['comment', 'created_at']),
            models.Index(fields=['profil', '-created_at']),
        ]
    
    def __str__(self):
        target = self.post if self.post else self.comment
        return f"{self.profil.nom_complet} likes {target}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.post and not self.comment:
            raise ValidationError(_("Un like doit être associé à un post ou un commentaire"))
        if self.post and self.comment:
            raise ValidationError(_("Un like ne peut pas être associé à la fois à un post et un commentaire"))


class View(ENSPMHubBaseModel):
    """Modèle pour tracker les vues des posts"""
    
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='views',
        verbose_name=_("Post")
    )
    
    profil = models.ForeignKey(
        'users.Profil',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='post_views',
        verbose_name=_("Profil")
    )
    
    # Pour les vues anonymes
    session_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Session key")
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("Adresse IP")
    )
    
    class Meta:
        verbose_name = _("Vue")
        verbose_name_plural = _("Vues")
        db_table = 'feed_views'
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['profil', '-created_at']),
        ]
    
    def __str__(self):
        viewer = self.profil.nom_complet if self.profil else "Anonymous"
        return f"{viewer} viewed {self.post}"


class Share(ENSPMHubBaseModel):
    """Modèle pour les partages de posts"""
    
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='shares',
        verbose_name=_("Post")
    )
    
    profil = models.ForeignKey(
        'users.Profil',
        on_delete=models.CASCADE,
        related_name='post_shares',
        verbose_name=_("Profil")
    )
    
    platform = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Plateforme"),
        help_text=_("Plateforme de partage (linkedin, twitter, email, etc.)")
    )
    
    class Meta:
        verbose_name = _("Partage")
        verbose_name_plural = _("Partages")
        db_table = 'feed_shares'
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['profil', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.profil.nom_complet} shared {self.post}"


class Report(ENSPMHubBaseModel):
    """Modèle pour les signalements de posts ou commentaires"""
    
    REASON_CHOICES = [
        ('spam', _('Spam')),
        ('harassment', _('Harcèlement')),
        ('hate_speech', _('Discours haineux')),
        ('violence', _('Violence')),
        ('false_info', _('Fausse information')),
        ('inappropriate', _('Contenu inapproprié')),
        ('other', _('Autre')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('reviewed', _('Examiné')),
        ('resolved', _('Résolu')),
        ('rejected', _('Rejeté')),
    ]
    
    reporter = models.ForeignKey(
        'users.Profil',
        on_delete=models.CASCADE,
        related_name='reports_made',
        verbose_name=_("Rapporteur")
    )
    
    post = models.ForeignKey(
        Post,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_("Post")
    )
    
    comment = models.ForeignKey(
        Comment,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_("Commentaire")
    )
    
    reason = models.CharField(
        max_length=50,
        choices=REASON_CHOICES,
        verbose_name=_("Raison")
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Description détaillée du signalement")
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_("Statut")
    )
    
    reviewed_by = models.ForeignKey(
        'users.Profil',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reports_reviewed',
        verbose_name=_("Examiné par")
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'examen")
    )
    
    resolution_note = models.TextField(
        blank=True,
        verbose_name=_("Note de résolution")
    )
    
    class Meta:
        verbose_name = _("Signalement")
        verbose_name_plural = _("Signalements")
        db_table = 'feed_reports'
        unique_together = [
            ('reporter', 'post'),
            ('reporter', 'comment'),
        ]
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['post', 'status']),
            models.Index(fields=['comment', 'status']),
        ]
    
    def __str__(self):
        target = self.post if self.post else self.comment
        return f"Report by {self.reporter.nom_complet} - {target}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.post and not self.comment:
            raise ValidationError(_("Un signalement doit être associé à un post ou un commentaire"))
        if self.post and self.comment:
            raise ValidationError(_("Un signalement ne peut pas être associé à la fois à un post et un commentaire"))