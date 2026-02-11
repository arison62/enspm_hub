import logging
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from django.db import transaction
from django.db.models import F, Q, Count, Exists, OuterRef, Subquery, IntegerField
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.utils import timezone

from core.api.exceptions import (
    BaseAPIException,
    ValidationErrorAPIException,
    PermissionDeniedAPIException,
    NotFoundAPIException
)
from core.utils.base64_utils import Base64FileHandler
from core.models import User
from core.utils.generate_unique_slug import generate_unique_slug
from network.models.chat import (
    Groupe, MembreGroupe, DemandeAccesGroupe,
    Conversation, ConversationType, ConversationParticipant, Message, MessageType
)
from users.models import Profil
from network.events import event_bus, GroupeEvents
from network.api.schemas.chat import GroupeOut, MembreGroupeOut
from network.services.chat import ChatService

logger = logging.getLogger(__name__)

class GroupeService:
    
    @staticmethod
    @transaction.atomic
    def creer_groupe(
        acting_user: User,
        nom: str,
        description: Optional[str] = None,
        type_acces: str = Groupe.TypeAcces.PUBLIC,
        image_base64: Optional[str] = None,
        request=None
    ) -> Groupe:
        try:
            profil = acting_user.profil
            
            # Validation
            if type_acces not in Groupe.TypeAcces:
                raise ValidationErrorAPIException(f"Type d'accès invalide: {type_acces}")
            if len(nom) < 3 or len(nom) > 255:
                raise ValidationErrorAPIException("Le nom doit contenir entre 3 et 255 caractères")
            
            slug = generate_unique_slug(nom, Groupe)
            if not slug:
                raise BaseAPIException("Impossible de générer un slug unique")
            
            est_admin_site = acting_user.is_admin_user()

            groupe = Groupe.objects.create(
                nom=nom,
                slug=slug,
                description=description or "",
                type_acces=type_acces,
                createur=profil,
                status=Groupe.Status.ACTIF if est_admin_site else Groupe.Status.INACTIF
            )
            
            # Gérer l'image
            if image_base64:
                try:
                    handler = Base64FileHandler()
                    groupe.image = handler.handle(image_base64, filename_prefix='group_image')
                    groupe.save(update_fields=['image'])
                except Exception as e:
                    logger.warning(f"Erreur image groupe: {e}")

            # Créer la conversation liée
            conversation = Conversation.objects.create(
                type=ConversationType.GROUP,
                groupe=groupe
            )

            # Ajouter le créateur comme admin
            MembreGroupe.objects.create(
                groupe=groupe,
                profil=profil,
                role=MembreGroupe.Role.ADMIN
            )

            # Ajouter le créateur à la conversation
            ConversationParticipant.objects.create(
                conversation=conversation,
                profil=profil,
                role=MembreGroupe.Role.ADMIN
            )
            
            # Message système
            ChatService.envoyer_message_systeme(
                conversation,
                f"Le groupe '{nom}' a été créé par {profil.nom_complet}."
            )

            # Sérialisation
            serialized_data = GroupeOut.from_orm(groupe).model_dump(mode='json')

            # ÉVÉNEMENT
            event_bus.publish(GroupeEvents.groupe_cree(
                groupe_id=groupe.id,
                data=serialized_data
            ))

            return groupe
            
        except Exception as e:
            logger.error(f"Erreur création groupe: {e}", exc_info=True)
            raise

    @staticmethod
    @transaction.atomic
    def modifier_groupe(
        acting_user: User,
        groupe_id: UUID,
        **kwargs
    ) -> Groupe:
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.select_for_update().get(id=groupe_id, deleted=False)
            
            if not groupe.est_admin(profil):
                raise PermissionDeniedAPIException("Seul un admin peut modifier le groupe")
            
            fields = ['nom', 'description', 'type_acces', 'status', 'est_ferme']
            for field in fields:
                if field in kwargs and kwargs[field] is not None:
                    setattr(groupe, field, kwargs[field])
            
            if 'image_base64' in kwargs and kwargs['image_base64']:
                handler = Base64FileHandler()
                groupe.image = handler.handle(kwargs['image_base64'], filename_prefix='group_image')
                
            groupe.save()
            
            # Sérialisation
            serialized_data = GroupeOut.from_orm(groupe).model_dump(mode='json')

            # ÉVÉNEMENT
            event_bus.publish(GroupeEvents.groupe_modifie(
                groupe_id=groupe.id,
                data=serialized_data
            ))
            
            return groupe
        except Groupe.DoesNotExist:
            raise NotFoundAPIException("Groupe introuvable")

    @staticmethod
    @transaction.atomic
    def supprimer_groupe(acting_user: User, groupe_id: UUID) -> bool:
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.select_for_update().get(id=groupe_id, deleted=False)
            
            if not groupe.est_admin(profil) and not acting_user.is_admin_user():
                raise PermissionDeniedAPIException("Permissions insuffisantes")
            
            # Sérialisation
            serialized_data = GroupeOut.from_orm(groupe).model_dump(mode='json')

            groupe.soft_delete()

            # ÉVÉNEMENT
            event_bus.publish(GroupeEvents.groupe_desactive(
                groupe_id=groupe.id,
                data=serialized_data
            ))
            
            return True
        except Groupe.DoesNotExist:
            raise NotFoundAPIException("Groupe introuvable")

    @staticmethod
    @transaction.atomic
    def ajouter_membre_groupe(
        acting_user: User,
        groupe_id: UUID,
        profil_id: UUID,
        role: str = MembreGroupe.Role.MEMBRE
    ) -> MembreGroupe:
        try:
            admin_profil = acting_user.profil
            groupe = Groupe.objects.get(id=groupe_id, deleted=False)
            
            if not groupe.est_admin(admin_profil):
                raise PermissionDeniedAPIException("Action réservée aux admins")

            profil_to_add = Profil.objects.get(id=profil_id, deleted=False)
            
            if groupe.est_membre(profil_to_add):
                raise ValidationErrorAPIException("Utilisateur déjà membre")
            
            membre = MembreGroupe.objects.create(
                groupe=groupe,
                profil=profil_to_add,
                role=role
            )
            
            # Associer à la conversation
            conv, _ = Conversation.objects.get_or_create(
                groupe=groupe,
                defaults={'type': ConversationType.GROUP}
            )
            ConversationParticipant.objects.get_or_create(
                conversation=conv,
                profil=profil_to_add,
                defaults={'role': role}
            )
            
            # Message système
            ChatService.envoyer_message_systeme(
                conv,
                f"{profil_to_add.nom_complet} a été ajouté au groupe par {admin_profil.nom_complet}."
            )
            
            # Sérialisation
            serialized_data = MembreGroupeOut.from_orm(membre).model_dump(mode='json')

            # ÉVÉNEMENT
            event_bus.publish(GroupeEvents.utilisateur_ajoute(
                groupe_id=groupe.id,
                profil_id=profil_to_add.id,
                data=serialized_data
            ))
            
            return membre
        except Groupe.DoesNotExist:
            raise NotFoundAPIException("Groupe introuvable")
        except Profil.DoesNotExist:
            raise NotFoundAPIException("Profil introuvable")

    @staticmethod
    @transaction.atomic
    def quitter_groupe(acting_user: User, groupe_id: UUID) -> bool:
        try:
            profil = acting_user.profil
            membre = MembreGroupe.objects.get(groupe_id=groupe_id, profil=profil, deleted=False)
            
            # Sécurité admin unique
            if membre.role == MembreGroupe.Role.ADMIN:
                if MembreGroupe.objects.filter(groupe_id=groupe_id, role=MembreGroupe.Role.ADMIN, deleted=False).count() <= 1:
                    raise ValidationErrorAPIException("Vous êtes le dernier admin. Nommez un successeur ou fermez le groupe.")
            
            # Sérialisation avant suppression
            serialized_data = MembreGroupeOut.from_orm(membre).model_dump(mode='json')

            membre.soft_delete()
            
            # Retirer de la conversation (soft delete)
            ConversationParticipant.objects.filter(conversation__groupe_id=groupe_id, profil=profil).update(deleted=True, deleted_at=timezone.now())
            
            # Message système
            conv = Conversation.objects.filter(groupe_id=groupe_id).first()
            if conv:
                ChatService.envoyer_message_systeme(
                    conv,
                    f"{profil.nom_complet} a quitté le groupe."
                )
            
            # ÉVÉNEMENT
            event_bus.publish(GroupeEvents.utilisateur_a_quitte(
                groupe_id=groupe_id,
                profil_id=profil.id,
                data=serialized_data
            ))
            
            return True
        except MembreGroupe.DoesNotExist:
            raise ValidationErrorAPIException("Vous n'êtes pas membre de ce groupe")

    # Recherche et listage
    @staticmethod
    def list_groupes(
        acting_user: User,
        query: Optional[str] = None,
        type_acces: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Groupe], int]:
        profil = acting_user.profil
        est_admin = acting_user.is_admin_user()
        
        queryset = Groupe.objects.filter(deleted=False)
        if not est_admin:
            queryset = queryset.filter(status=Groupe.Status.ACTIF)
        
        if query:
            queryset = queryset.filter(Q(nom__icontains=query) | Q(description__icontains=query))
        if type_acces:
            queryset = queryset.filter(type_acces=type_acces)
            
        # Annotations optimisées
        queryset = queryset.annotate(
            is_member=Exists(MembreGroupe.objects.filter(groupe=OuterRef('pk'), profil=profil, deleted=False)),
            nb_members=Count('membres', filter=Q(membres__deleted=False))
        ).order_by('-nb_members', '-created_at')
        
        total = queryset.count()
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        return list(page_obj.object_list), total

    @staticmethod
    def obtenir_details_groupe(acting_user: User, groupe_id: UUID) -> Groupe:
        profil = acting_user.profil
        try:
            groupe = Groupe.objects.annotate(
                is_member=Exists(MembreGroupe.objects.filter(groupe=OuterRef('pk'), profil=profil, deleted=False)),
                is_admin=Exists(MembreGroupe.objects.filter(groupe=OuterRef('pk'), profil=profil, role=MembreGroupe.Role.ADMIN, deleted=False)),
                nb_members=Count('membres', filter=Q(membres__deleted=False))
            ).get(id=groupe_id, deleted=False)
            return groupe
        except Groupe.DoesNotExist:
            raise NotFoundAPIException("Groupe introuvable")

    @staticmethod
    @transaction.atomic
    def approuver_demande(acting_user: User, demande_id: UUID) -> MembreGroupe:
        try:
            admin_profil = acting_user.profil
            demande = DemandeAccesGroupe.objects.select_for_update().get(id=demande_id, deleted=False)
            
            if not demande.groupe.est_admin(admin_profil):
                raise PermissionDeniedAPIException("Permissions insuffisantes")
            
            demande.status = DemandeAccesGroupe.Status.APPROUVE
            demande.date_traitement = timezone.now()
            demande.traite_par = admin_profil
            demande.save()
            
            membre = MembreGroupe.objects.create(groupe=demande.groupe, profil=demande.demandeur)
            
            # Sync conversation
            conv, _ = Conversation.objects.get_or_create(groupe=demande.groupe, defaults={'type': ConversationType.GROUP})
            ConversationParticipant.objects.get_or_create(conversation=conv, profil=demande.demandeur)
            
            # Message système
            ChatService.envoyer_message_systeme(
                conv,
                f"{demande.demandeur.nom_complet} a rejoint le groupe."
            )

            # Sérialisation
            serialized_data = MembreGroupeOut.from_orm(membre).model_dump(mode='json')

            # ÉVÉNEMENT
            event_bus.publish(GroupeEvents.utilisateur_a_rejoint(
                groupe_id=demande.groupe.id,
                profil_id=demande.demandeur.id,
                data=serialized_data
            ))

            return membre
        except DemandeAccesGroupe.DoesNotExist:
            raise NotFoundAPIException("Demande introuvable")
