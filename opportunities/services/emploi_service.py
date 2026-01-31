# opportunities/services/emploi_service.py
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
from core.utils.generate_unique_slug import generate_unique_slug
from opportunities.models import Emploi
from opportunities.utils.get_similar_opportunities import get_similar_opportunities
from network.models import MembreOrganisation
from core.api.exceptions import (
    PermissionDeniedAPIException,
    BadRequestAPIException
)

logger = logging.getLogger('app')


class EmploiService:
    """Service pour la gestion des offres d'emploi."""
    
    @staticmethod
    def _is_site_admin(user: User) -> bool:
        return user.role_systeme in ['admin_site', 'super_admin']
    
    @staticmethod
    def _is_partner(user: User) -> bool:
        return hasattr(user, 'profil') and user.profil.statut_global == 'partenaire'
    
    @staticmethod
    def _get_user_organisation(user: User):
        if not EmploiService._is_partner(user):
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
    def _can_manage_emploi(user: User, emploi: Emploi) -> bool:
        if EmploiService._is_site_admin(user):
            return True
        if emploi.createur_profil and emploi.createur_profil.user.id == user.id:
            return True
        if emploi.organisation:
            return MembreOrganisation.objects.filter(
                organisation=emploi.organisation,
                profil__user=user,
                role_organisation='administrateur_page',
                est_actif=True
            ).exists()
        return False
    
    @staticmethod
    def _auto_expire_emplois():
        """Met à jour automatiquement les emplois expirés."""
        today = date.today()
        Emploi.objects.filter(
            date_expiration__lt=today,
            statut='active'
        ).update(statut='expiree')
    
    @staticmethod
    @transaction.atomic
    def create_emploi(acting_user: User, data: Dict, request=None) -> Emploi:
        """Crée une nouvelle offre d'emploi."""
        is_partner = EmploiService._is_partner(acting_user)
        is_admin = EmploiService._is_site_admin(acting_user)
        
        if is_partner or is_admin:
            initial_status = 'active'
            est_valide = True
        else:
            initial_status = 'en_attente'
            est_valide = False
        
        organisation = None
        if is_partner:
            organisation = EmploiService._get_user_organisation(acting_user)
            if not organisation:
                raise BadRequestAPIException(
                    "Vous devez être membre actif d'une organisation."
                )
        
        slug = generate_unique_slug(data['titre'][:50], Emploi)
        if not slug:
            raise BadRequestAPIException("Impossible de générer un identifiant unique.")
        
        
   
        try:
            new_emploi = Emploi.objects.create(
                createur_profil=acting_user.profil,
                organisation=organisation,
                slug=slug,
                statut=initial_status,
                est_valide=est_valide,
                **data
            )
            logger.info(
                f"Emploi '{data['titre']}' (ID: {new_emploi.id}) cree par {acting_user.email}"
            )
            return new_emploi
        
        except Exception as e:
            
            logger.error(
                f"Erreur lors de la création de l'emploi '{data['titre']} par {acting_user.email}': {str(e)}"
            )
            raise BadRequestAPIException(f"Erreur lors de la création de l'emploi: {str(e)}")

    
    @staticmethod
    def list_emplois(
        filters: Optional[Dict] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Emploi], int]:
        """Liste les offres d'emploi avec filtres."""
        EmploiService._auto_expire_emplois()
        
        print("list_emplois", filters)
        queryset = Emploi.objects.filter()
        queryset = queryset.select_related('devise','createur_profil', 'organisation')
        
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

            
            if type_emploi := filters.get('type_emploi'):
                if isinstance(type_emploi, list):
                    queryset = queryset.filter(type_emploi__in=type_emploi)
                else:
                    queryset = queryset.filter(type_emploi=type_emploi)
                
            if statut := filters.get('statut'):
                if isinstance(statut, list):
                    queryset = queryset.filter(statut__in=statut)
                else:
                    queryset = queryset.filter(statut=statut)
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        emplois = list(queryset.order_by('-date_publication')[start:end])
        
        return emplois, total_count

     
    @staticmethod
    def list_pending_emplois(
        acting_user: User,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Emploi], int]:
        """Liste les emplois en attente."""
        if not EmploiService._is_site_admin(acting_user):
            raise PermissionDeniedAPIException(
                "Vous n'avez pas la permission de voir les emplois en attente."
            )
            
        EmploiService._auto_expire_emplois()
        queryset = Emploi.objects.filter(
            statut='en_attente',
            est_valide=False,
            deleted=False
        ).select_related('devise','createur_profil', 'organisation').order_by('date_publication')
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        emplois = list(queryset[start:end])
        
        return emplois, total_count
    
    @staticmethod
    def get_emploi_by_id(emploi_id: UUID) -> Optional[Emploi]:
        try:
            return Emploi.objects.select_related(
                'devise',
                'createur_profil',
                'organisation',
                'validateur_profil'
            ).get(id=emploi_id, deleted=False)
        except Emploi.DoesNotExist:
            return None
    
    @staticmethod
    def get_emploi_by_slug(slug: str) -> Optional[Emploi]:
        try:
            return Emploi.objects.select_related(
                'devise',
                'createur_profil',
                'organisation',
                'validateur_profil'
            ).get(slug=slug, deleted=False)
        except Emploi.DoesNotExist:
            return None
    
    @staticmethod
    @transaction.atomic
    def update_emploi(
        acting_user: User,
        emploi_id: UUID,
        data: Dict,
        request=None
    ) -> Emploi:
        """Met à jour une offre d'emploi."""
        emploi = get_object_or_404(Emploi, id=emploi_id, deleted=False)
        
        if not EmploiService._can_manage_emploi(acting_user, emploi):
            raise PermissionDeniedAPIException(
                "Vous n'avez pas la permission de modifier cette offre."
            )
        
        if 'slug' in data:
            new_slug = slugify(data['slug'])
            if Emploi.objects.filter(slug=new_slug).exclude(id=emploi_id).exists():
                raise BadRequestAPIException(f"Le slug '{new_slug}' est déjà utilisé.")
            data['slug'] = new_slug
        
        for field, value in data.items():
            setattr(emploi, field, value)
        
        emploi.save()
        
        logger.info(f"Emploi '{emploi.titre}' mis à jour par {acting_user.email}")
        
        return emploi
    
    @staticmethod
    @transaction.atomic
    def validate_emploi(
        acting_user: User,
        emploi_id: UUID,
        approved: bool,
        commentaire: Optional[str] = None,
        request=None
    ) -> Emploi:
        """Valide ou rejette une offre d'emploi."""
        if not EmploiService._is_site_admin(acting_user):
            raise PermissionDeniedAPIException(
                "Seuls les administrateurs peuvent valider les emplois."
            )
        
        emploi = get_object_or_404(Emploi, id=emploi_id, deleted=False)
        
        if emploi.est_valide:
            raise BadRequestAPIException("Cette offre a déjà été validée.")
        
        emploi.est_valide = approved
        emploi.validateur_profil = acting_user.profil
        emploi.date_validation = timezone.now()
        emploi.commentaire_validation = commentaire
        emploi.statut = 'active' if approved else 'rejetee'
        emploi.save()
        
        logger.info(f"Emploi '{emploi.titre}' {'approuvé' if approved else 'rejeté'}")
        
        return emploi
    
    @staticmethod
    @transaction.atomic
    def update_emploi_status(
        acting_user: User,
        emploi_id: UUID,
        new_status: str,
        request=None
    ) -> Emploi:
        """Met à jour le statut d'une offre."""
        emploi = get_object_or_404(Emploi, id=emploi_id, deleted=False)
        
        if not EmploiService._can_manage_emploi(acting_user, emploi):
            raise PermissionDeniedAPIException(
                "Vous n'avez pas la permission de modifier cette offre."
            )
        
        valid_statuses = [choice[0] for choice in Emploi.STATUT_CHOICES]
        if new_status not in valid_statuses:
            raise BadRequestAPIException(f"Statut invalide.")
        
        emploi.statut = new_status
        emploi.save()
        
        logger.info(f"Statut de l'emploi '{emploi.titre}' changé à '{new_status}'")
        
        return emploi
    
    @staticmethod
    @transaction.atomic
    def soft_delete_emploi(acting_user: User, emploi_id: UUID, request=None):
        emploi = get_object_or_404(Emploi, id=emploi_id)
        
        if not EmploiService._can_manage_emploi(acting_user, emploi):
            raise PermissionDeniedAPIException(
                "Vous n'avez pas la permission de supprimer cette offre."
            )
        
        emploi.soft_delete()
        logger.info(f"Emploi '{emploi.titre}' supprimé par {acting_user.email}")
    
    @staticmethod
    def get_emploi_statistics() -> Dict:
        total = Emploi.objects.count()
        active = Emploi.objects.filter(statut='active', est_valide=True).count()
        pending = Emploi.objects.filter(statut='en_attente', est_valide=False).count()
        
        stats_by_type = {}
        for type_emploi, _ in Emploi.TYPE_EMPLOI_CHOICES:
            stats_by_type[type_emploi] = Emploi.objects.filter(
                type_emploi=type_emploi,
                statut='active',
                est_valide=True
            ).count()
        
        return {
            'total_emplois': total,
            'active_emplois': active,
            'pending_emplois': pending,
            'by_type': stats_by_type
        }

    
    @staticmethod
    def get_similar_emploi(
            acting_user: User, 
            emploi_id: UUID, 
            limit=5
        ):
        """
         Recupere les emplois similaires
        :param acting_user:
        :param emploi_id:
        :param limit:
        :return:
        """
        return get_similar_opportunities(Emploi, emploi_id, limit)

# Instance singleton
emploi_service = EmploiService()