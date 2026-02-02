from typing import List
from uuid import UUID
from ninja import Router, Query
from django.db import models
from django.shortcuts import get_object_or_404
from core.api.auth import django_auth
from network.services.mentorship import MentoringService
from network.api.schemas.mentorship import (
    MentorProfileOut, MentorProfileCreate, MentorProfileUpdate, MentorFilter,
    DemandeMentoringOut, DemandeMentoringCreate, DemandeMentoringReponse, DemandeMentoringFilter,
    RelationMentoratOut, RelationMentoratUpdate, RelationMentoratFilter,
    SessionMentoratOut, SessionMentoratCreate, SessionMentoratRealisee,
    FeedbackMentoratOut, FeedbackMentoratCreate
)
from network.models.mentorship import MentorProfile, DemandeMentoring, RelationMentorat, SessionMentorat

mentorship_router = Router(tags=["Mentoring"])

# ============================================
# GESTION DES PROFILS MENTOR
# ============================================

@mentorship_router.post("/mentors/", response={201: MentorProfileOut}, auth=django_auth)
def create_mentor_profile(request, payload: MentorProfileCreate):
    mentor_profile = MentoringService.creer_profil_mentor(
        acting_user=request.user,
        **payload.dict()
    )
    return 201, mentor_profile

@mentorship_router.patch("/mentors/{mentor_profile_id}/", response=MentorProfileOut, auth=django_auth)
def update_mentor_profile(request, mentor_profile_id: UUID, payload: MentorProfileUpdate):
    mentor_profile = MentoringService.modifier_profil_mentor(
        acting_user=request.user,
        mentor_profile_id=mentor_profile_id,
        **payload.dict(exclude_unset=True)
    )
    return mentor_profile

@mentorship_router.get("/mentors/", response=List[MentorProfileOut], auth=django_auth)
def search_mentors(request, filters: Query[MentorFilter]):
    return MentoringService.rechercher_mentors(
        acting_user=request.user,
        **filters.dict(exclude_none=True)
    )

@mentorship_router.get("/mentors/{mentor_profile_id}/stats/", auth=django_auth)
def get_mentor_stats(request, mentor_profile_id: UUID):
    return MentoringService.obtenir_statistiques_mentor(
        acting_user=request.user,
        mentor_profile_id=mentor_profile_id
    )

# ============================================
# GESTION DES DEMANDES DE MENTORING
# ============================================

@mentorship_router.post("/demandes/", response={201: DemandeMentoringOut}, auth=django_auth)
def create_mentoring_request(request, payload: DemandeMentoringCreate):
    demande = MentoringService.creer_demande_mentoring(
        acting_user=request.user,
        **payload.dict()
    )
    return 201, demande

@mentorship_router.post("/demandes/{demande_id}/repondre/", response=DemandeMentoringOut, auth=django_auth)
def respond_mentoring_request(request, demande_id: UUID, payload: DemandeMentoringReponse):
    return MentoringService.repondre_demande_mentoring(
        acting_user=request.user,
        demande_id=demande_id,
        **payload.dict()
    )

@mentorship_router.post("/demandes/{demande_id}/annuler/", response=DemandeMentoringOut, auth=django_auth)
def cancel_mentoring_request(request, demande_id: UUID):
    return MentoringService.annuler_demande_mentoring(
        acting_user=request.user,
        demande_id=demande_id
    )

@mentorship_router.get("/demandes/envoyees/", response=List[DemandeMentoringOut], auth=django_auth)
def list_sent_requests(request, filters: Query[DemandeMentoringFilter]):
    return MentoringService.obtenir_demandes_envoyees(
        acting_user=request.user,
        **filters.dict(exclude_none=True)
    )

@mentorship_router.get("/demandes/recues/", response=List[DemandeMentoringOut], auth=django_auth)
def list_received_requests(request, filters: Query[DemandeMentoringFilter]):
    return MentoringService.obtenir_demandes_recues(
        acting_user=request.user,
        **filters.dict(exclude_none=True)
    )

# ============================================
# GESTION DES RELATIONS DE MENTORAT
# ============================================

@mentorship_router.get("/relations/", response=List[RelationMentoratOut], auth=django_auth)
def list_relations(request, filters: Query[RelationMentoratFilter]):
    return MentoringService.obtenir_relations_mentorat(
        acting_user=request.user,
        **filters.dict(exclude_none=True)
    )

@mentorship_router.patch("/relations/{relation_id}/", response=RelationMentoratOut, auth=django_auth)
def update_relation(request, relation_id: UUID, payload: RelationMentoratUpdate):
    return MentoringService.modifier_relation_mentorat(
        acting_user=request.user,
        relation_id=relation_id,
        **payload.dict(exclude_unset=True)
    )

@mentorship_router.post("/relations/{relation_id}/terminer/", response=RelationMentoratOut, auth=django_auth)
def terminate_relation(request, relation_id: UUID, raison: str = ""):
    return MentoringService.terminer_relation_mentorat(
        acting_user=request.user,
        relation_id=relation_id,
        raison=raison
    )

# ============================================
# GESTION DES SESSIONS
# ============================================

@mentorship_router.post("/sessions/", response={201: SessionMentoratOut}, auth=django_auth)
def create_session(request, payload: SessionMentoratCreate):
    session = MentoringService.creer_session_mentorat(
        acting_user=request.user,
        **payload.dict()
    )
    return 201, session

@mentorship_router.post("/sessions/{session_id}/realisee/", response=SessionMentoratOut, auth=django_auth)
def mark_session_realized(request, session_id: UUID, payload: SessionMentoratRealisee):
    return MentoringService.marquer_session_realisee(
        acting_user=request.user,
        session_id=session_id,
        **payload.dict()
    )

# ============================================
# GESTION DES FEEDBACKS
# ============================================

@mentorship_router.post("/feedbacks/", response={201: FeedbackMentoratOut}, auth=django_auth)
def create_feedback(request, payload: FeedbackMentoratCreate):
    feedback = MentoringService.creer_feedback_mentorat(
        acting_user=request.user,
        **payload.dict()
    )
    return 201, feedback
