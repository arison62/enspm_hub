from typing import List, Optional
from uuid import UUID
from ninja import Router, Query
from core.services.auth_service import jwt_auth
from core.utils.pagination import build_pagination_response
from network.services.chat import ChatService
from network.api.schemas.chat import (
    GroupeListResponse, GroupeOut, GroupeCreate, GroupeUpdate, GroupeFilter,
    MembreGroupeOut, MembreGroupeCreate, MembreGroupeRequestListResponse,
    MembreGroupeUpdate, MessageGroupeOut,
    MessageListResponse, MembreGroupeListResponse,
    MessageDMOut, MessageDMCreate, MessageDMListResponse,
    ConversationOut, ConversationRecentOut
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

@chat_router.patch("/groupes/{groupe_id}/membres/{membre_id}/", response={200: MembreGroupeOut}, auth=jwt_auth)
def update_group_member(request, membre_id: UUID, groupe_id: UUID, payload: MembreGroupeUpdate):
    membre = ChatService.modifier_membre_groupe(
        acting_user=request.auth,
        membre_id=membre_id,
        groupe_id=groupe_id,
        role=payload.role,
       
    )
    return 200, membre

@chat_router.delete("/groupes/{groupe_id}/membres/{membre_id}/", response={204: None}, auth=jwt_auth)
def remove_group_member(request, groupe_id: UUID, membre_id: UUID):
    
    ChatService.retirer_membre_groupe(
        acting_user=request.auth,
        profil_id=membre_id,
        group_id=groupe_id
    )
    return 204, None

@chat_router.get("/groupes/{groupe_id}/membres/", response={200: MembreGroupeListResponse}, auth=jwt_auth)
def list_group_members(request, groupe_id: UUID, querry: Query[Optional[str]] = None, page: int = 1, page_size: int = 20):
    membres, total = ChatService.obtenir_membres_groupe(
        acting_user=request.auth,
        groupe_id=groupe_id,
        page=page,
        page_size=page_size,
        query=querry
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

# ============================================
# GESTION DES CONVERSATIONS (DM)
# ============================================

@chat_router.post("/direct/init/{profil_id}/", response=ConversationOut, auth=jwt_auth)
def init_conversation(request, profil_id: UUID):
    """Initialise une conversation avec un autre profil"""
    return ChatService.obtenir_ou_creer_conversation(
        acting_user=request.auth,
        autre_profil_id=profil_id
    )

@chat_router.get("/direct/conversations/", response=List[ConversationRecentOut], auth=jwt_auth)
def list_recent_conversations(request):
    """Liste les conversations récentes"""
    return ChatService.obtenir_conversations_recentes(acting_user=request.auth)

@chat_router.get("/direct/{conversation_id}/messages/", response=MessageDMListResponse, auth=jwt_auth)
def list_conversation_messages(request, conversation_id: UUID, page: int = 1, page_size: int = 50):
    """Liste les messages d'une conversation"""
    messages, total = ChatService.obtenir_messages_dm(
        acting_user=request.auth,
        conversation_id=conversation_id,
        page=page,
        page_size=page_size
    )
    return build_pagination_response(messages, total, page, page_size)

@chat_router.post("/direct/{conversation_id}/messages/", response={201: MessageDMOut}, auth=jwt_auth)
def send_dm_message(request, conversation_id: UUID, payload: MessageDMCreate):
    """Envoie un message dans une conversation"""
    message = ChatService.envoyer_message_dm(
        acting_user=request.auth,
        conversation_id=conversation_id,
        **payload.model_dump()
    )
    return 201, message

@chat_router.post("/direct/{conversation_id}/lu/", response={204: None}, auth=jwt_auth)
def mark_conversation_read(request, conversation_id: UUID):
    """Marque une conversation comme lue"""
    ChatService.marquer_conversation_lue(
        acting_user=request.auth,
        conversation_id=conversation_id
    )
    return 204, None

@chat_router.get("/stats/", auth=jwt_auth)
def get_chat_stats(request):
    return ChatService.obtenir_statistiques_messages(acting_user=request.auth)
