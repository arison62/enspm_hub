# core/services/auth_service.py
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.db.models import Q
from django.conf import settings
from ninja.security import HttpBearer
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from core.models import User, PasswordResetToken
from django.utils import timezone
from core.utils.notifications import NotificationFactory
from core.services.audit_service import audit_log_service, AuditLog
import random
import string
import logging

logger = logging.getLogger('app')

# ==========================================
# 1. Classes de Sécurité Django Ninja (API Layer)
# ==========================================

class JWTAuthBearer(HttpBearer):
    """
    Classe de sécurité personnalisée pour valider le token JWT (Bearer)
    en utilisant rest_framework_simplejwt manuellement.
    """
    def authenticate(self, request, token):
        try:
            # 1. Validation cryptographique et temporelle du token
            # L'instanciation de AccessToken(token) vérifie automatiquement :
            # - La signature (avec SECRET_KEY)
            # - L'expiration (exp claim)
            # - Le format
            validated_token = AccessToken(token) # type: ignore
            
            # 2. Récupération de l'ID utilisateur
            # On utilise la clé définie dans tes settings "USER_ID_CLAIM": "user_id"
            user_id = validated_token[settings.SIMPLE_JWT.get('USER_ID_CLAIM', 'user_id')]
            
            # 3. Vérification de l'utilisateur en base
            # On s'assure qu'il existe, est actif et non supprimé (Soft Delete)
            user = User.objects.get(id=user_id, est_actif=True, deleted=False)
            request.user = user
            
            return user
            
        except (TokenError, InvalidToken) as e:
            # Le token est expiré, mal formé ou la signature est invalide
            logger.warning(f"Token JWT invalide : {str(e)}")
            return None
            
        except User.DoesNotExist:
            # Le token est valide crypto-graphiquement, mais l'user n'existe plus
            logger.warning(f"Token valide mais utilisateur introuvable (ID: {user_id})")
            return None
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'auth JWT: {str(e)}")
            return None
        
# ==========================================
# 2. Service Métier (Service Layer)
# ==========================================

class AuthService:
    """Service gérant la logique métier d'authentification et d'autorisation."""

    @staticmethod
    @transaction.atomic
    def login_user(request, email: str, password: str):
        """
        Authentifie l'utilisateur via le backend MatriculeEmailAuthBackend, 
        crée la session Django, génère les jetons JWT et l'AuditLog.
        
        :param request: Objet HttpRequest requis pour la session Django.
        :param login_id: Email ou Matricule.
        :param password: Mot de passe.
        :return: Dictionnaire contenant les tokens JWT et les données utilisateur.
        """
        
        # 1. Authentification via le backend personnalisé (Matricule ou Email)
        user = authenticate(request, username=email, password=password)
        
        if user is None:
            # Sécurité: Loguer les échecs d'authentification
            logger.warning(
                f"Échec de connexion (Identifiant ou Mot de passe invalide) pour: {email}",
                extra={'login_attempt': email}
            )
            # Nous pourrions lever une exception métier ici si nous ne voulions pas de 401
            # Mais la méthode d'API le gérera comme une erreur 401 ou 403.
            return None

        # 2. Création de la Session Django (pour les templates Inertia)
        login(request, user)
        
        # 3. Génération des jetons JWT (pour l'API React)
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # 4. Journalisation (CRITIQUE : Audit Trail)
        # Pour l'instant, on loggue avec logger.info
        audit_log_service.log_action(
            user=user, # type: ignore
            action=AuditLog.AuditAction.CREATE,
            entity_type='UserSession',
            entity_id=user.id, # type: ignore
            request=request,
            old_values=None,
            new_values={'login_id': email}
        )
        logger.info(
            "Connexion réussie.", 
            extra={
                'user_id': str(user.id), # type: ignore
                'login_id': email,
                'action_type': 'LOGIN_SUCCESS'
            }
        )

        # 5. Retour des données
        return {
            "user_id": str(user.id), # type: ignore
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user,
        }

    @staticmethod
    def logout_user(request):
        """Déconnecte l'utilisateur et gère l'AuditLog."""
        user_id = str(request.user.id) if request.user.is_authenticated else "anonymous"
        
        logout(request)
        
        # Journalisation (CRITIQUE : Audit Trail)
        logger.info(
            "Déconnexion réussie.",
            extra={
                'user_id': user_id, 
                'action_type': 'LOGOUT_SUCCESS'
            }
        )

    @staticmethod
    @transaction.atomic
    def request_password_reset(user_id: str, method: str = "email") -> bool:
        """
        Gère la demande de réinitialisation de mot de passe.
        Génère un token, l'enregistre en base et envoie la notification.
        
        :param user_id: email ou telephone de l'utilisateur demandant la réinitialisation.
        :param method: Méthode de notification ("email" ou "sms").
        :return: None
        """
        try:
            query = Q(email=user_id) | Q(telephone=user_id)
            user = User.objects.get(query, est_actif=True, deleted=False)
            otp_token = f"{random.randint(100000, 999999)}"
            duration = settings.PASSWORD_RESET_TOKEN_DURATION or timezone.now() + timedelta(minutes=5) # Par défaut 5 minutes
            
            PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
        
            token = PasswordResetToken.objects.create(user=user, token=otp_token)
            sender = NotificationFactory.get_sender(method)
            if method == "email":
                recipient = user.email
            elif method == "sms":
                recipient = user.telephone
            else:
                raise ValueError("Méthode de notification invalide")
            if not recipient:
                raise ValueError("L'utilisateur n'a pas de moyen de contact valide pour cette méthode")
            
            sender.send_otp(recipient=recipient, otp=otp_token)
            return True
        except User.DoesNotExist:
            logger.warning(f"Demande de réinitialisation de mot de passe pour utilisateur inconnu: {user_id}")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la demande de réinitialisation de mot de passe: {str(e)}")
            return False
    
    
    @staticmethod
    @transaction.atomic
    def confirm_password_reset(user_id: str, token: str, new_password: str) -> bool:
        """
        Vérifie le token de réinitialisation et met à jour le mot de passe.
        
        :param user_id: email ou telephone de l'utilisateur.
        :param token: Token OTP reçu par l'utilisateur.
        :param new_password: Nouveau mot de passe à définir.
        :return: True si la réinitialisation a réussi, False sinon.
        """
        try:
            query = Q(email=user_id) | Q(profil__telephone=user_id)
            user = User.objects.get(query, est_actif=True, deleted=False)
            reset_token = PasswordResetToken.objects.get(
                user=user,
                token=token,
                is_used=False,
                expires_at__gt=timezone.now()
            )
            user.set_password(new_password)
            user.save()
            reset_token.is_used = True
            reset_token.save()
            logger.info(f"Réinitialisation de mot de passe réussie pour l'utilisateur ID: {user.id}")
            return True
        except (User.DoesNotExist, PasswordResetToken.DoesNotExist):
            logger.warning(f"Échec de la réinitialisation de mot de passe pour utilisateur: {user_id} avec token: {token}")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation de mot de passe: {str(e)}")
            return False
        
    
# Instanciation de la classe de sécurité pour l'injection dans les endpoints
jwt_auth = JWTAuthBearer()