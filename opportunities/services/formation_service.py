
# opportunities/services/formation_service.py
import logging
from typing import List, Dict, Optional, Tuple
from uuid import UUID
from datetime import date
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify


from core.models import User
from opportunities.models import Formation
from organizations.models import MembreOrganisation
from core.api.exceptions import (
    PermissionDeniedAPIException,
    BadRequestAPIException
)
from core.utils.generate_unique_slug import generate_unique_slug
logger = logging.getLogger('app')


class FormationService:
    """Service pour la gestion des formations."""
    
    @staticmethod
    def _is_site_admin(user: User) -> bool:
        return user.role_systeme in ['admin_site', 'super_admin']
    
    @staticmethod
    def _is_partner(user: User) -> bool:
        return hasattr(user, 'profil') and user.profil.statut_global == 'partenaire'
    
    @staticmethod
    def _get_user_organisation(user: User):
        if not FormationService._is_partner(user):
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
    def _can_manage_formation(user: User, formation: Formation) -> bool:
        if FormationService._is_site_admin(user):
            return True
        if formation.createur_profil and formation.createur_profil.user.id == user.id:
            return True
        if formation.organisation:
            return MembreOrganisation.objects.filter(
                organisation=formation.organisation,
                profil__user=user,
                role_organisation='administrateur_page',
                est_actif=True
            ).exists()
        return False
    

    
    @staticmethod
    def _auto_expire_formations():
        """Met à jour automatiquement les formations expirées."""
        today = date.today()
        Formation.objects.filter(
            date_fin__lt=today,
            statut='active'
        ).update(statut='expiree')
    
    @staticmethod
    @transaction.atomic
    def create_formation(acting_user: User, data: Dict, request=None) -> Formation:
        """Crée une nouvelle formation."""
        is_partner = FormationService._is_partner(acting_user)
        is_admin = FormationService._is_site_admin(acting_user)
        
        if is_partner or is_admin:
            initial_status = 'active'
            est_valide = True
        else:
            initial_status = 'en_attente'
            est_valide = False
        
        organisation = None
        if is_partner:
            organisation = FormationService._get_user_organisation(acting_user)
            if not organisation:
                raise BadRequestAPIException(
                    "Vous devez être membre actif d'une organisation."
                )
        
        slug = generate_unique_slug(data['titre'][:50], Formation)
        
        if not slug:
            raise BadRequestAPIException("Impossible de générer un identifiant unique.")
        try:
                    
            new_formation = Formation.objects.create(
                createur_profil=acting_user.profil,
                organisation=organisation,
                slug=slug,
                statut=initial_status,
                est_valide=est_valide,
                **data
            )
            logger.info(f"Formation '{new_formation.titre}' crée par {acting_user.email}")
            return new_formation
        except Exception as e:
            logger.error(
                f"Une erreur est survenue lors de la création de la formation {data.get('titre')} par {acting_user.email}: {str(e)} "
            )   

            raise BadRequestAPIException(f"Une erreur est survenue: {str(e)}") 

        


    
    @staticmethod
    def list_formations(
        filters: Optional[Dict] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Formation], int]:
        """Liste les formations avec filtres."""

        page = max(1, int(page)) if page else 1
        page_size = min(max(1, int(page_size)), 100)
        
        FormationService._auto_expire_formations()
        
        queryset = Formation.objects.filter(
            deleted=False
        )
        
        queryset = queryset.select_related('createur_profil', 'organisation')
        
        if filters:
            # Filtre de recherche
            if search := filters.get('search'):
                search = str(search).strip()
                if search:
                    # Utiliser un Q object combine avec annotation pour meilleur performance
                    search_terms = search.split()
                    q_object = Q()
                    for term in search_terms:
                        q_object |= Q(titre__icontains=term)
                        q_object |= Q(description__icontains=term)
                        q_object |= Q(nom_structure__icontains=term)

                    queryset = queryset.filter(q_object).distinct()
            # adresse > ville > pays
                    
            if lieu := filters.get('lieu'):
                lieu = str(lieu).strip()
                if lieu:
                    queryset = queryset.filter(
                        Q(adresse__icontains=lieu) | 
                        Q(ville__icontains=lieu) | 
                        Q(pays__iexact=lieu)
                    ).distinct()

                
            if type_formation := filters.get('type_formation'):
                if isinstance(type_formation, list):
                    queryset = queryset.filter(type_formation__in=type_formation)
                else:
                    queryset = queryset.filter(type_formation=type_formation)
            
            if est_payante := filters.get('est_payante'):
                if isinstance(est_payante, list):
                    queryset = queryset.filter(est_payante__in=est_payante)
                else:
                    queryset = queryset.filter(est_payante=est_payante)
            if statut := filters.get("statut"):
                if isinstance(statut, list):
                    queryset = queryset.filter(statut__in=statut)
                else:
                    queryset = queryset.filter(statut=statut)
                
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        formations = list(queryset.order_by('-date_publication')[start:end])
        
        return formations, total_count
    
    @staticmethod
    def list_pending_formations(
        acting_user: User,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Formation], int]:
        """Liste les formations en attente."""
        if not FormationService._is_site_admin(acting_user):
            raise PermissionDeniedAPIException(
                "Vous n'avez pas la permission de voir les formations en attente."
            )
        
        queryset = Formation.objects.filter(
            statut='en_attente',
            est_valide=False,
            deleted=False
        ).select_related('createur_profil', 'organisation').order_by('date_publication')
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        formations = list(queryset[start:end])
        
        return formations, total_count
    
    @staticmethod
    def get_formation_by_id(formation_id: UUID) -> Optional[Formation]:
        try:
            return Formation.objects.select_related(
                'createur_profil',
                'organisation',
                'validateur_profil',
                'devise'
            ).get(id=formation_id, deleted=False)
        except Formation.DoesNotExist:
            return None
    
    @staticmethod
    def get_formation_by_slug(slug: str) -> Optional[Formation]:
        try:
            return Formation.objects.select_related(
                'createur_profil',
                'organisation',
                'validateur_profil',
                'devise'
            ).get(slug=slug, deleted=False)
        except Formation.DoesNotExist:
            return None
    
    @staticmethod
    @transaction.atomic
    def update_formation(
        acting_user: User,
        formation_id: UUID,
        data: Dict,
        request=None
    ) -> Formation:
        """Met à jour une formation."""
        formation = get_object_or_404(Formation, id=formation_id, deleted=False)
        
        if not FormationService._can_manage_formation(acting_user, formation):
            raise PermissionDeniedAPIException(
                "Vous n'avez pas la permission de modifier cette formation."
            )
        
        if 'slug' in data:
            new_slug = slugify(data['slug'])
            if Formation.objects.filter(slug=new_slug).exclude(id=formation_id).exists():
                raise BadRequestAPIException(f"Le slug '{new_slug}' est déjà utilisé.")
            data['slug'] = new_slug
        
        for field, value in data.items():
            setattr(formation, field, value)
        
        formation.save()
        
        logger.info(f"Formation '{formation.titre}' mise à jour par {acting_user.email}")
        
        return formation
    
    @staticmethod
    @transaction.atomic
    def validate_formation(
        acting_user: User,
        formation_id: UUID,
        approved: bool,
        commentaire: Optional[str] = None,
        request=None
    ) -> Formation:
        """Valide ou rejette une formation."""
        if not FormationService._is_site_admin(acting_user):
            raise PermissionDeniedAPIException(
                "Seuls les administrateurs peuvent valider les formations."
            )
        
        formation = get_object_or_404(Formation, id=formation_id, deleted=False)
        
        if formation.est_valide:
            raise BadRequestAPIException("Cette formation a déjà été validée.")
        
        formation.est_valide = approved
        formation.validateur_profil = acting_user.profil
        formation.date_validation = timezone.now()
        formation.commentaire_validation = commentaire
        formation.statut = 'active' if approved else 'rejetee'
        formation.save()
        
        logger.info(
            f"Formation '{formation.titre}' {'approuvée' if approved else 'rejetée'}"
        )
        
        return formation
    
    @staticmethod
    @transaction.atomic
    def update_formation_status(
        acting_user: User,
        formation_id: UUID,
        new_status: str,
        request=None
    ) -> Formation:
        """Met à jour le statut d'une formation."""
        formation = get_object_or_404(Formation, id=formation_id, deleted=False)
        
        if not FormationService._can_manage_formation(acting_user, formation):
            raise PermissionDeniedAPIException(
                "Vous n'avez pas la permission de modifier cette formation."
            )
        
        valid_statuses = [choice[0] for choice in Formation.STATUT_CHOICES]
        if new_status not in valid_statuses:
            raise BadRequestAPIException("Statut invalide.")
        
        formation.statut = new_status
        formation.save()
        
        logger.info(f"Statut de la formation '{formation.titre}' changé à '{new_status}'")
        
        return formation
    
    @staticmethod
    @transaction.atomic
    def soft_delete_formation(acting_user: User, formation_id: UUID, request=None):
        formation = get_object_or_404(Formation, id=formation_id)
        
        if not FormationService._can_manage_formation(acting_user, formation):
            raise PermissionDeniedAPIException(
                "Vous n'avez pas la permission de supprimer cette formation."
            )
        
        formation.soft_delete()
        logger.info(f"Formation '{formation.titre}' supprimée par {acting_user.email}")
    
    @staticmethod
    def get_formation_statistics() -> Dict:
        total = Formation.objects.count()
        active = Formation.objects.filter(statut='active', est_valide=True).count()
        pending = Formation.objects.filter(statut='en_attente', est_valide=False).count()
        
        stats_by_type = {}
        for type_formation, _ in Formation.TYPE_FORMATION_CHOICES:
            stats_by_type[type_formation] = Formation.objects.filter(
                type_formation=type_formation,
                statut='active',
                est_valide=True
            ).count()
        
        gratuites = Formation.objects.filter(
            est_payante=False,
            statut='active',
            est_valide=True
        ).count()
        
        payantes = Formation.objects.filter(
            est_payante=True,
            statut='active',
            est_valide=True
        ).count()
        
        return {
            'total_formations': total,
            'active_formations': active,
            'pending_formations': pending,
            'by_type': stats_by_type,
            'gratuites': gratuites,
            'payantes': payantes
        }


# Instance singleton
formation_service = FormationService()
