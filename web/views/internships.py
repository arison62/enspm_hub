from django.http import Http404
from inertia import defer, render as render_inertia
from django.views import View

from opportunities.api.schemas import StageOut
from opportunities.services.stage_service import stage_service

class InternshipsView(View):
    
    def get(self, request, slug=None):
        
        def get_stage_by_slug(slug):
            stage = stage_service.get_stage_by_slug(slug)
            if not stage:
                raise Http404("Stage non trouve")
            stage_data = StageOut.from_orm(stage).model_dump()
            return stage_data
        if slug:
            return render_inertia(request, "home/opportunities/OpportunityDetails", {
                "opportunity": defer(lambda: get_stage_by_slug(slug))
            })
        else:
            return render_inertia(request, "home/opportunities/Internships", None, {
                "seo_title" : "ENSPM Hub - Stages",
                "seo_description" : "ENSPM Hub - Plateforme de mise en relation des alumni, étudiants et partenaires de l'École Nationale Supérieure Polytechnique de Maroua."
            })
    
