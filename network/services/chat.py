import logging
import json
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from django.utils import timezone
from django.db import transaction
from django.db.models import F, Q, Count, OuterRef, Subquery
from django.core.paginator import Paginator

from core.api.exceptions import (
    ValidationErrorAPIException,
    PermissionDeniedAPIException,
    NotFoundAPIException
)
from core.utils.base64_utils import Base64FileHandler
from core.models import User
from network.models.chat import (
    Groupe, MembreGroupe, MessageGroupe, 
    Conversation, ConversationParticipant, MessageDM
)
from users.models import Profil
from network.events import (
    event_bus,
    EventTypes,
    MessageGroupeCreatedEvent,
    MessageGroupeReadEvent,
    MessageDMCreatedEvent,
    ConversationCreatedEvent,
    ConversationReadEvent,
    GroupeReadEvent,
)

logger = logging.getLogger(__name__)


class ChatService:
    
    @staticmethod
    @transaction.atomic
    def envoyer_message_groupe(
        acting_user: User,
        groupe_id: UUID,
        contenu: str,
        reponse_a_id: Optional[UUID] = None,
        piece_jointe_base64: Optional[str] = None,
        request=None
    ) -> MessageGroupe:
        """
        Envoie un message dans un groupe et publie un événement
        
        Args:
            acting_user: Utilisateur envoyant le message
            groupe_id: ID du groupe
            contenu: Contenu du message
            reponse_a_id: ID du message auquel on répond (optionnel)
            piece_jointe_base64: Pièce jointe en base64 (optionnel)
            request: Requête HTTP (optionnel)
        
        Returns:
            MessageGroupe: Le message créé
        
        Raises:
            ValidationErrorAPIException: Si les données sont invalides
            PermissionDeniedAPIException: Si l'utilisateur n'est pas membre du groupe
        """
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.get(
                id=groupe_id,
                deleted=False,
                status=Groupe.Status.ACTIF
            )
            
            # Vérifier que l'utilisateur est membre du groupe
            if not groupe.est_membre(profil):
                raise PermissionDeniedAPIException("Vous devez être membre du groupe pour envoyer des messages")
            
            # Valider le contenu
            if not contenu.strip():
                raise ValidationErrorAPIException("Le contenu ne peut pas être vide")
            
            if len(contenu) > 10000:
                raise ValidationErrorAPIException("Le contenu ne doit pas dépasser 10000 caractères")
            
            # Récupérer le message parent si c'est une réponse
            reponse_a = None
            if reponse_a_id:
                try:
                    reponse_a = MessageGroupe.objects.get(
                        id=reponse_a_id,
                        groupe=groupe,
                        deleted=False
                    )
                except MessageGroupe.DoesNotExist:
                    raise NotFoundAPIException("Message parent introuvable")
            
            # Créer le message
            message = MessageGroupe.objects.create(
                groupe=groupe,
                expediteur=profil,
                contenu=contenu,
                reponse_a=reponse_a
            )
            
            # Traiter la pièce jointe si fournie
            piece_jointe_url = None
            if piece_jointe_base64:
                base64_file_handler = Base64FileHandler()
                
                try:
                    file_data = base64_file_handler.handle(
                        piece_jointe_base64, 
                        filename_prefix='message_groupe_attachment'
                    )
                    message.piece_jointe = file_data
                    message.save()
                    piece_jointe_url = message.piece_jointe.url if message.piece_jointe else None
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement de la pièce jointe: {str(e)}")
            
            logger.info(
                f"Message groupe envoyé - Groupe: {groupe.nom}, "
                f"Expéditeur: {acting_user.id}, "
                f"Message ID: {message.id}"
            )
            
            # Incrémenter les compteurs pour les autres membres
            ChatService._incrementer_compteurs_membres(groupe, profil)
            
            # PUBLIER L'ÉVÉNEMENT au lieu d'appeler directement WebSocket
            event_bus.publish(
                EventTypes.MESSAGE_GROUPE_CREATED,
                MessageGroupeCreatedEvent(
                    message_id=message.id,
                    groupe_id=groupe.id,
                    expediteur_id=profil.id,
                    contenu=contenu,
                    reponse_a_id=reponse_a_id,
                    piece_jointe_url=piece_jointe_url,
                    message_data=ChatService._serialize_message_groupe(message)
                )
            )

            return message
            
        except Groupe.DoesNotExist:
            logger.error(f"Groupe introuvable: {groupe_id}")
            raise NotFoundAPIException("Groupe introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message: {str(e)}")
            raise
    
    
    @staticmethod
    def obtenir_messages_groupe(
        acting_user: User,
        groupe_id: UUID,
        page: int = 1,
        page_size: int = 20,
        request=None
    ) -> tuple[List[MessageGroupe], int]:
        """
        Obtient les messages d'un groupe
        
        Args:
            acting_user: Utilisateur demandant les messages
            groupe_id: ID du groupe
            page: Numéro de page
            page_size: Taille de la page
            request: Requête HTTP (optionnel)
        
        Returns:
            Tuple[List[MessageGroupe], int]: Liste des messages et total
        
        Raises:
            PermissionDeniedAPIException: Si l'utilisateur n'est pas membre
        """
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.get(
                id=groupe_id,
                deleted=False,
                status=Groupe.Status.ACTIF
            )
            
            # Vérifier que l'utilisateur est membre
            if not groupe.est_membre(profil):
                raise PermissionDeniedAPIException("Vous devez être membre du groupe pour voir les messages")
            
            queryset = MessageGroupe.objects.filter(
                groupe=groupe,
                deleted=False
            ).select_related('expediteur', 'reponse_a__expediteur').order_by('created_at')
            
            total_items = queryset.count()
            # Pagination
            start = (page - 1) * page_size
            end = start + page_size
            queryset = queryset[start:end]
            messages = list(queryset)
            
            logger.info(
                f"Messages groupe récupérés - Groupe: {groupe.nom}, "
                f"Nombre: {len(messages)}"
            )
            
            return messages, total_items
            
        except Groupe.DoesNotExist:
            logger.error(f"Groupe introuvable: {groupe_id}")
            raise NotFoundAPIException("Groupe introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des messages: {str(e)}")
            raise

 
    @staticmethod
    @transaction.atomic
    def marquer_message_groupe_lu(
        acting_user: User,
        message_id: UUID,
        request=None
    ) -> MessageGroupe:
        """Marque un message de groupe comme lu et publie un événement"""
        try:
            profil = acting_user.profil
            message = MessageGroupe.objects.select_for_update().get(
                id=message_id,
                deleted=False
            )
            
            # Vérifier que l'utilisateur est membre du groupe
            if not message.groupe.est_membre(profil):
                raise PermissionDeniedAPIException("Accès non autorisé")
            
            if not message.est_lu:
                message.est_lu = True
                message.save(update_fields=['est_lu'])
                
                # Publier l'événement
                event_bus.publish(
                    EventTypes.MESSAGE_GROUPE_READ,
                    MessageGroupeReadEvent(
                        message_id=message.id,
                        groupe_id=message.groupe.id,
                        reader_id=profil.id
                    )
                )
            
            return message
            
        except MessageGroupe.DoesNotExist:
            logger.error(f"Message introuvable: {message_id}")
            raise NotFoundAPIException("Message introuvable")
        except Exception as e:
            logger.error(f"Erreur lors du marquage du message: {str(e)}")
            raise
    

    
    # ============================================
    # GESTION DES CONVERSATIONS (DM)
    # ============================================
    
    @staticmethod
    @transaction.atomic
    def obtenir_ou_creer_conversation(
        acting_user: User,
        autre_profil_id: UUID,
        request=None
    ) -> Conversation:
        """Récupère ou crée une conversation DM entre deux utilisateurs"""
        try:
            profil1 = acting_user.profil
            profil2 = Profil.objects.get(id=autre_profil_id, deleted=False)

            if profil1 == profil2:
                raise ValidationErrorAPIException("Vous ne pouvez pas créer une conversation avec vous-même")

            conversation, created = Conversation.get_or_create_dm(profil1, profil2)

            logger.info(
                f"Conversation {'créée' if created else 'récupérée'} - "
                f"ID: {conversation.id}, Participants: {profil1.id}, {profil2.id}"
            )
            
            # Publier l'événement si nouvelle conversation
            if created:
                event_bus.publish(
                    EventTypes.CONVERSATION_CREATED,
                    ConversationCreatedEvent(
                        conversation_id=conversation.id,
                        participant_ids=[profil1.id, profil2.id]
                    )
                )

            return conversation
        except Profil.DoesNotExist:
            logger.error(f"Profil introuvable: {autre_profil_id}")
            raise NotFoundAPIException("Profil introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de l'obtention de la conversation: {str(e)}")
            raise

    @staticmethod
    @transaction.atomic
    def envoyer_message_dm(
        acting_user: User,
        conversation_id: UUID,
        contenu: str,
        piece_jointe_base64: Optional[str] = None,
        request=None
    ) -> MessageDM:
        """
        Envoie un message dans une conversation et publie un événement
        """
        try:
            profil = acting_user.profil
            conversation = Conversation.objects.get(id=conversation_id, deleted=False)
            
            # Vérifier que l'utilisateur est participant
            if not conversation.participants.filter(id=profil.id).exists():
                raise PermissionDeniedAPIException("Vous n'êtes pas participant à cette conversation")
            
            # Valider le contenu
            if not contenu.strip():
                raise ValidationErrorAPIException("Le contenu ne peut pas être vide")
            
            # Créer le message
            message = MessageDM.objects.create(
                conversation=conversation,
                expediteur=profil,
                contenu=contenu
            )
            
            # Traiter la pièce jointe
            piece_jointe_url = None
            if piece_jointe_base64:
                base64_file_handler = Base64FileHandler()
                try:
                    file_data = base64_file_handler.handle(
                        piece_jointe_base64, 
                        filename_prefix='message_dm_attachment'
                    )
                    message.piece_jointe = file_data
                    message.save()
                    piece_jointe_url = message.piece_jointe.url if message.piece_jointe else None
                except Exception as e:
                    logger.warning(f"Erreur pièce jointe: {str(e)}")
            
            # Mettre à jour la date de la conversation
            conversation.save()

            logger.info(f"Message DM envoyé - Conv: {conversation.id}, De: {acting_user.id}")
            
            # PUBLIER L'ÉVÉNEMENT
            event_bus.publish(
                EventTypes.MESSAGE_DM_CREATED,
                MessageDMCreatedEvent(
                    message_id=message.id,
                    conversation_id=conversation.id,
                    expediteur_id=profil.id,
                    contenu=contenu,
                    piece_jointe_url=piece_jointe_url,
                    message_data=ChatService._serialize_message_dm(message)
                )
            )

            return message
            
        except Conversation.DoesNotExist:
            raise NotFoundAPIException("Conversation introuvable")
        except Exception as e:
            logger.error(f"Erreur envoi message DM: {str(e)}")
            raise

    @staticmethod
    def obtenir_messages_dm(
        acting_user: User,
        conversation_id: UUID,
        page: int = 1,
        page_size: int = 50,
        request=None
    ) -> tuple[List[MessageDM], int]:
        """Obtient les messages d'une conversation"""
        try:
            profil = acting_user.profil
            conversation = Conversation.objects.get(id=conversation_id, deleted=False)
            
            if not conversation.participants.filter(id=profil.id).exists():
                raise PermissionDeniedAPIException("Accès non autorisé")
            
            queryset = MessageDM.objects.filter(
                conversation=conversation,
                deleted=False
            ).select_related('expediteur').order_by('created_at')
            
            total = queryset.count()
            start = (page - 1) * page_size
            end = start + page_size
            
            return list(queryset[start:end]), total
        except Conversation.DoesNotExist:
            raise NotFoundAPIException("Conversation introuvable")



    @staticmethod
    def obtenir_conversations(
        acting_user: User,
        page: int = 1,
        page_size: int = 20,
        request=None
    ) -> Tuple[List[Conversation], int]:
        """
        Obtient les conversations récentes paginées avec données enrichies.
        
        Args:
            acting_user: L'utilisateur connecté
            page: Numéro de la page (commence à 1)
            page_size: Nombre de conversations par page
            request: Requête HTTP optionnelle
        
        Returns:
            Tuple (liste des conversations enrichies, nombre total)
        """
        try:
            profil = acting_user.profil
            
            # Subqueries pour annotations
            dernier_message_date_sq = MessageDM.objects.filter(
                conversation=OuterRef('pk'),
                deleted=False
            ).order_by('-created_at').values('created_at')[:1]
            
            dernier_message_id_sq = MessageDM.objects.filter(
                conversation=OuterRef('pk'),
                deleted=False
            ).order_by('-created_at').values('id')[:1]
            
            # Requête principale - TOUTES les conversations (avec ou sans messages)
            conversations_qs = Conversation.objects.filter(
                participants=profil,
                deleted=False
            ).annotate(
                dernier_message_date=Subquery(dernier_message_date_sq),
                dernier_message_id=Subquery(dernier_message_id_sq),
                nombre_messages=Count(
                    'messages',
                    filter=Q(messages__deleted=False)
                )
            ).order_by('-dernier_message_date')
            
            # Pagination
            paginator = Paginator(conversations_qs, page_size)
            page_obj = paginator.get_page(page)
            
            if not page_obj.object_list:
                return [], 0
            
            conversation_ids = [conv.id for conv in page_obj.object_list]
            
            # ===== PRÉCHARGEMENT GROUPÉ (ÉVITE N+1) =====
            
            # 1. Autres participants
            autres_participants = {
                cp.conversation_id: cp.profil 
                for cp in ConversationParticipant.objects.filter(
                    conversation_id__in=conversation_ids
                ).exclude(profil=profil).select_related('profil')
            }
            
            # 2. Derniers messages
            dernier_msg_ids = [
                conv.dernier_message_id for conv in page_obj.object_list 
                if conv.dernier_message_id
            ]
            
            derniers_messages = {}
            if dernier_msg_ids:
                derniers_messages = {
                    msg.id: msg 
                    for msg in MessageDM.objects.filter(
                        id__in=dernier_msg_ids
                    ).select_related('expediteur')
                }
            
            # 3. Dates de lecture
            last_read_map = {
                cp.conversation_id: cp.last_read_at 
                for cp in ConversationParticipant.objects.filter(
                    conversation_id__in=conversation_ids,
                    profil=profil
                )
            }
            
            # 4. Messages non lus
            non_lus_map = {}
            for conv in page_obj.object_list:
                if conv.nombre_messages == 0:
                    non_lus_map[conv.id] = 0
                    continue
                    
                last_read = last_read_map.get(conv.id)
                
                query = MessageDM.objects.filter(
                    conversation_id=conv.id,
                    deleted=False
                ).exclude(expediteur=profil)
                
                if last_read:
                    query = query.filter(created_at__gt=last_read)
                else:
                    query = query.filter(est_lu=False)
                
                non_lus_map[conv.id] = query.count()
            
            # ===== ENRICHISSEMENT DES OBJETS =====
            
            for conv in page_obj.object_list:
                conv.conversation_id = conv.id  # Alias pour id
                conv.contact = autres_participants.get(conv.id)
                conv.dernier_message = derniers_messages.get(conv.dernier_message_id) if conv.dernier_message_id else None
                conv.messages_non_lus = non_lus_map.get(conv.id, 0)
                conv.updated_at = conv.dernier_message_date or conv.updated_at
                
                # Attributs supplémentaires utiles
                conv.nombre_messages = conv.nombre_messages
                conv.est_vide = conv.nombre_messages == 0
            
            return list(page_obj.object_list), paginator.count
            
        except Exception as e:
            logger.error(f"Erreur récupération conversations: {str(e)}", exc_info=True)
            raise


    @staticmethod
    def obtenir_conversation(
        acting_user: User,
        conversation_id: UUID,
        request=None
    ) -> Optional[Conversation]:
        """
        Obtient une conversation spécifique avec données enrichies.
        
        Args:
            acting_user: L'utilisateur connecté
            conversation_id: UUID de la conversation
            request: Requête HTTP optionnelle
        
        Returns:
            Objet Conversation enrichi ou None si non trouvée
        """
        try:
            profil = acting_user.profil
            
            conversation = Conversation.objects.filter(
                id=conversation_id,
                participants=profil,
                deleted=False
            ).annotate(
                nombre_messages=Count(
                    'messages',
                    filter=Q(messages__deleted=False)
                )
            ).first()
            
            if not conversation:
                return None
            
            # Dernier message (peut être None)
            dernier_message = MessageDM.objects.filter(
                conversation=conversation,
                deleted=False
            ).order_by('-created_at').select_related('expediteur').first()
            
            # Autre participant
            autre_participant = ConversationParticipant.objects.filter(
                conversation=conversation,
            ).exclude(profil=profil).select_related('profil').first()
            
            # Infos de lecture
            participant_info = ConversationParticipant.objects.filter(
                conversation=conversation,
                profil=profil
            ).first()
            
            last_read = participant_info.last_read_at if participant_info else None
            
            # Messages non lus
            if conversation.nombre_messages == 0:
                messages_non_lus = 0
            else:
                non_lus_q = MessageDM.objects.filter(
                    conversation=conversation,
                    deleted=False
                ).exclude(expediteur=profil)
                
                if last_read:
                    non_lus_q = non_lus_q.filter(created_at__gt=last_read)
                else:
                    non_lus_q = non_lus_q.filter(est_lu=False)
                
                messages_non_lus = non_lus_q.count()
            
            # Enrichir l'objet avec les attributs de ConversationRecentOut
            conversation.conversation_id = conversation.id
            conversation.contact = autre_participant.profil if autre_participant else None
            conversation.dernier_message = dernier_message
            conversation.messages_non_lus = messages_non_lus
            conversation.updated_at = dernier_message.created_at if dernier_message else conversation.updated_at
            
            # Attributs supplémentaires
            conversation.nombre_messages = conversation.nombre_messages
            conversation.est_vide = conversation.nombre_messages == 0
            
            return conversation
            
        except Exception as e:
            logger.error(f"Erreur récupération conversation {conversation_id}: {str(e)}", exc_info=True)
            raise
        
    
    @staticmethod
    def _incrementer_compteurs_membres(
        groupe: Groupe,
        expediteur: Profil
    ):
        """
        Incremente les compteurs de messages non lus pour tous les membres
        sauf l'expediteur.
        """
        try:
            MembreGroupe.objects.filter(
                groupe=groupe,
                deleted=False
            ).exclude(profil=expediteur).update(
                messages_non_lus=F('messages_non_lus') + 1
            )
        except Exception as e:
            logger.error(f"Erreur incrementation compteurs: {e}")
            
            
    @staticmethod
    def obtenir_groupe_conversations(
        acting_user: User,
        page: int = 1,
        page_size: int = 20,
        request=None
    ) -> Tuple[List[Groupe], int]:
        """
        Obtient les conversations de groupe récentes avec données enrichies.
        """
        try:
            profil = acting_user.profil
            
            # Subqueries
            dernier_message_date_sq = MessageGroupe.objects.filter(
                groupe=OuterRef('groupe'),
                deleted=False
            ).order_by('-created_at').values('created_at')[:1]
            
            dernier_message_id_sq = MessageGroupe.objects.filter(
                groupe=OuterRef('groupe'),
                deleted=False
            ).order_by('-created_at').values('id')[:1]
            
            # Récupérer via MembreGroupe (avec métadonnées)
            membres_qs = MembreGroupe.objects.filter(
                profil=profil,
                deleted=False
            ).select_related('groupe').annotate(
                dernier_message_date=Subquery(dernier_message_date_sq),
                dernier_message_id=Subquery(dernier_message_id_sq),
                nombre_messages=Count(
                    'groupe__messages',
                    filter=Q(groupe__messages__deleted=False)
                )
            ).order_by('-derniere_lecture', '-groupe__updated_at')
            
            paginator = Paginator(membres_qs, page_size)
            page_obj = paginator.get_page(page)
            
            if not page_obj.object_list:
                return [], 0
            
            # Précharger les derniers messages
            dernier_msg_ids = [
                m.dernier_message_id for m in page_obj.object_list 
                if m.dernier_message_id
            ]
            
            derniers_messages = {}
            if dernier_msg_ids:
                derniers_messages = {
                    msg.id: msg 
                    for msg in MessageGroupe.objects.filter(
                        id__in=dernier_msg_ids
                    ).select_related('expediteur')
                }
            
            # Enrichir les objets Groupe
            groupes = []
            for membre in page_obj.object_list:
                groupe = membre.groupe
                dernier_msg = derniers_messages.get(membre.dernier_message_id)
                
                # Attributs pour ConversationRecentOut
                groupe.conversation_id = groupe.id
                groupe.contact = dernier_msg.expediteur if dernier_msg else None
                groupe.dernier_message = dernier_msg
                groupe.messages_non_lus = membre.messages_non_lus
                groupe.updated_at = membre.dernier_message_date or groupe.updated_at
                groupe.derniere_lecture = membre.derniere_lecture
                groupe.nombre_messages = membre.nombre_messages
                groupe.est_vide = membre.nombre_messages == 0
                groupe.mon_role = membre.role
                
                groupes.append(groupe)
            
            return groupes, paginator.count
            
        except Exception as e:
            logger.error(f"Erreur récupération conversations groupe: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def obtenir_groupe_conversation(
        acting_user: User,
        groupe_id: UUID,
        request=None
    ) -> Optional[Groupe]:
        """Obtient une conversation de groupe spécifique"""
        try:
            profil = acting_user.profil
            
            membre = MembreGroupe.objects.filter(
                groupe_id=groupe_id,
                profil=profil,
                deleted=False
            ).select_related('groupe').annotate(
                nombre_messages=Count(
                    'groupe__messages',
                    filter=Q(groupe__messages__deleted=False)
                )
            ).first()
            
            if not membre:
                return None
            
            groupe = membre.groupe
            dernier_msg = MessageGroupe.objects.filter(
                groupe=groupe,
                deleted=False
            ).order_by('-created_at').select_related('expediteur').first()
            
            # Enrichir
            groupe.conversation_id = groupe.id
            groupe.contact = dernier_msg.expediteur if dernier_msg else None
            groupe.dernier_message = dernier_msg
            groupe.messages_non_lus = membre.messages_non_lus
            groupe.updated_at = dernier_msg.created_at if dernier_msg else groupe.updated_at
            groupe.derniere_lecture = membre.derniere_lecture
            groupe.nombre_messages = membre.nombre_messages
            groupe.est_vide = membre.nombre_messages == 0
            groupe.mon_role = membre.role
            
            return groupe
            
        except Exception as e:
            logger.error(f"Erreur: {str(e)}", exc_info=True)
            raise

    @staticmethod
    @transaction.atomic
    def marquer_groupe_lu(acting_user: User, groupe_id: UUID, request=None) -> bool:
        """Marque tous les messages d'un groupe comme lus et publie un événement"""
        try:
            profil = acting_user.profil
            
            membre = MembreGroupe.objects.filter(
                groupe_id=groupe_id,
                profil=profil,
                deleted=False
            ).first()
            
            if not membre:
                return False
            
            membre.marquer_lu()
            
            # Publier l'événement
            event_bus.publish(
                EventTypes.GROUPE_READ,
                GroupeReadEvent(
                    groupe_id=groupe_id,
                    profil_id=profil.id
                )
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur: {str(e)}")
            return False

    @staticmethod
    def get_total_messages_non_lus_groupes(acting_user: User) -> int:
        """Total de messages non lus dans tous les groupes"""
        from django.db.models import Sum
        return MembreGroupe.objects.filter(
            profil=acting_user.profil,
            deleted=False
        ).aggregate(total=Sum('messages_non_lus'))['total'] or 0
        
    @staticmethod
    @transaction.atomic
    def marquer_conversation_lue(
        acting_user: User,
        conversation_id: UUID,
        request=None
    ) -> bool:
        """Marque une conversation comme lue et publie un événement"""
        try:
            profil = acting_user.profil
            participant = ConversationParticipant.objects.get(
                conversation_id=conversation_id,
                profil=profil,
                deleted=False
            )
            participant.last_read_at = timezone.now()
            participant.save()
            
            # Marquer aussi les messages individuels comme lus (pour compatibilité)
            MessageDM.objects.filter(
                conversation_id=conversation_id,
                deleted=False,
                est_lu=False
            ).exclude(expediteur=profil).update(est_lu=True)
            
            # Publier l'événement
            event_bus.publish(
                EventTypes.CONVERSATION_READ,
                ConversationReadEvent(
                    conversation_id=conversation_id,
                    profil_id=profil.id
                )
            )
            
            return True
        except ConversationParticipant.DoesNotExist:
            raise NotFoundAPIException("Conversation non trouvée")

    @staticmethod
    def obtenir_statistiques_messages(
        acting_user: User,
        request=None
    ) -> Dict[str, Any]:
        """Obtient les statistiques de messagerie d'un utilisateur"""
        try:
            # Messages directs
            profil = acting_user.profil
            messages_dm_envoyes = MessageDM.objects.filter(
                expediteur=profil,
                deleted=False
            ).count()
            
            messages_dm_recus = MessageDM.objects.filter(
                conversation__participants=profil,
                deleted=False
            ).exclude(expediteur=profil).count()
            
            # Count unread messages from all conversations
            messages_non_lus = 0
            conversations = Conversation.objects.filter(participants=profil, deleted=False)
            for conv in conversations:
                participant_info = conv.conversation_participants.filter(profil=profil).first()
                last_read = participant_info.last_read_at if participant_info else None

                query = conv.messages.filter(deleted=False).exclude(expediteur=profil)
                if last_read:
                    query = query.filter(created_at__gt=last_read)
                else:
                    query = query.filter(est_lu=False)
                messages_non_lus += query.count()
            
            # Groupes
            groupes_membre = MembreGroupe.objects.filter(
                profil=profil,
                deleted=False
            ).count()
            
            groupes_admin = MembreGroupe.objects.filter(
                profil=profil,
                role='admin',
                deleted=False
            ).count()
            
            stats = {
                'messages_directs': {
                    'envoyes': messages_dm_envoyes,
                    'recus': messages_dm_recus,
                    'non_lus': messages_non_lus,
                },
                'groupes': {
                    'total': groupes_membre,
                    'admin': groupes_admin,
                    'membre': groupes_membre - groupes_admin,
                }
            }
            
            logger.info(f"Statistiques messages générées pour: {acting_user.id}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {str(e)}")
            raise
    
    # ============================================
    # MÉTHODES UTILITAIRES DE SÉRIALISATION
    # ============================================
    
    @staticmethod
    def _serialize_message_groupe(message: MessageGroupe) -> Dict[str, Any]:
        """Sérialise un message groupe pour l'événement"""
        return {
            'id': str(message.id),
            'groupe_id': str(message.groupe.id),
            'expediteur': {
                'id': str(message.expediteur.id),
                'nom_complet': message.expediteur.nom_complet,
                'photo_url': message.expediteur.photo_profil.url,
            },
            'contenu': message.contenu,
            'piece_jointe_url': message.piece_jointe.url if message.piece_jointe else None,
            'reponse_a_id': str(message.reponse_a.id) if message.reponse_a else None,
            'created_at': message.created_at.isoformat(),
        }
    
    @staticmethod
    def _serialize_message_dm(message: MessageDM) -> Dict[str, Any]:
        """Sérialise un message DM pour l'événement"""
        return {
            'id': str(message.id),
            'conversation_id': str(message.conversation.id),
            'expediteur': {
                'id': str(message.expediteur.id),
                'nom_complet': message.expediteur.nom_complet,
                'photo_url': message.expediteur.photo_profil.url,
            },
            'contenu': message.contenu,
            'piece_jointe_url': message.piece_jointe.url if message.piece_jointe else None,
            'created_at': message.created_at.isoformat(),
        }