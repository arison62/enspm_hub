# network/services/organisation.py

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils.text import slugify
from django.db.models import Count, Q

from core.api.exceptions import BaseAPIException
from core.utils.base64_utils import Base64FileHandler, Base64ImageHandler
from core.utils.generate_unique_slug import generate_unique_slug
from network.models.organisation import (
    Organisation, MembreOrganisation, AbonnementOrganisation
)
from users.models import Profil
from core.models import SecteurActivite, User

logger = logging.getLogger(__name__)




class OrganisationService:
    """Service de gestion des organisations et de leurs membres"""
    
    # ============================================
    # GESTION DES ORGANISATIONS
    # ============================================
    
    @staticmethod
    @transaction.atomic
    def creer_organisation(
        acting_user: User,
        nom_organisation: str,
        description: str,
        type_organisation: str,
        site_web: Optional[str] = None,
        adresse: Optional[str] = None,
        ville: Optional[str] = None,
        pays: Optional[str] = None,
        secteur_activites: Optional[List[UUID]] = None,
        logo_base64: Optional[str] = None,
        request=None
    ) -> Organisation:
        """
        Crée une nouvelle organisation
        
        Args:
            acting_user: Utilisateur créant l'organisation
            nom_organisation: Nom de l'organisation
            description: Description de l'organisation
            type_organisation: Type (entreprise, startup, etc.)
            site_web: URL du site web
            adresse: Adresse physique
            ville: Ville
            pays: Code pays
            secteur_activites: Liste des IDs de secteurs d'activité
            logo_base64: Logo en base64
            request: Requête HTTP (optionnel)
        
        Returns:
            Organisation: L'organisation créée
        
        Raises:
            ValidationError: Si les données sont invalides
        """
        try:
            # Valider le type d'organisation
            profil = acting_user.profil
            types_valides = [choice[0] for choice in Organisation.TYPE_CHOICES]
            if type_organisation not in types_valides:
                raise ValidationError(f"Type d'organisation invalide: {type_organisation}")
            
            # Générer un slug unique
            slug = generate_unique_slug(nom_organisation, Organisation)
            if not slug:
                raise BaseAPIException("Impossible de generer un identifiant")
            
            # Créer l'organisation
            organisation = Organisation.objects.create(
                nom_organisation=nom_organisation,
                slug=slug,
                description=description,
                type_organisation=type_organisation,
                site_web=site_web or "",
                adresse=adresse or "",
                ville=ville or "",
                pays=pays or "",
                statut='en_attente' 
            )
            
            # Traiter le logo si fourni
            if logo_base64:
                
                base64_image_handler = Base64FileHandler()
                
                try:
                    logo_data = base64_image_handler.handle(
                        logo_base64,
                        filename_prefix="organisation_logo"
                        max_dimensions = (800, 800)
                    )
                    organisation.logo = logo_data
                    organisation.save()
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement du logo: {str(e)}")
            
            # Ajouter les secteurs d'activité
            if secteur_activites:
                secteurs = SecteurActivite.objects.filter(
                    id__in=secteur_activites,
                    deleted=False
                )
                organisation.secteur_activites.set(secteurs)
            
            # Ajouter le créateur comme administrateur
            MembreOrganisation.objects.create(
                profil=profil,
                organisation=organisation,
                acces='admin'
            )
            
            logger.info(
                f"Organisation créée - ID: {organisation.id}, "
                f"Nom: {nom_organisation}, "
                f"Créateur: {acting_user.id}"
            )
            
            return organisation
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'organisation: {str(e)}")
            raise


    
    @staticmethod
    @transaction.atomic
    def modifier_organisation(
        acting_user: User,
        organisation_id: UUID,
        nom_organisation: Optional[str] = None,
        description: Optional[str] = None,
        type_organisation: Optional[str] = None,
        site_web: Optional[str] = None,
        adresse: Optional[str] = None,
        ville: Optional[str] = None,
        pays: Optional[str] = None,
        statut: Optional[str] = None,
        secteur_activites: Optional[List[UUID]] = None,
        logo_base64: Optional[str] = None,
        request=None
    ) -> Organisation:
        """
        Modifie une organisation existante
        
        Args:
            acting_user: Utilisateur effectuant la modification
            organisation_id: ID de l'organisation
            (autres paramètres optionnels à modifier)
            request: Requête HTTP (optionnel)
        
        Returns:
            Organisation: L'organisation modifiée
        
        Raises:
            ValidationError: Si les données sont invalides
            PermissionDenied: Si l'utilisateur n'a pas les droits
        """
        try:
            profil = acting_user.profil
            organisation = Organisation.objects.select_for_update().get(
                id=organisation_id,
                deleted=False
            )
            
            # Vérifier les permissions (doit être admin de l'organisation)
            if not OrganisationService.est_admin_organisation(profil, organisation):
                logger.warning(
                    f"Tentative de modification non autorisée de l'organisation "
                    f"{organisation_id} par {acting_user.id}"
                )
                raise PermissionDenied("Vous devez être administrateur pour modifier l'organisation")
            
            # Mettre à jour les champ
            if nom_organisation is not None:
                organisation.nom_organisation = nom_organisation
                # Régénérer le slug si le nom change
               
                slug = generate_unique_slug(nom_organisation, Organisation)
              
                if not slug:
                    logger.error("Erreur creation slug organisation")
                organisation.slug = slug
            
            if description is not None:
                organisation.description = description
            
            if type_organisation is not None:
                types_valides = [choice[0] for choice in Organisation.TYPE_CHOICES]
                if type_organisation not in types_valides:
                    raise ValidationError(f"Type d'organisation invalide: {type_organisation}")
                organisation.type_organisation = type_organisation
            
            if site_web is not None:
                organisation.site_web = site_web
            
            if adresse is not None:
                organisation.adresse = adresse
            
            if ville is not None:
                organisation.ville = ville
            
            if pays is not None:
                organisation.pays = pays
            
            if statut is not None:
                statuts_valides = [choice[0] for choice in Organisation.STATUT_CHOICES]
                if statut not in statuts_valides:
                    raise ValidationError(f"Statut invalide: {statut}")
                organisation.statut = statut
            
            organisation.save()
            
            # Traiter le logo si fourni
            if logo_base64:
                base64_image_handler = Base64FileHandler()
                
                try:
                    logo_data = base64_image_handler.handle(logo_base64, "organisation_logo", max_dimenssions =(
                        800, 800
                    ))
                    organisation.logo = logo_data
                    organisation.save()
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement du logo: {str(e)}")
            
            # Mettre à jour les secteurs d'activité
            if secteur_activites is not None:
                secteurs = SecteurActivite.objects.filter(
                    id__in=secteur_activites,
                    deleted=False
                )
                organisation.secteur_activites.set(secteurs)
            
            logger.info(
                f"Organisation modifiée - ID: {organisation.id}, "
                f"Par: {acting_user.id}"
            )
            
            return organisation
            
        except Organisation.DoesNotExist:
            logger.error(f"Organisation introuvable: {organisation_id}")
            raise ValidationError("Organisation introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la modification de l'organisation: {str(e)}")
            raise
        
        
        
    
    @staticmethod
    @transaction.atomic
    def supprimer_organisation(
        acting_user: User,
        organisation_id: UUID,
        request=None
    ) -> bool:
        """
        Supprime (soft delete) une organisation
        
        Args:
            acting_user: Utilisateur effectuant la suppression
            organisation_id: ID de l'organisation
            request: Requête HTTP (optionnel)
        
        Returns:
            bool: True si la suppression a réussi
        
        Raises:
            PermissionDenied: Si l'utilisateur n'a pas les droits
        """
        try:
            profil = acting_user.profil
            organisation = Organisation.objects.select_for_update().get(
                id=organisation_id,
                deleted=False
            )
            
            # Vérifier les permissions
            if not OrganisationService.est_admin_organisation(profil, organisation) or acting_user.is_admin_user():
                raise PermissionDenied("Vous devez être administrateur pour supprimer l'organisation")
            
            organisation.deleted = True
            organisation.save()
            
            logger.info(
                f"Organisation supprimée - ID: {organisation.id}, "
                f"Par: {acting_user.id}"
            )
            
            return True
            
        except Organisation.DoesNotExist:
            logger.error(f"Organisation introuvable: {organisation_id}")
            raise ValidationError("Organisation introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'organisation: {str(e)}")
            raise        
        

    
    @staticmethod
    def rechercher_organisations(
        acting_user: User,
        query: Optional[str] = None,
        type_organisation: Optional[str] = None,
        secteur_activites: Optional[List[UUID]] = None,
        ville: Optional[str] = None,
        pays: Optional[str] = None,
        statut: Optional[str] = None,
        request=None
    ) -> List[Organisation]:
        """
        Recherche des organisations selon des critères
        
        Args:
            acting_user: Utilisateur effectuant la recherche
            query: Terme de recherche (nom)
            type_organisation: Filtrer par type
            secteur_activites: Filtrer par secteurs
            ville: Filtrer par ville
            pays: Filtrer par pays
            statut: Filtrer par statut
            request: Requête HTTP (optionnel)
        
        Returns:
            List[Organisation]: Liste des organisations correspondantes
        """
        try:
            profil = acting_user.profil
            queryset = Organisation.objects.filter(
                deleted=False
            ).prefetch_related('secteur_activites')
            
            # Filtre par défaut : organisations actives uniquement (sauf pour admins)
            if not acting_user.is_admin_user():
                queryset = queryset.filter(statut='active')
            elif statut:
                queryset = queryset.filter(statut=statut)
            
            # Recherche textuelle
            if query:
                queryset = queryset.filter(
                    Q(nom_organisation__icontains=query) |
                    Q(description__icontains=query)
                )
            
            # Filtres spécifiques
            if type_organisation:
                queryset = queryset.filter(type_organisation=type_organisation)
            
            if secteur_activites:
                queryset = queryset.filter(
                    secteur_activites__id__in=secteur_activites
                ).distinct()
            
            if ville:
                queryset = queryset.filter(ville__icontains=ville)
            
            if pays:
                queryset = queryset.filter(pays=pays)
            
            organisations = list(queryset.order_by('-created_at'))
            
            logger.info(
                f"Recherche organisations - Utilisateur: {acting_user.id}, "
                f"Résultats: {len(organisations)}"
            )
            
            return organisations
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche d'organisations: {str(e)}")
            raise
    


    
    # ============================================
    # GESTION DES MEMBRES
    # ============================================
    
    @staticmethod
    @transaction.atomic
    def ajouter_membre_organisation(
        acting_user: User,
        organisation_id: UUID,
        profil_id: UUID,
        acces: str = 'membre',
        request=None
    ) -> MembreOrganisation:
        """
        Ajoute un membre à une organisation
        
        Args:
            acting_user: Utilisateur effectuant l'ajout
            organisation_id: ID de l'organisation
            profil_id: ID du profil à ajouter
            acces: Niveau d'accès ('admin' ou 'membre')
            request: Requête HTTP (optionnel)
        
        Returns:
            MembreOrganisation: Le membre ajouté
        
        Raises:
            ValidationError: Si les données sont invalides
            PermissionDenied: Si l'utilisateur n'a pas les droits
        """
        try:
            profil = acting_user.profil
            organisation = Organisation.objects.get(
                id=organisation_id,
                deleted=False
            )
            
            profil_to_add = Profil.objects.get(
                id=profil_id,
                deleted=False
            )
            
            # Vérifier les permissions (doit être admin)
            if not OrganisationService.est_admin_organisation(profil, organisation):
                raise PermissionDenied("Vous devez être administrateur pour ajouter des membres")
            
            # Vérifier que le profil n'est pas déjà membre
            if MembreOrganisation.objects.filter(
                profil=profil_to_add,
                organisation=organisation,
                deleted=False
            ).exists():
                raise ValidationError("Ce profil est déjà membre de l'organisation")
            
            # Valider le niveau d'accès
            acces_valides = [choice[0] for choice in MembreOrganisation.ACCES_CHOICES]
            if acces not in acces_valides:
                raise ValidationError(f"Niveau d'accès invalide: {acces}")
            
            # Créer le membre
            membre = MembreOrganisation.objects.create(
                profil=profil_to_add,
                organisation=organisation,
                acces=acces
            )
            
            logger.info(
                f"Membre ajouté à l'organisation - Organisation: {organisation.nom_organisation}, "
                f"Membre: {profil_to_add.user.id}, "
                f"Accès: {acces}, "
                f"Par: {acting_user.id}"
            )
            
            return membre
            
        except Organisation.DoesNotExist:
            logger.error(f"Organisation introuvable: {organisation_id}")
            raise ValidationError("Organisation introuvable")
        except Profil.DoesNotExist:
            logger.error(f"Profil introuvable: {profil_id}")
            raise ValidationError("Profil introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du membre: {str(e)}")
            raise
    
    @staticmethod
    @transaction.atomic
    def modifier_acces_membre(
        acting_user: User,
        membre_id: UUID,
        acces: str,
        request=None
    ) -> MembreOrganisation:
        """
        Modifie le niveau d'accès d'un membre
        
        Args:
            acting_user: Utilisateur effectuant la modification
            membre_id: ID du membre
            acces: Nouveau niveau d'accès
            request: Requête HTTP (optionnel)
        
        Returns:
            MembreOrganisation: Le membre modifié
        
        Raises:
            ValidationError: Si les données sont invalides
            PermissionDenied: Si l'utilisateur n'a pas les droits
        """
        try:
            profil = acting_user.profil
            membre = MembreOrganisation.objects.select_for_update().get(
                id=membre_id,
                deleted=False
            )
            
            # Vérifier les permissions
            if not OrganisationService.est_admin_organisation(profil, membre.organisation):
                raise PermissionDenied("Vous devez être administrateur pour modifier les accès")
            
            # Empêcher de se retirer soi-même les droits admin si c'est le dernier admin
            if membre.profil == acting_user and acces != 'admin':
                nb_admins = MembreOrganisation.objects.filter(
                    organisation=membre.organisation,
                    acces='admin',
                    deleted=False
                ).count()
                
                if nb_admins <= 1:
                    raise ValidationError(
                        "Vous ne pouvez pas retirer vos droits d'administrateur "
                        "car vous êtes le dernier administrateur"
                    )
            
            # Valider le niveau d'accès
            acces_valides = [choice[0] for choice in MembreOrganisation.ACCES_CHOICES]
            if acces not in acces_valides:
                raise ValidationError(f"Niveau d'accès invalide: {acces}")
            
            ancien_acces = membre.acces
            membre.acces = acces
            membre.save()
            
            logger.info(
                f"Accès membre modifié - Organisation: {membre.organisation.nom_organisation}, "
                f"Membre: {membre.profil.user.id}, "
                f"Ancien accès: {ancien_acces}, Nouveau accès: {acces}, "
                f"Par: {acting_user.id}"
            )
            
            return membre
            
        except MembreOrganisation.DoesNotExist:
            logger.error(f"Membre introuvable: {membre_id}")
            raise ValidationError("Membre introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la modification de l'accès: {str(e)}")
            raise
    
    @staticmethod
    @transaction.atomic
    def retirer_membre_organisation(
        acting_user: User,
        membre_id: UUID,
        request=None
    ) -> bool:
        """
        Retire un membre d'une organisation
        
        Args:
            acting_user: Utilisateur effectuant le retrait
            membre_id: ID du membre
            request: Requête HTTP (optionnel)
        
        Returns:
            bool: True si le retrait a réussi
        
        Raises:
            ValidationError: Si le retrait n'est pas possible
            PermissionDenied: Si l'utilisateur n'a pas les droits
        """
        try:
            profil = acting_user.profil
            membre = MembreOrganisation.objects.select_for_update().get(
                id=membre_id,
                deleted=False
            )
            
            # Permissions : admin OU le membre se retire lui-même
            est_admin = OrganisationService.est_admin_organisation(profil, membre.organisation)
            se_retire_lui_meme = membre.profil == acting_user
            
            if not (est_admin or se_retire_lui_meme):
                raise PermissionDenied("Vous n'avez pas les droits pour retirer ce membre")
            
            # Empêcher de retirer le dernier admin
            if membre.acces == 'admin':
                nb_admins = MembreOrganisation.objects.filter(
                    organisation=membre.organisation,
                    acces='admin',
                    deleted=False
                ).count()
                
                if nb_admins <= 1:
                    raise ValidationError(
                        "Impossible de retirer le dernier administrateur de l'organisation"
                    )
            
            membre.deleted = True
            membre.save()
            
            logger.info(
                f"Membre retiré de l'organisation - Organisation: {membre.organisation.nom_organisation}, "
                f"Membre: {membre.profil.user.id}, "
                f"Par: {acting_user.id}"
            )
            
            return True
            
        except MembreOrganisation.DoesNotExist:
            logger.error(f"Membre introuvable: {membre_id}")
            raise ValidationError("Membre introuvable")
        except Exception as e:
            logger.error(f"Erreur lors du retrait du membre: {str(e)}")
            raise
    
    @staticmethod
    def obtenir_membres_organisation(
        acting_user: User,
        organisation_id: UUID,
        acces: Optional[str] = None,
        request=None
    ) -> List[MembreOrganisation]:
        """Obtient la liste des membres d'une organisation"""
        try:
            organisation = Organisation.objects.get(
                id=organisation_id,
                deleted=False
            )
            
            queryset = MembreOrganisation.objects.filter(
                organisation=organisation,
                deleted=False
            ).select_related('profil').order_by('-date_membre')
            
            if acces:
                queryset = queryset.filter(acces=acces)
            
            membres = list(queryset)
            
            logger.info(
                f"Liste membres organisation - Organisation: {organisation.nom_organisation}, "
                f"Nombre: {len(membres)}"
            )
            
            return membres
            
        except Organisation.DoesNotExist:
            logger.error(f"Organisation introuvable: {organisation_id}")
            raise ValidationError("Organisation introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des membres: {str(e)}")
            raise
    
    # ============================================
    # GESTION DES ABONNEMENTS (FOLLOWERS)
    # ============================================
    
    @staticmethod
    @transaction.atomic
    def s_abonner_organisation(
        acting_user: User,
        organisation_id: UUID,
        request=None
    ) -> AbonnementOrganisation:
        """
        S'abonne à une organisation (follow)
        
        Args:
            acting_user: Utilisateur s'abonnant
            organisation_id: ID de l'organisation
            request: Requête HTTP (optionnel)
        
        Returns:
            AbonnementOrganisation: L'abonnement créé
        
        Raises:
            ValidationError: Si l'abonnement existe déjà
        """
        try:
            profil = acting_user.profil
            organisation = Organisation.objects.get(
                id=organisation_id,
                deleted=False
            )
            
            # Vérifier que l'organisation est active
            if organisation.statut != 'active':
                raise ValidationError("Cette organisation n'est pas active")
            
            # Vérifier que l'abonnement n'existe pas déjà
            if AbonnementOrganisation.objects.filter(
                profil=profil,
                organisation=organisation,
                deleted=False
            ).exists():
                raise ValidationError("Vous êtes déjà abonné à cette organisation")
            
            # Créer l'abonnement
            abonnement = AbonnementOrganisation.objects.create(
                profil=profil,
                organisation=organisation
            )
            
            logger.info(
                f"Nouvel abonnement - Organisation: {organisation.nom_organisation}, "
                f"Utilisateur: {acting_user.id}"
            )
            
            return abonnement
            
        except Organisation.DoesNotExist:
            logger.error(f"Organisation introuvable: {organisation_id}")
            raise ValidationError("Organisation introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de l'abonnement: {str(e)}")
            raise
    
    @staticmethod
    @transaction.atomic
    def se_desabonner_organisation(
        acting_user: User,
        organisation_id: UUID,
        request=None
    ) -> bool:
        """
        Se désabonne d'une organisation (unfollow)
        
        Args:
            acting_user: Utilisateur se désabonnant
            organisation_id: ID de l'organisation
            request: Requête HTTP (optionnel)
        
        Returns:
            bool: True si le désabonnement a réussi
        
        Raises:
            ValidationError: Si l'abonnement n'existe pas
        """
        try:
            profil = acting_user.profil
            abonnement = AbonnementOrganisation.objects.get(
                profil=profil,
                organisation_id=organisation_id,
                deleted=False
            )
            
            abonnement.deleted = True
            abonnement.save()
            
            logger.info(
                f"Désabonnement - Organisation ID: {organisation_id}, "
                f"Utilisateur: {acting_user.id}"
            )
            
            return True
            
        except AbonnementOrganisation.DoesNotExist:
            logger.error(f"Abonnement introuvable pour l'organisation: {organisation_id}")
            raise ValidationError("Vous n'êtes pas abonné à cette organisation")
        except Exception as e:
            logger.error(f"Erreur lors du désabonnement: {str(e)}")
            raise
    
    @staticmethod
    def obtenir_abonnes_organisation(
        acting_user: User,
        organisation_id: UUID,
        request=None
    ) -> List[AbonnementOrganisation]:
        """Obtient la liste des abonnés d'une organisation"""
        try:
            organisation = Organisation.objects.get(
                id=organisation_id,
                deleted=False
            )
            
            abonnes = AbonnementOrganisation.objects.filter(
                organisation=organisation,
                deleted=False
            ).select_related('profil').order_by('-date_abonnement')
            
            logger.info(
                f"Liste abonnés organisation - Organisation: {organisation.nom_organisation}, "
                f"Nombre: {abonnes.count()}"
            )
            
            return list(abonnes)
            
        except Organisation.DoesNotExist:
            logger.error(f"Organisation introuvable: {organisation_id}")
            raise ValidationError("Organisation introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des abonnés: {str(e)}")
            raise
    
    # ============================================
    # UTILITAIRES
    # ============================================
    
    @staticmethod
    def est_admin_organisation(profil: Profil, organisation: Organisation) -> bool:
        """Vérifie si un profil est administrateur d'une organisation"""
        return MembreOrganisation.objects.filter(
            profil=profil,
            organisation=organisation,
            acces='admin',
            deleted=False
        ).exists()
    
    @staticmethod
    def est_membre_organisation(profil: Profil, organisation: Organisation) -> bool:
        """Vérifie si un profil est membre d'une organisation"""
        return MembreOrganisation.objects.filter(
            profil=profil,
            organisation=organisation,
            deleted=False
        ).exists()
    
    @staticmethod
    def est_abonne_organisation(profil: Profil, organisation: Organisation) -> bool:
        """Vérifie si un profil est abonné à une organisation"""
        return AbonnementOrganisation.objects.filter(
            profil=profil,
            organisation=organisation,
            deleted=False
        ).exists()
    
    @staticmethod
    def obtenir_statistiques_organisation(
        acting_user: User,
        organisation_id: UUID,
        request=None
    ) -> Dict[str, Any]:
        """Obtient les statistiques d'une organisation"""
        try:
            organisation = Organisation.objects.get(
                id=organisation_id,
                deleted=False
            )
            
            # Compter les membres par type
            membres = MembreOrganisation.objects.filter(
                organisation=organisation,
                deleted=False
            )
            
            stats = {
                'organisation': {
                    'id': str(organisation.id),
                    'nom': organisation.nom_organisation,
                    'type': organisation.type_organisation,
                    'statut': organisation.statut,
                },
                'membres': {
                    'total': membres.count(),
                    'admins': membres.filter(acces='admin').count(),
                    'membres': membres.filter(acces='membre').count(),
                },
                'abonnes': {
                    'total': AbonnementOrganisation.objects.filter(
                        organisation=organisation,
                        deleted=False
                    ).count(),
                },
                'activite': {
                    'date_creation': organisation.created_at,
                    'derniere_modification': organisation.updated_at,
                }
            }
            
            logger.info(f"Statistiques générées pour organisation: {organisation.id}")
            
            return stats
            
        except Organisation.DoesNotExist:
            logger.error(f"Organisation introuvable: {organisation_id}")
            raise ValidationError("Organisation introuvable")
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {str(e)}")
            raise