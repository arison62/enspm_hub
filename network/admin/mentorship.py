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
    list_display = ('profil', 'status', 'est_actif', 'disponibilite', 'capacite', 'created_at')
    list_filter = ('status', 'est_actif', 'created_at')
    search_fields = ('profil__nom_complet', 'profil__email', 'biographie')
    ordering = ('-created_at',)
    list_per_page = 25
    
    filter_horizontal = ('filieres_expertise', 'domaines_expertise')
    
    fieldsets = (
        ('Informations du mentor', {
            'fields': ('profil', 'biographie', 'disponibilite', 'status')
        }),
        ('Capacité', {
            'fields': ('nombre_max_mentees', 'est_actif')
        }),
        ('Expertises', {
            'fields': ('filieres_expertise', 'domaines_expertise')
        }),
        ('Statistiques', {
            'fields': ('nombre_demandes_recues', 'nombre_demandes_acceptees', 'nombre_mentees_actuels'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('nombre_demandes_recues', 'nombre_demandes_acceptees', 'nombre_mentees_actuels')
    
    @admin.display(description='Capacité')
    def capacite(self, obj):
        actuels = obj.nombre_mentees_actuels
        max_mentees = obj.nombre_max_mentees
        places = max_mentees - actuels
        
        if places <= 0:
            return format_html('<span style="color: red; font-weight: bold;">Plein ({}/{})</span>', actuels, max_mentees)
        elif places == 1:
            return format_html('<span style="color: orange; font-weight: bold;">1 place dispo</span>')
        else:
            return format_html('<span style="color: green; font-weight: bold;">{} places dispo</span>', places)


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