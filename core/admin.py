# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.db.models import Count
from .models import (
    AnneePromotion, Domaine, Filiere, SecteurActivite,
    Devise, TitreHonorifique, ReseauSocial
)
from core.models import User, AuditLog, PasswordResetToken
from users.models import Profil, LienReseauSocialProfil, ExperienceProfessionnelle


# ==========================================
# 1. INLINE POUR PROFIL DANS USER ADMIN
# ==========================================
class LienReseauSocialProfilInline(admin.StackedInline):
    model = LienReseauSocialProfil
    can_delete = True
    verbose_name_plural = _('Liens reseaux sociaux')
    fk_name = 'profil'
    fields = ('reseau', 'url', 'est_actif')
    readonly_fields = ('id', 'created_at', 'updated_at')

class ExperienceProfessionnelleInline(admin.StackedInline):
    model = ExperienceProfessionnelle
    can_delete = True
    verbose_name_plural = _('Expériences professionnelles')
    fk_name = 'profil'
    fields = (
        'titre_poste', 'nom_entreprise', 'lieu', 
        'date_debut', 'date_fin', 'est_poste_actuel', 
        'description'
    )
    readonly_fields = ('id', 'created_at', 'updated_at')


class ProfilInline(admin.StackedInline):
    model = Profil
    can_delete = False
    verbose_name_plural = _('Profil')
    fk_name = 'user'
    fields = (
        'nom_complet', 'matricule', 'titre', 'statut_global',
         'annee_sortie', 'telephone', 'domaine',
        'bio', 'photo_profil', 'slug'
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [LienReseauSocialProfilInline, ExperienceProfessionnelleInline]


# ==========================================
# 2. ADMIN UTILISATEUR (AUTHENTIFICATION)
# ==========================================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Administration pour le modèle User (authentification).
    Le Profil est géré via inline.
    """
    list_display = (
        'email', 'role_systeme', 'est_actif_badge', 'telephone',
        'last_login', 'created_at', 'deleted_badge'
    )
    list_filter = (
        'role_systeme', 'est_actif', 'deleted',
        'is_staff', 'is_superuser', 'created_at'
    )
    search_fields = ('email',)
    ordering = ('-created_at',)
    list_per_page = 25
    list_display_links = ('email',)

    inlines = [ProfilInline]

    actions = ['activate_users', 'deactivate_users', 'soft_delete_users', 'restore_users', 'delete_users']

    fieldsets = (
        (_('Informations de connexion'), {
            'fields': ('email', 'password', 'telephone')
        }),
        (_('Rôle et permissions'), {
            'fields': ('role_systeme', 'est_actif', 'is_staff', 'is_superuser'),
        }),
        (_('Métadonnées'), {
            'fields': ('id', 'last_login', 'created_at', 'updated_at', 'deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (_('Informations de connexion'), {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role_systeme'),
        }),
    )

    readonly_fields = ('id', 'last_login', 'created_at', 'updated_at', 'deleted_at')

    # ======================================
    # Méthodes personnalisées
    # ======================================
    @admin.display(description='Actif', boolean=True)
    def est_actif_badge(self, obj):
        return obj.est_actif and not obj.deleted

    @admin.display(description='Supprimé', boolean=True)
    def deleted_badge(self, obj):
        return obj.deleted

    # ======================================
    # Actions personnalisées
    # ======================================
    @admin.action(description='Activer les utilisateurs sélectionnés')
    def activate_users(self, request, queryset):
        updated = queryset.update(est_actif=True)
        self.message_user(request, f'{updated} utilisateur(s) activé(s).')

    @admin.action(description='Désactiver les utilisateurs sélectionnés')
    def deactivate_users(self, request, queryset):
        updated = queryset.update(est_actif=False)
        self.message_user(request, f'{updated} utilisateur(s) désactivé(s).')

    @admin.action(description='Supprimer logiquement les utilisateurs')
    def soft_delete_users(self, request, queryset):
        count = 0
        for user in queryset.filter(deleted=False):
            user.soft_delete()
            if hasattr(user, 'profil'):
                user.profil.soft_delete()
            count += 1
        self.message_user(request, f'{count} utilisateur(s) supprimé(s) logiquement.')

    @admin.action(description='Restaurer les utilisateurs supprimés')
    def restore_users(self, request, queryset):
        count = 0
        for user in queryset.filter(deleted=True):
            user.restore()
            if hasattr(user, 'profil'):
                user.profil.restore()
            count += 1
        self.message_user(request, f'{count} utilisateur(s) restauré(s).')

    @admin.action(description='Supprimer permanentement les utilisateurs')
    def delete_users(self, request, queryset):
        count = 0
        for user in queryset.filter(deleted=True):
            print("User to delete : ", user)
            user.delete()
            if hasattr(user, 'profil'):
                user.profil.delete()
            count += 1
        self.message_user(request, f'{count} utilisateur(s) supprimé(s) permanentement.')
        
    # ======================================
    # Afficher tous les users (y compris soft-deleted)
    # ======================================
    def get_queryset(self, request):
        return User.all_objects.all()

    # Désactiver suppression permanente
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ==========================================
# 3. ADMIN PROFIL (DONNÉES MÉTIER)
# ==========================================
@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = (
        'nom_complet', 'user_email', 'matricule','slug', 'statut_global',
        'pays', 'ville', 'adresse',
        'photo_thumbnail', 'created_at', 
    )   
    list_filter = ('statut_global', 'created_at', 'deleted')
    search_fields = ('nom_complet', 'matricule', 'user__email', 'telephone', 'domaine')
    ordering = ('-created_at',)
    list_per_page = 25
    readonly_fields = ('id', 'created_at', 'updated_at', 'deleted_at')
    inlines = [LienReseauSocialProfilInline, ExperienceProfessionnelleInline]
    fieldsets = (
        (_('Lien utilisateur'), {
            'fields': ('user',)
        }),
        (_('Informations personnelles'), {
            'fields': ('nom_complet', 'matricule', 'titre', 'telephone', 'bio', 'photo_profil')
        }),
        (_('Adresse'), {
            'fields': ('pays', 'ville', 'adresse')
        }),
        (_('Statut et domaine'), {
            'fields': ('statut_global', 'domaine', 'annee_sortie')
        }),
        (_('Métadonnées'), {
            'fields': ('id', 'slug', 'created_at', 'updated_at', 'deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        return obj.user.email if obj.user else '-'
    user_email.short_description = _('Email')


    @admin.display(description='Photo')
    def photo_thumbnail(self, obj):
        if obj.photo_profil:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover;" />',
                obj.photo_profil
            )
        return format_html(
            '<div style="width: 50px; height: 50px; border-radius: 50%; '
            'background-color: #e0e0e0; display: flex; align-items: center; '
            'justify-content: center; color: #666; font-size: 12px;">N/A</div>'
        )
    photo_thumbnail.short_description = _('Photo')

    def get_queryset(self, request):
        return Profil.all_objects.select_related('user').all()

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ==========================================
# 4. ADMIN AUDIT LOG (VERSION CORRIGÉE)
# ==========================================
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Administration du journal d'audit - Lecture seule.
    """
    list_display = (
        'created_at', 'user_link', 'action_badge', 'entity_type', 'entity_id_short', 'ip_address'
    )
    list_filter = ('action', 'entity_type', 'created_at')
    search_fields = ('user__email', 'entity_type', 'entity_id', 'ip_address', 'user_agent')
    ordering = ('-created_at',)
    list_per_page = 50

    readonly_fields = (
        'id', 'user', 'action', 'entity_type', 'entity_id',
        'old_values', 'new_values', 'ip_address', 'user_agent',
        'created_at', 'updated_at'
    )

    fieldsets = (
        (_('Informations générales'), {
            'fields': ('id', 'created_at', 'user', 'action')
        }),
        (_('Entité concernée'), {
            'fields': ('entity_type', 'entity_id')
        }),
        (_('Modifications'), {
            'fields': ('old_values', 'new_values'),
            'classes': ('collapse',)
        }),
        (_('Contexte technique'), {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )

    # ======================================
    # Méthodes d'affichage personnalisées
    # ======================================
    @admin.display(description='Utilisateur')
    def user_link(self, obj):
        if obj.user:
            url = f'/admin/core/user/{obj.user.id}/change/'
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'

    @admin.display(description='Action')
    def action_badge(self, obj):
        colors = {
            'CREATE': '#28a745',
            'UPDATE': '#ffc107',
            'DELETE': '#dc3545',
            'VIEW': '#17a2b8',
            'ACCESS_DENIED': '#6c757d',
        }
        color = colors.get(obj.action, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_action_display()
        )

    @admin.display(description='ID Entité')
    def entity_id_short(self, obj):
        return str(obj.entity_id)[:8] + '...'

    # ======================================
    # Optimisations et sécurité
    # ======================================
    def get_queryset(self, request):
        return AuditLog.all_objects.select_related('user').all()

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
    


def activer_elements(modeladmin, request, queryset):
    """Action pour activer des éléments en masse"""
    count = queryset.update(est_actif=True)
    modeladmin.message_user(
        request,
        f"{count} élément(s) activé(s) avec succès.",
        level='success'
    )
activer_elements.short_description = "✅ Activer les éléments sélectionnés"


def desactiver_elements(modeladmin, request, queryset):
    """Action pour désactiver des éléments en masse"""
    count = queryset.update(est_actif=False)
    modeladmin.message_user(
        request,
        f"{count} élément(s) désactivé(s) avec succès.",
        level='warning'
    )
desactiver_elements.short_description = "❌ Désactiver les éléments sélectionnés"

# =========================================
# Mot de passe temporaire
# =========================================
@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at')
    list_filter = ('created_at', 'expires_at')
    search_fields = ('user__email', 'token')
    ordering = ('-created_at',)



# ==========================================
# 1. ANNÉE DE PROMOTION
# ==========================================

@admin.register(AnneePromotion)
class AnneePromotionAdmin(admin.ModelAdmin):
    list_display = [
        'annee',
        'libelle',
        'statut_badge',
        'nombre_profils',
        'ordre_affichage',
        'date_creation'
    ]
    list_filter = ['est_active', 'created_at']
    search_fields = ['annee', 'libelle', 'description']
    ordering = ['-annee']
    actions = [activer_elements, desactiver_elements]
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('annee', 'libelle', 'description')
        }),
        ('Affichage', {
            'fields': ('est_active', 'ordre_affichage'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def statut_badge(self, obj):
        """Badge coloré pour le statut"""
        if obj.est_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">✓ Active</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">✗ Inactive</span>'
        )
    statut_badge.short_description = 'Statut'
    
    def nombre_profils(self, obj):
        """Nombre de profils associés"""
        count = obj.profils.count()
        if count > 0:
            return format_html(
                '<a href="/admin/users/profil/?annee_sortie__id__exact={}">{} profil(s)</a>',
                obj.id,
                count
            )
        return '0 profil'
    nombre_profils.short_description = 'Profils'
    
    def date_creation(self, obj):
        """Date de création formatée"""
        return obj.created_at.strftime('%d/%m/%Y à %H:%M')
    date_creation.short_description = 'Créé le'


# ==========================================
# 2. DOMAINE
# ==========================================

class FiliereInline(admin.TabularInline):
    """Inline pour gérer les filières depuis le domaine"""
    model = Filiere
    extra = 1
    fields = ['nom', 'code', 'niveau', 'duree_annees', 'est_actif', 'ordre_affichage']
    ordering = ['ordre_affichage', 'nom']


@admin.register(Domaine)
class DomaineAdmin(admin.ModelAdmin):
    list_display = [
        'nom',
        'code',
        'categorie',
        'nombre_filieres',
        'nombre_profils',
        'statut_badge',
        'ordre_affichage'
    ]
    list_filter = ['categorie', 'est_actif', 'created_at']
    search_fields = ['nom', 'code', 'description']
    ordering = ['ordre_affichage', 'nom']
    actions = [activer_elements, desactiver_elements]
    inlines = [FiliereInline]
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('nom', 'code', 'categorie', 'description')
        }),
        ('Affichage', {
            'fields': ('est_actif', 'ordre_affichage'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def statut_badge(self, obj):
        if obj.est_actif:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">✓ Actif</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">✗ Inactif</span>'
        )
    statut_badge.short_description = 'Statut'
    
    def nombre_filieres(self, obj):
        """Nombre de filières associées"""
        count = obj.filieres.filter(est_actif=True).count()
        return f"{count} filière(s)"
    nombre_filieres.short_description = 'Filières'
    
    def nombre_profils(self, obj):
        """Nombre de profils associés"""
        count = obj.profils.count()
        if count > 0:
            return format_html(
                '<a href="/admin/users/profil/?domaine__id__exact={}">{} profil(s)</a>',
                obj.id,
                count
            )
        return '0 profil'
    nombre_profils.short_description = 'Profils'


# ==========================================
# 3. FILIÈRE
# ==========================================

@admin.register(Filiere)
class FiliereAdmin(admin.ModelAdmin):
    list_display = [
        'nom',
        'code',
        'domaine',
        'niveau',
        'duree_annees',
        'statut_badge',
        'ordre_affichage'
    ]
    list_filter = ['domaine', 'niveau', 'est_actif', 'created_at']
    search_fields = ['nom', 'code', 'description', 'domaine__nom']
    ordering = ['domaine__ordre_affichage', 'ordre_affichage', 'nom']
    actions = [activer_elements, desactiver_elements]
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('domaine', 'nom', 'code', 'niveau', 'duree_annees', 'description')
        }),
        ('Affichage', {
            'fields': ('est_actif', 'ordre_affichage'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def statut_badge(self, obj):
        if obj.est_actif:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">✓ Active</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">✗ Inactive</span>'
        )
    statut_badge.short_description = 'Statut'


# ==========================================
# 4. SECTEUR D'ACTIVITÉ
# ==========================================

@admin.register(SecteurActivite)
class SecteurActiviteAdmin(admin.ModelAdmin):
    list_display = [
        'nom',
        'code',
        'parent_badge',
        'nombre_sous_secteurs',
        'nombre_organisations',
        'statut_badge',
        'ordre_affichage'
    ]
    list_filter = ['est_actif', 'categorie_parent', 'created_at']
    search_fields = ['nom', 'code', 'description']
    ordering = ['ordre_affichage', 'nom']
    actions = [activer_elements, desactiver_elements]
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('nom', 'code', 'categorie_parent', 'description', 'icone')
        }),
        ('Affichage', {
            'fields': ('est_actif', 'ordre_affichage'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def statut_badge(self, obj):
        if obj.est_actif:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">✓ Actif</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">✗ Inactif</span>'
        )
    statut_badge.short_description = 'Statut'
    
    def parent_badge(self, obj):
        """Badge pour afficher le parent"""
        if obj.categorie_parent:
            return format_html(
                '<span style="background-color: #6c757d; color: white; padding: 3px 8px; border-radius: 3px;">↳ {}</span>',
                obj.categorie_parent.nom
            )
        return format_html(
            '<span style="background-color: #007bff; color: white; padding: 3px 8px; border-radius: 3px;">⬤ Parent</span>'
        )
    parent_badge.short_description = 'Hiérarchie'
    
    def nombre_sous_secteurs(self, obj):
        """Nombre de sous-secteurs"""
        count = obj.sous_secteurs.filter(est_actif=True).count()
        return f"{count} sous-secteur(s)"
    nombre_sous_secteurs.short_description = 'Sous-secteurs'
    
    def nombre_organisations(self, obj):
        """Nombre d'organisations associées"""
        count = obj.organisations.count()
        if count > 0:
            return format_html(
                '<a href="/admin/network/organisation/?secteur_activite__id__exact={}">{} org.</a>',
                obj.id,
                count
            )
        return '0 org.'
    nombre_organisations.short_description = 'Organisations'

# ==========================================
# 6. DEVISE
# ==========================================

@admin.register(Devise)
class DeviseAdmin(admin.ModelAdmin):
    list_display = [
        'code',
        'nom',
        'symbole',
        'taux_usd',
        'derniere_maj',
        'statut_badge',
        'ordre_affichage'
    ]
    list_filter = ['est_active', 'created_at']
    search_fields = ['code', 'nom', 'symbole']
    ordering = ['ordre_affichage', 'code']
    actions = [activer_elements, desactiver_elements, 'mettre_a_jour_taux']
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('code', 'nom', 'symbole')
        }),
        ('Taux de Change', {
            'fields': ('taux_change_usd', 'date_mise_a_jour_taux'),
            'description': 'Taux par rapport au USD (1 USD = X devise)'
        }),
        ('Affichage', {
            'fields': ('est_active', 'ordre_affichage'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def statut_badge(self, obj):
        if obj.est_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">✓ Active</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">✗ Inactive</span>'
        )
    statut_badge.short_description = 'Statut'
    
    def taux_usd(self, obj):
        """Taux de change formaté"""
        if obj.taux_change_usd:
            return f"1 USD = {obj.taux_change_usd} {obj.symbole}"
        return '-'
    taux_usd.short_description = 'Taux USD'
    
    def derniere_maj(self, obj):
        """Date de dernière mise à jour du taux"""
        if obj.date_mise_a_jour_taux:
            return obj.date_mise_a_jour_taux.strftime('%d/%m/%Y')
        return 'Jamais'
    derniere_maj.short_description = 'Dernière MAJ'
    
    def mettre_a_jour_taux(self, request, queryset):
        """Action pour mettre à jour les taux de change"""
        # TODO: Intégrer une API de taux de change (ex: exchangerate-api.com)
        self.message_user(
            request,
            "Fonctionnalité à implémenter: mise à jour automatique via API",
            level='warning'
        )
    mettre_a_jour_taux.short_description = "🔄 Mettre à jour les taux"


# ==========================================
# 7. TITRE HONORIFIQUE
# ==========================================

@admin.register(TitreHonorifique)
class TitreHonorifiqueAdmin(admin.ModelAdmin):
    list_display = [
        'titre',
        'nom_complet',
        'type_badge',
        'nombre_profils',
        'statut_badge',
        'ordre_affichage'
    ]
    list_filter = ['type_titre', 'est_actif', 'created_at']
    search_fields = ['titre', 'nom_complet', 'description']
    ordering = ['ordre_affichage', 'titre']
    actions = [activer_elements, desactiver_elements]
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('titre', 'nom_complet', 'type_titre', 'description')
        }),
        ('Affichage', {
            'fields': ('est_actif', 'ordre_affichage'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def statut_badge(self, obj):
        if obj.est_actif:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">✓ Actif</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">✗ Inactif</span>'
        )
    statut_badge.short_description = 'Statut'
    
    def type_badge(self, obj):
        """Badge coloré pour le type"""
        couleurs = {
            'academique': '#007bff',
            'professionnel': '#28a745',
            'honorifique': '#ffc107',
            'civilite': '#6c757d'
        }
        couleur = couleurs.get(obj.type_titre, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            couleur,
            obj.get_type_titre_display()
        )
    type_badge.short_description = 'Type'
    
    def nombre_profils(self, obj):
        """Nombre de profils utilisant ce titre"""
        count = obj.profils.count()
        if count > 0:
            return format_html(
                '<a href="/admin/users/profil/?titre__id__exact={}">{} profil(s)</a>',
                obj.id,
                count
            )
        return '0 profil'
    nombre_profils.short_description = 'Profils'


# ==========================================
# 8. RÉSEAU SOCIAL
# ==========================================

@admin.register(ReseauSocial)
class ReseauSocialAdmin(admin.ModelAdmin):
    list_display = [
        'nom',
        'code',
        'type_badge',
        'url_base',
        'nombre_liens',
        'statut_badge',
        'ordre_affichage'
    ]
    list_filter = ['type_reseau', 'est_actif', 'created_at']
    search_fields = ['nom', 'code', 'url_base']
    ordering = ['ordre_affichage', 'nom']
    actions = [activer_elements, desactiver_elements]
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('nom', 'code', 'type_reseau', 'url_base')
        }),
        ('Validation', {
            'fields': ('pattern_validation', 'placeholder_exemple'),
            'description': 'Pattern regex pour valider les URLs + exemple de placeholder'
        }),
        ('Affichage', {
            'fields': ('est_actif', 'ordre_affichage'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def statut_badge(self, obj):
        if obj.est_actif:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">✓ Actif</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">✗ Inactif</span>'
        )
    statut_badge.short_description = 'Statut'
    
    def type_badge(self, obj):
        """Badge coloré pour le type"""
        couleurs = {
            'professionnel': '#0077B5',
            'social': '#1DA1F2',
            'academique': '#007bff',
            'technique': '#333',
            'portfolio': '#FF6B6B'
        }
        couleur = couleurs.get(obj.type_reseau, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            couleur,
            obj.get_type_reseau_display()
        )
    type_badge.short_description = 'Type'
    
    def nombre_liens(self, obj):
        """Nombre de liens utilisant ce réseau"""
        count = obj.liens.count()
        if count > 0:
            return format_html(
                '<a href="/admin/users/lienreseausocial/?reseau__id__exact={}">{} lien(s)</a>',
                obj.id,
                count
            )
        return '0 lien'
    nombre_liens.short_description = 'Liens'

# ==========================================
# 5. PERSONNALISATION GLOBALE DU SITE ADMIN
# ==========================================
admin.site.site_header = "ENSPM Hub - Administration"
admin.site.site_title = "ENSPM Hub Admin"
admin.site.index_title = "Bienvenue sur l'interface d'administration ENSPM Hub"