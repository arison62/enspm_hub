# network/admin/mentorship.py
from django.contrib import admin
from django.utils.html import format_html, escape
from django.utils.translation import gettext_lazy as _
from network.models import (
    MentorProfile, MentorProfileValidation
)


# ============================================
# ADMIN POUR MENTOR PROFILE
# ============================================

@admin.register(MentorProfile)
class MentorProfileAdmin(admin.ModelAdmin):
    list_display = ('profil', 'status', 'est_actif', 'disponibilite', 'created_at')
    list_filter = ('status', 'est_actif', 'created_at')
    search_fields = ('profil__nom_complet', 'profil__email', 'biographie')
    ordering = ('-created_at',)
    list_per_page = 25
    
    filter_horizontal = ('filieres_expertise', 'domaines_expertise')
    
    fieldsets = (
        ('Informations du mentor', {
            'fields': ('profil', 'biographie', 'disponibilite', 'status', 'id')
        }),
        ('Capacité', {
            'fields': ('est_actif',)
        }),
        ('Expertises', {
            'fields': ('filieres_expertise', 'domaines_expertise')
        }),
        ('Statistiques', {
            'fields': ('nombre_demandes_recues',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('nombre_demandes_recues', 'created_at', 'updated_at', 'id')


# ============================================
# ADMIN POUR MENTOR PROFILE VALIDATION
# ============================================

@admin.register(MentorProfileValidation)
class MentorProfileValidationAdmin(admin.ModelAdmin):
    list_display = ('mentor_profile', 'status_avant', 'status_apres', 'valide_par', 'created_at')
    list_filter = ('status_apres', 'created_at')
    search_fields = ('mentor_profile__profil__nom_complet', 'commentaire')
    ordering = ('-created_at',)
    list_per_page = 25
    readonly_fields = ('created_at',)