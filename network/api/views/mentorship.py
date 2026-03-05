from typing import List
from uuid import UUID
from ninja import Router, Query
from core.services.auth_service import jwt_auth
from network.services.mentorship import MentoringService
from network.api.schemas.mentorship import (
    MentorProfileOut, MentorProfileCreate, MentorProfileUpdate, MentorFilter,
    MentorProfileValidationCreate
)

mentorship_router = Router(tags=["Mentoring"])

# ============================================
# GESTION DES PROFILS MENTOR
# ============================================

@mentorship_router.post("/mentors/", response={201: MentorProfileOut}, auth=jwt_auth)
def create_mentor_profile(request, payload: MentorProfileCreate):
    mentor_profile = MentoringService.creer_profil_mentor(
        acting_user=request.user,
        **payload.dict()
    )
    return 201, mentor_profile

@mentorship_router.patch("/mentors/{mentor_profile_id}/", response=MentorProfileOut, auth=jwt_auth)
def update_mentor_profile(request, mentor_profile_id: UUID, payload: MentorProfileUpdate):
    mentor_profile = MentoringService.modifier_profil_mentor(
        acting_user=request.user,
        mentor_profile_id=mentor_profile_id,
        **payload.dict(exclude_unset=True)
    )
    return mentor_profile

@mentorship_router.get("/mentors/", response=List[MentorProfileOut], auth=jwt_auth)
def search_mentors(request, filters: Query[MentorFilter]):
    return MentoringService.rechercher_mentors(
        acting_user=request.user,
        **filters.dict(exclude_none=True)
    )

@mentorship_router.get("/mentors/{mentor_profile_id}/stats/", auth=jwt_auth)
def get_mentor_stats(request, mentor_profile_id: UUID):
    return MentoringService.obtenir_statistiques_mentor(
        acting_user=request.user,
        mentor_profile_id=mentor_profile_id
    )

@mentorship_router.post("/mentors/{mentor_profile_id}/valider/", response=MentorProfileOut, auth=jwt_auth)
def validate_mentor_profile(request, mentor_profile_id: UUID, payload: MentorProfileValidationCreate):
    return MentoringService.valider_profil_mentor(
        acting_user=request.user,
        mentor_profile_id=mentor_profile_id,
        **payload.dict()
    )
