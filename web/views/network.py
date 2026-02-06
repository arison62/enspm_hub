from django.http import Http404
from inertia import defer, render as render_inertia
from django.views import View
from network.services.chat import ChatService
from network.api.schemas.chat import GroupeOut


class NetworkView(View):
    def get(self, request, slug = None):
        
        return render_inertia(request, "home/network/Network", None, {
            "seo_title" : "ENSPM Hub - Réseau des Alumni, Étudiants et Partenaires",
            "seo_description" : "ENSPM Hub - Plateforme de mise en relation des alumni, étudiants et partenaires de l'École Nationale Supérieure Polytechnique de Maroua."
        })
        

class NetworkGroupView(View):
    def get_group_by_slug(self, slug, user):
        try:
            group = ChatService.obtenir_details_groupe(user, slug=slug)
            return GroupeOut.from_orm(group).model_dump()
        except:
            raise Http404
    def get(self, request, slug=None):
        return render_inertia(request, "home/network/NetworkGroup", {"groupe": defer(lambda: self.get_group_by_slug(slug, request.user))}, {
            "seo_title" : "ENSPM Hub - Réseau des Alumni, Étudiants et Partenaires",
            "seo_description" : "ENSPM Hub - Plateforme de mise en relation des alumni, étudiants et partenaires de l'École Nationale Supérieure Polytechnique de Maroua."
        })


