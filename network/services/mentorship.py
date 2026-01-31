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
    MentorProfile, DemandeMentoring, RelationMentorat,
    SessionMentorat, FeedbackMentorat
)
from core.models import Filiere, Domaine, User

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
        
        Args:
            acting_user: User de l'utilisateur qui crée le profil mentor
            biographie: Présentation et expérience de mentorat
            disponibilite: Disponibilité du mentor
            nombre_max_mentees: Nombre maximum de mentorés
            filieres_expertise: Liste des IDs de filières d'expertise
            domaines_expertise: Liste des IDs de domaines d'expertise
            request: Requête HTTP (optionnel)
        
        Returns:
            MentorProfile: Le profil mentor créé
        
        Raises:
            ValidationError: Si les données sont invalides
            PermissionDenied: Si l'utilisateur n'a pas les droits
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
    def rechercher_mentors(
        acting_user: User,
        filieres: Optional[List[UUID]] = None,
        domaines: Optional[List[UUID]] = None,
        disponible_uniquement: bool = True,
        request=None
    ) -> List[MentorProfile]:
        """
        Recherche des mentors selon des critères
        
        Args:
            acting_user: Utilisateur effectuant la recherche
            filieres: Liste des IDs de filières recherchées
            domaines: Liste des IDs de domaines recherchés
            disponible_uniquement: Filtrer uniquement les mentors ayant de la place
            request: Requête HTTP (optionnel)
        
        Returns:
            List[MentorProfile]: Liste des profils mentors correspondants
        """
        try:
            queryset = MentorProfile.objects.filter(
                deleted=False,
                est_actif=True
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


    
    # ============================================
    # GESTION DES DEMANDES DE MENTORING
    # ============================================
    
    @staticmethod
    @transaction.atomic
    def creer_demande_mentoring(
        acting_user: User,
        message: str,
        objectifs: Optional[str] = None,
        attentes: Optional[str] = None,
        disponibilite_souhaitee: Optional[str] = None,
        format_prefere: Optional[str] = None,
        mentor_cible_id: Optional[UUID] = None,
        filieres_ids: Optional[List[UUID]] = None,
        domaines_ids: Optional[List[UUID]] = None,
        request=None
    ) -> DemandeMentoring:
        """
        Crée une demande de mentoring (directe ou générale)
        
        Args:
            acting_user: Étudiant faisant la demande
            message: Message d'introduction
            objectifs: Objectifs de mentorat
            attentes: Attentes vis-à-vis du mentorat
            disponibilite_souhaitee: Disponibilité souhaitée
            format_prefere: Format préféré (visio, téléphone, etc.)
            mentor_cible_id: ID du mentor ciblé (demande directe)
            filieres_ids: IDs des filières (demande générale)
            domaines_ids: IDs des domaines (demande générale)
            request: Requête HTTP (optionnel)
        
        Returns:
            DemandeMentoring: La demande créée
        
        Raises:
            ValidationError: Si les données sont invalides
        """
        try:
            # Vérifier que l'utilisateur est un étudiant
            profil = acting_user.profil
            if not profil.est_etudiant():
                logger.warning(
                    f"Tentative de création de demande par non-étudiant: {acting_user.id}"
                )
                raise PermissionDenied("Seuls les étudiants peuvent faire des demandes de mentoring")
            
            # Validation des paramètres selon le mode
            mentor_cible = None
            if mentor_cible_id:
                # Mode demande directe
                if filieres_ids or domaines_ids:
                    raise ValidationError(
                        "Une demande directe ne peut pas spécifier de filières ou domaines"
                    )
                try:
                    mentor_cible = MentorProfile.objects.get(
                        id=mentor_cible_id,
                        deleted=False,
                        est_actif=True
                    )
                except MentorProfile.DoesNotExist:
                    raise ValidationError("Mentor introuvable ou inactif")
            else:
                # Mode demande générale
                if not filieres_ids and not domaines_ids:
                    raise ValidationError(
                        "Une demande générale doit spécifier au moins une filière ou un domaine"
                    )
            
            # Créer la demande
            demande = DemandeMentoring.objects.create(
                mentee=profil,
                mentor_cible=mentor_cible,
                message=message,
                objectifs=objectifs or "",
                attentes=attentes or "",
                disponibilite_souhaitee=disponibilite_souhaitee or "",
                format_prefere=format_prefere or "",
                status='EN_ATTENTE',
                date_expiration=timezone.now() + timedelta(days=7)
            )
            
            # Ajouter filières et domaines pour demande générale
            if filieres_ids:
                filieres = Filiere.objects.filter(id__in=filieres_ids, deleted=False)
                demande.filieres.set(filieres)
            
            if domaines_ids:
                domaines = Domaine.objects.filter(id__in=domaines_ids, deleted=False)
                demande.domaines.set(domaines)
            
            # Notifier les mentors pertinents
            if mentor_cible:
                # Demande directe - notifier le mentor ciblé
                demande.mentors_notifies.add(mentor_cible)
                mentor_cible.nombre_demandes_recues += 1
                mentor_cible.save()
                
                logger.info(
                    f"Demande directe créée - ID: {demande.id}, "
                    f"Mentee: {acting_user.id}, "
                    f"Mentor cible: {mentor_cible.profil.user.id}"
                )
            else:
                # Demande générale - notifier les mentors compatibles
                mentors_compatibles = MentoringService._trouver_mentors_compatibles(demande)
                for mentor in mentors_compatibles:
                    demande.mentors_notifies.add(mentor)
                    mentor.nombre_demandes_recues += 1
                    mentor.save()
                
                logger.info(
                    f"Demande générale créée - ID: {demande.id}, "
                    f"Mentee: {acting_user.id}, "
                    f"Mentors notifiés: {len(mentors_compatibles)}"
                )
            
            return demande
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la demande: {str(e)}")
            raise
        
    @staticmethod
    def _trouver_mentors_compatibles(demande: DemandeMentoring) -> List[MentorProfile]:
        """Trouve les mentors compatibles avec une demande générale"""
        mentors = MentorProfile.objects.filter(
            deleted=False,
            est_actif=True
        ).select_related('profil')
        
        # Filtrer les mentors ayant de la place
        mentors_disponibles = [m for m in mentors if m.a_de_la_place()]
        
        # Filtrer par compatibilité
        mentors_compatibles = [
            m for m in mentors_disponibles
            if m.est_compatible_avec_demande(demande)
        ]
        
        return mentors_compatibles
    
    
    @staticmethod
    @transaction.atomic
    def repondre_demande_mentoring(
        acting_user: User,
        demande_id: UUID,
        accepter: bool,
        reponse_message: Optional[str] = None,
        request=None
    ) -> DemandeMentoring:
        """
        Répond à une demande de mentoring (accepter ou refuser)
        
        Args:
            acting_user: Mentor répondant à la demande
            demande_id: ID de la demande
            accepter: True pour accepter, False pour refuser
            reponse_message: Message de réponse
            request: Requête HTTP (optionnel)
        
        Returns:
            DemandeMentoring: La demande mise à jour
        
        Raises:
            ValidationError: Si la demande ne peut pas être traitée
            PermissionDenied: Si l'utilisateur n'a pas les droits
        """
        try:
            profil = acting_user.profil
            demande = DemandeMentoring.objects.select_for_update().get(
                id=demande_id,
                deleted=False
            )
            
            # Vérifier que l'utilisateur est un mentor
            if not hasattr(profil, 'mentor_profile'):
                raise PermissionDenied("Vous devez être mentor pour répondre à une demande")
            
            mentor_profile = profil.mentor_profile
            
            # Vérifier que le mentor a été notifié de cette demande
            if not demande.mentors_notifies.filter(id=mentor_profile.id).exists():
                raise PermissionDenied("Cette demande ne vous est pas destinée")
            
            # Vérifier le statut de la demande
            if demande.status != 'EN_ATTENTE':
                raise ValidationError("Cette demande a déjà été traitée")
            
            if demande.est_expiree():
                demande.status = 'EXPIREE'
                demande.save()
                raise ValidationError("Cette demande a expiré")
            
            # Traiter la réponse
            demande.mentor_repondant = mentor_profile
            demande.reponse_message = reponse_message or ""
            demande.reponse_date = timezone.now()
            
            if accepter:
                # Vérifier que le mentor a de la place
                if not mentor_profile.a_de_la_place():
                    raise ValidationError("Vous avez atteint votre capacité maximale de mentorés")
                
                demande.status = 'ACCEPTEE'
                mentor_profile.nombre_demandes_acceptees += 1
                mentor_profile.nombre_mentees_actuels += 1
                mentor_profile.save()
                
                # Créer la relation de mentorat
                relation = RelationMentorat.objects.create(
                    mentor=mentor_profile,
                    mentee=demande.mentee,
                    demande_origine=demande,
                    objectifs=demande.objectifs,
                    statut='ACTIVE'
                )
                
                logger.info(
                    f"Demande acceptée - ID: {demande.id}, "
                    f"Mentor: {acting_user.id}, "
                    f"Relation créée: {relation.id}"
                )
            else:
                demande.status = 'REFUSEE'
                
                logger.info(
                    f"Demande refusée - ID: {demande.id}, "
                    f"Mentor: {acting_user.nom_complet}"
                )
            
            demande.save()
            
            return demande
            
        except DemandeMentoring.DoesNotExist:
            logger.error(f"Demande introuvable: {demande_id}")
            raise ValidationError("Demande introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la réponse à la demande: {str(e)}")
            raise
    
    @staticmethod
    @transaction.atomic
    def annuler_demande_mentoring(
        acting_user: User,
        demande_id: UUID,
        request=None
    ) -> DemandeMentoring:
        """Annule une demande de mentoring (par le mentee uniquement)"""
        try:
            profil = acting_user.profil
            demande = DemandeMentoring.objects.select_for_update().get(
                id=demande_id,
                deleted=False
            )
            
            # Vérifier que l'utilisateur est bien le mentee
            if demande.mentee != profil:
                raise PermissionDenied("Seul le demandeur peut annuler sa demande")
            
            # Vérifier le statut
            if demande.status != 'EN_ATTENTE':
                raise ValidationError("Seules les demandes en attente peuvent être annulées")
            
            demande.status = 'ANNULEE'
            demande.save()
            
            logger.info(
                f"Demande annulée - ID: {demande.id}, "
                f"Mentee: {acting_user.id}"
            )
            
            return demande
            
        except DemandeMentoring.DoesNotExist:
            logger.error(f"Demande introuvable: {demande_id}")
            raise ValidationError("Demande introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation de la demande: {str(e)}")
            raise
        

    
    # ============================================
    # GESTION DES RELATIONS DE MENTORAT
    # ============================================
    
    @staticmethod
    @transaction.atomic
    def modifier_relation_mentorat(
        acting_user: User,
        relation_id: UUID,
        objectifs: Optional[str] = None,
        statut: Optional[str] = None,
        date_fin_prevue: Optional[str] = None,
        notes_privees: Optional[str] = None,
        request=None
    ) -> RelationMentorat:
        """Modifie une relation de mentorat existante"""
        try:
            profil = acting_user.profil
            relation = RelationMentorat.objects.select_for_update().get(
                id=relation_id,
                deleted=False
            )
            
            # Vérifier les permissions
            est_mentor = relation.mentor.profil == profil
            est_mentee = relation.mentee == profil
            
            if not (est_mentor or est_mentee):
                raise PermissionDenied("Vous n'avez pas accès à cette relation")
            
            # Mettre à jour les champs
            if objectifs is not None:
                relation.objectifs = objectifs
            
            if date_fin_prevue is not None:
                from datetime import datetime
                relation.date_fin_prevue = datetime.fromisoformat(date_fin_prevue).date()
            
            if notes_privees is not None:
                if est_mentor:
                    relation.notes_privees_mentor = notes_privees
                else:
                    relation.notes_privees_mentee = notes_privees
            
            if statut is not None and est_mentor:
                # Seul le mentor peut changer le statut
                ancien_statut = relation.statut
                relation.statut = statut
                
                # Mettre à jour le compteur du mentor si nécessaire
                if ancien_statut == 'ACTIVE' and statut in ['TERMINEE', 'ANNULEE']:
                    relation.mentor.nombre_mentees_actuels -= 1
                    relation.mentor.save()
                    relation.date_fin_reelle = timezone.now().date()
            
            relation.save()
            
            logger.info(
                f"Relation modifiée - ID: {relation.id}, "
                f"Par: {acting_user.id}"
            )
            
            return relation
            
        except RelationMentorat.DoesNotExist:
            logger.error(f"Relation introuvable: {relation_id}")
            raise ValidationError("Relation introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la modification de la relation: {str(e)}")
            raise
    

    
    @staticmethod
    @transaction.atomic
    def terminer_relation_mentorat(
        acting_user: User,
        relation_id: UUID,
        raison: str = "",
        request=None
    ) -> RelationMentorat:
        """Termine une relation de mentorat"""
        try:
            profil = acting_user.profil
            relation = RelationMentorat.objects.select_for_update().get(
                id=relation_id,
                deleted=False
            )
            
            # Vérifier que l'utilisateur est le mentor
            if relation.mentor.profil != profil:
                raise PermissionDenied("Seul le mentor peut terminer la relation")
            
            if relation.statut not in ['ACTIVE', 'EN_PAUSE']:
                raise ValidationError("Cette relation est déjà terminée")
            
            relation.terminer(raison)
            
            logger.info(
                f"Relation terminée - ID: {relation.id}, "
                f"Mentor: {acting_user.id}, "
                f"Raison: {raison}"
            )
            
            return relation
            
        except RelationMentorat.DoesNotExist:
            logger.error(f"Relation introuvable: {relation_id}")
            raise ValidationError("Relation introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la terminaison de la relation: {str(e)}")
            raise

    
    # ============================================
    # GESTION DES SESSIONS
    # ============================================
    
    @staticmethod
    @transaction.atomic
    def creer_session_mentorat(
        acting_user: User,
        relation_id: UUID,
        date_prevue: datetime,
        duree_minutes: int = 60,
        type_session: str = 'VIDEO',
        lieu_ou_lien: Optional[str] = None,
        theme: Optional[str] = None,
        objectifs_session: Optional[str] = None,
        request=None
    ) -> SessionMentorat:
        """Crée une session de mentorat"""
        try:
            profil = acting_user.profil
            relation = RelationMentorat.objects.get(
                id=relation_id,
                deleted=False
            )
            
            # Vérifier les permissions
            if relation.mentor.profil != profil and relation.mentee != profil:
                raise PermissionDenied("Vous n'avez pas accès à cette relation")
            
            if relation.statut != 'ACTIVE':
                raise ValidationError("La relation doit être active pour planifier une session")
            
            # Créer la session
            session = SessionMentorat.objects.create(
                relation=relation,
                date_prevue=date_prevue,
                duree_minutes=duree_minutes,
                type_session=type_session,
                lieu_ou_lien=lieu_ou_lien or "",
                theme=theme or "",
                objectifs_session=objectifs_session or "",
                statut='PLANIFIEE'
            )
            
            logger.info(
                f"Session créée - ID: {session.id}, "
                f"Relation: {relation.id}, "
                f"Date: {date_prevue}, "
                f"Par: {acting_user.id}"
            )
            
            return session
            
        except RelationMentorat.DoesNotExist:
            logger.error(f"Relation introuvable: {relation_id}")
            raise ValidationError("Relation introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la création de la session: {str(e)}")
            raise
    
    @staticmethod
    @transaction.atomic
    def marquer_session_realisee(
        acting_user: User,
        session_id: UUID,
        notes: str = "",
        actions_suivantes: str = "",
        duree_reelle_minutes: Optional[int] = None,
        presence_mentee: bool = True,
        request=None
    ) -> SessionMentorat:
        """Marque une session comme réalisée"""
        try:
            profil = acting_user.profil
            session = SessionMentorat.objects.select_for_update().get(
                id=session_id,
                deleted=False
            )
            
            # Vérifier que l'utilisateur est le mentor
            if session.relation.mentor.profil != profil:
                raise PermissionDenied("Seul le mentor peut valider la session")
            
            if session.statut != 'PLANIFIEE':
                raise ValidationError("Cette session a déjà été traitée")
            
            session.marquer_realisee(notes, actions_suivantes)
            
            if duree_reelle_minutes is not None:
                session.duree_reelle_minutes = duree_reelle_minutes
            
            session.presence_mentee = presence_mentee
            session.save()
            
            logger.info(
                f"Session marquée réalisée - ID: {session.id}, "
                f"Présence mentee: {presence_mentee}"
            )
            
            return session
            
        except SessionMentorat.DoesNotExist:
            logger.error(f"Session introuvable: {session_id}")
            raise ValidationError("Session introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la validation de la session: {str(e)}")
            raise
    
    # ============================================
    # GESTION DES FEEDBACKS
    # ============================================
    
    @staticmethod
    @transaction.atomic
    def creer_feedback_mentorat(
        acting_user: User,
        relation_id: UUID,
        note: float,
        commentaires: str = "",
        recommanderait: bool = True,
        request=None
    ) -> FeedbackMentorat:
        """Crée un feedback sur une relation terminée"""
        try:
            profil = acting_user.profil
            relation = RelationMentorat.objects.get(
                id=relation_id,
                deleted=False
            )
            
            # Vérifier que l'utilisateur est concerné
            if relation.mentor.profil != profil and relation.mentee != profil:
                raise PermissionDenied("Vous n'avez pas accès à cette relation")
            
            # Vérifier que la relation est terminée
            if relation.statut != 'TERMINEE':
                raise ValidationError("La relation doit être terminée pour laisser un feedback")
            
            # Vérifier qu'un feedback n'existe pas déjà
            if FeedbackMentorat.objects.filter(
                relation=relation,
                auteur=profil,
                deleted=False
            ).exists():
                raise ValidationError("Vous avez déjà laissé un feedback pour cette relation")
            
            # Créer le feedback
            feedback = FeedbackMentorat.objects.create(
                relation=relation,
                auteur=profil,
                note=note,
                commentaires=commentaires,
                recommanderait=recommanderait
            )
            
            logger.info(
                f"Feedback créé - ID: {feedback.id}, "
                f"Relation: {relation.id}, "
                f"Note: {note}, "
                f"Par: {acting_user.id}"
            )
            
            return feedback
            
        except RelationMentorat.DoesNotExist:
            logger.error(f"Relation introuvable: {relation_id}")
            raise ValidationError("Relation introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la création du feedback: {str(e)}")
            raise

    
    @staticmethod
    def obtenir_statistiques_mentor(
        acting_user: User,
        mentor_profile_id: UUID,
        request=None
    ) -> Dict[str, Any]:
        """Obtient les statistiques d'un mentor"""
        try:
            
            mentor_profile = MentorProfile.objects.get(
                id=mentor_profile_id,
                deleted=False
            )
            
            # Calculer les statistiques
            relations = RelationMentorat.objects.filter(
                mentor=mentor_profile,
                deleted=False
            )
            
            feedbacks = FeedbackMentorat.objects.filter(
                relation__mentor=mentor_profile,
                deleted=False
            ).aggregate(
                moyenne_note=Avg('note'),
                total_feedbacks=Count('id')
            )
            
            stats = {
                'profil': {
                    'id': str(mentor_profile.id),
                    'nom': mentor_profile.profil.nom_complet,
                    'actif': mentor_profile.est_actif,
                },
                'demandes': {
                    'recues': mentor_profile.nombre_demandes_recues,
                    'acceptees': mentor_profile.nombre_demandes_acceptees,
                    'taux_acceptation': (
                        (mentor_profile.nombre_demandes_acceptees / mentor_profile.nombre_demandes_recues * 100)
                        if mentor_profile.nombre_demandes_recues > 0 else 0
                    ),
                },
                'relations': {
                    'actives': relations.filter(statut='ACTIVE').count(),
                    'terminees': relations.filter(statut='TERMINEE').count(),
                    'total': relations.count(),
                },
                'sessions': {
                    'total': SessionMentorat.objects.filter(
                        relation__mentor=mentor_profile,
                        deleted=False
                    ).count(),
                    'realisees': SessionMentorat.objects.filter(
                        relation__mentor=mentor_profile,
                        statut='REALISEE',
                        deleted=False
                    ).count(),
                },
                'feedback': {
                    'moyenne_note': round(feedbacks['moyenne_note'] or 0, 2),
                    'total_feedbacks': feedbacks['total_feedbacks'],
                },
                'capacite': {
                    'max_mentees': mentor_profile.nombre_max_mentees,
                    'mentees_actuels': mentor_profile.nombre_mentees_actuels,
                    'places_disponibles': mentor_profile.get_nombre_places_disponibles(),
                }
            }
            
            logger.info(f"Statistiques générées pour mentor: {mentor_profile.id}")
            
            return stats
            
        except MentorProfile.DoesNotExist:
            logger.error(f"Profil mentor introuvable: {mentor_profile_id}")
            raise ValidationError("Profil mentor introuvable")
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {str(e)}")
            raise
