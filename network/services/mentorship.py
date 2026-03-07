# network/services/mentoring.py
import logging
from typing import Optional, List
from uuid import UUID
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.db.models import Q
from django.core.paginator import Paginator

from core.api.exceptions import BaseAPIException, NotFoundAPIException, PermissionDeniedAPIException, ValidationErrorAPIException
from network.models.mentorship import (
    MentorProfile, MentorProfileValidation
)
from core.services.notification_service import NotificationService
from core.models import Filiere, Domaine, User, Notification

logger = logging.getLogger(__name__)



class MentoringService:
    """Service de gestion du système de mentoring"""
    
    # ============================================
    # GESTION DES PROFILS MENTOR
    # ============================================
    
    @staticmethod
    @transaction.atomic
    def creer_profil_mentor(
        acting_user: User,
        biographie: str,
        disponibilite: int,
        filieres_expertise: Optional[List[UUID]] = None,
        domaines_expertise: Optional[List[UUID]] = None,
        request=None
    ) -> MentorProfile:
        """
        Crée un profil mentor pour un alumni
        """
        try:
            # Vérifier que l'utilisateur est un alumni
            profil = acting_user.profil
            if not profil.est_alumni():
                logger.warning(f"Tentative de création de profil mentor par non-alumni: {acting_user.id}")
                raise PermissionDeniedAPIException("Seuls les alumni peuvent devenir mentors")
            
            # Vérifier si un profil mentor existe déjà
            if hasattr(acting_user, 'mentor_profile') and not profil.mentor_profile.deleted:
                logger.warning(f"Profil mentor déjà existant pour: {acting_user.id}")
                raise ValidationErrorAPIException("Un profil mentor existe déjà pour cet utilisateur")
            
            # Créer le profil mentor
            mentor_profile = MentorProfile.objects.create(
                profil=profil,
                biographie=biographie,
                disponibilite=disponibilite,
            )
            
            # Ajouter les filières d'expertise
            if filieres_expertise:
                filieres = Filiere.objects.filter(id__in=filieres_expertise, deleted=False)
                mentor_profile.filieres_expertise.set(filieres)
            
            # Ajouter les domaines d'expertise
            if domaines_expertise:
                domaines = Domaine.objects.filter(id__in=domaines_expertise, deleted=False)
                mentor_profile.domaines_expertise.set(domaines)
            
            if acting_user.is_admin_user():
                mentor_profile.status = MentorProfile.Status.VALIDE
                mentor_profile.est_actif = True
            else:
                mentor_profile.status = MentorProfile.Status.EN_ATTENTE
                mentor_profile.est_actif = False
            
            mentor_profile.save()
            
            logger.info(
                f"Profil mentor créé - ID: {mentor_profile.id}, "
                f"Alumni: {acting_user.id}, "
            )
            
            return mentor_profile
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du profil mentor: {str(e)}")
            raise
        

    @staticmethod
    @transaction.atomic
    def modifier_profil_mentor(
        acting_user: User,
        mentor_profile_id: UUID,
        biographie: Optional[str] = None,
        disponibilite: Optional[int] = None,
        est_actif: Optional[bool] = None,
        filieres_expertise: Optional[List[UUID]] = None,
        domaines_expertise: Optional[List[UUID]] = None,
        request=None
    ) -> MentorProfile:
        """Modifie un profil mentor existant"""
        try:
            profil = acting_user.profil
            mentor_profile = MentorProfile.objects.select_for_update().get(
                id=mentor_profile_id,
                deleted=False
            )
            
            # Vérifier les permissions
            if mentor_profile.profil != profil:
                logger.warning(
                    f"Tentative de modification non autorisée du profil mentor {mentor_profile_id} "
                    f"par {acting_user.id}"
                )
                raise PermissionDeniedAPIException("Vous ne pouvez modifier que votre propre profil mentor")
            
            # Mettre à jour les champs
            if biographie is not None:
                mentor_profile.biographie = biographie
            if disponibilite is not None:
                mentor_profile.disponibilite = disponibilite
                
            if est_actif is not None:
                mentor_profile.est_actif = est_actif
            
            mentor_profile.save()
            
            # Mettre à jour les expertises
            if filieres_expertise is not None:
                filieres = Filiere.objects.filter(id__in=filieres_expertise, deleted=False)
                mentor_profile.filieres_expertise.set(filieres)
            
            if domaines_expertise is not None:
                domaines = Domaine.objects.filter(id__in=domaines_expertise, deleted=False)
                mentor_profile.domaines_expertise.set(domaines)
            
            logger.info(f"Profil mentor modifié - ID: {mentor_profile.id}")
            
            return mentor_profile
            
        except MentorProfile.DoesNotExist:
            logger.error(f"Profil mentor introuvable: {mentor_profile_id}")
            raise ValidationErrorAPIException("Profil mentor introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la modification du profil mentor: {str(e)}")
            raise
        
    @staticmethod
    @transaction.atomic
    def valider_profil_mentor(
        acting_user: User,
        mentor_profile_id: UUID,
        status: str,
        commentaire: str = "",
        request=None
    ) -> MentorProfile:
        """
        Valide ou refuse un profil mentor (Action Admin)
        """
        try:
            if not acting_user.is_admin_user():
                raise PermissionDenied("Seuls les administrateurs peuvent valider les profils mentors")

            mentor_profile = MentorProfile.objects.select_for_update().get(
                id=mentor_profile_id,
                deleted=False
            )

            if status not in MentorProfile.Status.values:
                raise ValidationErrorAPIException("Statut non valide")

            status_avant = mentor_profile.status
            mentor_profile.status = status
            mentor_profile.save()

            # Créer l'historique de validation
            MentorProfileValidation.objects.create(
                mentor_profile=mentor_profile,
                status_avant=status_avant,
                status_apres=status,
                commentaire=commentaire,
                valide_par=acting_user.profil
            )

            # Déclencher la notification
            if status == MentorProfile.Status.VALIDE:
                action_type = 'MENTOR_VALIDATED'
                title = "Profil Mentor Validé"
                content = "Félicitations ! Votre profil mentor a été validé par l'administration."
            else:
                action_type = 'MENTOR_REFUSED'
                title = "Profil Mentor Refusé"
                content = commentaire or "Votre profil mentor a été refusé par l'administration."

            NotificationService.creer_notification(
                destinataire=mentor_profile.profil,
                source=mentor_profile,
                action_type=action_type,
                title=title,
                content=content,
                category=Notification.Category.ADMIN,
                link=f"/network/mentors/{mentor_profile.id}",
            )

            logger.info(f"Profil mentor {mentor_profile_id} validé par {acting_user.id}. Nouveau statut: {status}")
            return mentor_profile

        except MentorProfile.DoesNotExist:
            raise NotFoundAPIException("Profil mentor introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la validation du profil mentor: {str(e)}")
            raise BaseAPIException("Erreur lors de la validation du profil mentor")

    
    @staticmethod
    def obtenir_mentors(
        acting_user: User,
        filieres: Optional[List[UUID]] = None,
        domaines: Optional[List[UUID]] = None,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        request=None
    ) -> tuple[List[MentorProfile], int]:
        """
        Recherche des mentors selon des critères
        """
        query = dict()
        if not acting_user.is_admin_user():
            query['est_actif'] = True
            query['satus'] = MentorProfile.Status.VALIDE
        try:
            queryset = MentorProfile.objects.filter(
                **query
            ).select_related('profil').prefetch_related(
                'filieres_expertise',
                'domaines_expertise'
            )
            
            if search:
                queryset = queryset.filter(
                    Q(profil__nom_complet__icontains=search) |
                    Q(biographie__icontains=search) |
                    Q(disponibilite__icontains=search)
                ).distinct()
            # Filtrer par filières
            if filieres:
                queryset = queryset.filter(filieres_expertise__id__in=filieres).distinct()
            
            # Filtrer par domaines
            if domaines:
                queryset = queryset.filter(domaines_expertise__id__in=domaines).distinct()
            
            # Pagination
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            mentors = list(page_obj.object_list)
            
            logger.info(
                f"Recherche de mentors - Utilisateur: {acting_user.id}, "
                f"Résultats: {len(mentors)}"
            )
            
            return mentors, paginator.count
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de mentors: {str(e)}")
            raise

    @staticmethod
    @transaction.atomic
    def supprimer_profil_mentor(
        acting_user: User,
        mentor_profile_id: UUID,
        request=None
    ):
        """
        Supprimer un profil mentor.
        Seul le mentor lui-même ou un administrateur peut effectuer l'action.
        """
        try:
            mentor_profile = MentorProfile.objects.select_for_update().select_related(
                "profil__user"
            ).get(
                id=mentor_profile_id,
                deleted=False
            )

            # Vérification des permissions
            is_owner = mentor_profile.profil.id == acting_user.profil.id
            is_admin = acting_user.is_admin_user()

            if not (is_owner or is_admin):
                raise PermissionDeniedAPIException(
                    "Vous n'avez pas la permission de supprimer ce profil mentor"
                )

            mentor_profile.deleted = True
            mentor_profile.save(update_fields=["deleted", "updated_at"])

            logger.info(
                f"Profil mentor {mentor_profile_id} supprimé par utilisateur {acting_user.id}"
            )

            return mentor_profile

        except MentorProfile.DoesNotExist:
            raise NotFoundAPIException("Profil mentor introuvable")

        except PermissionDeniedAPIException:
            raise

        except Exception as e:
            logger.error(
                f"Erreur lors de la suppression du profil mentor {mentor_profile_id}: {str(e)}"
            )
            raise BaseAPIException("Erreur lors de la suppression du profil mentor")
