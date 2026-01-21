# feeds/models.py

from django.db import models
from core.models import ENSPMHubBaseModel
from django.utils.translation import gettext_lazy as _


# ==========================================
# 6. FLUX D'ACTUALITÉ
# ==========================================
class Post(ENSPMHubBaseModel):
    contenu = models.TextField()
    image = models.ImageField(upload_to='posts_images/', null=True, blank=True)
    auteur_profil = models.ForeignKey('users.Profil', null=True, blank=True, on_delete=models.SET_NULL,
                                      related_name='posts')
    auteur_organisation = models.ForeignKey('organizations.Organisation', null=True, blank=True, on_delete=models.SET_NULL,
                                            related_name='posts')
    nombre_likes = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("Post")
        db_table = 'post'

    def __str__(self):
        return f"Post par {self.auteur_profil or self.auteur_organisation}"


class Commentaire(ENSPMHubBaseModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='commentaires')
    contenu = models.TextField()
    auteur_profil = models.ForeignKey('users.Profil', null=True, blank=True, on_delete=models.SET_NULL)
    auteur_organisation = models.ForeignKey('organizations.Organisation', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = _("Commentaire")
        db_table = 'commentaire'


class Evenement(ENSPMHubBaseModel):
    titre = models.CharField(max_length=255)
    description = models.TextField()
    lieu = models.CharField(max_length=255, null=True, blank=True)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField(null=True, blank=True)
    lien_inscription = models.URLField(null=True, blank=True)
    organisateur_profil = models.ForeignKey('users.Profil', null=True, blank=True, on_delete=models.SET_NULL,
                                            related_name='evenements_organises')
    organisateur_organisation = models.ForeignKey('organizations.Organisation', null=True, blank=True, on_delete=models.SET_NULL,
                                                  related_name='evenements_organises')

    class Meta:
        verbose_name = _("Événement")
        db_table = 'evenement'