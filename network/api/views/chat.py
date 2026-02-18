from typing import List, Optional
from uuid import UUID
from ninja import Router, Query
from core.services.auth_service import jwt_auth
from core.utils.pagination import build_pagination_response
from network.services.groupe import GroupeService
from network.services.chat import ChatService
from network.api.schemas.chat import (
    GroupeOut, GroupeCreate, GroupeUpdate, GroupeFilter, GroupeListResponse,
    MembreGroupeOut, MembreGroupeCreate, MembreGroupeUpdate, MembreGroupeListResponse,
    MembreGroupeRequestListResponse, MembreGroupeRequest,
    ConversationOut, ConversationListResponse,
    MessageOut, MessageCreateIn, MessageListResponse
)

chat_router = Router(tags=["Chat"])

# ============================================
# CONVERSATIONS
# ============================================

@chat_router.get("/conversations/", response={200: ConversationListResponse}, auth=jwt_auth)
def list_conversations(request, page: int = 1, page_size: int = 20):
    """Liste toutes les conversation l'utilisateur"""
    conversations, total = ChatService.obtenir_conversations(
        acting_user=request.auth,
        page=page,
        page_size=page_size
    )
    return 200, build_pagination_response(conversations, total, page, page_size)

@chat_router.post("/direct/init/{profil_id}/", response={201: ConversationOut}, auth=jwt_auth)
def init_dm_conversation(request, profil_id: UUID):
    """Initialise ou récupère une conversation DM avec un autre profil"""
    conversation = ChatService.obtenir_ou_creer_dm(
        acting_user=request.auth,
        autre_profil_id=profil_id
    )
    return 201, conversation

# ============================================
# MESSAGES
# ============================================

@chat_router.get("/conversations/{conversation_id}/messages/", response={200: MessageListResponse}, auth=jwt_auth)
def list_messages(request, conversation_id: UUID, page: int = 1, page_size: int = 50):
    """Récupère les messages d'une conversation spécifique"""
    messages, total = ChatService.obtenir_messages(
        acting_user=request.auth,
        conversation_id=conversation_id,
        page=page,
        page_size=page_size
    )
    return 200, build_pagination_response(messages, total, page, page_size)


@chat_router.post("/conversations/{conversation_id}/lu/", response={204: None}, auth=jwt_auth)
def mark_conversation_read(request, conversation_id: UUID):
    """Marque tous les messages d'une conversation comme lus"""
    ChatService.marquer_conversation_lue(request.auth, conversation_id)
    return 204, None


@chat_router.post("/conversations/{conversation_id}/messages/", response={201: MessageOut}, auth=jwt_auth)
def send_message(request, conversation_id: UUID, payload: MessageCreateIn):
    """Envoie un message dans une conversation"""
    message = ChatService.envoyer_message(
        acting_user=request.auth,
        conversation_id=conversation_id,
        **payload.model_dump(exclude_unset=True)
    )
    return 201, message

@chat_router.post("/messages/{message_id}/lu/", response={204: None}, auth=jwt_auth)
def mark_message_read(request, message_id: UUID):
    """Marque un message spécifique comme lu"""
    ChatService.marquer_lu(request.auth, message_id)
    return 204, None

@chat_router.delete("/conversations/{conversation_id}/messages/{message_id}/", response={204: None}, auth=jwt_auth)
def delete_message(request, message_id: UUID, conversation_id: UUID):
    ChatService.supprimer_message(request.auth, message_id, conversation_id)
    return 204, None

# ============================================
# GROUPES
# ============================================

@chat_router.get("/groupes/", response={200: GroupeListResponse}, auth=jwt_auth)
def list_groupes(request, filters: Query[GroupeFilter], page: int = 1, page_size: int = 20):
    groupes, total = GroupeService.list_groupes(
        acting_user=request.auth,
        **filters.model_dump(exclude_none=True),
        page=page,
        page_size=page_size
    )
    return 200, build_pagination_response(groupes, total, page, page_size)

@chat_router.get("/groupes/mes-groupes/", response={200: GroupeListResponse}, auth=jwt_auth)
def list_my_groupes(request, role: Optional[str] = None, page: int = 1, page_size: int = 20):
    groupes, total = GroupeService.obtenir_mes_groupes(
        acting_user=request.auth,
        role=role,
        page=page,
        page_size=page_size
    )
    return 200, build_pagination_response(groupes, total, page, page_size)

@chat_router.post("/groupes/", response={201: GroupeOut}, auth=jwt_auth)
def create_groupe(request, payload: GroupeCreate):
    groupe = GroupeService.creer_groupe(
        acting_user=request.auth,
        **payload.model_dump()
    )
    return 201, groupe

@chat_router.get("/groupes/{groupe_id}/", response={200: GroupeOut}, auth=jwt_auth)
def get_groupe_details(request, groupe_id: UUID):
    return GroupeService.obtenir_details_groupe(request.auth, groupe_id)

@chat_router.patch("/groupes/{groupe_id}/", response={200: GroupeOut}, auth=jwt_auth)
def update_groupe(request, groupe_id: UUID, payload: GroupeUpdate):
    return GroupeService.modifier_groupe(
        acting_user=request.auth,
        groupe_id=groupe_id,
        **payload.model_dump(exclude_unset=True)
    )

@chat_router.delete("/groupes/{groupe_id}/", response={204: None}, auth=jwt_auth)
def delete_groupe(request, groupe_id: UUID):
    GroupeService.supprimer_groupe(request.auth, groupe_id)
    return 204, None

@chat_router.post("/groupes/{groupe_id}/rejoindre/", response={204: None}, auth=jwt_auth)
def join_groupe(request, groupe_id: UUID):
    GroupeService.rejoindre_groupe_public(request.auth, groupe_id)
    return 204, None

@chat_router.post("/groupes/{groupe_id}/quitter/", response={204: None}, auth=jwt_auth)
def leave_groupe(request, groupe_id: UUID):
    GroupeService.quitter_groupe(request.auth, groupe_id)
    return 204, None

# Gestion des membres
@chat_router.get("/groupes/{groupe_id}/membres/", response={200: MembreGroupeListResponse}, auth=jwt_auth)
def list_group_members(request, groupe_id: UUID, query: Query[Optional[str]] = None, page: int = 1, page_size: int = 20):
    membres, total = GroupeService.obtenir_membres_groupe(
        acting_user=request.auth,
        groupe_id=groupe_id,
        page=page,
        page_size=page_size,
        query=query
    )
    return 200, build_pagination_response(membres, total, page, page_size)

@chat_router.post("/groupes/{groupe_id}/membres/", response={201: MembreGroupeOut}, auth=jwt_auth)
def add_group_member(request, groupe_id: UUID, payload: MembreGroupeCreate):
    membre = GroupeService.ajouter_membre_groupe(
        acting_user=request.auth,
        groupe_id=groupe_id,
        profil_id=payload.profil_id,
        role=payload.role
    )
    return 201, membre

@chat_router.patch("/groupes/{groupe_id}/membres/{membre_id}/", response={200: MembreGroupeOut}, auth=jwt_auth)
def update_group_member(request, groupe_id: UUID, membre_id: UUID, payload: MembreGroupeUpdate):
    membre = GroupeService.modifier_membre_groupe(
        acting_user=request.auth,
        groupe_id=groupe_id,
        membre_id=membre_id,
        role=payload.role
    )
    return 200, membre

@chat_router.delete("/groupes/{groupe_id}/membres/{membre_id}/", response={204: None}, auth=jwt_auth)
def remove_group_member(request, groupe_id: UUID, membre_id: UUID):
    GroupeService.retirer_membre_groupe(
        acting_user=request.auth,
        groupe_id=groupe_id,
        profil_id=membre_id
    )
    return 204, None

# Gestion des demandes
@chat_router.post("/groupes/{groupe_id}/demandes/", response={204: None}, auth=jwt_auth)
def create_group_request(request, groupe_id: UUID, message: Optional[str] = None):
    GroupeService.creer_demande_acces(request.auth, groupe_id, message)
    return 204, None

@chat_router.post("/groupes/{groupe_id}/demandes/annuler/", response={204: None}, auth=jwt_auth)
def cancel_group_request(request, groupe_id: UUID):
    GroupeService.annuler_demande(request.auth, groupe_id)
    return 204, None

@chat_router.get("/groupes/{groupe_id}/demandes/", response={200: MembreGroupeRequestListResponse}, auth=jwt_auth)
def list_group_requests(request, groupe_id: UUID, status: Optional[str] = None, page: int = 1, page_size: int = 20):
    demandes, total = GroupeService.obtenir_demandes_groupe(
        acting_user=request.auth,
        groupe_id=groupe_id,
        status=status,
        page=page,
        page_size=page_size
    )
    return 200, build_pagination_response(demandes, total, page, page_size)

@chat_router.get("/demandes/mes-demandes/", response={200: MembreGroupeRequestListResponse}, auth=jwt_auth)
def list_my_requests(request, status: Optional[str] = None, page: int = 1, page_size: int = 20):
    demandes, total = GroupeService.obtenir_mes_demandes(
        acting_user=request.auth,
        status=status,
        page=page,
        page_size=page_size
    )
    return 200, build_pagination_response(demandes, total, page, page_size)

@chat_router.post("/groupes/demandes/{demande_id}/approuver/", response={204: None}, auth=jwt_auth)
def accept_group_request(request, demande_id: UUID):
    GroupeService.approuver_demande(
        acting_user=request.auth,
        demande_id=demande_id
    )
    return 204, None

@chat_router.post("/groupes/demandes/{demande_id}/refuser/", response={204: None}, auth=jwt_auth)
def reject_group_request(request, demande_id: UUID):
    GroupeService.refuser_demande(
        acting_user=request.auth,
        demande_id=demande_id
    )
    return 204, None

# Statistiques
@chat_router.get("/stats/", auth=jwt_auth)
def get_chat_stats(request):
    return ChatService.obtenir_statistiques_messages(request.auth)

@chat_router.get("/stats/messages/", auth=jwt_auth)
def get_chat_stats_alias(request):
    return ChatService.obtenir_statistiques_messages(request.auth)
