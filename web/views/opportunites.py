from django.http import Http404
from inertia import defer, render as render_inertia
from django.views import View

from opportunities.api.schemas import (FormationOut, EmploiOut, StageOut)
from opportunities.services.formation_service import formation_service
from opportunities.services.emploi_service import emploi_service
from opportunities.services.formation_service import formation_service
from opportunities.services.stage_service import stage_service

class OpportunitiesView(View):
    def get(self, request):
        return render_inertia(request, "home/opportunities/Opportunities", None, {
            "seo_title" : "ENSPM Hub - Opportunités",
            "seo_description": "ENSPM Hub - Reseau d'opportnuites de formation et emploi."
        })

class JobView(View):
    
    def get(self, request, slug):
        def get_opportunity_by_slug(slug):
            opportunity = emploi_service.get_emploi_by_slug(slug)
            if not opportunity:
                raise Http404("Opportunity non trouve")
            opportunity_data = EmploiOut.from_orm(opportunity).model_dump()
            return opportunity_data
        
        return render_inertia(request, "home/opportunities/OpportunityDetails", {
            "opportunity": defer(lambda: get_opportunity_by_slug(slug))
        })

class TrainingView(View):
    
    def get(self, request, slug):
        def get_formation_by_slug(slug):
            formation = formation_service.get_formation_by_slug(slug)
            if not formation:
                raise Http404("Formation non trouve")
            formation_data = FormationOut.from_orm(formation).model_dump()
            return formation_data
        
        return render_inertia(request, "home/opportunities/OpportunityDetails", {
            "opportunity": defer(lambda: get_formation_by_slug(slug))
        })
        
class IntershipView(View):
    
    def get(self, request, slug):
        def get_stage_by_slug(slug):
            stage = stage_service.get_stage_by_slug(slug)
            if not stage:
                raise Http404("Stage non trouve")
            stage_data = StageOut.from_orm(stage).model_dump()
            return stage_data
        
        return render_inertia(request, "home/opportunities/OpportunityDetails", {
            "opportunity": defer(lambda: get_stage_by_slug(slug))
        })
    
    
