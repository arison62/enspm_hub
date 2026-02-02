from typing import List, Dict, Any
from uuid import UUID
from ninja import Router, Query
from core.api.auth import django_auth
from network.services.chat import ChatService
from network.api.schemas.chat import (
    GroupeOut, GroupeCreate, GroupeUpdate, GroupeFilter,
    MembreGroupeOut, MembreGroupeCreate, MembreGroupeUpdate,
    MessageGroupeOut, MessageGroupeCreate,
    MessageDirectOut, MessageDirectCreate
)

chat_router = Router(tags=["Chat"])

# ============================================
# GESTION DES GROUPES
# ============================================

@chat_router.post("/groupes/", response={201: GroupeOut}, auth=django_auth)
def create_group(request, payload: GroupeCreate):
    groupe = ChatService.creer_groupe(
        acting_user=request.user,
        **payload.dict()
    )
    return 201, groupe

@chat_router.patch("/groupes/{groupe_id}/", response=GroupeOut, auth=django_auth)
def update_group(request, groupe_id: UUID, payload: GroupeUpdate):
    groupe = ChatService.modifier_groupe(
        acting_user=request.user,
        groupe_id=groupe_id,
        **payload.dict(exclude_unset=True)
    )
    return groupe

@chat_router.delete("/groupes/{groupe_id}/", response={204: None}, auth=django_auth)
def delete_group(request, groupe_id: UUID):
    ChatService.supprimer_groupe(
        acting_user=request.user,
        groupe_id=groupe_id
    )
    return 204, None

@chat_router.get("/groupes/", response=List[GroupeOut], auth=django_auth)
def search_groups(request, filters: Query[GroupeFilter]):
    return ChatService.rechercher_groupes(
        acting_user=request.user,
        **filters.dict(exclude_none=True)
    )

# ============================================
# GESTION DES MEMBRES
# ============================================

@chat_router.post("/groupes/{groupe_id}/membres/", response={201: MembreGroupeOut}, auth=django_auth)
def add_group_member(request, groupe_id: UUID, payload: MembreGroupeCreate):
    # payload already contains groupe_id but we use the one from URL for consistency
    membre = ChatService.ajouter_membre_groupe(
        acting_user=request.user,
        groupe_id=groupe_id,
        profil_id=payload.profil_id,
        role=payload.role
    )
    return 201, membre

@chat_router.post("/groupes/{groupe_id}/quitter/", response={204: None}, auth=django_auth)
def leave_group(request, groupe_id: UUID):
    ChatService.quitter_groupe(
        acting_user=request.user,
        groupe_id=groupe_id
    )
    return 204, None

@chat_router.delete("/membres/{membre_id}/", response={204: None}, auth=django_auth)
def remove_group_member(request, membre_id: UUID):
    ChatService.retirer_membre_groupe(
        acting_user=request.user,
        membre_id=membre_id
    )
    return 204, None

# ============================================
# GESTION DES MESSAGES
# ============================================

@chat_router.get("/groupes/{groupe_id}/messages/", response=List[MessageGroupeOut], auth=django_auth)
def list_group_messages(request, groupe_id: UUID, limit: int = 50, offset: int = 0):
    return ChatService.obtenir_messages_groupe(
        acting_user=request.user,
        groupe_id=groupe_id,
        limit=limit,
        offset=offset
    )

@chat_router.post("/messages/{message_id}/lu/", response=MessageGroupeOut, auth=django_auth)
def mark_group_message_read(request, message_id: UUID):
    return ChatService.marquer_message_groupe_lu(
        acting_user=request.user,
        message_id=message_id
    )

@chat_router.get("/direct/{profil_id}/", response=List[MessageDirectOut], auth=django_auth)
def list_direct_messages(request, profil_id: UUID, limit: int = 50, offset: int = 0):
    return ChatService.obtenir_conversation(
        acting_user=request.user,
        autre_profil_id=profil_id,
        limit=limit,
        offset=offset
    )

@chat_router.get("/conversations/", auth=django_auth)
def list_recent_conversations(request):
    # This returns a complex list of dicts, might need a schema but for now returning as is
    # It contains 'contact' (Profil), 'dernier_message' (MessageDirect), 'messages_non_lus' (int)
    conversations = ChatService.obtenir_conversations_recentes(acting_user=request.user)

    # Simple formatting for response if needed or use a custom schema
    return conversations

@chat_router.post("/direct/{expediteur_id}/lu/", auth=django_auth)
def mark_conversation_read(request, expediteur_id: UUID):
    count = ChatService.marquer_conversation_lue(
        acting_user=request.user,
        expediteur_id=expediteur_id
    )
    return {"marked_read": count}

@chat_router.get("/stats/", auth=django_auth)
def get_chat_stats(request):
    return ChatService.obtenir_statistiques_messages(acting_user=request.user)
