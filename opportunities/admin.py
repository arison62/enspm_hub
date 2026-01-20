# opportunities/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Stage, Emploi, Formation

# ==========================================
# ADMIN POUR STAGES
# ==========================================

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_stage', 'nom_structure', 'adresse', 'statut', 'est_valide', 'date_publication')
    search_fields = ('titre', 'nom_structure', 'adresse', 'ville', 'description')
    list_filter = ('type_stage', 'statut', 'est_valide', 'pays')
    ordering = ('-date_publication',)
    readonly_fields = ('created_at', 'updated_at', 'date_publication', 'date_validation')
    fieldsets = (
        (_('Informations Générales'), {'fields': ('titre', 'slug', 'nom_structure', 'description', 'type_stage')}),
        (_('Relations'), {'fields': ('createur_profil', 'organisation')}),
        (_('Secteur'), {'fields': ('secteurs', 'domaines', 'filieres')}),
        (_('Localisation'), {'fields': ('adresse', 'ville', 'pays')}),
        (_('Contacts'), {'fields': ('email_contact', 'telephone_contact')}),
        (_('Liens'), {'fields': ('lien_offre_original', 'lien_candidature')}),
        (_('Dates'), {'fields': ('date_debut', 'date_fin')}),
        (_('Statut'), {'fields': ('statut', 'est_valide', 'validateur_profil', 'commentaire_validation')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at', 'date_publication', 'date_validation'), 'classes': ('collapse',)}),
    )
    raw_id_fields = ('createur_profil', 'organisation', 'validateur_profil')
    prepopulated_fields = {'slug': ('titre',)}

# ==========================================
# ADMIN POUR EMPLOIS
# ==========================================

@admin.register(Emploi)
class EmploiAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_emploi', 'nom_structure', 'adresse', 'statut', 'est_valide', 'date_publication')
    search_fields = ('titre', 'nom_structure', 'adresse', 'ville', 'description')
    list_filter = ('type_emploi', 'statut', 'est_valide', 'pays')
    ordering = ('-date_publication',)
    readonly_fields = ('created_at', 'updated_at', 'date_publication', 'date_validation')
    fieldsets = (
        (_('Informations Générales'), {'fields': ('titre', 'slug', 'nom_structure', 'description', 'type_emploi')}),
        (_('Relations'), {'fields': ('createur_profil', 'organisation')}),
        (_('Localisation'), {'fields': ('adresse', 'ville', 'pays')}),
        (_('Contacts'), {'fields': ('email_contact', 'telephone_contact')}),
        (_('Liens'), {'fields': ('lien_offre_original', 'lien_candidature')}),
        (_('Salaire'), {'fields': ('salaire_min', 'salaire_max', 'devise')}),
        (_('Dates'), {'fields': ('date_publication', 'date_expiration')}),
        (_('Statut'), {'fields': ('statut', 'est_valide', 'validateur_profil', 'commentaire_validation')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at', 'date_validation'), 'classes': ('collapse',)}),
    )
    raw_id_fields = ('createur_profil', 'organisation', 'validateur_profil', 'devise')
    prepopulated_fields = {'slug': ('titre',)}

# ==========================================
# ADMIN POUR FORMATIONS
# ==========================================

@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_formation', 'nom_structure', 'adresse', 'est_payante', 'statut', 'est_valide', 'date_publication')
    search_fields = ('titre', 'nom_structure', 'adresse', 'ville', 'description')
    list_filter = ('type_formation', 'est_payante', 'statut', 'est_valide', 'pays')
    ordering = ('-date_publication',)
    readonly_fields = ('created_at', 'updated_at', 'date_publication', 'date_validation')
    fieldsets = (
        (_('Informations Générales'), {'fields': ('titre', 'slug', 'nom_structure', 'description', 'type_formation')}),
        (_('Relations'), {'fields': ('createur_profil', 'organisation')}),
        (_('Localisation'), {'fields': ('adresse', 'ville', 'pays')}),
        (_('Contacts'), {'fields': ('email_contact', 'telephone_contact')}),
        (_('Liens'), {'fields': ('lien_formation', 'lien_inscription')}),
        (_('Prix et Durée'), {'fields': ('est_payante', 'prix', 'devise', 'duree_heures')}),
        (_('Dates'), {'fields': ('date_debut', 'date_fin')}),
        (_('Statut'), {'fields': ('statut', 'est_valide', 'validateur_profil', 'commentaire_validation')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at', 'date_publication', 'date_validation'), 'classes': ('collapse',)}),
    )
    raw_id_fields = ('createur_profil', 'organisation', 'validateur_profil', 'devise')
    prepopulated_fields = {'slug': ('titre',)}