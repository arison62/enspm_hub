# opportunities/services/stage_service.py
import logging
from typing import Any, List, Dict, Optional, Tuple
from uuid import UUID
from datetime import date
from django.db import transaction
from django.db.models import Q, Count, Prefetch, QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify

from core.models import User, SecteurActivite, Domaine, Filiere
from opportunities.models import Stage
from opportunities.utils.get_similar_opportunities import get_similar_opportunities
from network.models import MembreOrganisation
from core.api.exceptions import (
    PermissionDeniedAPIException,
    NotFoundAPIException,
    BadRequestAPIException
)
from core.utils.generate_unique_slug import generate_unique_slug
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
    
    @staticmethod
    def _get_related_objects(model_class, ids, model_name):
        """Récupère les objets en lot avec validation."""
        if not ids:
            return []
        if not all(isinstance(id, UUID) for id in ids):
            raise BadRequestAPIException(f"Les IDs doivent de type UUID. {model_name} : {ids}")
        
        # Recupere les objets
        objects = list(model_class.objects.filter(id__in=ids))
        
        # Vérifier que tous les IDs ont été trouvés
        found_ids = {obj.id for obj in objects}
        missing_ids = [str(id) for id in ids if id not in found_ids]
        
        if missing_ids:
            raise BadRequestAPIException(
                f"{model_name.capitalize()} introuvables avec les IDs: {', '.join(missing_ids)}"
            )
        
        return objects
    
    @staticmethod
    def _normalize_uuid_list(values: Any) -> List[UUID]:
        """Normalise une liste de valeur en liste de UUID."""
        if not values:
            return []
        
        # Convertir en liste si ce n'est pas deja le cas
        if not isinstance(values, (list, tuple, set, QuerySet)):
            values = [values]
        
        uuid_list = []
        for value in values:
            try:
                if isinstance(value, UUID):
                    uuid_list.append(value)
                else:
                    uuid_list.append(UUID(value))
            except (ValueError, TypeError):
                continue
        
        return uuid_list
   
        
    
    # ==========================================
    # UTILITAIRES
    # ==========================================
    
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
        Crée un nouveau stage avec optimisation des requêtes et gestion robuste des erreurs.
        
        Optimisations clés :
        1. Récupération en lot des relations ManyToMany
        2. Validation préalable des données
        3. Gestion précise des exceptions
        4. Optimisation des requêtes SQL
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
        
        domaine_ids = data.pop('domaines', [])
        filiere_ids = data.pop('filieres', [])
        secteur_ids = data.pop('secteurs', [])
        
        # Validation et récupération en lot des objets
        domaines = StageService._get_related_objects(Domaine, domaine_ids, "domaines")
        filieres = StageService._get_related_objects(Filiere, filiere_ids, "filieres")
        secteurs = StageService._get_related_objects(SecteurActivite, secteur_ids, "secteurs")
        
        # Génération du slug unique avec tentative intelligente
        base_slug = slugify(data['titre'])[:50]  # Limiter la longueur du titre
        slug = generate_unique_slug(base_slug, Stage)
        if not slug:
            raise BadRequestAPIException(
                "Impossible de générer un identifiant unique après 5 tentatives."
            )
        
        try:
            # Création du stage avec toutes les données pré-validées
            new_stage = Stage.objects.create(
                createur_profil=acting_user.profil,
                organisation=organisation,
                slug=slug,
                statut=initial_status,
                est_valide=est_valide,
                **data
            )
            
            # Attribution des relations ManyToMany en une seule opération par type
            if domaines:
                new_stage.domaines.set(domaines)
            if filieres:
                new_stage.filieres.set(filieres)
            if secteurs:
                new_stage.secteurs.set(secteurs)
            
            logger.info(
                f"Stage '{new_stage.titre}' (ID: {new_stage.id}) créé par {acting_user.email} "
                f"- Statut: {initial_status}, Validé: {est_valide}, "
                f"Domaines: {len(domaines)}, Filières: {len(filieres)}, Secteurs: {len(secteurs)}"
            )
            
            return new_stage
            
        except Exception as e:
            logger.error(
                f"Erreur lors de la création du stage '{data.get('titre')}' par {acting_user.email}: {str(e)}",
                exc_info=True
            )
            raise BadRequestAPIException(f"Erreur lors de la création du stage: {str(e)}")
    

    @staticmethod
    def list_stages(
        filters: Optional[Dict] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Stage], int]:
        """"
        Liste tous les stages avec filtres et pagination.
        
        Optimisation cles:
        1. Utilisation d'annotation pour eviter les doublons
        2. Validation des parametres de pagination
        3. Filtres conditionnels bases sur les permissions
        4. Optimisation des requete SQL
        5. Gestion intelligente des relations ManyToMany
        """
        # Validation des paramètres de pagination
        page = max(1, int(page)) if page else 1
        page_size = min(max(1, int(page_size)), 100)
        
        StageService._auto_expire_stages()
        
        # Base queryset optimisee
        queryset = Stage.objects.filter(
            deleted=False
        )
    
        queryset = queryset.select_related('createur_profil', 'organisation')
        queryset = queryset.prefetch_related('secteurs', 'domaines', 'filieres')
        
        
        if filters:
            # Filtre de recherche
            if search := filters.get('search'):
                search = str(search).strip()
                if search:
                    # Utiliser un Q object combine avec annotation pour meilleur performance
                    search_terms = search.split()
                    q_objects = Q()
                    for term in search_terms:
                        q_objects |= Q(titre__icontains=term) 
                        q_objects |= Q(nom_structure__icontains=term) 
                        q_objects |= Q(description__icontains=term)
                        
                    queryset = queryset.filter(q_objects).distinct()
            
            # Filtre de lieu
            if lieu := filters.get('lieu'):
                lieu = str(lieu).strip()
                if lieu:
                    queryset = queryset.filter(
                         Q(adresse__icontains=lieu) |
                        Q(ville__icontains=lieu) |
                        Q(pays__name__icontains=lieu) 
                    ).distinct()
            
            # Filtre type_stage avec gestion
            if type_stage := filters.get('type_stage'):
                if isinstance(type_stage, (list, tuple)):
                    valid_types = [type for type, _ in Stage.TYPE_STAGE_CHOICES]
                    if valid_types:
                        queryset = queryset.filter(type_stage__in=valid_types)
                    elif type_stage:
                        queryset = queryset.filter(type_stage=type_stage).distinct()
            
            # Filtres ManyToMany
            many_to_many_filters = [
                ('domaines', 'domaine__id__in'),
                ('filieres', 'filiere__id__in'),
                ('secteurs', 'secteur__id__in')
            ]
            
            has_many_to_many_filter = False
            for filter_name, lookup in many_to_many_filters:
                if values := filters.get(filter_name):
                    uuid_values = StageService._normalize_uuid_list(values)
                    if uuid_values:
                        queryset = queryset.filter(**{lookup: uuid_values})
                        has_many_to_many_filter = True
                        
            # Appliquer distinct() si necessaire pour eviter les performances inutiles
            if has_many_to_many_filter:
                queryset = queryset.distinct()
                
            # Filtre de statut
            if statut := filters.get('statut'):
                if isinstance(statut, (list, tuple)):
                    queryset = queryset.filter(statut__in=statut).distinct()
                else:
                    queryset = queryset.filter(statut=statut).distinct()
            
        total_count = queryset.count()
        
        # pagination
        start = (page - 1) * page_size
        end  = start + page_size
        
        # Selectionner uniquement les champs necessaire
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
        queryset = queryset.prefetch_related('secteurs', 'domaines', 'filieres')
        
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
            ).prefetch_related(
                'secteurs', 
                'domaines', 
                'filieres'
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
            ).prefetch_related(
                'secteurs', 
                'domaines', 
                'filieres'
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

    @staticmethod
    def get_similar_stages(
            acting_user: User, 
            stage_id: UUID, 
            limit=5
        ):
        """
         Recupere les emplois similaires
        :param acting_user:
        :param stage_id:
        :param limit:
        :return:
        """
        return get_similar_opportunities(Stage, stage_id, limit)    
    


# Instance singleton
stage_service = StageService()