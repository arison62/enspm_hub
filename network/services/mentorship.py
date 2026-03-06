# network/services/mentoring.py
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models
from django.utils import timezone
from django.db.models import Count, Avg

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
        disponibilite: str,
        nombre_max_mentees: int = 3,
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
                raise PermissionDenied("Seuls les alumni peuvent devenir mentors")
            
            # Vérifier si un profil mentor existe déjà
            if hasattr(acting_user, 'mentor_profile') and not profil.mentor_profile.deleted:
                logger.warning(f"Profil mentor déjà existant pour: {acting_user.id}")
                raise ValidationError("Un profil mentor existe déjà pour cet utilisateur")
            
            # Créer le profil mentor
            mentor_profile = MentorProfile.objects.create(
                profil=profil,
                biographie=biographie,
                disponibilite=disponibilite,
                nombre_max_mentees=nombre_max_mentees,
                est_actif=True
            )
            
            # Ajouter les filières d'expertise
            if filieres_expertise:
                filieres = Filiere.objects.filter(id__in=filieres_expertise, deleted=False)
                mentor_profile.filieres_expertise.set(filieres)
            
            # Ajouter les domaines d'expertise
            if domaines_expertise:
                domaines = Domaine.objects.filter(id__in=domaines_expertise, deleted=False)
                mentor_profile.domaines_expertise.set(domaines)
            
            logger.info(
                f"Profil mentor créé - ID: {mentor_profile.id}, "
                f"Alumni: {acting_user.id}, "
                f"Max mentees: {nombre_max_mentees}"
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
        disponibilite: Optional[str] = None,
        nombre_max_mentees: Optional[int] = None,
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
                raise PermissionDenied("Vous ne pouvez modifier que votre propre profil mentor")
            
            # Mettre à jour les champs
            if biographie is not None:
                mentor_profile.biographie = biographie
            if disponibilite is not None:
                mentor_profile.disponibilite = disponibilite
            if nombre_max_mentees is not None:
                mentor_profile.nombre_max_mentees = nombre_max_mentees
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
            raise ValidationError("Profil mentor introuvable")
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
                raise ValidationError(f"Statut invalide: {status}")

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
            action_type = 'MENTOR_VALIDATED' if status == MentorProfile.Status.VALIDE else 'MENTOR_REFUSED'
            NotificationService.creer_notification(
                destinataire=mentor_profile.profil,
                source=mentor_profile,
                action_type=action_type,
                category=Notification.Category.ADMIN,
                content=commentaire if status == MentorProfile.Status.REFUSE else None
            )

            logger.info(f"Profil mentor {mentor_profile_id} validé par {acting_user.id}. Nouveau statut: {status}")
            return mentor_profile

        except MentorProfile.DoesNotExist:
            raise ValidationError("Profil mentor introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la validation du profil mentor: {str(e)}")
            raise

    
    @staticmethod
    def rechercher_mentors(
        acting_user: User,
        filieres: Optional[List[UUID]] = None,
        domaines: Optional[List[UUID]] = None,
        disponible_uniquement: bool = True,
        request=None
    ) -> List[MentorProfile]:
        """
        Recherche des mentors selon des critères
        """
        try:
            queryset = MentorProfile.objects.filter(
                deleted=False,
                est_actif=True,
                status=MentorProfile.Status.VALIDE
            ).select_related('profil').prefetch_related(
                'filieres_expertise',
                'domaines_expertise'
            )
            
            # Filtrer par disponibilité
            if disponible_uniquement:
                queryset = queryset.filter(
                    nombre_mentees_actuels__lt=models.F('nombre_max_mentees')
                )
            
            # Filtrer par filières
            if filieres:
                queryset = queryset.filter(filieres_expertise__id__in=filieres).distinct()
            
            # Filtrer par domaines
            if domaines:
                queryset = queryset.filter(domaines_expertise__id__in=domaines).distinct()
            
            mentors = list(queryset)
            
            logger.info(
                f"Recherche de mentors - Utilisateur: {acting_user.id}, "
                f"Résultats: {len(mentors)}"
            )
            
            return mentors
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de mentors: {str(e)}")
            raise

    @staticmethod
    def obtenir_statistiques_mentor(
        acting_user: User,
        mentor_profile_id: UUID,
        request=None
    ) -> Dict[str, Any]:
        """Obtient les statistiques simplifiées d'un mentor"""
        try:
            
            mentor_profile = MentorProfile.objects.get(
                id=mentor_profile_id,
                deleted=False
            )
            
            stats = {
                'profil': {
                    'id': str(mentor_profile.id),
                    'nom': mentor_profile.profil.nom_complet,
                    'actif': mentor_profile.est_actif,
                    'status': mentor_profile.status,
                },
                'capacite': {
                    'max_mentees': mentor_profile.nombre_max_mentees,
                    'mentees_actuels': mentor_profile.nombre_mentees_actuels,
                    'places_disponibles': mentor_profile.get_nombre_places_disponibles(),
                }
            }
            
            logger.info(f"Statistiques simplifiées générées pour mentor: {mentor_profile.id}")
            
            return stats
            
        except MentorProfile.DoesNotExist:
            logger.error(f"Profil mentor introuvable: {mentor_profile_id}")
            raise ValidationError("Profil mentor introuvable")
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {str(e)}")
            raise
