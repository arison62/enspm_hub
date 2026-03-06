import logging
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, Q, Exists, OuterRef, Sum
from django.core.paginator import Paginator

from core.api.exceptions import (
    BadRequestAPIException,
    BaseAPIException,
    ValidationErrorAPIException,
    PermissionDeniedAPIException,
    NotFoundAPIException
)
from core.utils.base64_utils import Base64FileHandler
from core.models import User
from network.models.chat import (
    MembreGroupe,
    Conversation, ConversationParticipant,
    Message, MessageType, MessageMeta
)
from users.models import Profil
from network.events import (
    event_bus,
    ChatEvents,
)
from network.api.schemas.chat import MessageOut, ConversationOut

logger = logging.getLogger(__name__)


MODEL_MAP = {
    "message": ("network", "message"),
    "mentor_profile": ("network", "mentorprofile"),
    "post": ("feeds", "post"),
    "comment": ("feeds", "comment"),
    "stage": ("opportunities", "stage"),
    "emploi": ("opportunities", "emploi"),
    "formation": ("opportunities", "formation"),
}

class ChatService:
    
    @staticmethod
    @transaction.atomic
    def envoyer_message(
        acting_user: User,
        conversation_id: UUID,
        contenu: str,
        client_id: Optional[UUID] = None,
        media_base64: Optional[str] = None,
        reference_id: Optional[str] = None,
        reference_type: Optional[str] = None,
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
            
            reference_ct = None
            reference_obj_id = None
            reference_type_cache = None

            try:
                if reference_type and reference_id:
                    if reference_type not in MODEL_MAP:
                        raise BadRequestAPIException(f"Type de référence inconnu: {reference_type}")
                    
                    app_label, model = MODEL_MAP[reference_type]
                    reference_ct = ContentType.objects.get(app_label=app_label, model=model)
                    # Vérifier que l'objet existe réellement
                    reference_ct.get_object_for_this_type(id=reference_id)
                    reference_obj_id = reference_id
                    reference_type_cache = reference_type

            except ObjectDoesNotExist:
                raise NotFoundAPIException("Message parent introuvable")

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
                reference_content_type=reference_ct,       # None si pas de référence
                reference_object_id=reference_obj_id,      # None si pas de référence
                reference_type=reference_type_cache,       # cache string
            )
                        
            # Mettre à jour la date de la conversation pour le tri
            conversation.save(update_fields=['updated_at'])

            # Incrémenter les compteurs de messages non lus pour les autres
            ChatService._incrementer_compteurs(conversation, profil)
            
            # SÉRIALISATION AVANT PUBLICATION
            message_frais = Message.objects.select_related(
                'expediteur',
            ).get(id=message.id)
            
            serialized_data = MessageOut.from_orm(message_frais).model_dump(mode='json')

            # PUBLIER L'ÉVÉNEMENT avec room_type et room_id
            if conversation.type == Conversation.ConversationType.GROUP and conversation.groupe:
                room_type = 'group'
                room_id = conversation.id
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

        if conversation.type == Conversation.ConversationType.GROUP and conversation.groupe:
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
    def obtenir_preview_message(reference_id: UUID, reference_type: str) -> dict[str, Any]:
        
        try:
            app_label, model = MODEL_MAP[reference_type]
            ct = ContentType.objects.get(app_label=app_label, model=model)
            reference = ct.get_object_for_this_type(id=reference_id)
            return reference.get_chat_preview()
        except ObjectDoesNotExist:
            raise NotFoundAPIException("L'objet n'existe pas")
        except Exception as e:
            logger.error(f"Erreur obtenir preview: {str(e)}", exc_info=True)
            raise BaseAPIException("Erreur obtenir preview")
        
    @staticmethod
    def _traiter_media(media_base64: str) -> Optional[Dict[str, Any]]:
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
            raise BadRequestAPIException(f"Erreur traitement média: {str(e)}")

    @staticmethod
    def _incrementer_compteurs(conversation: Conversation, expediteur: Profil):
        """Incrémente les messages non lus pour tous les participants sauf l'expéditeur"""
        ConversationParticipant.objects.filter(
            conversation=conversation,
            deleted=False
        ).exclude(profil=expediteur).update(
            messages_non_lus=F('messages_non_lus') + 1
        )

        if conversation.type == Conversation.ConversationType.GROUP and conversation.groupe:
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
            
            if message.conversation.type == Conversation.ConversationType.GROUP and message.conversation.groupe:
                MembreGroupe.objects.filter(
                    groupe=message.conversation.groupe,
                    profil=profil
                ).update(
                    derniere_lecture=timezone.now(),
                    messages_non_lus=0
                )
            
            serialized_data = MessageOut.from_orm(message).model_dump(mode='json')

            if message.conversation.type == Conversation.ConversationType.GROUP and message.conversation.groupe:
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
    def obtenir_conversations(acting_user: User, 
                              type: Optional[str] = None, 
                              query: Optional[str] = None, 
                              page: int = 1, page_size: int = 20) -> Tuple[List[Conversation], int]:
        """Obtient la liste des conversations de l'utilisateur (DMs et Groupes)"""
        
        profil = acting_user.profil
    
        queryset = Conversation.objects.filter(
            participants=profil,
            deleted=False
        ).select_related('groupe').order_by('-updated_at')
        
        if type and type in Conversation.ConversationType.values:
            queryset = queryset.filter(type=type)
        if query:
            qs = ConversationParticipant.objects.filter(
                conversation=OuterRef('pk'),
                profil__nom_complet__icontains=query
            ).exclude(profil=profil)
            
            queryset = queryset.filter(
                Q(groupe__nom__icontains=query) |
                Exists(qs)
            ).distinct()
        total = queryset.count()
        
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        conversations = list(page_obj.object_list)
        conv_ids = [c.id for c in conversations]

        # Récupérer tous les participants avec optimisation
        participants_data = {}
        my_participant_data = {}
        for cp in ConversationParticipant.objects.filter(conversation_id__in=conv_ids).select_related('profil'):
            if cp.conversation_id not in participants_data:
                participants_data[cp.conversation_id] = []
            participants_data[cp.conversation_id].append(cp.profil)
            
            if cp.profil.id == profil.id:
                my_participant_data[cp.conversation_id] = cp
        
        # Récupérer les derniers messages
        last_messages = {}
        for msg in Message.objects.filter(
            conversation_id__in=conv_ids,
            deleted=False
        ).order_by('conversation_id', '-created_at').distinct('conversation_id').select_related('expediteur'):
            last_messages[msg.conversation_id] = msg
                
        for conv in conversations:
            conv.info_participants = participants_data.get(conv.id, [])
            conv.dernier_message = last_messages.get(conv.id)
            
            my_info = my_participant_data.get(conv.id)
            conv.messages_non_lus = my_info.messages_non_lus if my_info else 0
            conv.role = my_info.role if my_info else None
            
            if conv.type == Conversation.ConversationType.DM:
                other_p = next((p for p in conv.info_participants if p.id != profil.id), None)
                conv.contact = other_p
                conv.est_ferme = False
            else:
                conv.contact = None
                conv.est_ferme = conv.groupe.est_ferme if conv.groupe else False
                    
        return conversations, total

    @staticmethod
    def obtenir_conversation(
        acting_user: User,
        conversation_id: UUID,
    ) -> Conversation:
        """
        Récupère UNE conversation spécifique par son ID, uniquement si l'utilisateur y participe.
        Retourne None si la conversation n'existe pas ou n'est pas accessible.
        """
        profil = acting_user.profil

        try:
            conv = Conversation.objects.get(
                id=conversation_id,
                participants=profil,
                deleted=False
            )
        except Conversation.DoesNotExist:
            raise NotFoundAPIException("Conversation introuvable")

        conv = Conversation.objects.filter(id=conv.id)\
            .select_related('groupe')\
            .prefetch_related('participants')\
            .first()

        if not conv:
            raise NotFoundAPIException("Conversation introuvable")

        # Dernier message
        dernier_message = Message.objects.filter(
            conversation=conv,
            deleted=False
        ).select_related('expediteur')\
        .order_by('-created_at')\
        .first()

        try:
            my_participant = ConversationParticipant.objects.get(
                conversation=conv,
                profil=profil
            )
        except ConversationParticipant.DoesNotExist:
            my_participant = None

        # Enrichissement de l'objet conversation
        conv.dernier_message = dernier_message
        conv.messages_non_lus = my_participant.messages_non_lus if my_participant else 0
        conv.role = my_participant.role if my_participant else None

        if conv.type == Conversation.ConversationType.DM:
            other = next((p for p in conv.participants.all() if p.id != profil.id), None)
            conv.contact = other
            conv.est_ferme = False
        else:
            conv.contact = None
            conv.est_ferme = conv.groupe.est_ferme if conv.groupe else False

        return conv

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
        profil1 = acting_user.profil
        
        try:
            profil2 = Profil.objects.get(id=autre_profil_id, deleted=False)
        except Profil.DoesNotExist:
            raise NotFoundAPIException("Profil destinataire introuvable")

        if profil1.id == profil2.id:
            raise ValidationErrorAPIException("Vous ne pouvez pas créer un DM avec vous-même")

        with transaction.atomic():

            convs_p1 = ConversationParticipant.objects.filter(
                profil=profil1,
                deleted=False,
                conversation__type=Conversation.ConversationType.DM,
                conversation__deleted=False
            ).values_list('conversation', flat=True)

            # Étape 2: Chercher une conversation existante
            candidates = ConversationParticipant.objects.filter(
                conversation__in=convs_p1,
                profil=profil2,
                deleted=False
            ).values_list('conversation', flat=True)

            # Étape 3: Vérifier le nombre total de participants (sous-requête)
            existing = None
            for conv_id in candidates:
                # Compter les participants actifs de cette conversation
                participant_count = ConversationParticipant.objects.filter(
                    conversation_id=conv_id,
                    deleted=False
                ).count()
                
                if participant_count == 2:
                    existing = Conversation.objects.select_related('groupe').prefetch_related('participants').get(id=conv_id)
                    break

            if existing:
                return existing

            # Création avec vérification unique en base
            try:
                conv = Conversation.objects.create(type=Conversation.ConversationType.DM)
                
                ConversationParticipant.objects.bulk_create([
                    ConversationParticipant(conversation=conv, profil=profil1),
                    ConversationParticipant(conversation=conv, profil=profil2)
                ])
            except IntegrityError:
                # Si erreur d'intégrité, quelqu'un a créé entre-temps
                # On récupère la conversation existante
                return ChatService.obtenir_ou_creer_dm(acting_user, autre_profil_id)

            conv.refresh_from_db()
            
            serialized_data = ConversationOut.from_orm(conv).model_dump(mode='json')
            event = ChatEvents.conversation_creee(conv.id, serialized_data)
            event_bus.publish(event)
            
            return conv

    @staticmethod
    def obtenir_statistiques_messages(acting_user: User) -> Dict[str, Any]:
        profil = acting_user.profil

        total_unread = ConversationParticipant.objects.filter(
            profil=profil,
            deleted=False
        ).aggregate(total_unread=Sum('messages_non_lus'))['total_unread'] or 0

        dm_unread = ConversationParticipant.objects.filter(
            profil=profil,
            conversation__type=Conversation.ConversationType.DM,
            deleted=False
        ).aggregate(total=Sum('messages_non_lus'))['total'] or 0

        group_unread = ConversationParticipant.objects.filter(
            profil=profil,
            conversation__type=Conversation.ConversationType.GROUP,
            deleted=False
        ).aggregate(total=Sum('messages_non_lus'))['total'] or 0

        # Additional stats to match original
        messages_dm_envoyes = Message.objects.filter(
            expediteur=profil,
            conversation__type=Conversation.ConversationType.DM,
            deleted=False
        ).count()

        messages_dm_recus = Message.objects.filter(
            conversation__type=Conversation.ConversationType.DM,
            conversation__participants=profil,
            deleted=False
        ).exclude(expediteur=profil).count()

        groupes_membre = MembreGroupe.objects.filter(
            profil=profil,
            deleted=False
        ).count()

        groupes_admin = MembreGroupe.objects.filter(
            profil=profil,
            role=MembreGroupe.Role.ADMIN,
            deleted=False
        ).count()

        return {
            'total_messages_non_lus': total_unread,
            'messages_directs': {
                'envoyes': messages_dm_envoyes,
                'recus': messages_dm_recus,
                'non_lus': dm_unread,
            },
            'groupes': {
                'total': groupes_membre,
                'admin': groupes_admin,
                'membre': groupes_membre - groupes_admin,
                'non_lus': group_unread,
            }
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
            
            if conv.type == Conversation.ConversationType.GROUP and conv.groupe:
                MembreGroupe.objects.filter(groupe=conv.groupe, profil=profil).update(
                    messages_non_lus=0,
                    derniere_lecture=timezone.now()
                )
            
            return True
        except Conversation.DoesNotExist:
            raise NotFoundAPIException("Conversation introuvable")

    @staticmethod
    def get_total_messages_non_lus_groupes(acting_user: User) -> int:
        profil = acting_user.profil
        return ConversationParticipant.objects.filter(
            profil=profil,
            conversation__type=Conversation.ConversationType.GROUP,
            deleted=False
        ).aggregate(total=Sum('messages_non_lus'))['total'] or 0

    @staticmethod
    def supprimer_message(acting_user: User, message_id: UUID, conversation_id: UUID):
        profil = acting_user.profil
        try:
            message = Message.objects.select_related(
                'conversation', 
                'conversation__groupe'
            ).get(id=message_id)
            
            conversation = message.conversation
            groupe = conversation.groupe  # None si c'est un DM

            # Vérification des droits
            if message.expediteur == profil:
                # L'expéditeur peut toujours supprimer son message
                pass
            else:
                # Si ce n'est pas l'expéditeur, on vérifie s'il s'agit d'un groupe et que l'utilisateur est admin
                if groupe is not None:
                    if not groupe.est_admin(profil):
                        raise PermissionDeniedAPIException(
                            "Vous n'avez pas la permission de supprimer ce message"
                        )
                else:
                    # C'est un DM, seul l'expéditeur peut supprimer
                    raise PermissionDeniedAPIException(
                        "Vous n'avez pas la permission de supprimer ce message"
                    )

            # Marquage comme supprimé (soft delete)
            message.deleted = True
            message.save(update_fields=['deleted'])
            serialized_data = MessageOut.from_orm(message).model_dump(mode='json')
            event = ChatEvents.message_supprime(
                message_id=message.id,
                room_id=message.conversation.id,
                conversation_id=conversation_id,
                data=serialized_data
            )
            event_bus.publish(event)
            return True

        except Message.DoesNotExist:
            raise NotFoundAPIException("Message introuvable")