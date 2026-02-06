# network/admin/groupe.py
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html, escape
from django.utils.translation import gettext_lazy as _
from network.models import Groupe, MembreGroupe, MessageGroupe, MessageDirect


# ============================================
# INLINES
# ============================================

class MembreGroupeInline(admin.TabularInline):
    """Inline pour les membres d'un groupe"""
    model = MembreGroupe
    extra = 1
    fields = ('profil_link', 'role_badge', 'date_membre')
    readonly_fields = ('profil_link', 'role_badge', 'date_membre')
    can_delete = True
    verbose_name = _('membre')
    verbose_name_plural = _('membres du groupe')
    
    @admin.display(description=_('Profil'))
    def profil_link(self, obj):
        if obj.profil:
            url = f'/admin/users/profil/{obj.profil.id}/change/'
            display_text = escape(obj.profil.nom_complet)
            return format_html('<a href="{}" target="_blank">{}</a>', url, display_text)
        return '-'
    
    @admin.display(description=_('Rôle'))
    def role_badge(self, obj):
        colors = {
            'admin': '#dc3545',
            'membre': '#6c757d',
        }
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: 500;">{}</span>',
            color, obj.get_role_display()
        )


class MessageGroupeInline(admin.StackedInline):
    """Inline pour les messages d'un groupe (lecture seule)"""
    model = MessageGroupe
    extra = 0
    fields = ('expediteur_link', 'contenu_preview', 'piece_jointe_link', 'est_lu_badge', 'created_at')
    readonly_fields = ('expediteur_link', 'contenu_preview', 'piece_jointe_link', 'est_lu_badge', 'created_at')
    can_delete = False
    verbose_name = _('message')
    verbose_name_plural = _('messages récents')
    ordering = ('-created_at',)
    max_num = 10  # Limite à 10 messages affichés
    
    @admin.display(description=_('Expéditeur'))
    def expediteur_link(self, obj):
        if obj.expediteur:
            url = f'/admin/users/profil/{obj.expediteur.id}/change/'
            display_text = escape(obj.expediteur.nom_complet)
            return format_html('<a href="{}" target="_blank">{}</a>', url, display_text)
        return '-'
    
    @admin.display(description=_('Contenu'))
    def contenu_preview(self, obj):
        if obj.contenu:
            preview = escape(obj.contenu[:100])
            if len(obj.contenu) > 100:
                preview += '...'
            return format_html('<div style="max-width: 400px; white-space: pre-wrap;">{}</div>', preview)
        return '-'
    
    @admin.display(description=_('Pièce jointe'))
    def piece_jointe_link(self, obj):
        if obj.piece_jointe:
            return format_html(
                '<a href="{}" target="_blank" style="color: #17a2b8;">📎 Télécharger</a>',
                obj.piece_jointe.url
            )
        return _('Aucune')
    
    @admin.display(description=_('Lu'), boolean=True)
    def est_lu_badge(self, obj):
        return obj.est_lu


# ============================================
# ADMIN POUR GROUPE
# ============================================

@admin.register(Groupe)
class GroupeAdmin(admin.ModelAdmin):
    """
    Administration pour le modèle Groupe
    """
    list_display = (
        'nom', 'slug', 'type_acces_badge', 'createur_link', 'nombre_membres',
        'image_preview', 'created_at', 'deleted_badge', 'status_badge'
    )
    list_filter = (
        'type_acces', 'deleted', 'created_at'
    )
    search_fields = ('nom', 'description', 'createur__nom_complet', 'slug', 'status')
    ordering = ('-created_at',)
    list_per_page = 25
    list_display_links = ('nom',)
    
    inlines = [MembreGroupeInline, MessageGroupeInline]
    
    actions = ['soft_delete_groupes', 'restore_groupes']
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('nom', 'slug', 'description', 'type_acces', 'status')
        }),
        (_('Créateur'), {
            'fields': ('createur_link_display',)
        }),
        (_('Visuel'), {
            'fields': ('image_preview', 'image')
        }),
        (_('Métadonnées'), {
            'fields': ('id', 'created_at', 'updated_at', 'deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'deleted_at',
        'createur_link_display', 'image_preview'
    )
    
    # ======================================
    # Méthodes d'affichage personnalisées
    # ======================================
    
    @admin.display(description=_('Type d\'accès'))
    def type_acces_badge(self, obj):
        colors = {
            'public': '#28a745',
            'prive': '#ffc107',
        }
        color = colors.get(obj.type_acces, '#6c757d')
        icon = '🌍' if obj.type_acces == 'public' else '🔒'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 12px; '
            'border-radius: 4px; font-size: 12px; font-weight: 500; display: inline-flex; '
            'align-items: center; gap: 6px;">{} {}</span>',
            color, icon, obj.get_type_acces_display()
        )
    
    @admin.display(description=_('Créateur'))
    def createur_link(self, obj):
        if obj.createur:
            url = f'/admin/users/profil/{obj.createur.id}/change/'
            display_text = escape(obj.createur.nom_complet)
            return format_html('<a href="{}" target="_blank">{}</a>', url, display_text)
        return '-'
    
    @admin.display(description=_('Créateur'))
    def createur_link_display(self, obj):
        """Version pour fieldsets (lecture seule)"""
        if obj.createur:
            url = f'/admin/users/profil/{obj.createur.id}/change/'
            display_text = escape(obj.createur.nom_complet)
            return format_html('<a href="{}" target="_blank" style="font-weight: 500;">{}</a>', url, display_text)
        return '-'
    
    @admin.display(description=_("Est actif"))
    def status_badge(self, obj):
        colors = {
            'actif': '#28a745',
            'inactif': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: 500;">{}</span>',
            color, obj.get_status_display()
        )
    
    @admin.display(description=_('Nombre de membres'))
    def nombre_membres(self, obj):
        count = obj.get_nombre_membres()
        color = '#28a745' if count > 0 else '#6c757d'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: 500;">{} membres</span>',
            color, count
        )
    
    @admin.display(description=_('Image'))
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<div style="display: inline-block; border: 2px solid #dee2e6; '
                'border-radius: 4px; overflow: hidden;">'
                '<img src="{}" width="80" height="80" '
                'style="object-fit: cover; display: block;" /></div>',
                obj.image.url
            )
        return format_html(
            '<span style="color: #6c757d; font-style: italic;">Aucune image</span>'
        )
    
    @admin.display(description=_('Supprimé'), boolean=True)
    def deleted_badge(self, obj):
        return obj.deleted
    
    # ======================================
    # Actions personnalisées
    # ======================================
    
    @admin.action(description=_('Supprimer logiquement les groupes sélectionnés'))
    def soft_delete_groupes(self, request, queryset):
        count = 0
        for groupe in queryset.filter(deleted=False):
            groupe.soft_delete()
            count += 1
        self.message_user(
            request,
            _(f'{count} groupe(s) supprimé(s) logiquement.'),
            level='SUCCESS'
        )
    
    @admin.action(description=_('Restaurer les groupes supprimés'))
    def restore_groupes(self, request, queryset):
        count = 0
        for groupe in queryset.filter(deleted=True):
            groupe.restore()
            count += 1
        self.message_user(
            request,
            _(f'{count} groupe(s) restauré(s).'),
            level='SUCCESS'
        )
    
    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return Groupe.all_objects.select_related('createur').all()


# ============================================
# ADMIN POUR MEMBRE GROUPE
# ============================================

@admin.register(MembreGroupe)
class MembreGroupeAdmin(admin.ModelAdmin):
    """
    Administration pour le modèle MembreGroupe
    """
    list_display = (
        'profil_link', 'groupe_link', 'role_badge', 'est_admin_badge',
        'date_membre', 'created_at'
    )
    list_filter = ('role', 'created_at', 'deleted')
    search_fields = (
        'profil__nom_complet', 'groupe__nom','groupe__slug'
    )
    ordering = ('-created_at',)
    list_per_page = 50
    list_display_links = None  # Désactive les liens pour éviter la confusion
    
    actions = ['promouvoir_admins', 'retrograder_membres', 'soft_delete_membres', 'restore_membres']
    
    fieldsets = (
        (_('Informations principales'), {
            'fields': ('profil_link_display', 'groupe_link_display', 'role')
        }),
        (_('Dates'), {
            'fields': ('date_membre', 'created_at', 'updated_at')
        }),
        (_('Métadonnées'), {
            'fields': ('deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = (
        'date_membre', 'created_at', 'updated_at', 'deleted_at',
        'profil_link_display', 'groupe_link_display'
    )
    
    # ======================================
    # Méthodes d'affichage personnalisées
    # ======================================
    
    @admin.display(description=_('Profil'))
    def profil_link(self, obj):
        if obj.profil:
            url = f'/admin/users/profil/{obj.profil.id}/change/'
            display_text = escape(obj.profil.nom_complet)
            return format_html('<a href="{}" target="_blank">{}</a>', url, display_text)
        return '-'
    
    @admin.display(description=_('Profil'))
    def profil_link_display(self, obj):
        """Version pour fieldsets"""
        if obj.profil:
            url = f'/admin/users/profil/{obj.profil.id}/change/'
            display_text = escape(obj.profil.nom_complet)
            return format_html('<a href="{}" target="_blank" style="font-weight: 500;">{}</a>', url, display_text)
        return '-'
    
    @admin.display(description=_('Groupe'))
    def groupe_link(self, obj):
        if obj.groupe:
            url = f'/admin/network/groupe/{obj.groupe.id}/change/'
            display_text = escape(obj.groupe.nom)
            return format_html('<a href="{}" target="_blank">{}</a>', url, display_text)
        return '-'
    
    @admin.display(description=_('Groupe'))
    def groupe_link_display(self, obj):
        """Version pour fieldsets"""
        if obj.groupe:
            url = f'/admin/network/groupe/{obj.groupe.id}/change/'
            display_text = escape(obj.groupe.nom)
            return format_html('<a href="{}" target="_blank" style="font-weight: 500;">{}</a>', url, display_text)
        return '-'
    
    @admin.display(description=_('Rôle'))
    def role_badge(self, obj):
        colors = {
            'admin': '#dc3545',
            'membre': '#6c757d',
        }
        color = colors.get(obj.role, '#6c757d')
        icon = '👑' if obj.role == 'admin' else '👤'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 12px; '
            'border-radius: 4px; font-size: 12px; font-weight: 500; display: inline-flex; '
            'align-items: center; gap: 6px;">{} {}</span>',
            color, icon, obj.get_role_display()
        )
    
    @admin.display(description=_('Est admin'), boolean=True)
    def est_admin_badge(self, obj):
        return obj.est_admin
    
    @admin.display(description=_('Supprimé'), boolean=True)
    def deleted_badge(self, obj):
        return obj.deleted
    
    # ======================================
    # Actions personnalisées
    # ======================================
    
    @admin.action(description=_('Promouvoir en administrateur'))
    def promouvoir_admins(self, request, queryset):
        updated = queryset.update(role='admin')
        self.message_user(
            request,
            _(f'{updated} membre(s) promu(s) en administrateur(s).'),
            level='SUCCESS'
        )
    
    @admin.action(description=_('Rétrograder en membre'))
    def retrograder_membres(self, request, queryset):
        updated = queryset.update(role='membre')
        self.message_user(
            request,
            _(f'{updated} administrateur(s) rétrogradé(s) en membre(s).'),
            level='SUCCESS'
        )
    
    @admin.action(description=_('Supprimer logiquement les membres'))
    def soft_delete_membres(self, request, queryset):
        count = 0
        for membre in queryset.filter(deleted=False):
            membre.soft_delete()
            count += 1
        self.message_user(
            request,
            _(f'{count} membre(s) supprimé(s) logiquement.'),
            level='SUCCESS'
        )
    
    @admin.action(description=_('Restaurer les membres supprimés'))
    def restore_membres(self, request, queryset):
        count = 0
        for membre in queryset.filter(deleted=True):
            membre.restore()
            count += 1
        self.message_user(
            request,
            _(f'{count} membre(s) restauré(s).'),
            level='SUCCESS'
        )
    
    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return MembreGroupe.all_objects.select_related('profil', 'groupe').all()


# ============================================
# ADMIN POUR MESSAGE GROUPE
# ============================================
@admin.register(MessageGroupe)
class MessageGroupeAdmin(admin.ModelAdmin):
    """
    Administration pour le modèle MessageGroupe avec support des réponses
    """
    list_display = (
        'message_hierarchy', 'groupe_link', 'expediteur_link', 'contenu_preview',
        'reponse_a_badge', 'piece_jointe_badge', 'est_lu_badge', 'created_at'
    )
    list_filter = ('est_lu', 'created_at', 'deleted', 'groupe')
    search_fields = (
        'contenu', 'expediteur__nom_complet',
        'groupe__nom', 'expediteur__email', 'reponse_a__contenu'
    )
    ordering = ('-created_at',)
    list_per_page = 50
    
    # Pour permettre la sélection dans l'admin avec autocomplete
    autocomplete_fields = ['groupe', 'expediteur', 'reponse_a']
    
    actions = ['marquer_comme_lus', 'marquer_comme_non_lus', 'soft_delete_messages', 'restore_messages']
    
    fieldsets = (
        (_('Message'), {
            'fields': ('groupe_link_display', 'expediteur_link_display', 'contenu')
        }),
        (_('Réponse'), {
            'fields': ('reponse_a_link_display', 'reponse_a_preview'),
            'classes': ('collapse',)
        }),
        (_('Pièce jointe'), {
            'fields': ('piece_jointe_preview',)
        }),
        (_('Statut'), {
            'fields': ('est_lu',)
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at')
        }),
        (_('Métadonnées'), {
            'fields': ('deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = (
        'created_at', 'updated_at', 'deleted_at',
        'groupe_link_display', 'expediteur_link_display',
        'reponse_a_link_display', 'reponse_a_preview',
        'piece_jointe_preview'
    )
    
    # ======================================
    # Méthodes d'affichage personnalisées
    # ======================================
    
    @admin.display(description=_('Message'), ordering='contenu')
    def message_hierarchy(self, obj):
        """Affiche le message avec indentation visuelle pour les réponses"""
        if obj.reponse_a:
            # Indentation visuelle avec flèche
            return format_html(
                '<div style="padding-left: 20px; border-left: 3px solid #e9ecef; margin-left: 15px;">'
                '<span style="color: #6c757d; font-size: 0.9em;">↪️ Réponse à [{}]</span><br/>'
                '<strong>{}</strong>: {}</div>',
                escape(obj.reponse_a.expediteur.nom_complet if obj.reponse_a.expediteur else '?'),
                escape(obj.expediteur.nom_complet),
                escape(obj.contenu[:60] + '...' if len(obj.contenu) > 60 else obj.contenu)
            )
        return format_html(
            '<strong>{}</strong>: {}',
            escape(obj.expediteur.nom_complet),
            escape(obj.contenu[:80] + '...' if len(obj.contenu) > 80 else obj.contenu)
        )
    
    @admin.display(description=_('Groupe'))
    def groupe_link(self, obj):
        if obj.groupe:
            url = f'/admin/network/groupe/{obj.groupe.id}/change/'
            display_text = escape(obj.groupe.nom)
            return format_html('<a href="{}" target="_blank">{}</a>', url, display_text)
        return '-'
    
    @admin.display(description=_('Groupe'))
    def groupe_link_display(self, obj):
        if obj.groupe:
            url = f'/admin/network/groupe/{obj.groupe.id}/change/'
            display_text = escape(obj.groupe.nom)
            return format_html('<a href="{}" target="_blank" style="font-weight: 500;">{}</a>', url, display_text)
        return '-'
    
    @admin.display(description=_('Expéditeur'))
    def expediteur_link(self, obj):
        if obj.expediteur:
            url = f'/admin/users/profil/{obj.expediteur.id}/change/'
            display_text = escape(obj.expediteur.nom_complet)
            return format_html('<a href="{}" target="_blank">{}</a>', url, display_text)
        return '-'
    
    @admin.display(description=_('Expéditeur'))
    def expediteur_link_display(self, obj):
        if obj.expediteur:
            url = f'/admin/users/profil/{obj.expediteur.id}/change/'
            display_text = escape(obj.expediteur.nom_complet)
            return format_html('<a href="{}" target="_blank" style="font-weight: 500;">{}</a>', url, display_text)
        return '-'
    
    @admin.display(description=_('Réponse à'))
    def reponse_a_link_display(self, obj):
        if obj.reponse_a:
            url = f'/admin/network/messagegroupe/{obj.reponse_a.id}/change/'
            display_text = f"{obj.reponse_a.expediteur.nom_complet}: {obj.reponse_a.contenu[:50]}"
            return format_html(
                '<a href="{}" target="_blank" style="font-weight: 500; color: #17a2b8;">↪️ {}</a>',
                url, escape(display_text)
            )
        return format_html('<span style="color: #6c757d; font-style: italic;">Message original</span>')
    
    @admin.display(description=_('Aperçu de la réponse'))
    def reponse_a_preview(self, obj):
        """Affiche un aperçu enrichi du message parent"""
        if obj.reponse_a:
            msg = obj.reponse_a
            contenu = escape(msg.contenu[:120] + '...' if len(msg.contenu) > 120 else msg.contenu)
            expediteur = escape(msg.expediteur.nom_complet if msg.expediteur else '?')
            
            return format_html(
                '<div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px; '
                'border-left: 4px solid #17a2b8; margin: 8px 0;">'
                '<div style="font-weight: 500; color: #495057; margin-bottom: 6px;">'
                '↪️ {} • <span style="color: #6c757d; font-size: 0.85em;">{}</span>'
                '</div>'
                '<div style="color: #212529;">{}</div>'
                '</div>',
                expediteur,
                msg.created_at.strftime('%d/%m/%Y %H:%M'),
                contenu
            )
        return format_html('<span style="color: #6c757d;">Aucune réponse parente</span>')
    
    @admin.display(description=_('Réponse'), boolean=False)
    def reponse_a_badge(self, obj):
        if obj.reponse_a:
            return format_html(
                '<span style="background-color: #17a2b8; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-size: 11px;">↪️ Réponse</span>'
            )
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">💬 Original</span>'
        )
    
    @admin.display(description=_('Contenu'))
    def contenu_preview(self, obj):
        if obj.contenu:
            preview = escape(obj.contenu[:80])
            if len(obj.contenu) > 80:
                preview += '...'
            return format_html('<div style="max-width: 300px; white-space: pre-wrap;">{}</div>', preview)
        return '-'
    
    @admin.display(description=_('Pièce jointe'))
    def piece_jointe_badge(self, obj):
        if obj.piece_jointe:
            return format_html(
                '<span style="background-color: #17a2b8; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-size: 11px;">📎 Fichier</span>'
            )
        return format_html(
            '<span style="color: #6c757d; font-style: italic;">Aucune</span>'
        )
    
    @admin.display(description=_('Pièce jointe'))
    def piece_jointe_preview(self, obj):
        if obj.piece_jointe:
            file_url = obj.piece_jointe.url
            file_name = obj.piece_jointe.name.split('/')[-1]
            
            if obj.piece_jointe.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                preview_html = format_html(
                    '<div style="margin-bottom: 10px;">'
                    '<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 4px;" />'
                    '</div>',
                    file_url
                )
            else:
                preview_html = format_html(
                    '<div style="margin-bottom: 10px; padding: 10px; background-color: #f8f9fa; '
                    'border-radius: 4px; border-left: 4px solid #17a2b8;">'
                    '<strong>📎 {}</strong><br/>'
                    '<small style="color: #6c757d;">{} octets</small>'
                    '</div>',
                    file_name, obj.piece_jointe.size
                )
            
            return format_html(
                '{}'
                '<a href="{}" target="_blank" style="display: inline-block; padding: 6px 12px; '
                'background-color: #17a2b8; color: white; text-decoration: none; border-radius: 4px; '
                'font-weight: 500;">⬇️ Télécharger</a>',
                preview_html, file_url
            )
        return format_html(
            '<span style="color: #6c757d; font-style: italic;">Aucune pièce jointe</span>'
        )
    
    @admin.display(description=_('Lu'), boolean=True)
    def est_lu_badge(self, obj):
        if obj.est_lu:
            return format_html(
                '<span style="color: #28a745; font-weight: 500;">✅ Oui</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-weight: 500;">❌ Non</span>'
        )
    
    @admin.display(description=_('Supprimé'), boolean=True)
    def deleted_badge(self, obj):
        return obj.deleted
    
    # ======================================
    # Actions personnalisées (inchangées)
    # ======================================
    
    @admin.action(description=_('Marquer comme lus'))
    def marquer_comme_lus(self, request, queryset):
        updated = queryset.update(est_lu=True)
        self.message_user(
            request,
            _(f'{updated} message(s) marqué(s) comme lus.'),
            level='SUCCESS'
        )
    
    @admin.action(description=_('Marquer comme non lus'))
    def marquer_comme_non_lus(self, request, queryset):
        updated = queryset.update(est_lu=False)
        self.message_user(
            request,
            _(f'{updated} message(s) marqué(s) comme non lus.'),
            level='SUCCESS'
        )
    
    @admin.action(description=_('Supprimer logiquement les messages'))
    def soft_delete_messages(self, request, queryset):
        count = 0
        for message in queryset.filter(deleted=False):
            message.soft_delete()
            count += 1
        self.message_user(
            request,
            _(f'{count} message(s) supprimé(s) logiquement.'),
            level='SUCCESS'
        )
    
    @admin.action(description=_('Restaurer les messages supprimés'))
    def restore_messages(self, request, queryset):
        count = 0
        for message in queryset.filter(deleted=True):
            message.restore()
            count += 1
        self.message_user(
            request,
            _(f'{count} message(s) restauré(s).'),
            level='SUCCESS'
        )
    
    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return MessageGroupe.all_objects.select_related(
            'groupe', 'expediteur', 'reponse_a', 'reponse_a__expediteur'
        ).all()
    