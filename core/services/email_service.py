# core/services/email_service.py
import logging
from typing import List, Optional, Dict, Any
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from huey.contrib.djhuey import task
import resend

resend.api_key = settings.RESEND_API_KEY

logger = logging.getLogger('app')

class EmailService:
    """
    Service générique pour l'envoi d'emails avec templates HTML.
    Utilise Huey pour l'envoi asynchrone en arrière-plan.
    """
    
    @staticmethod
    def send_email_sync(
        subject: str,
        to_emails: List[str],
        template_name: str,
        context: Dict[str, Any],
        from_email: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[tuple]] = None
    ) -> bool:
        """
        Envoie un email de manière synchrone.
        
        Args:
            subject: Sujet de l'email
            to_emails: Liste des destinataires
            template_name: Nom du template HTML (ex: 'emails/welcome.html')
            context: Contexte à passer au template
            from_email: Email de l'expéditeur (utilise DEFAULT_FROM_EMAIL si None)
            cc_emails: Liste des destinataires en copie
            bcc_emails: Liste des destinataires en copie cachée
            attachments: Liste de tuples (filename, content, mimetype)
            
        Returns:
            bool: True si l'envoi a réussi, False sinon
        """
        try:
            # Utiliser l'email par défaut si non spécifié
            from_email = from_email or settings.DEFAULT_FROM_EMAIL
            # Ajouter les variables globales au contexte
            context.update({
                'site_name': getattr(settings, 'SITE_NAME', 'ENSPM Hub'),
                'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
                'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@enspmhub.com'),
                'current_year': __import__('datetime').datetime.now().year,
            })
            
            # Rendre le template HTML
            html_content = render_to_string(template_name, context)
            
            # Générer la version texte brut
            text_content = strip_tags(html_content)
            
            # Créer l'email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=to_emails,
                cc=cc_emails or [],
                bcc=bcc_emails or []
            )
            
            # Attacher la version HTML
            email.attach_alternative(html_content, "text/html")
            
            # Ajouter les pièces jointes si présentes
            if attachments:
                for filename, content, mimetype in attachments:
                    email.attach(filename, content, mimetype)
            
            # Envoyer l'email
            email.send(fail_silently=False)
            
            logger.info(
                f"Email envoyé avec succès: '{subject}' à {', '.join(to_emails)}"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Erreur lors de l'envoi de l'email '{subject}' à {', '.join(to_emails)}: {str(e)}",
                exc_info=True
            )
            return False
        
    @staticmethod
    def resend_email_sync(
        subject: str,
        to_emails: List[str],
        template_name: str,
        context: Dict[str, Any],
        from_email: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[tuple]] = None
    ) -> bool:
        """
        Envoie un email via Resend de manière synchrone.
        """
        try:
            from_email = from_email or settings.DEFAULT_FROM_EMAIL
            logger.info(f"FROM_EMAIL : {from_email}")
            context.update({
                'site_name': getattr(settings, 'SITE_NAME', 'ENSPM Hub'),
                'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
                'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@localhost:8000'),
                'current_year': __import__('datetime').datetime.now().year,
            })
            
            html_content = render_to_string(template_name, context)
            text_content = strip_tags(html_content)
            
            # Préparer les pièces jointes pour Resend
            resend_attachments = []
            if attachments:
                for filename, content, mimetype in attachments:
                    resend_attachments.append({
                        "filename": filename,
                        "content": list(content) if isinstance(content, bytes) else content,
                    })
            
            params: resend.Emails.SendParams = {
                "from": from_email, # type: ignore
                "to": to_emails,
                "subject": subject,
                "html": html_content,
                "text": text_content,
            }
            
            if cc_emails:
                params["cc"] = cc_emails
            if bcc_emails:
                params["bcc"] = bcc_emails
            if resend_attachments:
                params["attachments"] = resend_attachments
            
            email = resend.Emails.send(params)
            
            logger.info(f"Email envoyé via Resend: '{subject}' à {', '.join(to_emails)} - ID: {email.get('id')}")
            return True
        except Exception as e:
            logger.error(f"Erreur Resend '{subject}' à {', '.join(to_emails)}: {str(e)}", exc_info=True)
            return False
    
    @staticmethod
    def send_email_async(
        subject: str,
        to_emails: List[str],
        template_name: str,
        context: Dict[str, Any],
        from_email: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[tuple]] = None
    ):
        """
        Envoie un email de manière asynchrone via Huey.
        Même signature que send_email_sync.
        """
        send_email_task.schedule(
            args=(
                subject, to_emails, template_name, context, 
                from_email, cc_emails, bcc_emails, attachments
            ),
            delay=0
        )
        logger.info(f"Email '{subject}' planifié pour envoi asynchrone à {', '.join(to_emails)}")



    @staticmethod
    def resend_email_async(
        subject: str,
        to_emails: List[str],
        template_name: str,
        context: Dict[str, Any],
        from_email: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[tuple]] = None
    ):
        """
        Envoie un email de manière asynchrone via Huey.
        Même signature que resend_email_sync.
        """
        resend_email_task.schedule(
            args=(
                subject, to_emails, template_name, context, 
                from_email, cc_emails, bcc_emails, attachments
            ),
            delay=0
        )
        logger.info(f"Email '{subject}' planifié pour envoi asynchrone à {', '.join(to_emails)}")



# ==========================================
# TÂCHES HUEY (BACKGROUND TASKS)
# ==========================================

@task(retries=3, retry_delay=60)
def send_email_task(
    subject: str,
    to_emails: List[str],
    template_name: str,
    context: Dict[str, Any],
    from_email: Optional[str] = None,
    cc_emails: Optional[List[str]] = None,
    bcc_emails: Optional[List[str]] = None,
    attachments: Optional[List[tuple]] = None
):
    """
    Tâche Huey pour l'envoi d'email en arrière-plan.
    Avec 3 tentatives de réessai en cas d'échec (délai de 60s entre chaque tentative).
    """
    return EmailService.send_email_sync(
        subject=subject,
        to_emails=to_emails,
        template_name=template_name,
        context=context,
        from_email=from_email,
        cc_emails=cc_emails,
        bcc_emails=bcc_emails,
        attachments=attachments
    )

@task(retries=3, retry_delay=60)
def resend_email_task(
    subject: str,
    to_emails: List[str],
    template_name: str,
    context: Dict[str, Any],
    from_email: Optional[str] = None,
    cc_emails: Optional[List[str]] = None,
    bcc_emails: Optional[List[str]] = None,
    attachments: Optional[List[tuple]] = None
):
    """
    Tâche Huey pour l'envoi d'email en arrière-plan.
    Avec 3 tentatives de réessai en cas d'échec (délai de 60s entre chaque tentative).
    """
    return EmailService.resend_email_sync(
        subject=subject,
        to_emails=to_emails,
        template_name=template_name,
        context=context,
        from_email=from_email,
        cc_emails=cc_emails,
        bcc_emails=bcc_emails,
        attachments=attachments
    )

# ==========================================
# FONCTIONS UTILITAIRES PRÉDÉFINIES
# ==========================================

class EmailTemplates:
    """
    Collection de méthodes pour envoyer des emails prédéfinis.
    """
    
    @staticmethod
    def send_welcome_email(user_email: str, user_name: str, temp_password: str):
        """Envoie un email de bienvenue avec le mot de passe temporaire."""
        EmailService.send_email_async(
            subject="Bienvenue sur ENSPM Hub !",
            to_emails=[user_email],
            template_name='emails/welcome.html',
            context={
                'user_name': user_name,
                'temp_password': temp_password,
                'login_url': f"{settings.SITE_URL}/login"
            }
        )
    
    @staticmethod
    def send_password_reset_email(user_email: str, user_name: str, otp_code: str):
        """Envoie un email de réinitialisation de mot de passe."""
        EmailService.send_email_async(
            subject="Réinitialisation de votre mot de passe",
            to_emails=[user_email],
            template_name='emails/password_reset.html',
            context={
                'user_name': user_name,
                'otp_code': otp_code,
                'reset_url': f"{settings.SITE_URL}/password-reset"
            }
        )
    
    @staticmethod
    def resend_password_reset_email(user_email: str, user_name: str, otp_code: str):
        """Envoie un email de réinitialisation de mot de passe."""
        EmailService.resend_email_async(
            subject="Réinitialisation de votre mot de passe",
            to_emails=[user_email],
            template_name='emails/password_reset.html',
            context={
                'user_name': user_name,
                'otp_code': otp_code,
                'reset_url': f"{settings.SITE_URL}/password-reset"
            }
        )
   
    @staticmethod
    def send_account_activated_email(user_email: str, user_name: str):
        """Envoie un email de confirmation d'activation de compte."""
        EmailService.send_email_async(
            subject="Votre compte a été activé",
            to_emails=[user_email],
            template_name='emails/account_activated.html',
            context={
                'user_name': user_name,
                'login_url': f"{settings.SITE_URL}/login"
            }
        )
    
    @staticmethod
    def send_notification_email(
        user_email: str, 
        user_name: str, 
        notification_title: str,
        notification_message: str,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None
    ):
        """Envoie un email de notification générique."""
        EmailService.send_email_async(
            subject=notification_title,
            to_emails=[user_email],
            template_name='emails/notification.html',
            context={
                'user_name': user_name,
                'notification_title': notification_title,
                'notification_message': notification_message,
                'action_url': action_url,
                'action_text': action_text
            }
        )


# Instanciation du service
email_service = EmailService()