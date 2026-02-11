from django.contrib import admin
from django.utils.html import format_html, escape
from django.utils.translation import gettext_lazy as _
from network.models import (
    Groupe, MembreGroupe, Conversation, ConversationParticipant, Message, MessageMeta, DemandeAccesGroupe
)

# ============================================
# INLINES
# ============================================

class MembreGroupeInline(admin.TabularInline):
    model = MembreGroupe
    extra = 1
    fields = ('profil_link', 'role', 'date_membre', 'messages_non_lus')
    readonly_fields = ('profil_link', 'date_membre')
    
    @admin.display(description=_('Profil'))
    def profil_link(self, obj):
        if obj.profil:
            return obj.profil.nom_complet
        return '-'

class MessageInline(admin.StackedInline):
    model = Message
    extra = 0
    fields = ('expediteur', 'contenu', 'type', 'media_preview', 'created_at')
    readonly_fields = ('expediteur', 'created_at', 'media_preview')
    can_delete = False
    max_num = 10

    @admin.display(description=_('Aperçu Média'))
    def media_preview(self, obj):
        if obj.media:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.media.url, obj.media_name or 'Voir média')
        return '-'

class ConversationParticipantInline(admin.TabularInline):
    model = ConversationParticipant
    extra = 0
    fields = ('profil', 'role', 'messages_non_lus', 'last_read_at', 'joined_at')
    readonly_fields = ('joined_at',)

# ============================================
# ADMINS
# ============================================

@admin.register(Groupe)
class GroupeAdmin(admin.ModelAdmin):
    list_display = ('nom', 'slug', 'type_acces', 'status', 'created_at', 'is_active')
    list_filter = ('type_acces', 'status', 'deleted')
    search_fields = ('nom', 'slug', 'description')
    inlines = [MembreGroupeInline]

    def is_active(self, obj):
        return obj.status == Groupe.Status.ACTIF
    is_active.boolean = True

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'groupe_link', 'participants_count', 'created_at', 'updated_at')
    list_filter = ('type', 'deleted')
    search_fields = ('id', 'groupe__nom')
    inlines = [ConversationParticipantInline, MessageInline]

    @admin.display(description=_('Groupe'))
    def groupe_link(self, obj):
        if obj.groupe:
            return obj.groupe.nom
        return '-'

    @admin.display(description=_('Participants'))
    def participants_count(self, obj):
        return obj.participants.count()

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation_id_short', 'expediteur', 'type', 'contenu_preview', 'created_at')
    list_filter = ('type', 'created_at', 'deleted')
    search_fields = ('contenu', 'expediteur__nom_complet', 'conversation__id')
    autocomplete_fields = ['conversation', 'expediteur', 'reponse_a']

    @admin.display(description=_('Conv ID'))
    def conversation_id_short(self, obj):
        return str(obj.conversation.id)[:8]

    @admin.display(description=_('Contenu'))
    def contenu_preview(self, obj):
        if obj.contenu:
            return obj.contenu[:50] + ('...' if len(obj.contenu) > 50 else '')
        return '-'

@admin.register(MessageMeta)
class MessageMetaAdmin(admin.ModelAdmin):
    list_display = ('message', 'profil', 'date_lecture')
    list_filter = ('date_lecture',)
    autocomplete_fields = ['message', 'profil']

@admin.register(DemandeAccesGroupe)
class DemandeAccesGroupeAdmin(admin.ModelAdmin):
    list_display = ('groupe', 'demandeur', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('groupe__nom', 'demandeur__nom_complet')
