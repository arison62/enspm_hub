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
from network.api.schemas.chat import GroupeOut, MembreGroupeOut, MembreGroupeRequest
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
            membre = MembreGroupe.objects.create(
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
            
            # Sérialisation (dernière version avant suppression logique)
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
    def obtenir_mes_groupes(
        acting_user: User,
        role: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Groupe], int]:
        profil = acting_user.profil
        membres_queryset = MembreGroupe.objects.filter(profil=profil, deleted=False)
        if role:
            membres_queryset = membres_queryset.filter(role=role)

        groupe_ids = membres_queryset.values_list('groupe_id', flat=True)
        queryset = Groupe.objects.filter(id__in=groupe_ids, deleted=False, status=Groupe.Status.ACTIF).order_by('-created_at')
        
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
    def obtenir_membres_groupe(
        acting_user: User,
        groupe_id: UUID,
        page: int = 1,
        page_size: int = 20,
        query: Optional[str] = None
    ) -> tuple[List[MembreGroupe], int]:
        try:
            groupe = Groupe.objects.get(id=groupe_id, deleted=False)
            queryset = MembreGroupe.objects.filter(groupe=groupe, deleted=False).select_related('profil')
            if query:
                queryset = queryset.filter(profil__nom_complet__icontains=query)

            total = queryset.count()
            paginator = Paginator(queryset.order_by('role', '-created_at'), page_size)
            page_obj = paginator.get_page(page)

            return list(page_obj.object_list), total
        except Groupe.DoesNotExist:
            raise NotFoundAPIException("Groupe introuvable")

    @staticmethod
    @transaction.atomic
    def rejoindre_groupe_public(acting_user: User, groupe_id: UUID) -> MembreGroupe:
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.get(id=groupe_id, deleted=False, status=Groupe.Status.ACTIF)

            if groupe.type_acces != Groupe.TypeAcces.PUBLIC:
                raise PermissionDeniedAPIException("Ce groupe est privé")

            if groupe.est_membre(profil):
                raise ValidationErrorAPIException("Déjà membre")

            membre = MembreGroupe.objects.create(groupe=groupe, profil=profil, role=MembreGroupe.Role.MEMBRE)

            # Sync conversation
            conv, _ = Conversation.objects.get_or_create(groupe=groupe, defaults={'type': ConversationType.GROUP})
            ConversationParticipant.objects.get_or_create(conversation=conv, profil=profil)

            ChatService.envoyer_message_systeme(conv, f"{profil.nom_complet} a rejoint le groupe.")

            # ÉVÉNEMENT
            serialized_data = MembreGroupeOut.from_orm(membre).model_dump(mode='json')
            event_bus.publish(GroupeEvents.utilisateur_a_rejoint(groupe.id, profil.id, serialized_data))

            return membre
        except Groupe.DoesNotExist:
            raise NotFoundAPIException("Groupe introuvable")

    @staticmethod
    @transaction.atomic
    def creer_demande_acces(acting_user: User, groupe_id: UUID, message: Optional[str] = None) -> DemandeAccesGroupe:
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.get(id=groupe_id, deleted=False, status=Groupe.Status.ACTIF)

            if groupe.type_acces != Groupe.TypeAcces.PRIVE:
                raise ValidationErrorAPIException("Groupe non privé")

            if groupe.est_membre(profil):
                raise ValidationErrorAPIException("Déjà membre")

            demande, created = DemandeAccesGroupe.objects.get_or_create(
                groupe=groupe,
                demandeur=profil,
                status=DemandeAccesGroupe.Status.EN_ATTENTE,
                deleted=False,
                defaults={'message': message or ""}
            )

            if not created:
                raise ValidationErrorAPIException("Demande déjà en cours")

            return demande
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
            
            if demande.status != DemandeAccesGroupe.Status.EN_ATTENTE:
                raise ValidationErrorAPIException("Demande déjà traitée")

            demande.status = DemandeAccesGroupe.Status.APPROUVE
            demande.date_traitement = timezone.now()
            demande.traite_par = admin_profil
            demande.save()
            
            membre = MembreGroupe.objects.create(groupe=demande.groupe, profil=demande.demandeur)
            
            conv, _ = Conversation.objects.get_or_create(groupe=demande.groupe, defaults={'type': ConversationType.GROUP})
            ConversationParticipant.objects.get_or_create(conversation=conv, profil=demande.demandeur)
            
            ChatService.envoyer_message_systeme(conv, f"{demande.demandeur.nom_complet} a rejoint le groupe.")

            serialized_data = MembreGroupeOut.from_orm(membre).model_dump(mode='json')
            event_bus.publish(GroupeEvents.utilisateur_a_rejoint(demande.groupe.id, demande.demandeur.id, serialized_data))

            return membre
        except DemandeAccesGroupe.DoesNotExist:
            raise NotFoundAPIException("Demande introuvable")

    @staticmethod
    @transaction.atomic
    def refuser_demande(acting_user: User, demande_id: UUID) -> DemandeAccesGroupe:
        try:
            admin_profil = acting_user.profil
            demande = DemandeAccesGroupe.objects.select_for_update().get(id=demande_id, deleted=False)

            if not demande.groupe.est_admin(admin_profil):
                raise PermissionDeniedAPIException("Permissions insuffisantes")

            demande.status = DemandeAccesGroupe.Status.REFUSE
            demande.date_traitement = timezone.now()
            demande.traite_par = admin_profil
            demande.save()

            return demande
        except DemandeAccesGroupe.DoesNotExist:
            raise NotFoundAPIException("Demande introuvable")

    @staticmethod
    @transaction.atomic
    def annuler_demande(acting_user: User, groupe_id: UUID) -> bool:
        try:
            profil = acting_user.profil
            demande = DemandeAccesGroupe.objects.get(groupe_id=groupe_id, demandeur=profil, status=DemandeAccesGroupe.Status.EN_ATTENTE, deleted=False)
            demande.soft_delete()
            return True
        except DemandeAccesGroupe.DoesNotExist:
            raise NotFoundAPIException("Demande introuvable")

    @staticmethod
    def obtenir_demandes_groupe(
        acting_user: User,
        groupe_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[DemandeAccesGroupe], int]:
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.get(id=groupe_id, deleted=False)
            if not groupe.est_admin(profil):
                raise PermissionDeniedAPIException("Permissions insuffisantes")

            queryset = DemandeAccesGroupe.objects.filter(groupe=groupe, deleted=False).select_related('demandeur')
            if status:
                queryset = queryset.filter(status=status)

            total = queryset.count()
            paginator = Paginator(queryset.order_by('-created_at'), page_size)
            page_obj = paginator.get_page(page)

            return list(page_obj.object_list), total
        except Groupe.DoesNotExist:
            raise NotFoundAPIException("Groupe introuvable")

    @staticmethod
    def obtenir_mes_demandes(
        acting_user: User,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[DemandeAccesGroupe], int]:
        profil = acting_user.profil
        queryset = DemandeAccesGroupe.objects.filter(demandeur=profil, deleted=False).select_related('groupe')
        if status:
            queryset = queryset.filter(status=status)

        total = queryset.count()
        paginator = Paginator(queryset.order_by('-created_at'), page_size)
        page_obj = paginator.get_page(page)

        return list(page_obj.object_list), total

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

            membre = MembreGroupe.objects.create(groupe=groupe, profil=profil_to_add, role=role)

            conv, _ = Conversation.objects.get_or_create(groupe=groupe, defaults={'type': ConversationType.GROUP})
            ConversationParticipant.objects.get_or_create(conversation=conv, profil=profil_to_add, defaults={'role': role})

            ChatService.envoyer_message_systeme(conv, f"{profil_to_add.nom_complet} a été ajouté au groupe par {admin_profil.nom_complet}.")

            serialized_data = MembreGroupeOut.from_orm(membre).model_dump(mode='json')
            event_bus.publish(GroupeEvents.utilisateur_ajoute(groupe.id, profil_to_add.id, serialized_data))

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

            if membre.role == MembreGroupe.Role.ADMIN:
                if MembreGroupe.objects.filter(groupe_id=groupe_id, role=MembreGroupe.Role.ADMIN, deleted=False).count() <= 1:
                    raise ValidationErrorAPIException("Dernier admin")

            serialized_data = MembreGroupeOut.from_orm(membre).model_dump(mode='json')
            membre.soft_delete()
            ConversationParticipant.objects.filter(conversation__groupe_id=groupe_id, profil=profil).update(deleted=True, deleted_at=timezone.now())

            conv = Conversation.objects.filter(groupe_id=groupe_id).first()
            if conv:
                ChatService.envoyer_message_systeme(conv, f"{profil.nom_complet} a quitté le groupe.")

            event_bus.publish(GroupeEvents.utilisateur_a_quitte(groupe_id, profil.id, serialized_data))
            return True
        except MembreGroupe.DoesNotExist:
            raise ValidationErrorAPIException("Non membre")

    @staticmethod
    @transaction.atomic
    def modifier_membre_groupe(acting_user: User, groupe_id: UUID, membre_id: UUID, role: str) -> MembreGroupe:
        try:
            admin_profil = acting_user.profil
            groupe = Groupe.objects.get(id=groupe_id, deleted=False)
            if not groupe.est_admin(admin_profil):
                raise PermissionDeniedAPIException("Non admin")

            membre = MembreGroupe.objects.get(groupe=groupe, profil_id=membre_id, deleted=False)
            membre.role = role
            membre.save()

            # Sync conversation role
            ConversationParticipant.objects.filter(conversation__groupe=groupe, profil_id=membre_id).update(role=role)

            serialized_data = MembreGroupeOut.from_orm(membre).model_dump(mode='json')
            event_bus.publish(GroupeEvents.role_modifie(groupe.id, membre_id, serialized_data))

            return membre
        except (Groupe.DoesNotExist, MembreGroupe.DoesNotExist):
            raise NotFoundAPIException("Membre ou groupe introuvable")

    @staticmethod
    @transaction.atomic
    def retirer_membre_groupe(acting_user: User, groupe_id: UUID, profil_id: UUID) -> bool:
        try:
            admin_profil = acting_user.profil
            groupe = Groupe.objects.get(id=groupe_id, deleted=False)
            if not groupe.est_admin(admin_profil):
                raise PermissionDeniedAPIException("Non admin")

            membre = MembreGroupe.objects.get(groupe=groupe, profil_id=profil_id, deleted=False)

            if membre.role == MembreGroupe.Role.ADMIN:
                if MembreGroupe.objects.filter(groupe_id=groupe_id, role=MembreGroupe.Role.ADMIN, deleted=False).count() <= 1:
                    raise ValidationErrorAPIException("Dernier admin")

            serialized_data = MembreGroupeOut.from_orm(membre).model_dump(mode='json')
            membre.soft_delete()
            ConversationParticipant.objects.filter(conversation__groupe=groupe, profil_id=profil_id).update(deleted=True, deleted_at=timezone.now())

            conv = Conversation.objects.filter(groupe_id=groupe_id).first()
            if conv:
                ChatService.envoyer_message_systeme(conv, f"{membre.profil.nom_complet} a été retiré du groupe par {admin_profil.nom_complet}.")

            event_bus.publish(GroupeEvents.utilisateur_retire(groupe.id, profil_id, serialized_data))
            return True
        except (Groupe.DoesNotExist, MembreGroupe.DoesNotExist):
            raise NotFoundAPIException("Membre ou groupe introuvable")
