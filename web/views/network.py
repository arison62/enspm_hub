# from django.http import Http404
# from inertia import defer, render as render_inertia
# from organizations.services.organisation_service import organisation_service
# from django.views import View
# from organizations.api.schemas import OrganisationCompleteOut

# class NetworkView(View):
#     def get(self, request, slug = None):
        
#         def get_organisation_by_slug(slug):
#             org = organisation_service.get_organisation_by_slug(
#                 slug=slug,
#                 acting_user=request.user
#             )
            
#             if not org:
#                 raise Http404("Organisation non trouve")
#             org_data = OrganisationCompleteOut.from_orm(org).model_dump()
#             return org_data
        
#         if slug:
#             return render_inertia(request, "home/network/NetworkProfile", {
#                 "organisation": defer(lambda: get_organisation_by_slug(slug))
#             })
#         return render_inertia(request, "home/network/Network", None, {
#             "seo_title" : "ENSPM Hub - Réseau des Alumni, Étudiants et Partenaires",
#             "seo_description" : "ENSPM Hub - Plateforme de mise en relation des alumni, étudiants et partenaires de l'École Nationale Supérieure Polytechnique de Maroua."
#         })


