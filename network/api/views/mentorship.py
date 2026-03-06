from typing import List
from uuid import UUID
from ninja import Router, Query
from core.services.auth_service import jwt_auth
from core.utils.pagination import build_pagination_response
from network.services.mentorship import MentoringService
from network.api.schemas.mentorship import (
    MentorProfileListResponse, MentorProfileOut, MentorProfileCreate, MentorProfileUpdate, MentorFilter,
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

@mentorship_router.get("/mentors/", response={200: MentorProfileListResponse}, auth=jwt_auth)
def search_mentors(request, filters: Query[MentorFilter], page: int = 1, page_size: int = 20):
    mentors, total = MentoringService.obtenir_mentors(
        acting_user=request.user,
        page=page,
        page_size=page_size,
        **filters.dict(exclude_none=True)
    )
    return 200, build_pagination_response(mentors, total, page, page_size)


@mentorship_router.post("/mentors/{mentor_profile_id}/valider/", response=MentorProfileOut, auth=jwt_auth)
def validate_mentor_profile(request, mentor_profile_id: UUID, payload: MentorProfileValidationCreate):
    return MentoringService.valider_profil_mentor(
        acting_user=request.user,
        mentor_profile_id=mentor_profile_id,
        **payload.dict()
    )
