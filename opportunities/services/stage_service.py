# opportunities/services/stage_service.py
import logging
from typing import List, Dict, Optional, Tuple
from uuid import UUID
from datetime import date
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from nanoid import generate

from core.models import User
from opportunities.models import Stage
from organizations.models import MembreOrganisation
from core.api.exceptions import (
    PermissionDeniedAPIException,
    NotFoundAPIException,
    BadRequestAPIException
)

logger = logging.getLogger('app')


class StageService:
    """Service contenant la logique métier pour la gestion des stages."""
    
    # ==========================================
    # PERMISSIONS & VÉRIFICATIONS
    # ==========================================
    
    @staticmethod
    def _is_site_admin(user: User) -> bool:
        """Vérifie si l'utilisateur est administrateur du site."""
        return user.role_systeme in ['admin_site', 'super_admin']
    
    @staticmethod
    def _is_partner(user: User) -> bool:
        """Vérifie si l'utilisateur est un partenaire (agit pour une organisation)."""
        return hasattr(user, 'profil') and user.profil.statut_global == 'partenaire'
    
    @staticmethod
    def _get_user_organisation(user: User):
        """Récupère l'organisation active du partenaire."""
        if not StageService._is_partner(user):
            return None
        
        try:
            membre = MembreOrganisation.objects.filter(
                profil=user.profil,
                est_actif=True
            ).select_related('organisation').first()
            return membre.organisation if membre else None
        except Exception:
            return None
    
    @staticmethod
    def _can_manage_stage(user: User, stage: Stage) -> bool:
        """Vérifie si l'utilisateur peut modifier/supprimer le stage."""
        # Admin du site peut tout gérer
        if StageService._is_site_admin(user):
            return True
        
        # Créateur peut gérer son stage
        if stage.createur_profil and stage.createur_profil.user.id == user.id:
            return True
        
        # Si le stage appartient à une organisation et que l'utilisateur est membre admin
        if stage.organisation:
            return MembreOrganisation.objects.filter(
                organisation=stage.organisation,
                profil__user=user,
                role_organisation='administrateur_page',
                est_actif=True
            ).exists()
        
        return False
    
    # ==========================================
    # UTILITAIRES
    # ==========================================
    
    @staticmethod
    def generate_unique_slug(base_name: str) -> str:
        """Génère un slug unique format : titre-stage-nanoId"""
        return slugify(f"{base_name}-{generate(size=6)}")
    
    @staticmethod
    def _auto_expire_stages():
        """Met à jour automatiquement les stages expirés."""
        today = date.today()
        Stage.objects.filter(
            date_fin__lt=today,
            statut='active'
        ).update(statut='expiree')
    
    # ==========================================
    # CRUD STAGES
    # ==========================================
    
    @staticmethod
    @transaction.atomic
    def create_stage(acting_user: User, data: Dict, request=None) -> Stage:
        """
        Crée un nouveau stage.
        
        Logique de validation :
        - Partenaire (organisation) : validation automatique, statut 'active'
        - Utilisateur normal : nécessite validation, statut 'en_attente'
        - Admin site : validation automatique, statut 'active'
        """
        is_partner = StageService._is_partner(acting_user)
        is_admin = StageService._is_site_admin(acting_user)
        
        # Déterminer le statut initial et la validation
        if is_partner or is_admin:
            initial_status = 'active'
            est_valide = True
        else:
            initial_status = 'en_attente'
            est_valide = False
        
        # Récupérer l'organisation si partenaire
        organisation = None
        if is_partner:
            organisation = StageService._get_user_organisation(acting_user)
            if not organisation:
                raise BadRequestAPIException(
                    "Vous devez être membre actif d'une organisation pour poster au nom d'une entreprise."
                )
        
        # Génération du slug unique
        success = False
        for attempt in range(3):
            try:
                slug = StageService.generate_unique_slug(data.get('titre'))
                new_stage = Stage.objects.create(
                    createur_profil=acting_user.profil,
                    organisation=organisation,
                    slug=slug,
                    statut=initial_status,
                    est_valide=est_valide,
                    **data
                )
                success = True
                break
            except Exception:
                continue
        
        if not success:
            raise BadRequestAPIException(
                "Impossible de générer un identifiant unique après plusieurs tentatives."
            )
        
        logger.info(
            f"Stage '{new_stage.titre}' (ID: {new_stage.id}) créé par {acting_user.email} "
            f"- Statut: {initial_status}, Validé: {est_valide}"
        )
        
        return new_stage
    
    @staticmethod
    def list_stages(
        filters: Dict = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Stage], int]:
        """
        Liste les stages avec filtres et pagination.
        
        Args:
            filters: Filtres (search, type_stage, lieu, ville, pays)
            page: Numéro de page
            page_size: Taille de page
            include_pending: Si True, inclut les stages en attente (admin uniquement)
        """
        StageService._auto_expire_stages()
        # Base queryset : stages validés et actifs
        queryset = Stage.objects.filter()
        queryset = queryset.select_related('createur_profil', 'organisation')
        
        # Application des filtres
        if filters:
            if search := filters.get('search'):
                queryset = queryset.filter(
                    Q(titre__icontains=search) |
                    Q(description__icontains=search) |
                    Q(nom_structure__icontains=search) |
                    Q(lieu__icontains=search)
                )
            
            if type_stage := filters.get('type_stage'):
                queryset = queryset.filter(type_stage=type_stage)
            
            if lieu := filters.get('lieu'):
                queryset = queryset.filter(lieu__icontains=lieu)
            
            if ville := filters.get('ville'):
                queryset = queryset.filter(ville__icontains=ville)
            
            if pays := filters.get('pays'):
                queryset = queryset.filter(pays__iexact=pays)
            
            if statut := filters.get('statut'):
                queryset = queryset.filter(statut=statut)
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        stages = list(queryset.order_by('-date_publication')[start:end])
        
        return stages, total_count

    @staticmethod
    def list_pending_stages(
        acting_user: User,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Stage], int]:
        """
        Liste les stages en attente de validation.
        Réservé aux administrateurs du site.
        """
        if not StageService._is_site_admin(acting_user):
            raise PermissionDeniedAPIException(
                "Vous n'avez pas la permission de voir les stages en attente."
            )
        StageService._auto_expire_stages()
        queryset = Stage.objects.filter(
            statut='en_attente',
            est_valide=False,
            deleted=False
        ).select_related('createur_profil', 'organisation').order_by('date_publication')
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        stages = list(queryset[start:end])
        
        return stages, total_count
    
    @staticmethod
    def get_stage_by_id(stage_id: UUID) -> Optional[Stage]:
        """Récupère un stage par son ID."""
        try:
            return Stage.objects.select_related(
                'createur_profil',
                'organisation',
                'validateur_profil'
            ).get(id=stage_id, deleted=False)
        except Stage.DoesNotExist:
            logger.warning(f"Stage non trouvé avec l'ID: {stage_id}")
            return None
    
    @staticmethod
    def get_stage_by_slug(slug: str) -> Optional[Stage]:
        """Récupère un stage par son slug."""
        try:
            return Stage.objects.select_related(
                'createur_profil',
                'organisation',
                'validateur_profil'
            ).get(slug=slug, deleted=False)
        except Stage.DoesNotExist:
            logger.warning(f"Stage non trouvé avec le slug: {slug}")
            return None
    
    @staticmethod
    @transaction.atomic
    def update_stage(
        acting_user: User,
        stage_id: UUID,
        data: Dict,
        request=None
    ) -> Stage:
        """
        Met à jour un stage.
        Seul le créateur, admin de l'organisation ou admin du site peut modifier.
        """
        stage = get_object_or_404(Stage, id=stage_id, deleted=False)
        
        if not StageService._can_manage_stage(acting_user, stage):
            raise PermissionDeniedAPIException(
                "Vous n'avez pas la permission de modifier ce stage."
            )
        
        # Gestion du slug
        if 'slug' in data:
            new_slug = slugify(data['slug'])
            if Stage.objects.filter(slug=new_slug).exclude(id=stage_id).exists():
                raise BadRequestAPIException(f"Le slug '{new_slug}' est déjà utilisé.")
            data['slug'] = new_slug
        
        for field, value in data.items():
            setattr(stage, field, value)
        
        stage.save()
        
        logger.info(
            f"Stage '{stage.titre}' (ID: {stage_id}) mis à jour par {acting_user.email}"
        )
        
        return stage
    
    @staticmethod
    @transaction.atomic
    def validate_stage(
        acting_user: User,
        stage_id: UUID,
        approved: bool,
        commentaire: Optional[str] = None,
        request=None
    ) -> Stage:
        """
        Valide ou rejette un stage.
        Réservé aux administrateurs du site.
        """
        if not StageService._is_site_admin(acting_user):
            raise PermissionDeniedAPIException(
                "Seuls les administrateurs peuvent valider les stages."
            )
        
        stage = get_object_or_404(Stage, id=stage_id, deleted=False)
        
        if stage.est_valide:
            raise BadRequestAPIException("Ce stage a déjà été validé.")
        
        stage.est_valide = approved
        stage.validateur_profil = acting_user.profil
        stage.date_validation = timezone.now()
        stage.commentaire_validation = commentaire
        
        if approved:
            stage.statut = 'active'
        else:
            stage.statut = 'rejetee'
        
        stage.save()
        
        action = "approuvé" if approved else "rejeté"
        logger.info(
            f"Stage '{stage.titre}' (ID: {stage_id}) {action} par {acting_user.email}"
        )
        
        return stage
    
    @staticmethod
    @transaction.atomic
    def update_stage_status(
        acting_user: User,
        stage_id: UUID,
        new_status: str,
        request=None
    ) -> Stage:
        """
        Met à jour le statut d'un stage (active, expiree, pourvue).
        Seul le gestionnaire du stage peut changer le statut.
        """
        stage = get_object_or_404(Stage, id=stage_id, deleted=False)
        
        if not StageService._can_manage_stage(acting_user, stage):
            raise PermissionDeniedAPIException(
                "Vous n'avez pas la permission de modifier ce stage."
            )
        
        valid_statuses = [choice[0] for choice in Stage.STATUT_CHOICES]
        if new_status not in valid_statuses:
            raise BadRequestAPIException(
                f"Statut invalide. Valides : {', '.join(valid_statuses)}"
            )
        
        old_status = stage.statut
        stage.statut = new_status
        stage.save()
        
        logger.info(
            f"Statut du stage '{stage.titre}' changé de '{old_status}' à '{new_status}' "
            f"par {acting_user.email}"
        )
        
        return stage
    
    @staticmethod
    @transaction.atomic
    def soft_delete_stage(acting_user: User, stage_id: UUID, request=None):
        """Suppression logique d'un stage."""
        stage = get_object_or_404(Stage, id=stage_id)
        
        if not StageService._can_manage_stage(acting_user, stage):
            raise PermissionDeniedAPIException(
                "Vous n'avez pas la permission de supprimer ce stage."
            )
        
        stage.soft_delete()
        
        logger.info(
            f"Stage '{stage.titre}' (ID: {stage_id}) supprimé par {acting_user.email}"
        )
    
    @staticmethod
    @transaction.atomic
    def restore_stage(acting_user: User, stage_id: UUID, request=None) -> Stage:
        """Restaure un stage supprimé. Réservé aux administrateurs."""
        if not StageService._is_site_admin(acting_user):
            raise PermissionDeniedAPIException(
                "Seuls les administrateurs peuvent restaurer un stage."
            )
        
        try:
            stage = Stage.all_objects.get(id=stage_id, deleted=True)
        except Stage.DoesNotExist:
            raise NotFoundAPIException("Stage supprimé introuvable.")
        
        stage.restore()
        
        logger.info(
            f"Stage '{stage.titre}' (ID: {stage_id}) restauré par {acting_user.email}"
        )
        
        return stage
    
    # ==========================================
    # STATISTIQUES
    # ==========================================
    
    @staticmethod
    def get_stage_statistics() -> Dict:
        """Retourne les statistiques globales des stages."""
        total_stages = Stage.objects.count()
        active_stages = Stage.objects.filter(statut='active', est_valide=True).count()
        pending_stages = Stage.objects.filter(statut='en_attente', est_valide=False).count()
        expired_stages = Stage.objects.filter(statut='expiree').count()
        pourvue_stages = Stage.objects.filter(statut='pourvue').count()
        
        stats_by_type = {}
        for type_stage, _ in Stage.TYPE_STAGE_CHOICES:
            stats_by_type[type_stage] = Stage.objects.filter(
                type_stage=type_stage,
                statut='active',
                est_valide=True
            ).count()
        
        return {
            'total_stages': total_stages,
            'active_stages': active_stages,
            'pending_stages': pending_stages,
            'expired_stages': expired_stages,
            'pourvue_stages': pourvue_stages,
            'by_type': stats_by_type
        }
    
    @staticmethod
    def get_user_stages(
        user: User,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Stage], int]:
        """Liste les stages créés par un utilisateur."""
        queryset = Stage.objects.filter(
            createur_profil__user=user,
            deleted=False
        ).select_related('organisation').order_by('-date_publication')
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        stages = list(queryset[start:end])
        
        return stages, total_count


# Instance singleton
stage_service = StageService()