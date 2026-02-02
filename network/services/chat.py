# network/services/chats.py
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.db.models import Q

from core.api.exceptions import BaseAPIException
from core.utils.base64_utils import Base64FileHandler
from core.models import User
from core.utils.generate_unique_slug import generate_unique_slug
from network.models.chat import (
    Groupe, MembreGroupe, MessageGroupe, MessageDirect
)
from users.models import Profil

logger = logging.getLogger(__name__)




class ChatService:
    """Service de gestion de la messagerie (groupes et messages directs)"""
    
    
    #===============================================
    # GESTION DES GROUPES
    #===============================================
    @staticmethod
    @transaction.atomic
    def creer_groupe(
        acting_user: User,
        nom: str,
        description: Optional[str] = None,
        type_acces: str = 'public',
        image_base64: Optional[str] = None,
        request=None
    ) -> Groupe:
        """
        Crée un nouveau groupe de discussion
        
        Args:
            acting_user: Utilisateur créant le groupe
            nom: Nom du groupe
            description: Description du groupe
            type_acces: Type d'accès ('public' ou 'prive')
            image_base64: Image du groupe en base64
            request: Requête HTTP (optionnel)
        
        Returns:
            Groupe: Le groupe créé
        
        Raises:
            ValidationError: Si les données sont invalides
        """
        try:
            profil = acting_user.profil
            # Valider le type d'accès
            if type_acces not in ['public', 'prive']:
                raise ValidationError(f"Type d'accès invalide: {type_acces}")
            
            # Valider le nom
            if len(nom) < 3:
                raise ValidationError("Le nom doit contenir au moins 3 caractères")
            
            if len(nom) > 255:
                raise ValidationError("Le nom ne doit pas dépasser 255 caractères")
            
            # Générer un slug unique
            slug = generate_unique_slug(nom, Groupe)
            
            if slug is None:
                raise BaseAPIException("Impossible de générer un slug unique")
            
            # Créer le groupe
            groupe = Groupe.objects.create(
                nom=nom,
                slug=slug,
                description=description or "",
                type_acces=type_acces,
                createur=profil
            )
            
            # Traiter l'image si fournie
            if image_base64:
                try:
                    base64_image_handler = Base64FileHandler()
                    image_data = base64_image_handler.handle(
                        image_base64, 
                        filename_prefix='group_image',
                        max_dimensions=(800, 800),
                    )
                    groupe.image = image_data
                    groupe.save()
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement de l'image: {str(e)}")
                
            # Ajouter le créateur comme administrateur du groupe
            MembreGroupe.objects.create(
                groupe=groupe,
                profil=profil,
                role='admin'
            )
            
            logger.info(
                f"Groupe créé - ID: {groupe.id}, "
                f"Nom: {nom}, "
                f"Type: {type_acces}, "
                f"Créateur: {acting_user.id}"
            )
            
            return groupe
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du groupe: {str(e)}")
            raise


    @staticmethod
    @transaction.atomic
    def modifier_groupe(
        acting_user: User,
        groupe_id: UUID,
        nom: Optional[str] = None,
        description: Optional[str] = None,
        type_acces: Optional[str] = None,
        image_base64: Optional[str] = None,
        request=None
    ) -> Groupe:
        """
        Modifie un groupe existant
        
        Args:
            acting_user: Utilisateur effectuant la modification
            groupe_id: ID du groupe
            nom: Nouveau nom
            description: Nouvelle description
            type_acces: Nouveau type d'accès
            image_base64: Nouvelle image en base64
            request: Requête HTTP (optionnel)
        
        Returns:
            Groupe: Le groupe modifié
        
        Raises:
            ValidationError: Si les données sont invalides
            PermissionDenied: Si l'utilisateur n'a pas les droits
        """
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.select_for_update().get(
                id=groupe_id,
                deleted=False
            )
            
            # Vérifier les permissions (doit être admin du groupe)
            if not groupe.est_admin(profil):
                logger.warning(
                    f"Tentative de modification non autorisée du groupe {groupe_id} "
                    f"par {acting_user.id}"
                )
                raise PermissionDenied("Vous devez être administrateur pour modifier le groupe")
            
            # Mettre à jour les champs
            if nom is not None:
                if len(nom) < 3 or len(nom) > 255:
                    raise ValidationError("Le nom doit contenir entre 3 et 255 caractères")
                
                groupe.nom = nom
                # Régénérer le slug
                slug = generate_unique_slug(nom, Groupe)
                
                if slug is None:
                    raise BaseAPIException("Impossible de générer un slug unique")
                groupe.slug = slug
            
            if description is not None:
                groupe.description = description
            
            if type_acces is not None:
                if type_acces not in ['public', 'prive']:
                    raise ValidationError(f"Type d'accès invalide: {type_acces}")
                groupe.type_acces = type_acces
            
            groupe.save()

            
            # Traiter l'image si fournie
            if image_base64:
                try:
                    base64_image_handler = Base64FileHandler()
                    if image_base64:
                        image_data = base64_image_handler.handle(
                            image_base64, 
                            filename_prefix='group_image',
                            max_dimensions=(800, 800),
                        )
                        groupe.image = image_data
                        groupe.save()
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement de l'image: {str(e)}")
            
            logger.info(
                f"Groupe modifié - ID: {groupe.id}, "
                f"Par: {acting_user.id}"
            )
            
            return groupe
            
        except Groupe.DoesNotExist:
            logger.error(f"Groupe introuvable: {groupe_id}")
            raise ValidationError("Groupe introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la modification du groupe: {str(e)}")
            raise

    
    @staticmethod
    @transaction.atomic
    def supprimer_groupe(
        acting_user: User,
        groupe_id: UUID,
        request=None
    ) -> bool:
        """
        Supprime (soft delete) un groupe
        
        Args:
            acting_user: Utilisateur effectuant la suppression
            groupe_id: ID du groupe
            request: Requête HTTP (optionnel)
        
        Returns:
            bool: True si la suppression a réussi
        
        Raises:
            PermissionDenied: Si l'utilisateur n'a pas les droits
        """
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.select_for_update().get(
                id=groupe_id,
                deleted=False
            )
            
            # Vérifier les permissions
            if not groupe.est_admin(profil) or not acting_user.is_admin_user():
                raise PermissionDenied("Vous devez être administrateur pour supprimer le groupe")
            
            groupe.deleted = True
            groupe.save()
            
            logger.info(
                f"Groupe supprimé - ID: {groupe.id}, "
                f"Par: {acting_user.id}"
            )
            
            return True
            
        except Groupe.DoesNotExist:
            logger.error(f"Groupe introuvable: {groupe_id}")
            raise ValidationError("Groupe introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du groupe: {str(e)}")
            raise

    
    @staticmethod
    def rechercher_groupes(
        acting_user: User,
        query: Optional[str] = None,
        type_acces: Optional[str] = None,
        request=None
    ) -> List[Groupe]:
        """
        Recherche des groupes
        
        Args:
            acting_user: Utilisateur effectuant la recherche
            query: Terme de recherche
            type_acces: Filtrer par type d'accès
            request: Requête HTTP (optionnel)
        
        Returns:
            List[Groupe]: Liste des groupes correspondants
        """
        try:
           
            queryset = Groupe.objects.filter(
                deleted=False
            ).select_related('createur')
            
            # Recherche textuelle
            if query:
                queryset = queryset.filter(
                    Q(nom__icontains=query) |
                    Q(description__icontains=query)
                )
            
            # Filtre par type d'accès
            if type_acces:
                queryset = queryset.filter(type_acces=type_acces)
            
            groupes = list(queryset.order_by('-created_at'))
            
            logger.info(
                f"Recherche groupes - Utilisateur: {acting_user.id}, "
                f"Résultats: {len(groupes)}"
            )
            
            return groupes
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de groupes: {str(e)}")
            raise

    
    @staticmethod
    @transaction.atomic
    def ajouter_membre_groupe(
        acting_user: User,
        groupe_id: UUID,
        profil_id: UUID,
        role: str = 'membre',
        request=None
    ) -> MembreGroupe:
        """
        Ajoute un membre à un groupe (invitation par un admin)
        
        Args:
            acting_user: Administrateur ajoutant le membre
            groupe_id: ID du groupe
            profil_id: ID du profil à ajouter
            role: Rôle du membre ('membre' ou 'admin')
            request: Requête HTTP (optionnel)
        
        Returns:
            MembreGroupe: Le membre ajouté
        
        Raises:
            ValidationError: Si les données sont invalides
            PermissionDenied: Si l'utilisateur n'a pas les droits
        """
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.get(
                id=groupe_id,
                deleted=False
            )
            
            profil_to_add = Profil.objects.get(
                id=profil_id,
                deleted=False
            )
            
            # Vérifier les permissions
            if not groupe.est_admin(profil):
                raise PermissionDenied("Vous devez être administrateur pour ajouter des membres")
            
            # Vérifier que le profil n'est pas déjà membre
            if groupe.est_membre(profil_to_add):
                raise ValidationError("Ce profil est déjà membre du groupe")
            
            # Valider le rôle
            if role not in ['membre', 'admin']:
                raise ValidationError(f"Rôle invalide: {role}")
            
            # Créer le membre
            membre = MembreGroupe.objects.create(
                groupe=groupe,
                profil=profil_to_add,
                role=role
            )
            
            logger.info(
                f"Membre ajouté au groupe - Groupe: {groupe.nom}, "
                f"Membre: {profil_to_add.user.id}, "
                f"Rôle: {role}, "
                f"Par: {acting_user.id}"
            )
            
            return membre
            
        except Groupe.DoesNotExist:
            logger.error(f"Groupe introuvable: {groupe_id}")
            raise ValidationError("Groupe introuvable")
        except Profil.DoesNotExist:
            logger.error(f"Profil introuvable: {profil_id}")
            raise ValidationError("Profil introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du membre: {str(e)}")
            raise

    
    @staticmethod
    @transaction.atomic
    def quitter_groupe(
        acting_user: User,
        groupe_id: UUID,
        request=None
    ) -> bool:
        """
        Quitte un groupe
        
        Args:
            acting_user: Utilisateur quittant le groupe
            groupe_id: ID du groupe
            request: Requête HTTP (optionnel)
        
        Returns:
            bool: True si le départ a réussi
        
        Raises:
            ValidationError: Si le départ n'est pas possible
        """
        try:
            profil = acting_user.profil
            membre = MembreGroupe.objects.select_for_update().get(
                groupe_id=groupe_id,
                profil=profil,
                deleted=False
            )
            
            # Empêcher de quitter si c'est le dernier admin
            if membre.role == 'admin':
                nb_admins = MembreGroupe.objects.filter(
                    groupe=membre.groupe,
                    role='admin',
                    deleted=False
                ).count()
                
                if nb_admins <= 1:
                    raise ValidationError(
                        "Vous ne pouvez pas quitter le groupe car vous êtes le dernier administrateur. "
                        "Nommez un autre administrateur ou supprimez le groupe."
                    )
            
            membre.deleted = True
            membre.save()
            
            logger.info(
                f"Membre a quitté le groupe - Groupe: {membre.groupe.nom}, "
                f"Membre: {acting_user.id}"
            )
            
            return True
            
        except MembreGroupe.DoesNotExist:
            logger.error(f"Membre introuvable pour le groupe: {groupe_id}")
            raise ValidationError("Vous n'êtes pas membre de ce groupe")
        except Exception as e:
            logger.error(f"Erreur lors du départ du groupe: {str(e)}")
            raise


    
    @staticmethod
    @transaction.atomic
    def retirer_membre_groupe(
        acting_user: User,
        membre_id: UUID,
        request=None
    ) -> bool:
        """
        Retire un membre du groupe (par un admin)
        
        Args:
            acting_user: Administrateur retirant le membre
            membre_id: ID du membre
            request: Requête HTTP (optionnel)
        
        Returns:
            bool: True si le retrait a réussi
        
        Raises:
            PermissionDenied: Si l'utilisateur n'a pas les droits
        """
        try:
            profil = acting_user.profil
            membre = MembreGroupe.objects.select_for_update().get(
                id=membre_id,
                deleted=False
            )
            
            # Vérifier les permissions
            if not membre.groupe.est_admin(profil):
                raise PermissionDenied("Vous devez être administrateur pour retirer des membres")
            
            # Empêcher de retirer le dernier admin
            if membre.role == 'admin':
                nb_admins = MembreGroupe.objects.filter(
                    groupe=membre.groupe,
                    role='admin',
                    deleted=False
                ).count()
                
                if nb_admins <= 1:
                    raise ValidationError("Impossible de retirer le dernier administrateur")
            
            membre.deleted = True
            membre.save()
            
            logger.info(
                f"Membre retiré du groupe - Groupe: {membre.groupe.nom}, "
                f"Membre: {membre.profil.user.id}, "
                f"Par: {acting_user.id}"
            )
            
            return True
            
        except MembreGroupe.DoesNotExist:
            logger.error(f"Membre introuvable: {membre_id}")
            raise ValidationError("Membre introuvable")
        except Exception as e:
            logger.error(f"Erreur lors du retrait du membre: {str(e)}")
            raise

    
    # ============================================
    # GESTION DES MESSAGES DE GROUPE
    # ============================================
    
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
        Envoie un message dans un groupe
        
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
            ValidationError: Si les données sont invalides
            PermissionDenied: Si l'utilisateur n'est pas membre du groupe
        """
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.get(
                id=groupe_id,
                deleted=False
            )
            
            # Vérifier que l'utilisateur est membre du groupe
            if not groupe.est_membre(profil):
                raise PermissionDenied("Vous devez être membre du groupe pour envoyer des messages")
            
            # Valider le contenu
            if not contenu.strip():
                raise ValidationError("Le contenu ne peut pas être vide")
            
            if len(contenu) > 10000:
                raise ValidationError("Le contenu ne doit pas dépasser 10000 caractères")
            
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
                    raise ValidationError("Message parent introuvable")
            
            # Créer le message
            message = MessageGroupe.objects.create(
                groupe=groupe,
                expediteur=profil,
                contenu=contenu,
                reponse_a=reponse_a
            )
            
            # Traiter la pièce jointe si fournie
            if piece_jointe_base64:
                base64_file_handler = Base64FileHandler()
                
                try:

                    file_data = base64_file_handler.handle(
                        piece_jointe_base64, 
                        filename_prefix='message_groupe_attachment'
                    )
                    message.piece_jointe = file_data
                    message.save()
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement de la pièce jointe: {str(e)}")
            
            logger.info(
                f"Message groupe envoyé - Groupe: {groupe.nom}, "
                f"Expéditeur: {acting_user.id}, "
                f"Message ID: {message.id}"
            )
            
            return message
            
        except Groupe.DoesNotExist:
            logger.error(f"Groupe introuvable: {groupe_id}")
            raise ValidationError("Groupe introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message: {str(e)}")
            raise
    
    
    @staticmethod
    def obtenir_messages_groupe(
        acting_user: User,
        groupe_id: UUID,
        limit: Optional[int] = 50,
        offset: int = 0,
        request=None
    ) -> List[MessageGroupe]:
        """
        Obtient les messages d'un groupe
        
        Args:
            acting_user: Utilisateur demandant les messages
            groupe_id: ID du groupe
            limit: Nombre maximum de messages à retourner
            offset: Décalage pour la pagination
            request: Requête HTTP (optionnel)
        
        Returns:
            List[MessageGroupe]: Liste des messages
        
        Raises:
            PermissionDenied: Si l'utilisateur n'est pas membre
        """
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.get(
                id=groupe_id,
                deleted=False
            )
            
            # Vérifier que l'utilisateur est membre
            if not groupe.est_membre(profil):
                raise PermissionDenied("Vous devez être membre du groupe pour voir les messages")
            
            queryset = MessageGroupe.objects.filter(
                groupe=groupe,
                deleted=False
            ).select_related('expediteur', 'reponse_a__expediteur').order_by('created_at')
            
            if limit:
                queryset = queryset[offset:offset+limit]
            
            messages = list(queryset)
            
            logger.info(
                f"Messages groupe récupérés - Groupe: {groupe.nom}, "
                f"Nombre: {len(messages)}"
            )
            
            return messages
            
        except Groupe.DoesNotExist:
            logger.error(f"Groupe introuvable: {groupe_id}")
            raise ValidationError("Groupe introuvable")
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
        """Marque un message de groupe comme lu"""
        try:
            profil = acting_user.profil
            message = MessageGroupe.objects.select_for_update().get(
                id=message_id,
                deleted=False
            )
            
            # Vérifier que l'utilisateur est membre du groupe
            if not message.groupe.est_membre(profil):
                raise PermissionDenied("Accès non autorisé")
            
            if not message.est_lu:
                message.marquer_comme_lu()
            
            return message
            
        except MessageGroupe.DoesNotExist:
            logger.error(f"Message introuvable: {message_id}")
            raise ValidationError("Message introuvable")
        except Exception as e:
            logger.error(f"Erreur lors du marquage du message: {str(e)}")
            raise
    

    
    # ============================================
    # GESTION DES MESSAGES DIRECTS
    # ============================================
    
    @staticmethod
    @transaction.atomic
    def envoyer_message_direct(
        acting_user: User,
        destinataire_id: UUID,
        contenu: str,
        piece_jointe_base64: Optional[str] = None,
        request=None
    ) -> MessageDirect:
        """
        Envoie un message direct à un utilisateur
        
        Args:
            acting_user: Utilisateur envoyant le message
            destinataire_id: ID du destinataire
            contenu: Contenu du message
            piece_jointe_base64: Pièce jointe en base64 (optionnel)
            request: Requête HTTP (optionnel)
        
        Returns:
            MessageDirect: Le message créé
        
        Raises:
            ValidationError: Si les données sont invalides
        """
        try:
            profil = acting_user.profil
            destinataire = Profil.objects.get(
                id=destinataire_id,
                deleted=False
            )
            
            # Empêcher de s'envoyer un message à soi-même
            if acting_user.id == destinataire.id:
                raise ValidationError("Vous ne pouvez pas vous envoyer un message à vous-même")
            
            # Valider le contenu
            if not contenu.strip():
                raise ValidationError("Le contenu ne peut pas être vide")
            
            if len(contenu) > 10000:
                raise ValidationError("Le contenu ne doit pas dépasser 10000 caractères")
            
            # Créer le message
            message = MessageDirect.objects.create(
                expediteur=profil,
                destinataire=destinataire,
                contenu=contenu
            )
            
            # Traiter la pièce jointe si fournie
            if piece_jointe_base64:
                base64_file_handler = Base64FileHandler()
                try:
                    file_data = base64_file_handler.handle(
                        piece_jointe_base64, 
                        filename_prefix=f'message_direct_attachment'
                    )
                    message.piece_jointe = file_data
                    message.save()
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement de la pièce jointe: {str(e)}")
            
            logger.info(
                f"Message direct envoyé - De: {acting_user.id}, "
                f"À: {destinataire.user.id}, "
                f"Message ID: {message.id}"
            )
            
            return message
            
        except Profil.DoesNotExist:
            logger.error(f"Destinataire introuvable: {destinataire_id}")
            raise ValidationError("Destinataire introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message direct: {str(e)}")
            raise

    
    @staticmethod
    def obtenir_conversation(
        acting_user: User,
        autre_profil_id: UUID,
        limit: Optional[int] = 50,
        offset: int = 0,
        request=None
    ) -> List[MessageDirect]:
        """
        Obtient la conversation entre deux utilisateurs
        
        Args:
            acting_user: Utilisateur demandant la conversation
            autre_profil_id: ID de l'autre utilisateur
            limit: Nombre maximum de messages
            offset: Décalage pour la pagination
            request: Requête HTTP (optionnel)
        
        Returns:
            List[MessageDirect]: Liste des messages de la conversation
        """
        try:
            autre_profil = Profil.objects.get(
                id=autre_profil_id,
                deleted=False
            )
            
            queryset = MessageDirect.get_conversation(acting_user.profil, autre_profil)
            
            if limit:
                queryset = queryset[offset:offset+limit]
            
            messages = list(queryset)
            
            logger.info(
                f"Conversation récupérée - Entre: {acting_user.id} "
                f"et {autre_profil.user.id}, "
                f"Nombre: {len(messages)}"
            )
            
            return messages
            
        except Profil.DoesNotExist:
            logger.error(f"Profil introuvable: {autre_profil_id}")
            raise ValidationError("Profil introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la conversation: {str(e)}")
            raise
        

    
    @staticmethod
    def obtenir_conversations_recentes(
        acting_user: User,
        request=None
    ) -> List[Dict[str, Any]]:
        """
        Obtient les conversations récentes d'un utilisateur
        
        Args:
            acting_user: Utilisateur demandant les conversations
            request: Requête HTTP (optionnel)
        
        Returns:
            List[Dict]: Liste des conversations avec derniers messages
        """
        try:
            profil = acting_user.profil
            # Obtenir les IDs des contacts
            contact_ids = MessageDirect.get_conversations_recentes(profil)
            
            # Récupérer les profils et derniers messages
            conversations = []
            for contact_id in contact_ids:
                try:
                    contact = Profil.objects.get(id=contact_id, deleted=False)
                    
                    # Récupérer le dernier message
                    dernier_message = MessageDirect.objects.filter(
                        Q(expediteur=profil, destinataire=contact) |
                        Q(expediteur=contact, destinataire=profil),
                        deleted=False
                    ).order_by('-created_at').first()
                    
                    # Compter les messages non lus
                    messages_non_lus = MessageDirect.objects.filter(
                        expediteur=contact,
                        destinataire=profil,
                        est_lu=False,
                        deleted=False
                    ).count()
                    
                    conversations.append({
                        'contact': contact,
                        'dernier_message': dernier_message,
                        'messages_non_lus': messages_non_lus,
                    })
                except Profil.DoesNotExist:
                    continue
            
            # Trier par date du dernier message
            conversations.sort(
                key=lambda x: x['dernier_message'].created_at if x['dernier_message'] else (datetime.min if not settings.USE_TZ else datetime.min.replace(tzinfo=timezone.utc)),
                reverse=True
            )
            
            logger.info(
                f"Conversations récentes récupérées - Utilisateur: {acting_user.id}, "
                f"Nombre: {len(conversations)}"
            )
            
            return conversations
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des conversations: {str(e)}")
            raise

    
    @staticmethod
    @transaction.atomic
    def marquer_conversation_lue(
        acting_user: User,
        expediteur_id: UUID,
        request=None
    ) -> int:
        """
        Marque tous les messages d'une conversation comme lus
        
        Args:
            acting_user: Utilisateur (destinataire)
            expediteur_id: ID de l'expéditeur
            request: Requête HTTP (optionnel)
        
        Returns:
            int: Nombre de messages marqués comme lus
        """
        try:
            profil = acting_user.profil
            expediteur = Profil.objects.get(
                id=expediteur_id,
                deleted=False
            )
            
            MessageDirect.marquer_conversation_comme_lue(expediteur, acting_user.profil)
            
            nb_messages = MessageDirect.objects.filter(
                expediteur=expediteur,
                destinataire=profil,
                est_lu=True,
                deleted=False
            ).count()
            
            logger.info(
                f"Conversation marquée comme lue - Entre: {expediteur.user.id} "
                f"et {acting_user.id}, "
                f"Messages: {nb_messages}"
            )
            
            return nb_messages
            
        except Profil.DoesNotExist:
            logger.error(f"Expéditeur introuvable: {expediteur_id}")
            raise ValidationError("Expéditeur introuvable")
        except Exception as e:
            logger.error(f"Erreur lors du marquage de la conversation: {str(e)}")
            raise


    
    @staticmethod
    def obtenir_statistiques_messages(
        acting_user: User,
        request=None
    ) -> Dict[str, Any]:
        """Obtient les statistiques de messagerie d'un utilisateur"""
        try:
            # Messages directs
            profil = acting_user.profil
            messages_directs_envoyes = MessageDirect.objects.filter(
                expediteur=profil,
                deleted=False
            ).count()
            
            messages_directs_recus = MessageDirect.objects.filter(
                destinataire=profil,
                deleted=False
            ).count()
            
            messages_non_lus = MessageDirect.get_non_lus_count(profil)
            
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
                    'envoyes': messages_directs_envoyes,
                    'recus': messages_directs_recus,
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
