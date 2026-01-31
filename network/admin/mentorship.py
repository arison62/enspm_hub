# network/admin/mentorship.py
from django.contrib import admin
from django.utils.html import format_html, escape
from django.utils.translation import gettext_lazy as _
from network.models import (
    MentorProfile, DemandeMentoring, 
    RelationMentorat, SessionMentorat, FeedbackMentorat
)


# ============================================
# ADMIN POUR MENTOR PROFILE
# ============================================

@admin.register(MentorProfile)
class MentorProfileAdmin(admin.ModelAdmin):
    list_display = ('profil', 'est_actif', 'disponibilite', 'capacite', 'created_at')
    list_filter = ('est_actif', 'created_at')
    search_fields = ('profil__nom_complet', 'profil__email', 'biographie')
    ordering = ('-created_at',)
    list_per_page = 25
    
    filter_horizontal = ('filieres_expertise', 'domaines_expertise')
    
    fieldsets = (
        ('Informations du mentor', {
            'fields': ('profil', 'biographie', 'disponibilite')
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
# ADMIN POUR DEMANDE MENTORING
# ============================================

@admin.register(DemandeMentoring)
class DemandeMentoringAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'type_demande', 'status', 'mentee', 'mentor_cible', 'created_at')
    list_filter = ('status', 'created_at', 'mentor_cible')
    search_fields = ('mentee__nom_complet', 'mentee__user__email', 'message', 'objectifs')
    ordering = ('-created_at',)
    list_per_page = 30
    
    fieldsets = (
        ('Demande', {
            'fields': ('mentee', 'mentor_cible', 'status', 'date_expiration')
        }),
        ('Contenu', {
            'fields': ('message', 'objectifs', 'attentes')
        }),
        ('Modalités', {
            'fields': ('disponibilite_souhaitee', 'format_prefere')
        }),
        ('Ciblage', {
            'fields': ('filieres', 'domaines'),
            'classes': ('collapse',)
        }),
        ('Réponse', {
            'fields': ('mentor_repondant', 'reponse_message', 'reponse_date'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('filieres', 'domaines')
    
    @admin.display(description='Type')
    def type_demande(self, obj):
        if obj.mentor_cible:
            return format_html('<span style="background-color: #6f42c1; color: white; padding: 2px 8px; border-radius: 4px;">Directe</span>')
        return format_html('<span style="background-color: #17a2b8; color: white; padding: 2px 8px; border-radius: 4px;">Générale</span>')


# ============================================
# ADMIN POUR RELATION MENTORAT
# ============================================

@admin.register(RelationMentorat)
class RelationMentoratAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'statut', 'mentor', 'mentee', 'date_debut', 'nombre_sessions')
    list_filter = ('statut', 'date_debut')
    search_fields = ('mentor__profil__nom_complet', 'mentee__nom_complet', 'objectifs')
    ordering = ('-date_debut',)
    list_per_page = 30
    
    fieldsets = (
        ('Relation', {
            'fields': ('mentor', 'mentee', 'demande_origine', 'statut')
        }),
        ('Objectifs', {
            'fields': ('objectifs', 'date_debut', 'date_fin_prevue', 'date_fin_reelle')
        }),
        ('Suivi', {
            'fields': ('nombre_sessions', 'derniere_session', 'notes_privees_mentor', 'notes_privees_mentee'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('nombre_sessions', 'derniere_session')


# ============================================
# ADMIN POUR SESSION MENTORAT
# ============================================

@admin.register(SessionMentorat)
class SessionMentoratAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'relation', 'date_prevue', 'type_session', 'statut', 'presence_mentee')
    list_filter = ('statut', 'type_session', 'date_prevue')
    search_fields = ('relation__mentor__profil__nom_complet', 'relation__mentee__nom_complet', 'theme')
    ordering = ('-date_prevue',)
    list_per_page = 30
    
    fieldsets = (
        ('Relation', {
            'fields': ('relation',)
        }),
        ('Planification', {
            'fields': ('date_prevue', 'duree_minutes', 'type_session', 'statut', 'lieu_ou_lien')
        }),
        ('Contenu', {
            'fields': ('theme', 'objectifs_session')
        }),
        ('Compte-rendu', {
            'fields': ('date_reelle', 'duree_reelle_minutes', 'notes', 'actions_suivantes', 'presence_mentee')
        }),
    )


# ============================================
# ADMIN POUR FEEDBACK MENTORAT
# ============================================

@admin.register(FeedbackMentorat)
class FeedbackMentoratAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'relation', 'auteur', 'note', 'recommanderait', 'created_at')
    list_filter = ('recommanderait', 'created_at')
    search_fields = ('auteur__nom_complet', 'relation__mentor__profil__nom_complet', 'commentaires')
    ordering = ('-created_at',)
    list_per_page = 30
    
    fieldsets = (
        ('Relation', {
            'fields': ('relation', 'auteur')
        }),
        ('Évaluation', {
            'fields': ('note', 'commentaires', 'recommanderait')
        }),
    )