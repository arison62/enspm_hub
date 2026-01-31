# network/admin/organisation.py
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html, escape
from django.utils.translation import gettext_lazy as _
from network.models import Organisation, AbonnementOrganisation, MembreOrganisation


class MembreOrganisationInline(admin.TabularInline):
    model = MembreOrganisation
    extra = 1
    fields = ('profil', 'acces', 'date_membre')
    readonly_fields = ('date_membre',)
    verbose_name_plural = _('Membres de l\'organisation')


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    """
    Administration pour le modele Organisation
    """
    list_display = (
        'nom_organisation', 'type_organisation', 'statut_badge',
        'pays', 'created_at', 'deleted_badge'
    )
    list_filter = (
        'type_organisation', 'statut', 'pays', 'deleted',
        'created_at'
    )
    
    search_fields = ('nom_organisation',)
    ordering = ('-created_at',)
    list_per_page = 25
    list_display_links = ('nom_organisation',)

    inlines = [MembreOrganisationInline]
    
    actions = ['activate_organisations', 'deactivate_organisations', 'soft_delete_organisations', 'restore_organisations']
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('nom_organisation', 'type_organisation', 'secteur_activites', 'description')
        }),
        (_('Coordonnées'), {
            'fields': ('adresse', 'ville', 'pays', 'site_web')
        }),
        (_('Visuel et statut'), {
            'fields': ('logo_preview', 'logo', 'statut')
        }),
        (_('Métadonnées'), {
            'fields': ('id', 'created_at', 'updated_at', 'deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('id', 'created_at', 'updated_at', 'deleted_at', 'logo_preview')
    # ======================================
    # Méthodes personnalisées
    # ======================================
    @admin.display(description='Statut', boolean=False)
    def statut_badge(self, obj):
        colors = {
            'active': '#28a745',
            'inactive': '#dc3545',
            'en_attente': '#ffc107',
        }
        color = colors.get(obj.statut, '#6c757d')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_statut_display()
        )

    @admin.display(description='Supprimé', boolean=True)
    def deleted_badge(self, obj):
        return obj.deleted

    @admin.display(description=_('Aperçu du logo'))
    def logo_preview(self, obj):
        if obj.logo:
            safe_url = escape(obj.logo.url)
            return format_html('<img src="{}" width="100" height="100" style="object-fit: contain;" />', safe_url)
        return _('Aucun logo')
    
    # ======================================
    # Actions personnalisées
    # ======================================
    @admin.action(description='Activer les organisations sélectionnées')
    def activate_organisations(self, request, queryset):
        updated = queryset.update(statut='active')
        self.message_user(request, f'{updated} organisation(s) activée(s).')

    @admin.action(description='Désactiver les organisations sélectionnées')
    def deactivate_organisations(self, request, queryset):
        updated = queryset.update(statut='inactive')
        self.message_user(request, f'{updated} organisation(s) désactivée(s).')

    @admin.action(description='Supprimer logiquement les organisations')
    def soft_delete_organisations(self, request, queryset):
        count = 0
        for org in queryset.filter(deleted=False):
            org.soft_delete()
            count += 1
        self.message_user(request, f'{count} organisation(s) supprimée(s) logiquement.')

    @admin.action(description='Restaurer les organisations supprimées')
    def restore_organisations(self, request, queryset):
        count = 0
        for org in queryset.filter(deleted=True):
            org.restore()
            count += 1
        self.message_user(request, f'{count} organisation(s) restaurée(s).')
    
    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return Organisation.all_objects.prefetch_related('secteur_activite').all()
    


@admin.register(MembreOrganisation)
class MembreOrganisationAdmin(admin.ModelAdmin):
    """
    Administration pour le modele MembreOrganisation
    """
    list_display = (
        'profil_link', 'acces_badge', 'date_membre',
    )
    list_filter = ('acces', 'date_membre')
    search_fields = ('profil__nom_complet', 'organisation__nom_organisation')
    ordering = ('-date_membre',)
    list_per_page = 50
    fieldsets = (
        (_('Informations principales'), {
            'fields': ('profil', 'organisation', 'acces')
        }),
        (_('Dates'), {
            'fields': ('date_membre', 'created_at', 'updated_at')
        }),
        (_('Métadonnées'), {
            'fields': ('deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('date_membre', 'created_at', 'updated_at', 'deleted_at', 'deleted')
    

    # ======================================
    # Méthodes d'affichage personnalisées
    # ======================================
    
    @admin.display(description='Profil')
    def profil_link(self, obj):
        if obj.profil:
            url = f'/admin/users/profil/{obj.profil.id}/change/'
            return format_html('<a href="{}">{}</a>', url, escape(obj.profil.nom_complet))
        return '-'

    @admin.display(description='Organisation')
    def organisation_link(self, obj):
        if obj.organisation:
            url = f'/admin/network/organisation/{obj.organisation.id}/change/'
            return format_html('<a href="{}">{}</a>', url, escape(obj.organisation.nom_organisation))
        return '-'
    
    @admin.display(description='Accès', boolean=False)
    def acces_badge(self, obj):
        colors = {
            'admin': '#28a745',
            'membre': '#6c757d',
        }
        color = colors.get(obj.acces, '#6c757d')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_acces_display()
        )

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return MembreOrganisation.all_objects.select_related('profil', 'organisation').all()
    

@admin.register(AbonnementOrganisation)
class AbonnementOrganisationAdmin(admin.ModelAdmin):
    """
    Administration pour les abonnements aux organisations.
    """
    list_display = (
        'profil_link', 'organisation_link', 'date_abonnement'
    )
    list_filter = ('date_abonnement',)
    search_fields = ('profil__nom_complet', 'organisation__nom_organisation')
    ordering = ('-date_abonnement',)
    list_per_page = 50

    fieldsets = (
        (_('Informations'), {
            'fields': ('profil', 'organisation', 'date_abonnement')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at', 'deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('date_abonnement', 'created_at', 'updated_at', 'deleted_at', 'deleted')

    # ======================================
    # Méthodes d'affichage personnalisées
    # ======================================
    @admin.display(description='Profil')
    def profil_link(self, obj):
        if obj.profil:
            url = f'/admin/users/profil/{obj.profil.id}/change/'
            return format_html('<a href="{}">{}</a>', url, escape(obj.profil.nom_complet))
        return '-'

    @admin.display(description='Organisation')
    def organisation_link(self, obj):
        if obj.organisation:
            url = f'/admin/network/organisation/{obj.organisation.id}/change/'
            return format_html('<a href="{}">{}</a>', url, escape(obj.organisation.nom_organisation))
        return '-'

    def get_queryset(self, request):
        return AbonnementOrganisation.all_objects.select_related('profil', 'organisation').all()
