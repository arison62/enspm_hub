import logging
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from django.utils import timezone
from django.db import transaction
from django.db.models import F, Q, Count, OuterRef, Subquery, Sum
from django.core.paginator import Paginator

from core.api.exceptions import (
    ValidationErrorAPIException,
    PermissionDeniedAPIException,
    NotFoundAPIException
)
from core.utils.base64_utils import Base64FileHandler
from core.models import User
from network.models.chat import (
    Groupe, MembreGroupe,
    Conversation, ConversationParticipant, ConversationType,
    Message, MessageType, MessageMeta
)
from users.models import Profil
from network.events import (
    event_bus,
    ChatEvents,
)
from network.api.schemas.chat import MessageOut, ConversationOut

logger = logging.getLogger(__name__)

class ChatService:
    
    @staticmethod
    @transaction.atomic
    def envoyer_message(
        acting_user: User,
        conversation_id: UUID,
        contenu: str,
        client_id: Optional[UUID] = None,
        media_base64: Optional[str] = None,
        reponse_a_id: Optional[UUID] = None,
        type_message: str = MessageType.USER,
        request=None
    ) -> Message:
        """
        Envoie un message dans une conversation et publie un événement sur l'EventBus
        """
        try:
            profil = acting_user.profil
            conversation = Conversation.objects.select_related('groupe').get(id=conversation_id, deleted=False)
            
            # Vérifier participation
            if not conversation.participants.filter(id=profil.id).exists():
                raise PermissionDeniedAPIException("Vous n'êtes pas participant à cette conversation")
            
            # Traiter média
            media_info = None
            if media_base64:
                media_info = ChatService._traiter_media(media_base64)
            
            # Message parent
            reponse_a = None
            if reponse_a_id:
                try:
                    reponse_a = Message.objects.get(id=reponse_a_id, conversation=conversation, deleted=False)
                except Message.DoesNotExist:
                    raise NotFoundAPIException("Message parent introuvable")

            # Créer message
            message = Message.objects.create(
                client_id=client_id or uuid4(),
                conversation=conversation,
                type=type_message,
                expediteur=profil if type_message == MessageType.USER else None,
                contenu=contenu,
                media=media_info['file'] if media_info else None,
                media_type=media_info['mime_type'] if media_info else None,
                media_name=media_info['nom'] if media_info else None,
                media_size=media_info['taille'] if media_info else None,
                reponse_a=reponse_a
            )
            
            # Mettre à jour la date de la conversation pour le tri
            conversation.save(update_fields=['updated_at'])

            # Incrémenter les compteurs de messages non lus pour les autres
            ChatService._incrementer_compteurs(conversation, profil)
            
            # SÉRIALISATION AVANT PUBLICATION
            message_frais = Message.objects.select_related(
                'expediteur', 'reponse_a', 'reponse_a__expediteur'
            ).get(id=message.id)
            
            serialized_data = MessageOut.from_orm(message_frais).model_dump(mode='json')

            # PUBLIER L'ÉVÉNEMENT avec room_type et room_id
            if conversation.type == ConversationType.GROUP and conversation.groupe:
                room_type = 'group'
                room_id = conversation.groupe.id
            else:
                room_type = 'conv'
                room_id = conversation.id

            event = ChatEvents.message_envoye(
                message_id=message.id,
                conversation_id=conversation.id,
                message_data=serialized_data,
                room_type=room_type,
                room_id=room_id
            )
            event_bus.publish(event)

            return message
            
        except Conversation.DoesNotExist:
            raise NotFoundAPIException("Conversation introuvable")
        except Exception as e:
            logger.error(f"Erreur envoi message: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def envoyer_message_systeme(conversation: Conversation, contenu: str) -> Message:
        """Helper pour envoyer un message système et publier l'événement"""
        message = Message.objects.create(
            conversation=conversation,
            type=MessageType.SYSTEM,
            contenu=contenu
        )

        message_frais = Message.objects.get(id=message.id)
        serialized_data = MessageOut.from_orm(message_frais).model_dump(mode='json')

        if conversation.type == ConversationType.GROUP and conversation.groupe:
            room_type = 'group'
            room_id = conversation.groupe.id
        else:
            room_type = 'conv'
            room_id = conversation.id

        event = ChatEvents.message_envoye(
            message_id=message.id,
            conversation_id=conversation.id,
            message_data=serialized_data,
            room_type=room_type,
            room_id=room_id
        )
        event_bus.publish(event)
        return message

    @staticmethod
    def _traiter_media(media_base64: str) -> Dict[str, Any]:
        try:
            from core.utils.base64_utils import decode_base64_strict, detect_mime_from_magic
            handler = Base64FileHandler()
            file_data = handler.handle(media_base64, filename_prefix='chat_media')
            
            binary, _ = decode_base64_strict(media_base64)
            mime_type, _ = detect_mime_from_magic(binary)
            
            return {
                'file': file_data,
                'mime_type': mime_type,
                'nom': getattr(file_data, 'name', 'file'),
                'taille': getattr(file_data, 'size', 0)
            }
        except Exception as e:
            logger.warning(f"Erreur traitement média: {e}")
            return None

    @staticmethod
    def _incrementer_compteurs(conversation: Conversation, expediteur: Profil):
        """Incrémente les messages non lus pour tous les participants sauf l'expéditeur"""
        ConversationParticipant.objects.filter(
            conversation=conversation,
            deleted=False
        ).exclude(profil=expediteur).update(
            messages_non_lus=F('messages_non_lus') + 1
        )

        if conversation.type == ConversationType.GROUP and conversation.groupe:
            MembreGroupe.objects.filter(
                groupe=conversation.groupe,
                deleted=False
            ).exclude(profil=expediteur).update(
                messages_non_lus=F('messages_non_lus') + 1
            )

    @staticmethod
    @transaction.atomic
    def marquer_lu(acting_user: User, message_id: UUID):
        profil = acting_user.profil
        try:
            message = Message.objects.select_related('conversation', 'conversation__groupe').get(id=message_id, deleted=False)
            
            MessageMeta.objects.update_or_create(
                message=message,
                profil=profil,
                defaults={'date_lecture': timezone.now()}
            )
            
            ConversationParticipant.objects.filter(
                conversation=message.conversation,
                profil=profil
            ).update(
                last_read_at=timezone.now(),
                messages_non_lus=0
            )
            
            if message.conversation.type == ConversationType.GROUP and message.conversation.groupe:
                MembreGroupe.objects.filter(
                    groupe=message.conversation.groupe,
                    profil=profil
                ).update(
                    derniere_lecture=timezone.now(),
                    messages_non_lus=0
                )
            
            serialized_data = MessageOut.from_orm(message).model_dump(mode='json')

            if message.conversation.type == ConversationType.GROUP and message.conversation.groupe:
                room_type = 'group'
                room_id = message.conversation.groupe.id
            else:
                room_type = 'conv'
                room_id = message.conversation.id

            event = ChatEvents.message_lu(
                message.id,
                message.conversation.id,
                profil.id,
                serialized_data,
                room_type=room_type,
                room_id=room_id
            )
            event_bus.publish(event)

        except Message.DoesNotExist:
            raise NotFoundAPIException("Message introuvable")

    @staticmethod
    def obtenir_conversations(acting_user: User, page: int = 1, page_size: int = 20) -> Tuple[List[Conversation], int]:
        """Obtient la liste des conversations de l'utilisateur avec le dernier message"""
        profil = acting_user.profil
        
        queryset = Conversation.objects.filter(
            participants=profil,
            deleted=False
        ).order_by('-updated_at')
        
        total = queryset.count()
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        conversations = list(page_obj.object_list)
        conv_ids = [c.id for c in conversations]

        participants_data = {}
        for cp in ConversationParticipant.objects.filter(conversation_id__in=conv_ids).select_related('profil'):
            if cp.conversation_id not in participants_data:
                participants_data[cp.conversation_id] = []
            participants_data[cp.conversation_id].append(cp.profil)
            
        last_messages = {}
        for msg in Message.objects.filter(
            conversation_id__in=conv_ids,
            deleted=False
        ).order_by('conversation_id', '-created_at').distinct('conversation_id').select_related('expediteur'):
            last_messages[msg.conversation_id] = msg
            
        for conv in conversations:
            conv.info_participants = participants_data.get(conv.id, [])
            conv.dernier_message = last_messages.get(conv.id)
            
            my_info = ConversationParticipant.objects.filter(conversation=conv, profil=profil).first()
            conv.messages_non_lus = my_info.messages_non_lus if my_info else 0
            
            if conv.type == ConversationType.DM:
                other_p = next((p for p in conv.info_participants if p.id != profil.id), None)
                conv.contact = other_p
            else:
                conv.contact = None
                
        return conversations, total

    @staticmethod
    def obtenir_messages(acting_user: User, conversation_id: UUID, page: int = 1, page_size: int = 50) -> Tuple[List[Message], int]:
        """Obtient les messages d'une conversation"""
        profil = acting_user.profil
        try:
            conversation = Conversation.objects.get(id=conversation_id, participants=profil, deleted=False)
            
            queryset = Message.objects.filter(
                conversation=conversation,
                deleted=False
            ).select_related(
                'expediteur',
                'reponse_a',
                'reponse_a__expediteur'
            ).order_by('-created_at')
            
            total = queryset.count()
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            messages = list(page_obj.object_list)
            messages.reverse()
            
            return messages, total
            
        except Conversation.DoesNotExist:
            raise NotFoundAPIException("Conversation introuvable")

    @staticmethod
    def obtenir_ou_creer_dm(acting_user: User, autre_profil_id: UUID) -> Conversation:
        """Récupère ou crée une conversation DM entre deux profils"""
        profil1 = acting_user.profil
        try:
            profil2 = Profil.objects.get(id=autre_profil_id, deleted=False)
        except Profil.DoesNotExist:
            raise NotFoundAPIException("Profil destinataire introuvable")

        if profil1.id == profil2.id:
            raise ValidationErrorAPIException("Vous ne pouvez pas créer un DM avec vous-même")

        existing = Conversation.objects.filter(
            type=ConversationType.DM,
            participants=profil1
        ).filter(
            participants=profil2
        ).annotate(p_count=Count('participants')).filter(p_count=2).first()

        if existing:
            return existing

        with transaction.atomic():
            conv = Conversation.objects.create(type=ConversationType.DM)
            ConversationParticipant.objects.create(conversation=conv, profil=profil1)
            ConversationParticipant.objects.create(conversation=conv, profil=profil2)
            
            conv_frais = Conversation.objects.get(id=conv.id)
            serialized_data = ConversationOut.from_orm(conv_frais).model_dump(mode='json')
            event = ChatEvents.conversation_creee(conv.id, serialized_data)
            event_bus.publish(event)
            
        return conv

    @staticmethod
    def obtenir_statistiques_messages(acting_user: User) -> Dict[str, Any]:
        profil = acting_user.profil

        res = ConversationParticipant.objects.filter(
            profil=profil,
            deleted=False
        ).aggregate(total_unread=Sum('messages_non_lus'))
        
        return {
            'total_messages_non_lus': res.get('total_unread') or 0,
        }

    @staticmethod
    def marquer_conversation_lue(acting_user: User, conversation_id: UUID):
        """Marque tous les messages d'une conversation comme lus"""
        profil = acting_user.profil
        try:
            conv = Conversation.objects.get(id=conversation_id, participants=profil, deleted=False)
            
            ConversationParticipant.objects.filter(conversation=conv, profil=profil).update(
                messages_non_lus=0,
                last_read_at=timezone.now()
            )
            
            if conv.type == ConversationType.GROUP and conv.groupe:
                MembreGroupe.objects.filter(groupe=conv.groupe, profil=profil).update(
                    messages_non_lus=0,
                    derniere_lecture=timezone.now()
                )
            
            return True
        except Conversation.DoesNotExist:
            raise NotFoundAPIException("Conversation introuvable")
