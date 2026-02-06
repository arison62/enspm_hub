# network/services/chats.py
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.db.models import F, Q, Count, Exists, IntegerField, OuterRef, Subquery
from django.db.models.functions import Coalesce

from core.api.exceptions import BaseAPIException
from core.utils.base64_utils import Base64FileHandler
from core.models import User
from core.utils.generate_unique_slug import generate_unique_slug
from network.models.chat import (
    Groupe, MembreGroupe, MessageGroupe, 
    MessageDirect, DemandeAccesGroupe
)
from users.models import Profil

logger = logging.getLogger(__name__)




class ChatService:
    """Service de gestion de la messagerie (groupes et messages directs)"""
    
    
    #===============================================
    # GESTION DES GROUPES
    #===============================================
    @staticmethod
    @transaction.atomic
    def creer_groupe(
        acting_user: User,
        nom: str,
        description: Optional[str] = None,
        type_acces: str = 'public',
        image_base64: Optional[str] = None,
        request=None
    ) -> Groupe:
        """
        Crée un nouveau groupe de discussion
        
        Args:
            acting_user: Utilisateur créant le groupe
            nom: Nom du groupe
            description: Description du groupe
            type_acces: Type d'accès ('public' ou 'prive')
            image_base64: Image du groupe en base64
            request: Requête HTTP (optionnel)
        
        Returns:
            Groupe: Le groupe créé
        
        Raises:
            ValidationError: Si les données sont invalides
        """
        try:
            profil = acting_user.profil
            # Valider le type d'accès
            if type_acces not in ['public', 'prive']:
                raise ValidationError(f"Type d'accès invalide: {type_acces}")
            
            # Valider le nom
            if len(nom) < 3:
                raise ValidationError("Le nom doit contenir au moins 3 caractères")
            
            if len(nom) > 255:
                raise ValidationError("Le nom ne doit pas dépasser 255 caractères")
            
            # Générer un slug unique
            slug = generate_unique_slug(nom, Groupe)
            
            if slug is None:
                raise BaseAPIException("Impossible de générer un slug unique")
            
            # Créer le groupe
            est_actif = acting_user.is_admin_user()  # Les admins peuvent créer des groupes actifs directement
            groupe = Groupe.objects.create(
                nom=nom,
                slug=slug,
                description=description or "",
                type_acces=type_acces,
                createur=profil,
                status=Groupe.Status.ACTIF if est_actif else Groupe.Status.INACTIF
            )
            
            # Traiter l'image si fournie
            if image_base64:
                try:
                    base64_image_handler = Base64FileHandler()
                    image_data = base64_image_handler.handle(
                        image_base64, 
                        filename_prefix='group_image',
                        max_dimensions=(800, 800),
                    )
                    groupe.image = image_data
                    groupe.save()
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement de l'image: {str(e)}")
                
            # Ajouter le créateur comme administrateur du groupe
            MembreGroupe.objects.create(
                groupe=groupe,
                profil=profil,
                role='admin'
            )
            
            logger.info(
                f"Groupe créé - ID: {groupe.id}, "
                f"Nom: {nom}, "
                f"Type: {type_acces}, "
                f"Créateur: {acting_user.id}"
            )
            
            return groupe
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du groupe: {str(e)}")
            raise


    @staticmethod
    @transaction.atomic
    def modifier_groupe(
        acting_user: User,
        groupe_id: UUID,
        nom: Optional[str] = None,
        description: Optional[str] = None,
        type_acces: Optional[str] = None,
        status: Optional[str] = None,
        image_base64: Optional[str] = None,
        request=None
    ) -> Groupe:
        """
        Modifie un groupe existant
        
        Args:
            acting_user: Utilisateur effectuant la modification
            groupe_id: ID du groupe
            nom: Nouveau nom
            description: Nouvelle description
            type_acces: Nouveau type d'accès
            image_base64: Nouvelle image en base64
            request: Requête HTTP (optionnel)
        
        Returns:
            Groupe: Le groupe modifié
        
        Raises:
            ValidationError: Si les données sont invalides
            PermissionDenied: Si l'utilisateur n'a pas les droits
        """
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.select_for_update().get(
                id=groupe_id,
                deleted=False,
            )
            
            # Vérifier les permissions (doit être admin du groupe)
            if not groupe.est_admin(profil):
                logger.warning(
                    f"Tentative de modification non autorisée du groupe {groupe_id} "
                    f"par {acting_user.id}"
                )
                raise PermissionDenied("Vous devez être administrateur pour modifier le groupe")
            
            # Mettre à jour les champs
            if nom is not None:
                if len(nom) < 3 or len(nom) > 255:
                    raise ValidationError("Le nom doit contenir entre 3 et 255 caractères")
                
                groupe.nom = nom
                # Régénérer le slug
                slug = generate_unique_slug(nom, Groupe)
                
                if slug is None:
                    raise BaseAPIException("Impossible de générer un slug unique")
                groupe.slug = slug
            
            if description is not None:
                groupe.description = description
            
            if type_acces is not None:
                if type_acces not in ['public', 'prive']:
                    raise ValidationError(f"Type d'accès invalide: {type_acces}")
                groupe.type_acces = type_acces
            
            # Seuls les admins peuvent modifier le statut du groupe
            if status is not None:
                if not acting_user.is_admin_user():
                    raise PermissionDenied("Seuls les administrateurs peuvent modifier le statut du groupe")
                if status not in [Groupe.Status.ACTIF, Groupe.Status.INACTIF]:
                    raise ValidationError(f"Statut invalide: {status}")
                groupe.status = status
            groupe.save()

            
            # Traiter l'image si fournie
            if image_base64:
                try:
                    base64_image_handler = Base64FileHandler()
                    if image_base64:
                        image_data = base64_image_handler.handle(
                            image_base64, 
                            filename_prefix='group_image',
                            max_dimensions=(800, 800),
                        )
                        groupe.image = image_data
                        groupe.save()
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement de l'image: {str(e)}")
            
            logger.info(
                f"Groupe modifié - ID: {groupe.id}, "
                f"Par: {acting_user.id}"
            )
            
            return groupe
            
        except Groupe.DoesNotExist:
            logger.error(f"Groupe introuvable: {groupe_id}")
            raise ValidationError("Groupe introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la modification du groupe: {str(e)}")
            raise

    
    @staticmethod
    @transaction.atomic
    def supprimer_groupe(
        acting_user: User,
        groupe_id: UUID,
        request=None
    ) -> bool:
        """
        Supprime (soft delete) un groupe
        
        Args:
            acting_user: Utilisateur effectuant la suppression
            groupe_id: ID du groupe
            request: Requête HTTP (optionnel)
        
        Returns:
            bool: True si la suppression a réussi
        
        Raises:
            PermissionDenied: Si l'utilisateur n'a pas les droits
        """
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.select_for_update().get(
                id=groupe_id,
                deleted=False
            )
            
            # Vérifier les permissions
            if not groupe.est_admin(profil) or not acting_user.is_admin_user():
                raise PermissionDenied("Vous devez être administrateur pour supprimer le groupe")
            
            groupe.deleted = True
            groupe.save()
            
            logger.info(
                f"Groupe supprimé - ID: {groupe.id}, "
                f"Par: {acting_user.id}"
            )
            
            return True
            
        except Groupe.DoesNotExist:
            logger.error(f"Groupe introuvable: {groupe_id}")
            raise ValidationError("Groupe introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du groupe: {str(e)}")
            raise

    
    @staticmethod
    def list_groupes(
        acting_user: User,
        query: Optional[str] = None,
        type_acces: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        request=None
    ) -> tuple[List[Groupe], int]:
        """
        Recherche des groupes
        
        Args:
            acting_user: Utilisateur effectuant la recherche
            query: Terme de recherche
            type_acces: Filtrer par type d'accès
            page: Numéro de page
            page_size: Taille de page
            request: Requête HTTP (optionnel)
        
        Returns:
            tuple: (Liste des groupes, nombre total)
        """
        est_admin = acting_user.is_admin_user()
        
        try:
            profil = acting_user.profil
            queryset = Groupe.objects.none()
            if est_admin:
                queryset = Groupe.objects.filter(
                    deleted=False
                ).select_related('createur')
            else:   
                queryset = Groupe.objects.filter(
                    deleted=False
                ).exclude(
                    Q(status=Groupe.Status.INACTIF)
                ).select_related('createur')
            
            # Recherche textuelle
            if query:
                queryset = queryset.filter(
                    Q(nom__icontains=query) |
                    Q(description__icontains=query)
                )
            
            # Filtre par type d'accès
            if type_acces:
                queryset = queryset.filter(type_acces=type_acces)
            
            count_demandes = DemandeAccesGroupe.objects.filter(
                groupe_id=OuterRef('id'),
                status=DemandeAccesGroupe.Status.EN_ATTENTE,
                deleted=False
            ).values('groupe_id').annotate(total=Count('id')).values('total')

            count_membres = MembreGroupe.objects.filter(
                groupe_id=OuterRef('id'),
                deleted=False
            ).values('groupe_id').annotate(total=Count('id')).values('total')

            count_messages = MessageGroupe.objects.filter(
                groupe_id=OuterRef('id'),
                deleted=False
            ).values('groupe_id').annotate(total=Count('id')).values('total')

            # Appliquez les annotations
            queryset = queryset.annotate(
                is_member=Exists(
                    MembreGroupe.objects.filter(
                        groupe_id=OuterRef('id'), profil=profil, deleted=False
                    )
                ),
                is_admin=Exists(
                    MembreGroupe.objects.filter(
                        groupe_id=OuterRef('id'), profil=profil, role=MembreGroupe.Role.ADMIN, deleted=False
                    )
                ),
                has_user_pending_request=Exists(
                    DemandeAccesGroupe.objects.filter(
                        groupe_id=OuterRef('id'), demandeur=profil, status=DemandeAccesGroupe.Status.EN_ATTENTE, deleted=False
                    )
                ),
                # Utilisation de Subquery pour les counts
                # Coalesce permet de renvoyer 0 au lieu de NULL si aucune ligne n'est trouvée
                pending_request=Coalesce(Subquery(count_demandes, output_field=IntegerField()), 0),
                nb_members=Coalesce(Subquery(count_membres, output_field=IntegerField()), 0),
                nb_messages=Coalesce(Subquery(count_messages, output_field=IntegerField()), 0)
            )
            
            queryset = queryset.order_by('-nb_members', '-nb_messages','-created_at')
            total_items = queryset.count()
            
            # Pagination
            start = (page - 1) * page_size
            end = start + page_size
            queryset = queryset[start:end]
            
            logger.info(f"Recherche de groupes - Par: {acting_user.id}")
            
            return list(queryset), total_items
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de groupes: {str(e)}")
            raise

    
    @staticmethod
    def obtenir_mes_groupes(
        acting_user: User,
        role: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        request=None
    ) -> tuple[List[Groupe], int]:
        """
        Obtient les groupes dont l'utilisateur est membre
        
        Args:
            acting_user: Utilisateur
            role: Filtrer par rôle ('membre' ou 'admin')
            page: Numéro de page
            page_size: Taille de page
            request: Requête HTTP (optionnel)
        
        Returns:
            tuple: (Liste des groupes, nombre total)
        """
        try:
            profil = acting_user.profil
            
            # Construire la requête
            membres_queryset = MembreGroupe.objects.filter(
                profil=profil,
                deleted=False
            )
            
            # Filtrer par rôle si spécifié
            if role:
                if role not in ['membre', 'admin']:
                    raise ValidationError(f"Rôle invalide: {role}")
                membres_queryset = membres_queryset.filter(role=role)
            
            # Récupérer les IDs des groupes
            groupe_ids = membres_queryset.values_list('groupe_id', flat=True)
            
            # Récupérer les groupes
            queryset = Groupe.objects.filter(
                id__in=groupe_ids,
                deleted=False,
                status=Groupe.Status.ACTIF
            ).select_related('createur').annotate(
                user_role=F('membres__role')
            ).order_by('-created_at')
            
            total_items = queryset.count()
            
            # Pagination
            start = (page - 1) * page_size
            end = start + page_size
            groupes = list(queryset[start:end])
            
            logger.info(
                f"Mes groupes récupérés - Utilisateur: {acting_user.id}, "
                f"Nombre: {len(groupes)}"
            )
            
            return groupes, total_items
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des groupes: {str(e)}")
            raise
    
    @staticmethod
    def obtenir_details_groupe(
        acting_user: User,
        groupe_id: Optional[UUID] = None,
        slug: Optional[str] = None,
        request=None
    ) -> Groupe:
        """
        Obtient les détails complets d'un groupe avec annotations
        
        Args:
            acting_user: Utilisateur demandant les détails
            groupe_id: ID du groupe (optionnel)
            slug: Slug du groupe (optionnel)
            request: Requête HTTP (optionnel)
        
        Returns:
            Groupe: Le groupe avec annotations (is_member, is_admin, pending_request, etc.)
        
        Raises:
            ValidationError: Si ni groupe_id ni slug n'est fourni, ou si le groupe n'existe pas
        """
        if not groupe_id and not slug:
            raise ValidationError("ID ou slug du groupe requis")
        
        try:
            profil = acting_user.profil
            est_admin = acting_user.is_admin_user()
            
            # Construire les filtres
            filters = {'deleted': False}
            if groupe_id:
                filters['id'] = groupe_id
            else:
                filters['slug'] = slug
            
            # Construire la requête de base
            queryset = Groupe.objects.filter(**filters).select_related('createur')
            
            # Exclure les groupes inactifs si l'utilisateur n'est pas admin
            if not est_admin:
                queryset = queryset.exclude(Q(status=Groupe.Status.INACTIF))
            
            # Annotations pour les demandes en attente
            count_demandes = DemandeAccesGroupe.objects.filter(
                groupe_id=OuterRef('id'),
                status=DemandeAccesGroupe.Status.EN_ATTENTE,
                deleted=False
            ).values('groupe_id').annotate(total=Count('id')).values('total')
            
            # Annotations pour les membres
            count_membres = MembreGroupe.objects.filter(
                groupe_id=OuterRef('id'),
                deleted=False
            ).values('groupe_id').annotate(total=Count('id')).values('total')
            
            # Annotations pour les messages
            count_messages = MessageGroupe.objects.filter(
                groupe_id=OuterRef('id'),
                deleted=False
            ).values('groupe_id').annotate(total=Count('id')).values('total')
            
            # Appliquer les annotations
            queryset = queryset.annotate(
                is_member=Exists(
                    MembreGroupe.objects.filter(
                        groupe_id=OuterRef('id'),
                        profil=profil,
                        deleted=False
                    )
                ),
                is_admin=Exists(
                    MembreGroupe.objects.filter(
                        groupe_id=OuterRef('id'),
                        profil=profil,
                        role=MembreGroupe.Role.ADMIN,
                        deleted=False
                    )
                ),
                has_user_pending_request=Exists(
                    DemandeAccesGroupe.objects.filter(
                        groupe_id=OuterRef('id'),
                        demandeur=profil,
                        status=DemandeAccesGroupe.Status.EN_ATTENTE,
                        deleted=False
                    )
                ),
                # Utilisation de Subquery pour les counts
                # Coalesce permet de renvoyer 0 au lieu de NULL si aucune ligne n'est trouvée
                pending_request=Coalesce(
                    Subquery(count_demandes, output_field=IntegerField()),
                    0
                ),
                nb_members=Coalesce(
                    Subquery(count_membres, output_field=IntegerField()),
                    0
                ),
                nb_messages=Coalesce(
                    Subquery(count_messages, output_field=IntegerField()),
                    0
                )
            )
            
            # Récupérer le groupe
            groupe = queryset.first()
            
            if not groupe:
                identifier = f"ID: {groupe_id}" if groupe_id else f"Slug: {slug}"
                logger.error(f"Groupe introuvable - {identifier}")
                raise ValidationError("Groupe introuvable")
            
            logger.info(
                f"Détails groupe récupérés - Groupe: {groupe.nom}, "
                f"Par: {acting_user.id}"
            )
            
            return groupe
            
        except Groupe.DoesNotExist:
            identifier = f"ID: {groupe_id}" if groupe_id else f"Slug: {slug}"
            logger.error(f"Groupe introuvable - {identifier}")
            raise ValidationError("Groupe introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails: {str(e)}")
            raise
    
    @staticmethod
    def obtenir_membres_groupe(
        acting_user: User,
        groupe_id: UUID,
        page: int = 1,
        page_size: int = 20,
        request=None
    ) -> tuple[List[MembreGroupe], int]:
        """
        Obtient les membres d'un groupe
        
        Args:
            acting_user: Utilisateur demandant les membres
            groupe_id: ID du groupe
            request: Requête HTTP (optionnel)
        
        Returns:
            List[MembreGroupe]: Liste des membres du groupe
        """
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.get(
                id=groupe_id,
                deleted=False,
                status=Groupe.Status.ACTIF
            )
            
            # Récupérer les membres
            membres = MembreGroupe.objects.filter(
                groupe=groupe,
                deleted=False
            ).select_related('profil').order_by('-created_at')
            
            total_items = membres.count()
            
            # Pagination
            start = (page - 1) * page_size
            end = start + page_size
            membres = list(membres[start:end])
                        
            return membres, total_items
            
        except Groupe.DoesNotExist:
            logger.error(f"Groupe introuvable: {groupe_id}")
            raise ValidationError("Groupe introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des membres: {str(e)}")
            raise
       
    
    @staticmethod
    @transaction.atomic
    def rejoindre_groupe_public(
        acting_user: User,
        groupe_id: UUID,
        request=None
    ) -> MembreGroupe:
        """
        Rejoindre directement un groupe public
        
        Args:
            acting_user: Utilisateur rejoignant le groupe
            groupe_id: ID du groupe
            request: Requête HTTP (optionnel)
        
        Returns:
            MembreGroupe: Le membre créé
        
        Raises:
            ValidationError: Si le groupe n'est pas public ou si l'utilisateur est déjà membre
            PermissionDenied: Si le groupe est privé
        """
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.get(
                id=groupe_id,
                deleted=False,
                status=Groupe.Status.ACTIF
            )
            
            # Vérifier que le groupe est public
            if groupe.type_acces != Groupe.TypeAcces.PUBLIC:
                raise PermissionDenied(
                    "Ce groupe est privé. Vous devez faire une demande d'accès."
                )
            
            # Vérifier que l'utilisateur n'est pas déjà membre
            if groupe.est_membre(profil):
                raise ValidationError("Vous êtes déjà membre de ce groupe")
            
            # Ajouter l'utilisateur comme membre
            membre = MembreGroupe.objects.create(
                groupe=groupe,
                profil=profil,
                role=MembreGroupe.Role.MEMBRE
            )
            
            logger.info(
                f"Utilisateur a rejoint le groupe public - Groupe: {groupe.nom}, "
                f"Utilisateur: {acting_user.id}"
            )
            
            return membre
            
        except Groupe.DoesNotExist:
            logger.error(f"Groupe introuvable: {groupe_id}")
            raise ValidationError("Groupe introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la jonction au groupe: {str(e)}")
            raise
    
        
    @staticmethod
    @transaction.atomic
    def creer_demande_acces(
        acting_user: User,
        groupe_id: UUID,
        message: Optional[str] = None,
        request=None
    ) -> DemandeAccesGroupe:
        """
        Crée une demande d'accès à un groupe privé
        
        Args:
            acting_user: Utilisateur faisant la demande
            groupe_id: ID du groupe
            message: Message optionnel expliquant la demande
            request: Requête HTTP (optionnel)
        
        Returns:
            DemandeAccesGroupe: La demande créée
        
        Raises:
            ValidationError: Si les données sont invalides
            PermissionDenied: Si le groupe n'est pas privé
        """
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.get(
                id=groupe_id,
                deleted=False,
                status=Groupe.Status.ACTIF
            )
            
            # Vérifier que le groupe est privé
            if groupe.type_acces != Groupe.TypeAcces.PRIVE:
                raise ValidationError(
                    "Les demandes d'accès ne sont possibles que pour les groupes privés. "
                    "Ce groupe est public, vous pouvez le rejoindre directement."
                )
            
            # Vérifier que l'utilisateur n'est pas déjà membre
            if groupe.est_membre(profil):
                raise ValidationError("Vous êtes déjà membre de ce groupe")
            
            # Vérifier qu'il n'y a pas déjà une demande en attente
            demande_existante = DemandeAccesGroupe.objects.filter(
                groupe=groupe,
                demandeur=profil,
                status=DemandeAccesGroupe.Status.EN_ATTENTE,
                deleted=False
            ).first()
            
            if demande_existante:
                raise ValidationError(
                    "Vous avez déjà une demande en attente pour ce groupe"
                )
            
            # Valider le message si fourni
            if message and len(message) > 1000:
                raise ValidationError(
                    "Le message ne doit pas dépasser 1000 caractères"
                )
            
            # Créer la demande
            demande = DemandeAccesGroupe.objects.create(
                groupe=groupe,
                demandeur=profil,
                message=message or "",
                status=DemandeAccesGroupe.Status.EN_ATTENTE
            )
            
            logger.info(
                f"Demande d'accès créée - Groupe: {groupe.nom}, "
                f"Demandeur: {acting_user.id}, "
                f"Demande ID: {demande.id}"
            )
            
            return demande
            
        except Groupe.DoesNotExist:
            logger.error(f"Groupe introuvable: {groupe_id}")
            raise ValidationError("Groupe introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la création de la demande: {str(e)}")
            raise
    
    
        
    @staticmethod
    @transaction.atomic
    def approuver_demande(
        acting_user: User,
        demande_id: UUID,
        request=None
    ) -> MembreGroupe:
        """
        Approuve une demande d'accès et ajoute le demandeur au groupe
        
        Args:
            acting_user: Administrateur approuvant la demande
            demande_id: ID de la demande
            request: Requête HTTP (optionnel)
        
        Returns:
            MembreGroupe: Le membre ajouté au groupe
        
        Raises:
            ValidationError: Si la demande ne peut pas être approuvée
            PermissionDenied: Si l'utilisateur n'est pas administrateur
        """
        try:
            profil = acting_user.profil
            demande = DemandeAccesGroupe.objects.select_for_update().get(
                id=demande_id,
                deleted=False
            )
            
            # Vérifier que l'utilisateur est admin du groupe
            if not demande.groupe.est_admin(profil):
                raise PermissionDenied(
                    "Seuls les administrateurs du groupe peuvent approuver les demandes"
                )
            
            # Vérifier que la demande est en attente
            if demande.status != DemandeAccesGroupe.Status.EN_ATTENTE:
                raise ValidationError(
                    f"Cette demande a déjà été traitée (statut: {demande.get_status_display()})"
                )
            
            # Vérifier que le demandeur n'est pas déjà membre
            # (au cas où il aurait été ajouté autrement entre-temps)
            if demande.groupe.est_membre(demande.demandeur):
                demande.status = DemandeAccesGroupe.Status.APPROUVE
                demande.date_traitement = timezone.now()
                demande.traite_par = profil
                demande.save(update_fields=['status', 'date_traitement', 'traite_par', 'updated_at'])
                
                raise ValidationError(
                    "Le demandeur est déjà membre du groupe"
                )
            
            # Mettre à jour la demande
            demande.status = DemandeAccesGroupe.Status.APPROUVE
            demande.date_traitement = timezone.now()
            demande.traite_par = profil
            demande.save(update_fields=['status', 'date_traitement', 'traite_par', 'updated_at'])
            
            # Ajouter le demandeur comme membre
            membre = MembreGroupe.objects.create(
                groupe=demande.groupe,
                profil=demande.demandeur,
                role=MembreGroupe.Role.MEMBRE
            )
            
            logger.info(
                f"Demande approuvée - Groupe: {demande.groupe.nom}, "
                f"Demandeur: {demande.demandeur.user.id}, "
                f"Approuvé par: {acting_user.id}"
            )
            
            return membre
            
        except DemandeAccesGroupe.DoesNotExist:
            logger.error(f"Demande introuvable: {demande_id}")
            raise ValidationError("Demande introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de l'approbation de la demande: {str(e)}")
            raise
         
    
        
    @staticmethod
    @transaction.atomic
    def refuser_demande(
        acting_user: User,
        demande_id: UUID,
        request=None
    ) -> DemandeAccesGroupe:
        """
        Refuse une demande d'accès
        
        Args:
            acting_user: Administrateur refusant la demande
            demande_id: ID de la demande
            request: Requête HTTP (optionnel)
        
        Returns:
            DemandeAccesGroupe: La demande refusée
        
        Raises:
            ValidationError: Si la demande ne peut pas être refusée
            PermissionDenied: Si l'utilisateur n'est pas administrateur
        """
        try:
            profil = acting_user.profil
            demande = DemandeAccesGroupe.objects.select_for_update().get(
                id=demande_id,
                deleted=False
            )
            
            # Vérifier que l'utilisateur est admin du groupe
            if not demande.groupe.est_admin(profil):
                raise PermissionDenied(
                    "Seuls les administrateurs du groupe peuvent refuser les demandes"
                )
            
            # Vérifier que la demande est en attente
            if demande.status != DemandeAccesGroupe.Status.EN_ATTENTE:
                raise ValidationError(
                    f"Cette demande a déjà été traitée (statut: {demande.get_status_display()})"
                )
            
            # Mettre à jour la demande
            demande.status = DemandeAccesGroupe.Status.REFUSE
            demande.date_traitement = timezone.now()
            demande.traite_par = profil
            demande.save(update_fields=['status', 'date_traitement', 'traite_par', 'updated_at'])
            
            logger.info(
                f"Demande refusée - Groupe: {demande.groupe.nom}, "
                f"Demandeur: {demande.demandeur.user.id}, "
                f"Refusé par: {acting_user.id}"
            )
            
            return demande
            
        except DemandeAccesGroupe.DoesNotExist:
            logger.error(f"Demande introuvable: {demande_id}")
            raise ValidationError("Demande introuvable")
        except Exception as e:
            logger.error(f"Erreur lors du refus de la demande: {str(e)}")
            raise
        
    
        
    @staticmethod
    @transaction.atomic
    def annuler_demande(
        acting_user: User,
        demande_id: UUID,
        request=None
    ) -> bool:
        """
        Annule une demande d'accès (par le demandeur)
        
        Args:
            acting_user: Utilisateur annulant sa demande
            demande_id: ID de la demande
            request: Requête HTTP (optionnel)
        
        Returns:
            bool: True si l'annulation a réussi
        
        Raises:
            ValidationError: Si la demande ne peut pas être annulée
            PermissionDenied: Si l'utilisateur n'est pas le demandeur
        """
        try:
            profil = acting_user.profil
            demande = DemandeAccesGroupe.objects.select_for_update().get(
                id=demande_id,
                deleted=False
            )
            
            # Vérifier que l'utilisateur est le demandeur
            if demande.demandeur != profil:
                raise PermissionDenied(
                    "Vous ne pouvez annuler que vos propres demandes"
                )
            
            # Vérifier que la demande est en attente
            if demande.status != DemandeAccesGroupe.Status.EN_ATTENTE:
                raise ValidationError(
                    f"Cette demande a déjà été traitée et ne peut plus être annulée"
                )
            
            # Soft delete de la demande
            demande.deleted = True
            demande.save(update_fields=['deleted', 'updated_at'])
            
            logger.info(
                f"Demande annulée - Groupe: {demande.groupe.nom}, "
                f"Demandeur: {acting_user.id}"
            )
            
            return True
            
        except DemandeAccesGroupe.DoesNotExist:
            logger.error(f"Demande introuvable: {demande_id}")
            raise ValidationError("Demande introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation de la demande: {str(e)}")
            raise
        
        
    
        
    @staticmethod
    def obtenir_demandes_groupe(
        acting_user: User,
        groupe_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        request=None
    ) -> tuple[List[DemandeAccesGroupe], int]:
        """
        Obtient les demandes d'accès d'un groupe (pour les admins)
        
        Args:
            acting_user: Administrateur du groupe
            groupe_id: ID du groupe
            status: Filtrer par statut (optionnel)
            page: Numéro de page
            page_size: Taille de page
            request: Requête HTTP (optionnel)
        
        Returns:
            tuple: (Liste des demandes, nombre total)
        
        Raises:
            PermissionDenied: Si l'utilisateur n'est pas administrateur
        """
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.get(
                id=groupe_id,
                deleted=False
            )
            
            # Vérifier que l'utilisateur est admin du groupe
            if not groupe.est_admin(profil):
                raise PermissionDenied(
                    "Seuls les administrateurs peuvent voir les demandes d'accès"
                )
            
            # Construire la requête
            queryset = DemandeAccesGroupe.objects.filter(
                groupe=groupe,
                deleted=False
            ).select_related('demandeur', 'traite_par')
            
            # Filtrer par statut si spécifié
            if status:
                if status not in [s[0] for s in DemandeAccesGroupe.Status.choices]:
                    raise ValidationError(f"Statut invalide: {status}")
                queryset = queryset.filter(status=status)
            
            queryset = queryset.order_by('-created_at')
            total_items = queryset.count()
            
            # Pagination
            start = (page - 1) * page_size
            end = start + page_size
            demandes = list(queryset[start:end])
            
            logger.info(
                f"Demandes récupérées - Groupe: {groupe.nom}, "
                f"Nombre: {len(demandes)}"
            )
            
            return demandes, total_items
            
        except Groupe.DoesNotExist:
            logger.error(f"Groupe introuvable: {groupe_id}")
            raise ValidationError("Groupe introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des demandes: {str(e)}")
            raise
    
        
    @staticmethod
    def obtenir_mes_demandes(
        acting_user: User,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        request=None
    ) -> tuple[List[DemandeAccesGroupe], int]:
        """
        Obtient les demandes d'accès de l'utilisateur
        
        Args:
            acting_user: Utilisateur
            status: Filtrer par statut (optionnel)
            page: Numéro de page
            page_size: Taille de page
            request: Requête HTTP (optionnel)
        
        Returns:
            tuple: (Liste des demandes, nombre total)
        """
        try:
            profil = acting_user.profil
            
            # Construire la requête
            queryset = DemandeAccesGroupe.objects.filter(
                demandeur=profil,
                deleted=False
            ).select_related('groupe', 'traite_par')
            
            # Filtrer par statut si spécifié
            if status:
                if status not in [s[0] for s in DemandeAccesGroupe.Status.choices]:
                    raise ValidationError(f"Statut invalide: {status}")
                queryset = queryset.filter(status=status)
            
            queryset = queryset.order_by('-created_at')
            total_items = queryset.count()
            
            # Pagination
            start = (page - 1) * page_size
            end = start + page_size
            demandes = list(queryset[start:end])
            
            logger.info(
                f"Mes demandes récupérées - Utilisateur: {acting_user.id}, "
                f"Nombre: {len(demandes)}"
            )
            
            return demandes, total_items
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des demandes: {str(e)}")
            raise
    
    
    @staticmethod
    @transaction.atomic
    def ajouter_membre_groupe(
        acting_user: User,
        groupe_id: UUID,
        profil_id: UUID,
        role: str = 'membre',
        request=None
    ) -> MembreGroupe:
        """
        Ajoute un membre à un groupe (invitation par un admin)
        
        Args:
            acting_user: Administrateur ajoutant le membre
            groupe_id: ID du groupe
            profil_id: ID du profil à ajouter
            role: Rôle du membre ('membre' ou 'admin')
            request: Requête HTTP (optionnel)
        
        Returns:
            MembreGroupe: Le membre ajouté
        
        Raises:
            ValidationError: Si les données sont invalides
            PermissionDenied: Si l'utilisateur n'a pas les droits
        """
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.get(
                id=groupe_id,
                deleted=False,
                status=Groupe.Status.ACTIF
            )
            
            profil_to_add = Profil.objects.get(
                id=profil_id,
                deleted=False
            )
            
            # Vérifier les permissions
            if not groupe.est_admin(profil):
                raise PermissionDenied("Vous devez être administrateur pour ajouter des membres")
            
            # Vérifier que le profil n'est pas déjà membre
            if groupe.est_membre(profil_to_add):
                raise ValidationError("Ce profil est déjà membre du groupe")
            
            # Valider le rôle
            if role not in ['membre', 'admin']:
                raise ValidationError(f"Rôle invalide: {role}")
            
            # Créer le membre
            membre = MembreGroupe.objects.create(
                groupe=groupe,
                profil=profil_to_add,
                role=role
            )
            
            # NOUVELLE LOGIQUE : Si le profil ajouté avait une demande en attente, l'approuver automatiquement
            demande_en_attente = DemandeAccesGroupe.objects.filter(
                groupe=groupe,
                demandeur=profil_to_add,
                status=DemandeAccesGroupe.Status.EN_ATTENTE,
                deleted=False
            ).first()
            
            if demande_en_attente:
                from django.utils import timezone
                demande_en_attente.status = DemandeAccesGroupe.Status.APPROUVE
                demande_en_attente.date_traitement = timezone.now()
                demande_en_attente.traite_par = profil
                demande_en_attente.save(update_fields=['status', 'date_traitement', 'traite_par', 'updated_at'])
                
                logger.info(
                    f"Demande d'accès approuvée automatiquement lors de l'ajout - "
                    f"Demande ID: {demande_en_attente.id}"
                )
            
            logger.info(
                f"Membre ajouté au groupe - Groupe: {groupe.nom}, "
                f"Membre: {profil_to_add.user.id}, "
                f"Rôle: {role}, "
                f"Par: {acting_user.id}"
            )
            
            return membre
            
        except Groupe.DoesNotExist:
            logger.error(f"Groupe introuvable: {groupe_id}")
            raise ValidationError("Groupe introuvable")
        except Profil.DoesNotExist:
            logger.error(f"Profil introuvable: {profil_id}")
            raise ValidationError("Profil introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du membre: {str(e)}")
            raise

    
    @staticmethod
    @transaction.atomic
    def quitter_groupe(
        acting_user: User,
        groupe_id: UUID,
        request=None
    ) -> bool:
        """
        Quitte un groupe
        
        Args:
            acting_user: Utilisateur quittant le groupe
            groupe_id: ID du groupe
            request: Requête HTTP (optionnel)
        
        Returns:
            bool: True si le départ a réussi
        
        Raises:
            ValidationError: Si le départ n'est pas possible
        """
        try:
            profil = acting_user.profil
            membre = MembreGroupe.objects.select_for_update().get(
                groupe_id=groupe_id,
                profil=profil,
                deleted=False
            )
            
            # Empêcher de quitter si c'est le dernier admin
            if membre.role == 'admin':
                nb_admins = MembreGroupe.objects.filter(
                    groupe=membre.groupe,
                    role='admin',
                    deleted=False
                ).count()
                
                if nb_admins <= 1:
                    raise ValidationError(
                        "Vous ne pouvez pas quitter le groupe car vous êtes le dernier administrateur. "
                        "Nommez un autre administrateur ou supprimez le groupe."
                    )
            
            membre.deleted = True
            membre.save()
            
            logger.info(
                f"Membre a quitté le groupe - Groupe: {membre.groupe.nom}, "
                f"Membre: {acting_user.id}"
            )
            
            return True
            
        except MembreGroupe.DoesNotExist:
            logger.error(f"Membre introuvable pour le groupe: {groupe_id}")
            raise ValidationError("Vous n'êtes pas membre de ce groupe")
        except Exception as e:
            logger.error(f"Erreur lors du départ du groupe: {str(e)}")
            raise


    @staticmethod
    @transaction.atomic
    def retirer_membre_groupe(
        acting_user: User,
        profil_id: UUID,
        group_id: UUID,
        request=None
    ) -> bool:
        """
        Retire un membre du groupe (par un admin)
        Args:
            acting_user: Administrateur retirant le membre
            profil_id: ID du profil à retirer
            group_id: ID du groupe
            request: Requête HTTP (optionnel)
        Returns:
            bool: True si le retrait a réussi
        Raises:
            PermissionDenied: Si l'utilisateur n'a pas les droits
        """
        try:
            profil = acting_user.profil
            membre = MembreGroupe.objects.select_for_update().get(
                groupe__id=group_id,
                profil__id=profil_id,
                deleted=False
            )
            # Vérifier les permissions
            if not membre.groupe.est_admin(profil):
                raise PermissionDenied("Vous devez être administrateur pour retirer des membres")
            # Empêcher de retirer le dernier admin
            if membre.role == 'admin':
                nb_admins = MembreGroupe.objects.filter(
                    groupe=membre.groupe,
                    role='admin',
                    deleted=False
                ).count()
                if nb_admins <= 1:
                    raise ValidationError("Impossible de retirer le dernier administrateur")
            membre.deleted = True
            membre.save()
            logger.info(
                f"Membre retiré du groupe - Groupe: {membre.groupe.nom}, "
                f"Membre: {membre.profil.user.id}, "
                f"Par: {acting_user.id}"
            )
            return True
        except MembreGroupe.DoesNotExist:
            logger.error(f"Association membre-groupe introuvable: profil {profil_id}, groupe {group_id}")
            raise ValidationError("Association membre-groupe introuvable")
        except Exception as e:
            logger.error(f"Erreur lors du retrait du membre: {str(e)}")
            raise
    
    # ============================================
    # GESTION DES MESSAGES DE GROUPE
    # ============================================
    
    @staticmethod
    @transaction.atomic
    def envoyer_message_groupe(
        acting_user: User,
        groupe_id: UUID,
        contenu: str,
        reponse_a_id: Optional[UUID] = None,
        piece_jointe_base64: Optional[str] = None,
        request=None
    ) -> MessageGroupe:
        """
        Envoie un message dans un groupe
        
        Args:
            acting_user: Utilisateur envoyant le message
            groupe_id: ID du groupe
            contenu: Contenu du message
            reponse_a_id: ID du message auquel on répond (optionnel)
            piece_jointe_base64: Pièce jointe en base64 (optionnel)
            request: Requête HTTP (optionnel)
        
        Returns:
            MessageGroupe: Le message créé
        
        Raises:
            ValidationError: Si les données sont invalides
            PermissionDenied: Si l'utilisateur n'est pas membre du groupe
        """
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.get(
                id=groupe_id,
                deleted=False,
                status=Groupe.Status.ACTIF
            )
            
            # Vérifier que l'utilisateur est membre du groupe
            if not groupe.est_membre(profil):
                raise PermissionDenied("Vous devez être membre du groupe pour envoyer des messages")
            
            # Valider le contenu
            if not contenu.strip():
                raise ValidationError("Le contenu ne peut pas être vide")
            
            if len(contenu) > 10000:
                raise ValidationError("Le contenu ne doit pas dépasser 10000 caractères")
            
            # Récupérer le message parent si c'est une réponse
            reponse_a = None
            if reponse_a_id:
                try:
                    reponse_a = MessageGroupe.objects.get(
                        id=reponse_a_id,
                        groupe=groupe,
                        deleted=False
                    )
                except MessageGroupe.DoesNotExist:
                    raise ValidationError("Message parent introuvable")
            
            # Créer le message
            message = MessageGroupe.objects.create(
                groupe=groupe,
                expediteur=profil,
                contenu=contenu,
                reponse_a=reponse_a
            )
            
            # Traiter la pièce jointe si fournie
            if piece_jointe_base64:
                base64_file_handler = Base64FileHandler()
                
                try:

                    file_data = base64_file_handler.handle(
                        piece_jointe_base64, 
                        filename_prefix='message_groupe_attachment'
                    )
                    message.piece_jointe = file_data
                    message.save()
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement de la pièce jointe: {str(e)}")
            
            logger.info(
                f"Message groupe envoyé - Groupe: {groupe.nom}, "
                f"Expéditeur: {acting_user.id}, "
                f"Message ID: {message.id}"
            )
            
            return message
            
        except Groupe.DoesNotExist:
            logger.error(f"Groupe introuvable: {groupe_id}")
            raise ValidationError("Groupe introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message: {str(e)}")
            raise
    
    
    @staticmethod
    def obtenir_messages_groupe(
        acting_user: User,
        groupe_id: UUID,
        page: int = 1,
        page_size: int = 20,
        request=None
    ) -> tuple[List[MessageGroupe], int]:
        """
        Obtient les messages d'un groupe
        
        Args:
            acting_user: Utilisateur demandant les messages
            groupe_id: ID du groupe
            limit: Nombre maximum de messages à retourner
            offset: Décalage pour la pagination
            request: Requête HTTP (optionnel)
        
        Returns:
            List[MessageGroupe]: Liste des messages
        
        Raises:
            PermissionDenied: Si l'utilisateur n'est pas membre
        """
        try:
            profil = acting_user.profil
            groupe = Groupe.objects.get(
                id=groupe_id,
                deleted=False,
                status=Groupe.Status.ACTIF
            )
            
            # Vérifier que l'utilisateur est membre
            if not groupe.est_membre(profil):
                raise PermissionDenied("Vous devez être membre du groupe pour voir les messages")
            
            queryset = MessageGroupe.objects.filter(
                groupe=groupe,
                deleted=False
            ).select_related('expediteur', 'reponse_a__expediteur').order_by('created_at')
            
            total_items = queryset.count()
            # Pagination
            start = (page - 1) * page_size
            end = start + page_size
            queryset = queryset[start:end]
            messages = list(queryset)
            
            logger.info(
                f"Messages groupe récupérés - Groupe: {groupe.nom}, "
                f"Nombre: {len(messages)}"
            )
            
            return messages, total_items
            
        except Groupe.DoesNotExist:
            logger.error(f"Groupe introuvable: {groupe_id}")
            raise ValidationError("Groupe introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des messages: {str(e)}")
            raise

 
    @staticmethod
    @transaction.atomic
    def marquer_message_groupe_lu(
        acting_user: User,
        message_id: UUID,
        request=None
    ) -> MessageGroupe:
        """Marque un message de groupe comme lu"""
        try:
            profil = acting_user.profil
            message = MessageGroupe.objects.select_for_update().get(
                id=message_id,
                deleted=False
            )
            
            # Vérifier que l'utilisateur est membre du groupe
            if not message.groupe.est_membre(profil):
                raise PermissionDenied("Accès non autorisé")
            
            if not message.est_lu:
                message.marquer_comme_lu()
            
            return message
            
        except MessageGroupe.DoesNotExist:
            logger.error(f"Message introuvable: {message_id}")
            raise ValidationError("Message introuvable")
        except Exception as e:
            logger.error(f"Erreur lors du marquage du message: {str(e)}")
            raise
    

    
    # ============================================
    # GESTION DES MESSAGES DIRECTS
    # ============================================
    
    @staticmethod
    @transaction.atomic
    def envoyer_message_direct(
        acting_user: User,
        destinataire_id: UUID,
        contenu: str,
        piece_jointe_base64: Optional[str] = None,
        request=None
    ) -> MessageDirect:
        """
        Envoie un message direct à un utilisateur
        
        Args:
            acting_user: Utilisateur envoyant le message
            destinataire_id: ID du destinataire
            contenu: Contenu du message
            piece_jointe_base64: Pièce jointe en base64 (optionnel)
            request: Requête HTTP (optionnel)
        
        Returns:
            MessageDirect: Le message créé
        
        Raises:
            ValidationError: Si les données sont invalides
        """
        try:
            profil = acting_user.profil
            destinataire = Profil.objects.get(
                id=destinataire_id,
                deleted=False
            )
            
            # Empêcher de s'envoyer un message à soi-même
            if acting_user.id == destinataire.id:
                raise ValidationError("Vous ne pouvez pas vous envoyer un message à vous-même")
            
            # Valider le contenu
            if not contenu.strip():
                raise ValidationError("Le contenu ne peut pas être vide")
            
            if len(contenu) > 10000:
                raise ValidationError("Le contenu ne doit pas dépasser 10000 caractères")
            
            # Créer le message
            message = MessageDirect.objects.create(
                expediteur=profil,
                destinataire=destinataire,
                contenu=contenu
            )
            
            # Traiter la pièce jointe si fournie
            if piece_jointe_base64:
                base64_file_handler = Base64FileHandler()
                try:
                    file_data = base64_file_handler.handle(
                        piece_jointe_base64, 
                        filename_prefix=f'message_direct_attachment'
                    )
                    message.piece_jointe = file_data
                    message.save()
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement de la pièce jointe: {str(e)}")
            
            logger.info(
                f"Message direct envoyé - De: {acting_user.id}, "
                f"À: {destinataire.user.id}, "
                f"Message ID: {message.id}"
            )
            
            return message
            
        except Profil.DoesNotExist:
            logger.error(f"Destinataire introuvable: {destinataire_id}")
            raise ValidationError("Destinataire introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message direct: {str(e)}")
            raise

    
    @staticmethod
    def obtenir_conversation(
        acting_user: User,
        autre_profil_id: UUID,
        limit: Optional[int] = 50,
        offset: int = 0,
        request=None
    ) -> List[MessageDirect]:
        """
        Obtient la conversation entre deux utilisateurs
        
        Args:
            acting_user: Utilisateur demandant la conversation
            autre_profil_id: ID de l'autre utilisateur
            limit: Nombre maximum de messages
            offset: Décalage pour la pagination
            request: Requête HTTP (optionnel)
        
        Returns:
            List[MessageDirect]: Liste des messages de la conversation
        """
        try:
            autre_profil = Profil.objects.get(
                id=autre_profil_id,
                deleted=False
            )
            
            queryset = MessageDirect.get_conversation(acting_user.profil, autre_profil)
            
            if limit:
                queryset = queryset[offset:offset+limit]
            
            messages = list(queryset)
            
            logger.info(
                f"Conversation récupérée - Entre: {acting_user.id} "
                f"et {autre_profil.user.id}, "
                f"Nombre: {len(messages)}"
            )
            
            return messages
            
        except Profil.DoesNotExist:
            logger.error(f"Profil introuvable: {autre_profil_id}")
            raise ValidationError("Profil introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la conversation: {str(e)}")
            raise
        

    
    @staticmethod
    def obtenir_conversations_recentes(
        acting_user: User,
        request=None
    ) -> List[Dict[str, Any]]:
        """
        Obtient les conversations récentes d'un utilisateur
        
        Args:
            acting_user: Utilisateur demandant les conversations
            request: Requête HTTP (optionnel)
        
        Returns:
            List[Dict]: Liste des conversations avec derniers messages
        """
        try:
            profil = acting_user.profil
            # Obtenir les IDs des contacts
            contact_ids = MessageDirect.get_conversations_recentes(profil)
            
            # Récupérer les profils et derniers messages
            conversations = []
            for contact_id in contact_ids:
                try:
                    contact = Profil.objects.get(id=contact_id, deleted=False)
                    
                    # Récupérer le dernier message
                    dernier_message = MessageDirect.objects.filter(
                        Q(expediteur=profil, destinataire=contact) |
                        Q(expediteur=contact, destinataire=profil),
                        deleted=False
                    ).order_by('-created_at').first()
                    
                    # Compter les messages non lus
                    messages_non_lus = MessageDirect.objects.filter(
                        expediteur=contact,
                        destinataire=profil,
                        est_lu=False,
                        deleted=False
                    ).count()
                    
                    conversations.append({
                        'contact': contact,
                        'dernier_message': dernier_message,
                        'messages_non_lus': messages_non_lus,
                    })
                except Profil.DoesNotExist:
                    continue
            
            # Trier par date du dernier message
            conversations.sort(
                key=lambda x: x['dernier_message'].created_at if x['dernier_message'] else (datetime.min if not settings.USE_TZ else datetime.min.replace(tzinfo=timezone.utc)),
                reverse=True
            )
            
            logger.info(
                f"Conversations récentes récupérées - Utilisateur: {acting_user.id}, "
                f"Nombre: {len(conversations)}"
            )
            
            return conversations
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des conversations: {str(e)}")
            raise

    
    @staticmethod
    @transaction.atomic
    def marquer_conversation_lue(
        acting_user: User,
        expediteur_id: UUID,
        request=None
    ) -> int:
        """
        Marque tous les messages d'une conversation comme lus
        
        Args:
            acting_user: Utilisateur (destinataire)
            expediteur_id: ID de l'expéditeur
            request: Requête HTTP (optionnel)
        
        Returns:
            int: Nombre de messages marqués comme lus
        """
        try:
            profil = acting_user.profil
            expediteur = Profil.objects.get(
                id=expediteur_id,
                deleted=False
            )
            
            MessageDirect.marquer_conversation_comme_lue(expediteur,profil)
            
            nb_messages = MessageDirect.objects.filter(
                expediteur=expediteur,
                destinataire=profil,
                est_lu=True,
                deleted=False
            ).count()
            
            logger.info(
                f"Conversation marquée comme lue - Entre: {expediteur.user.id} "
                f"et {acting_user.id}, "
                f"Messages: {nb_messages}"
            )
            
            return nb_messages
            
        except Profil.DoesNotExist:
            logger.error(f"Expéditeur introuvable: {expediteur_id}")
            raise ValidationError("Expéditeur introuvable")
        except Exception as e:
            logger.error(f"Erreur lors du marquage de la conversation: {str(e)}")
            raise


    
    @staticmethod
    def obtenir_statistiques_messages(
        acting_user: User,
        request=None
    ) -> Dict[str, Any]:
        """Obtient les statistiques de messagerie d'un utilisateur"""
        try:
            # Messages directs
            profil = acting_user.profil
            messages_directs_envoyes = MessageDirect.objects.filter(
                expediteur=profil,
                deleted=False
            ).count()
            
            messages_directs_recus = MessageDirect.objects.filter(
                destinataire=profil,
                deleted=False
            ).count()
            
            messages_non_lus = MessageDirect.get_non_lus_count(profil)
            
            # Groupes
            groupes_membre = MembreGroupe.objects.filter(
                profil=profil,
                deleted=False
            ).count()
            
            groupes_admin = MembreGroupe.objects.filter(
                profil=profil,
                role='admin',
                deleted=False
            ).count()
            
            stats = {
                'messages_directs': {
                    'envoyes': messages_directs_envoyes,
                    'recus': messages_directs_recus,
                    'non_lus': messages_non_lus,
                },
                'groupes': {
                    'total': groupes_membre,
                    'admin': groupes_admin,
                    'membre': groupes_membre - groupes_admin,
                }
            }
            
            logger.info(f"Statistiques messages générées pour: {acting_user.id}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {str(e)}")
            raise


