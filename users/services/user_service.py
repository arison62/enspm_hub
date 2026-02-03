import logging
import os
from typing import List, Literal, Optional
from django.db import IntegrityError, transaction
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.core.files.uploadedfile import UploadedFile
from django.core.files.storage import default_storage
from django.utils.text import slugify
from django.db.models import Q
from core.models import User
from users.models import Profil, LienReseauSocialProfil
from core.services.audit_service import audit_log_service, AuditLog
from core.utils.generate_unique_slug import generate_unique_slug
from PIL import Image
from io import BytesIO

logger = logging.getLogger('app')

class UserService:
    """
    Service contenant la logique métier pour la gestion des utilisateurs.
    """
    
    ALLOWED_PHOTO_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']
    MAX_PHOTO_SIZE = 5 * 1024 * 1024
    PHOTO_MAX_DIMENSIONS = (800, 800)
        
    @staticmethod
    @transaction.atomic
    def create_user(acting_user: User, user_data: dict, request=None) -> User:
        if User.objects.filter(email=user_data.get('email')).exists():
            raise ValueError(f"Un utilisateur avec l'email {user_data.get('email')} existe déjà.")

        profil_data = user_data.pop('profil', {})
        random_password = get_random_string(12)
        user_data['password'] = make_password(random_password)

        if user_data.get('role_systeme') in ['admin_site', 'super_admin']:
            user_data['is_staff'] = True

        new_user = User.objects.create(**user_data)
        slug = generate_unique_slug(profil_data.get('nom_complet'), Profil)
        if slug:
            profil_data['slug'] = slug


        Profil.objects.create(user=new_user, **profil_data)

        if not slug:
            raise ValueError("Impossible de générer un identifiant unique après plusieurs tentatives.")
        
        logger.info(f"Nouvel utilisateur créé (ID: {new_user.id}) par {acting_user.email}.")

        audit_data = {**user_data, 'profil': profil_data}
        audit_data.pop('password', None)

        audit_log_service.log_action(
            user=acting_user,
            action=AuditLog.AuditAction.CREATE,
            entity_type='User',
            entity_id=new_user.id,
            request=request,
            new_values=audit_data
        )
        return new_user
    
    @staticmethod
    @transaction.atomic
    def update_user(acting_user: User, user_to_update: User, data_update: dict, request=None) -> User:
        profil_data = data_update.pop('profil', None)
        old_values = {}
        new_values_log = {}

        # 1. Mise à jour des données de base de l'User
        if data_update:
            for field, value in data_update.items():
                old_values[field] = getattr(user_to_update, field)
                setattr(user_to_update, field, value)
            user_to_update.save()
            new_values_log.update(data_update)

        # 2. Mise à jour du Profil et du Slug
        if profil_data:
            profil, _ = Profil.objects.get_or_create(user=user_to_update)
            
            # Gestion spécifique du slug (Modèle LinkedIn)
            if 'slug' in profil_data:
                new_slug = slugify(profil_data['slug'])
                
                # Validation d'unicité
                if Profil.objects.filter(slug=new_slug).exclude(id=profil.id).exists():
                    raise ValueError(f"Le slug '{new_slug}' est déjà utilisé par un autre membre.")
                
                # Si le slug a changé, on le prépare pour le log
                if profil.slug != new_slug:
                    old_values['profil__slug'] = profil.slug
                    profil.slug = new_slug
                    profil_data['slug'] = new_slug # On garde la version nettoyée

            # Mise à jour des autres champs du profil
            for field, value in profil_data.items():
                if field != 'slug': # Déjà géré au-dessus
                    old_values[f'profil__{field}'] = getattr(profil, field)
                    setattr(profil, field, value)
            
            profil.save()
            new_values_log.update({f'profil__{k}': v for k, v in profil_data.items()})

        logger.info(f"Utilisateur (ID: {user_to_update.id}) mis à jour par {acting_user.email}. Slug: {user_to_update.profil.slug}") # type: ignore

        # 3. Journalisation complète dans l'AuditTrail
        
        audit_log_service.log_action(
            user=acting_user,
            action=AuditLog.AuditAction.UPDATE,
            entity_type='User',
            entity_id=user_to_update.id,
            request=request,
            old_values=old_values,
            new_values=new_values_log
        )
        return user_to_update

    @staticmethod
    @transaction.atomic
    def soft_delete_user(acting_user: User, user_to_delete: User, request=None):
        user_to_delete.soft_delete()
        logger.info(f"Utilisateur (ID: {user_to_delete.id}) supprimé (soft delete) par {acting_user.email}.")
        audit_log_service.log_action(
            user=acting_user,
            action=AuditLog.AuditAction.DELETE,
            entity_type='User',
            entity_id=user_to_delete.id,
            request=request
        )

    @staticmethod
    def _validate_photo(photo_file: UploadedFile):
        if not photo_file:
            raise ValueError("Aucun fichier n'a été fourni.")
        file_ext = os.path.splitext(photo_file.name)[1].lower()
        if file_ext not in UserService.ALLOWED_PHOTO_EXTENSIONS:
            raise ValueError(f"Format de fichier non autorisé. Acceptés : {', '.join(UserService.ALLOWED_PHOTO_EXTENSIONS)}")
        if photo_file.size > UserService.MAX_PHOTO_SIZE:
            raise ValueError(f"La taille du fichier dépasse {UserService.MAX_PHOTO_SIZE / (1024*1024)} MB.")
        try:
            Image.open(photo_file).verify()
        except Exception:
            raise ValueError("Le fichier n'est pas une image valide.")

    @staticmethod
    def _optimize_photo(photo_file: UploadedFile) -> BytesIO:
        image = Image.open(photo_file)
        if image.mode in ('RGBA', 'LA'):
            image = image.convert('RGB')
        image.thumbnail(UserService.PHOTO_MAX_DIMENSIONS, Image.Resampling.LANCZOS)
        output = BytesIO()
        image.save(output, format='WebP', quality=80)
        output.seek(0)
        return output

    @staticmethod
    @transaction.atomic
    def upload_profile_photo(acting_user: User, user: User, photo_file: UploadedFile, request=None) -> str:
        import time
        UserService._validate_photo(photo_file)
        profil, _ = Profil.objects.get_or_create(user=user)

        if profil.photo_profil and profil.photo_profil.path and os.path.exists(profil.photo_profil.path):
            os.remove(profil.photo_profil.path)

        optimized_photo = UserService._optimize_photo(photo_file)
        file_name = f"profile_{user.id}_{time.time()}.webp"
        saved_path = default_storage.save(os.path.join('photos_profils', file_name), optimized_photo)

        profil.photo_profil = saved_path # type: ignore
        profil.save()

        logger.info(f"Photo de profil mise à jour pour {user.id} par {acting_user.email}.")
        audit_log_service.log_action(
            user=acting_user,
            action=AuditLog.AuditAction.UPDATE,
            entity_type='Profil',
            entity_id=profil.id,
            request=request,
            new_values={'photo_profil': saved_path}
        )
        
        return profil.photo_profil.url

    @staticmethod
    @transaction.atomic
    def delete_profile_photo(acting_user: User, user: User, request=None):
        profil = getattr(user, 'profil', None)
        if not profil or not profil.photo_profil:
            return user

        if profil.photo_profil.path and os.path.exists(profil.photo_profil.path):
            os.remove(profil.photo_profil.path)

        profil.photo_profil = None
        profil.save()

        logger.info(f"Photo de profil de {user.id} supprimée par {acting_user.email}.")
        audit_log_service.log_action(
            user=acting_user,
            action=AuditLog.AuditAction.UPDATE,
            entity_type='Profil',
            entity_id=profil.id,
            request=request,
            new_values={'photo_profil': None}
        )
        return user

        
    @staticmethod
    def get_user_by_id(user_id: str, include_relations: bool = True) -> Optional[User]:
        """
        Récupère un utilisateur par son ID avec toutes ses relations.
        
        Args:
            user_id: UUID de l'utilisateur
            include_relations: Si True, inclut profil et réseaux sociaux
        
        Returns:
            User ou None si non trouvé
        """
        try:
            queryset = User.objects
            if include_relations:
                queryset = User.objects.select_related(
                'profil'
            ).prefetch_related(
                'profil__liens_reseaux'
            ).prefetch_related(
                'profil__domaine'
            ).prefetch_related(
                'profil__annee_sortie'
            ).prefetch_related(
                'profil__titre'
            )
            return queryset.get(id=user_id)
        except User.DoesNotExist:
            logger.warning(f"Utilisateur non trouvé avec l'ID: {user_id}")
            return None
        
    @staticmethod
    def get_user_by_slug(slug: str) -> Optional[User]:
        """
        Récupère un utilisateur par le slug de son profil.
        
        Args:
            slug: Slug du profil (ex: aminatou-seidou-x7r2p9)
        
        Returns:
            User ou None si non trouvé
        """
        try:
            return User.objects.select_related(
                'profil'
            ).prefetch_related(
                'profil__liens_reseaux'
            ).prefetch_related(
                'profil__domaine'
            ).prefetch_related(
                'profil__annee_sortie'
            ).prefetch_related(
                'profil__titre'
            ).get(profil__slug=slug)
        except User.DoesNotExist:
            logger.warning(f"Utilisateur non trouvé avec le slug: {slug}")
            return None
    
        
    @staticmethod
    def list_users(filters: Optional[dict] =  None, page: int = 1, page_size: int = 20):
        """
        Liste les utilisateurs avec filtres et pagination.
        
        Args:
            filters: Dictionnaire de filtres (search, role_systeme, statut_global, etc.)
            page: Numéro de page
            page_size: Nombre d'éléments par page
        
        Returns:
            Tuple (queryset, total_count)
        """
        queryset = User.objects.select_related('profil').prefetch_related(
            'profil__liens_reseaux'
            ).prefetch_related(
                'profil__domaine'
            ).prefetch_related(
                'profil__annee_sortie'
            ).prefetch_related(
                'profil__titre'
            ).prefetch_related(
                'profil__experiences'
            )
        
        if filters:
            # Recherche textuelle
            if search := filters.get('search'):
                queryset = queryset.filter(
                    Q(email__icontains=search) |
                    Q(profil__nom_complet__icontains=search) |
                    Q(profil__matricule__icontains=search) |
                    Q(profil__telephone__icontains=search) |
                    Q(profil__bio__icontains=search)
                )
            
            # Filtres exacts
            
            if role := filters.get('role_systeme'):
                if isinstance(role, list):
                    queryset = queryset.filter(role_systeme__in=role)
                else:   
                    queryset = queryset.filter(role_systeme=role)
            
            if statut := filters.get('statut_global'):
                if isinstance(statut, list):
                    queryset = queryset.filter(profil__statut_global__in=statut)
                else:
                    queryset = queryset.filter(profil__statut_global=statut)
            
            if est_actif := filters.get('est_actif'):
                if isinstance(est_actif, list):
                    queryset = queryset.filter(est_actif__in=est_actif)
                else:
                    queryset = queryset.filter(est_actif=filters['est_actif'])
            
            if pays := filters.get('pays'):
                if isinstance(pays, list):
                    queryset = queryset.filter(profil__pays__name__in=pays)
                else:
                    queryset = queryset.filter(profil__pays__code__iexact=pays)
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        return queryset[start:end], total_count
    
      
    # ==========================================
    # GESTION DES RÉSEAUX SOCIAUX
    # ==========================================
    
    @staticmethod
    @transaction.atomic
    def add_social_link(
        acting_user: User, 
        user: User, 
        reseau_id: str, 
        url: str,
        request=None
    ) -> LienReseauSocialProfil:
        """
        Ajoute un lien réseau social à un profil.
        
        Args:
            acting_user: Utilisateur effectuant l'action
            user: Utilisateur cible
            nom_reseau: Nom du réseau (ex: 'LinkedIn')
            url: URL du profil sur le réseau
            request: Objet request pour l'audit
        
        Returns:
            LienReseauSocial créé
        """
        profil = getattr(user, 'profil', None)
        if not profil:
            raise ValueError("L'utilisateur n'a pas de profil.")
        
        social_link = LienReseauSocialProfil.objects.create(
            profil=profil,
            reseau_id=reseau_id,
            url=url,
            est_actif=True
        )
        
        logger.info(f"Lien {reseau_id} ajouté au profil {profil.id} par {acting_user.email}")
        
        audit_log_service.log_action(
            user=acting_user,
            action=AuditLog.AuditAction.CREATE,
            entity_type='LienReseauSocial',
            entity_id=social_link.id,
            request=request,
            new_values={'nom_reseau': reseau_id, 'url': url}
        )
        
        return social_link
    
        
    @staticmethod
    @transaction.atomic
    def update_social_link(
        acting_user: User,
        link_id: str,
        url: Optional[str] = None,
        est_actif: Optional[bool] = None,
        request=None
    ) -> LienReseauSocialProfil:
        """
        Met à jour un lien réseau social.
        
        Args:
            acting_user: Utilisateur effectuant l'action
            link_id: UUID du lien à mettre à jour
            url: Nouvelle URL (optionnel)
            est_actif: Nouveau statut actif (optionnel)
            request: Objet request pour l'audit
        
        Returns:
            LienReseauSocial mis à jour
        """
        try:
            social_link = LienReseauSocialProfil.objects.get(id=link_id)
        except LienReseauSocialProfil.DoesNotExist:
            raise ValueError(f"Lien réseau social avec l'ID {link_id} introuvable.")
        
        old_values = {}
        new_values = {}
        
        if url is not None and url != social_link.url:
            old_values['url'] = social_link.url
            social_link.url = url
            new_values['url'] = url
        
        if est_actif is not None and est_actif != social_link.est_actif:
            old_values['est_actif'] = social_link.est_actif
            social_link.est_actif = est_actif
            new_values['est_actif'] = est_actif
        
        social_link.save()
        
        logger.info(f"Lien {social_link.reseau} (ID: {link_id}) mis à jour par {acting_user.email}")
        
        audit_log_service.log_action(
            user=acting_user,
            action=AuditLog.AuditAction.UPDATE,
            entity_type='LienReseauSocial',
            entity_id=social_link.id,
            request=request,
            old_values=old_values,
            new_values=new_values
        )
        
        return social_link
    
    @staticmethod
    @transaction.atomic
    def delete_social_link(acting_user: User, link_id: str, request=None):
        """
        Supprime (soft delete) un lien réseau social.
        
        Args:
            acting_user: Utilisateur effectuant l'action
            link_id: UUID du lien à supprimer
            request: Objet request pour l'audit
        """
        try:
            social_link = LienReseauSocialProfil.objects.get(id=link_id)
        except LienReseauSocialProfil.DoesNotExist:
            raise ValueError(f"Lien réseau social avec l'ID {link_id} introuvable.")
        
        social_link.soft_delete()
        
        logger.info(f"Lien {social_link.reseau} (ID: {link_id}) supprimé par {acting_user.email}")
        
        audit_log_service.log_action(
            user=acting_user,
            action=AuditLog.AuditAction.DELETE,
            entity_type='LienReseauSocial',
            entity_id=social_link.id,
            request=request
        )
    
    @staticmethod
    def get_social_links(user: User) -> list[LienReseauSocialProfil]:
        """
        Récupère tous les liens réseaux sociaux actifs d'un utilisateur.
        
        Args:
            user: Utilisateur cible
        
        Returns:
            Liste des LienReseauSocial actifs
        """
        profil = getattr(user, 'profil', None)
        if not profil:
            return []
        
        return list(
            LienReseauSocialProfil.objects.filter(
                profil=profil,
                est_actif=True
            ).order_by('nom_reseau')
        )
    
    
    # ==========================================
    # GESTION DU MOT DE PASSE
    # ==========================================
    
    @staticmethod
    @transaction.atomic
    def change_password(
        user: User, 
        old_password: str, 
        new_password: str,
        request=None
    ) -> bool:
        """
        Permet à un utilisateur de changer son propre mot de passe.
        
        Args:
            user: Utilisateur authentifié
            old_password: Ancien mot de passe
            new_password: Nouveau mot de passe
            request: Objet request pour l'audit
        
        Returns:
            True si succès
        
        Raises:
            ValueError: Si l'ancien mot de passe est incorrect
        """
        if not user.check_password(old_password):
            raise ValueError("L'ancien mot de passe est incorrect.")
        
        user.set_password(new_password)
        user.save()
        
        logger.info(f"Mot de passe changé pour l'utilisateur {user.email}")
        
        audit_log_service.log_action(
            user=user,
            action=AuditLog.AuditAction.UPDATE,
            entity_type='User',
            entity_id=user.id,
            request=request,
            new_values={'password': '***'}
        )
        
        return True
    
    @staticmethod
    @transaction.atomic
    def reset_password(
        acting_user: User,
        user_to_reset: User,
        new_password: Optional[str] = None,
        request=None
    ) -> str:
        """
        Réinitialise le mot de passe d'un utilisateur (admin uniquement).
        
        Args:
            acting_user: Administrateur effectuant l'action
            user_to_reset: Utilisateur dont le mot de passe doit être réinitialisé
            new_password: Nouveau mot de passe (généré si None)
            request: Objet request pour l'audit
        
        Returns:
            Le nouveau mot de passe en clair
        """
        if not new_password:
            new_password = get_random_string(12)
        
        user_to_reset.set_password(new_password)
        user_to_reset.save()
        
        logger.info(
            f"Mot de passe réinitialisé pour {user_to_reset.email} "
            f"par {acting_user.email}"
        )
        
        audit_log_service.log_action(
            user=acting_user,
            action=AuditLog.AuditAction.UPDATE,
            entity_type='User',
            entity_id=user_to_reset.id,
            request=request,
            new_values={'password_reset': True}
        )
        
        return new_password
    
    # ==========================================
    # GESTION DU COMPTE
    # ==========================================
    
    @staticmethod
    @transaction.atomic
    def toggle_user_status(
        acting_user: User,
        user_to_toggle: User,
        est_actif: bool,
        request=None
    ) -> User:
        """
        Active ou désactive un compte utilisateur.
        
        Args:
            acting_user: Administrateur effectuant l'action
            user_to_toggle: Utilisateur à activer/désactiver
            est_actif: True pour activer, False pour désactiver
            request: Objet request pour l'audit
        
        Returns:
            User mis à jour
        """
        old_status = user_to_toggle.est_actif
        user_to_toggle.est_actif = est_actif
        user_to_toggle.save()
        
        action_desc = "activé" if est_actif else "désactivé"
        logger.info(
            f"Compte {user_to_toggle.email} {action_desc} "
            f"par {acting_user.email}"
        )
        
        audit_log_service.log_action(
            user=acting_user,
            action=AuditLog.AuditAction.UPDATE,
            entity_type='User',
            entity_id=user_to_toggle.id,
            request=request,
            old_values={'est_actif': old_status},
            new_values={'est_actif': est_actif}
        )
        
        return user_to_toggle
    
    @staticmethod
    @transaction.atomic
    def restore_user(acting_user: User, user_to_restore: User, request=None) -> User:
        """
        Restaure un utilisateur supprimé (soft delete).
        
        Args:
            acting_user: Administrateur effectuant l'action
            user_to_restore: Utilisateur à restaurer
            request: Objet request pour l'audit
        
        Returns:
            User restauré
        """
        user_to_restore.restore()
        
        logger.info(
            f"Utilisateur {user_to_restore.email} restauré "
            f"par {acting_user.email}"
        )
        
        audit_log_service.log_action(
            user=acting_user,
            action=AuditLog.AuditAction.UPDATE,
            entity_type='User',
            entity_id=user_to_restore.id,
            request=request,
            new_values={'deleted': False}
        )
        
        return user_to_restore
    
    # ==========================================
    # STATISTIQUES & RAPPORTS
    # ==========================================
    
    @staticmethod
    def get_user_statistics() -> dict:
        """
        Retourne des statistiques globales sur les utilisateurs.
        
        Returns:
            Dictionnaire avec les stats
        """
        total_users = User.objects.count()
        active_users = User.objects.filter(est_actif=True).count()
        deleted_users = User.all_objects.filter(deleted=True).count()
        
        stats_by_role = {}
        for role, _ in User.ROLE_SYSTEME_CHOICES:
            stats_by_role[role] = User.objects.filter(role_systeme=role).count()
        
        stats_by_status = {}
        for status, _ in Profil.STATUT_GLOBAL_CHOICES:
            stats_by_status[status] = Profil.objects.filter(
                statut_global=status
            ).count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'deleted_users': deleted_users,
            'by_role': stats_by_role,
            'by_status': stats_by_status,
        }


    # ==========================================
    # Bulk Operations
    # ==========================================
    @staticmethod
    def bulk_create_users(
        acting_user: User,
        users_data: list[dict],
        request=None,
        mode: Literal['strict', 'skip'] = 'strict',
        batch_size: int = 100
    ) -> dict[str, List]:
        """
        Crée plusieurs utilisateurs en une seule opération.
        
        Args:
            acting_user: Administrateur effectuant l'action
            users_data: Liste de dictionnaires avec les données des utilisateurs
            request: Objet request pour l'audit
            mode: 'strict' pour arrêter à la première erreur, 
                  'skip' pour ignorer les erreurs et continuer
        Returns:
            - created_users: Liste des utilisateurs créés
            - errors: Liste des erreurs (index dans users_data et message), vide si mode 'strict'
        """
        created_users = []
        errors = []
        with transaction.atomic():
            user_objects = []
            profil_objects = []
            audit_batch = []  # Pour logger en batch
            
            for idx, data in enumerate(users_data):
                try:
                    profil_data = data.pop('profil', {})
                    user_data = data
                    

                    # Génération password si absent
                    if 'password' not in user_data:
                        random_password = get_random_string(12)
                        user_data['password'] = make_password(random_password)
                    else:
                        user_data['password'] = make_password(user_data['password'])
                    
                    # Set is_staff si role admin
                    if user_data.get('role_systeme') in ['admin_site', 'super_admin']:
                        user_data['is_staff'] = True
                    
                    # Vérification email unique (avant création pour éviter bulk fail)
                    if User.objects.filter(email=user_data.get('email')).exists():
                        raise ValueError(f"Un utilisateur avec l'email {user_data.get('email')} existe déjà.")
                    
                    # Créer objet User (pas encore save)
                    new_user = User(**user_data)
                    user_objects.append(new_user)
                    
                    # Générer slug unique avec retries
                    slug = generate_unique_slug(profil_data.get('nom_complet'), Profil)
                    if slug:
                        profil_data['slug'] = slug
                    new_profil = Profil(user=new_user, **profil_data)
                    profil_objects.append(new_profil)
                  
                    
                    if not slug:
                        raise ValueError("Impossible de générer un identifiant unique après plusieurs tentatives.")
                    
                    # Préparer audit data
                    audit_data = {**user_data, 'profil': profil_data}
                    audit_data.pop('password', None)
                    audit_batch.append(audit_data)
                    
                except Exception as e:
                    error_msg = f"Erreur à l'index {idx}: {str(e)}"
                    if mode == 'skip':
                        logger.error(error_msg)
                        errors.append({'index': idx, 'error': str(e)})
                        continue
                    else:
                        raise ValueError(error_msg)
            
            # Bulk create Users
            if user_objects:
                User.objects.bulk_create(user_objects, batch_size=batch_size)
                
                # Bulk create Profils
                Profil.objects.bulk_create(profil_objects, batch_size=batch_size)
                
                # Récupérer created_users (puisque objects ont maintenant IDs)
                created_users = [profil.user for profil in profil_objects]
                
                # Log audits en batch (un par user)
                for i, new_user in enumerate(created_users):
                    audit_log_service.log_action(
                        user=acting_user,
                        action=AuditLog.AuditAction.CREATE,
                        entity_type='User',
                        entity_id=new_user.id,
                        request=request,
                        new_values=audit_batch[i]
                    )
                
                logger.info(f"{len(created_users)} utilisateurs créés en batch par {acting_user.email}.")
        
        return {
            'created_users': created_users,
            'errors': errors
        }
                

# Instance singleton
user_service = UserService()

