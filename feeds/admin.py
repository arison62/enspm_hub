
# feeds/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from feeds.models import (
    Post, Comment, Like, View, Share, Report,
    FeedScoreConfig, PostScoreRecord, ProfilScoreRecord
)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'get_excerpt', 'is_pinned', 
                   'likes_count', 'comments_count', 'created_at']
    list_filter = ['is_pinned', 'is_archived', 'created_at']
    search_fields = ['content_text', 'author__nom_complet', 'author__matricule']
    readonly_fields = ['id', 'created_at', 'updated_at', 'content_text', 
                      'likes_count', 'comments_count', 'views_count', 'shares_count']
    date_hierarchy = 'created_at'
    
    def get_excerpt(self, obj):
        from django.utils.text import Truncator
        return Truncator(obj.content_text).words(15)
    get_excerpt.short_description = _("Extrait")
    
    fieldsets = (
        (_('Contenu'), {
            'fields': ('author', 'content', 'content_text')
        }),
        (_('Options'), {
            'fields': ('is_pinned', 'is_archived')
        }),
        (_('Statistiques'), {
            'fields': ('likes_count', 'comments_count', 'views_count', 'shares_count'),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('id', 'created_at', 'updated_at', 'deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'post', 'get_excerpt', 'parent', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content_text', 'author__nom_complet', 'post__content_text']
    readonly_fields = ['id', 'created_at', 'updated_at', 'content_text', 
                      'likes_count', 'replies_count']
    date_hierarchy = 'created_at'
    
    def get_excerpt(self, obj):
        from django.utils.text import Truncator
        return Truncator(obj.content_text).words(10)
    get_excerpt.short_description = _("Extrait")


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'profil', 'post', 'comment', 'created_at']
    list_filter = ['created_at']
    search_fields = ['profil__nom_complet']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'


@admin.register(View)
class ViewAdmin(admin.ModelAdmin):
    list_display = ['id', 'post', 'profil', 'ip_address', 'created_at']
    list_filter = ['created_at']
    search_fields = ['profil__nom_complet', 'ip_address']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ['id', 'post', 'profil', 'platform', 'created_at']
    list_filter = ['platform', 'created_at']
    search_fields = ['profil__nom_complet']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'reporter', 'reason', 'status', 'post', 'comment', 'created_at']
    list_filter = ['status', 'reason', 'created_at']
    search_fields = ['reporter__nom_complet', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Signalement'), {
            'fields': ('reporter', 'post', 'comment', 'reason', 'description')
        }),
        (_('Traitement'), {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'resolution_note')
        }),
        (_('Métadonnées'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FeedScoreConfig)
class FeedScoreConfigAdmin(admin.ModelAdmin):
    list_display = ['id', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (_('Configuration Profil'), {
            'fields': (
                'profil_base_score',
                'profil_activity_coeff',
                'profil_report_penalty_per_report',
                'profil_report_threshold'
            )
        }),
        (_('Configuration Post'), {
            'fields': (
                'post_base_score',
                'post_penality_per_report',
                'post_report_threshold',
                'time_decay_factor'
            )
        }),
        (_('Boost nouveaux posts'), {
            'fields': (
                'boost_new_posts',
                'new_posts_boost_factor',
                'boost_new_posts_threshold'
            )
        }),
        (_('Multiplicateurs et Coefficients'), {
            'fields': ('content_multipliers', 'engagement_coefficients')
        }),
        (_('Statut'), {
            'fields': ('is_active',)
        }),
        (_('Métadonnées'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PostScoreRecord)
class PostScoreRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'post', 'calculated_score', 'calculation_time']
    list_filter = ['calculation_time']
    search_fields = ['post__content_text']
    readonly_fields = ['id', 'created_at', 'calculation_time']
    date_hierarchy = 'calculation_time'


@admin.register(ProfilScoreRecord)
class ProfilScoreRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'profil', 'calculated_score', 'calculation_time']
    list_filter = ['calculation_time']
    search_fields = ['profil__nom_complet']
    readonly_fields = ['id', 'created_at', 'calculation_time']
    date_hierarchy = 'calculation_time'