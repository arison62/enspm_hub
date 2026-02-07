from typing import List, Optional
from uuid import UUID
from ninja import Router, Query
from core.services.auth_service import jwt_auth
from core.utils.pagination import build_pagination_response
from network.services.chat import ChatService
from network.api.schemas.chat import (
    GroupeListResponse, GroupeOut, GroupeCreate, GroupeUpdate, GroupeFilter,
    MembreGroupeOut, MembreGroupeCreate, MembreGroupeRequestListResponse, MessageGroupeOut, MessageDirectOut, 
    MessageListResponse, MembreGroupeListResponse
)

chat_router = Router(tags=["Chat"])

# ============================================
# GESTION DES GROUPES
# ============================================

@chat_router.post("/groupes/", response={201: GroupeOut}, auth=jwt_auth)
def create_group(request, payload: GroupeCreate):
    groupe = ChatService.creer_groupe(
        acting_user=request.auth,
        **payload.model_dump(exclude_unset=True)
    )
    return 201, groupe

@chat_router.patch("/groupes/{groupe_id}/", response=GroupeOut, auth=jwt_auth)
def update_group(request, groupe_id: UUID, payload: GroupeUpdate):
    groupe = ChatService.modifier_groupe(
        acting_user=request.auth,
        groupe_id=groupe_id,
        **payload.model_dump(exclude_unset=True)
    )
    return groupe

@chat_router.delete("/groupes/{groupe_id}/", response={204: None}, auth=jwt_auth)
def delete_group(request, groupe_id: UUID):
    ChatService.supprimer_groupe(
        acting_user=request.auth,
        groupe_id=groupe_id
    )
    return 204, None

@chat_router.get("/groupes/", response={200: GroupeListResponse }, auth=jwt_auth)
def search_groups(request, filters: Query[GroupeFilter], page: int = 1, page_size: int = 20):
    
    groups, total = ChatService.list_groupes(
        acting_user=request.auth,
        **filters.model_dump(exclude_none=True),
        page=page,
        page_size=page_size
    )
    return 200, build_pagination_response(groups, total, page, page_size)
    

# ============================================
# GESTION DES MEMBRES
# ============================================

@chat_router.post("/groupes/{groupe_id}/membres/", response={201: MembreGroupeOut}, auth=jwt_auth)
def add_group_member(request, groupe_id: UUID, payload: MembreGroupeCreate):
    # payload already contains groupe_id but we use the one from URL for consistency
    membre = ChatService.ajouter_membre_groupe(
        acting_user=request.auth,
        groupe_id=groupe_id,
        profil_id=payload.profil_id,
        role=payload.role
    )
    return 201, membre

@chat_router.post("/groupes/{groupe_id}/rejoindre/", response={204: None}, auth=jwt_auth)
def join_group(request, groupe_id: UUID):
    ChatService.rejoindre_groupe_public(
        acting_user=request.auth,
        groupe_id=groupe_id
    )
    return 204, None

@chat_router.post("/groupes/{groupe_id}/demandes/", response={204: None}, auth=jwt_auth)
def request_group(request, groupe_id: UUID):
    ChatService.creer_demande_acces(
        acting_user=request.auth,
        groupe_id=groupe_id
    )
    return 204, None

@chat_router.post("/groupes/{groupe_id}/demandes/annuler/", response={204: None}, auth=jwt_auth)
def cancel_group_request(request,groupe_id: UUID):
    ChatService.annuler_demande(
        acting_user=request.auth,
        groupe_id=groupe_id
    )
    return 204, None


   

@chat_router.post("/groupes/demandes/{demande_id}/approuver/", response={204: None}, auth=jwt_auth)
def accept_group_request(request, demande_id: UUID):
    ChatService.approuver_demande(
        acting_user=request.auth,
        demande_id=demande_id
    )
    return 204, None

@chat_router.post("/groupes/demandes/{demande_id}/refuser/", response={204: None}, auth=jwt_auth)
def reject_group_request(request, demande_id: UUID):
    ChatService.refuser_demande(
        acting_user=request.auth,
        demande_id=demande_id
    )
    return 204, None

@chat_router.get("/groupes/{groupe_id}/demandes/", response={200: MembreGroupeRequestListResponse}, auth=jwt_auth)
def list_group_requests(request, groupe_id: UUID, page: int = 1, page_size: int = 20, status: Query[str] = None):
    membres, total = ChatService.obtenir_demandes_groupe(
        acting_user=request.auth,
        groupe_id=groupe_id,
        status=status,
        page=page,
        page_size=page_size
    )
    return 200, build_pagination_response(membres, total, page, page_size)

@chat_router.post("/groupes/{groupe_id}/quitter/", response={204: None}, auth=jwt_auth)
def leave_group(request, groupe_id: UUID):
    ChatService.quitter_groupe(
        acting_user=request.auth,
        groupe_id=groupe_id
    )
    return 204, None

@chat_router.delete("/groupes/{groupe_id}/membres/{membre_id}/", response={204: None}, auth=jwt_auth)
def remove_group_member(request, groupe_id: UUID, membre_id: UUID):
    
    ChatService.retirer_membre_groupe(
        acting_user=request.auth,
        profil_id=membre_id,
        group_id=groupe_id
    )
    return 204, None

@chat_router.get("/groupes/{groupe_id}/membres/", response={200: MembreGroupeListResponse}, auth=jwt_auth)
def list_group_members(request, groupe_id: UUID, page: int = 1, page_size: int = 20):
    membres, total = ChatService.obtenir_membres_groupe(
        acting_user=request.auth,
        groupe_id=groupe_id,
        page=page,
        page_size=page_size
    )
    return 200, build_pagination_response(membres, total, page, page_size)


# ============================================
# GESTION DES MESSAGES
# ============================================

@chat_router.get("/groupes/{groupe_id}/messages/", response={200: MessageListResponse}, auth=jwt_auth)
def list_group_messages(request, groupe_id: UUID, page: int = 1, page_size: int = 20):
    messages_groupe, total = ChatService.obtenir_messages_groupe(
        acting_user=request.auth,
        groupe_id=groupe_id,
        page=page,
        page_size=page_size
    )
    return 200, build_pagination_response(messages_groupe, total, page, page_size)

@chat_router.post("/messages/{message_id}/lu/", response=MessageGroupeOut, auth=jwt_auth)
def mark_group_message_read(request, message_id: UUID):
    return ChatService.marquer_message_groupe_lu(
        acting_user=request.auth,
        message_id=message_id
    )

@chat_router.get("/direct/{profil_id}/", response=List[MessageDirectOut], auth=jwt_auth)
def list_direct_messages(request, profil_id: UUID, limit: int = 50, offset: int = 0):
    return ChatService.obtenir_conversation(
        acting_user=request.auth,
        autre_profil_id=profil_id,
        limit=limit,
        offset=offset
    )

@chat_router.get("/conversations/", auth=jwt_auth)
def list_recent_conversations(request):
    # This returns a complex list of dicts, might need a schema but for now returning as is
    # It contains 'contact' (Profil), 'dernier_message' (MessageDirect), 'messages_non_lus' (int)
    conversations = ChatService.obtenir_conversations_recentes(acting_user=request.auth)

    # Simple formatting for response if needed or use a custom schema
    return conversations

@chat_router.post("/direct/{expediteur_id}/lu/", auth=jwt_auth)
def mark_conversation_read(request, expediteur_id: UUID):
    count = ChatService.marquer_conversation_lue(
        acting_user=request.auth,
        expediteur_id=expediteur_id
    )
    return {"marked_read": count}

@chat_router.get("/stats/", auth=jwt_auth)
def get_chat_stats(request):
    return ChatService.obtenir_statistiques_messages(acting_user=request.auth)
