# core/services/notification_service.py
import logging
from typing import Optional, List, Any
from uuid import UUID
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from core.models import Notification, User
from users.models import Profil
from core.mixins import NotifiableSource
from network.events import event_bus, BaseEvent

logger = logging.getLogger(__name__)

class NotificationService:
    """Service de gestion des notifications"""

    @staticmethod
    @transaction.atomic
    def creer_notification(
        destinataire: Profil,
        source: Any,
        action_type: str,
        category: str = Notification.Category.SYSTEM,
        title: Optional[str] = None,
        content: Optional[str] = None,
        link: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> Notification:
        """
        Crée une notification et déclenche l'envoi en temps réel.
        """
        try:
            source_ct = ContentType.objects.get_for_model(source)

            # Utiliser le mixin si disponible pour obtenir les données par défaut
            if isinstance(source, NotifiableSource):
                preview = source.get_notification_preview(action_type)
                title = title or preview.get('title')
                content = content or preview.get('content')
                link = link or preview.get('link')
                icon = icon or preview.get('icon')

            notification = Notification.objects.create(
                destinataire=destinataire,
                source_content_type=source_ct,
                source_object_id=source.id,
                category=category,
                action_type=action_type,
                title=title or "Nouvelle notification",
                content=content or "",
                link=link,
                icon=icon,
                is_read=False
            )

            # Publier un événement pour le dispatch WebSocket
            # On réutilise le pattern event_bus du projet
            event = BaseEvent.create(
                event_type="NotificationCreee",
                payload={
                    "notification_id": str(notification.id),
                    "destinataire_id": str(destinataire.id),
                    "title": notification.title,
                    "content": notification.content,
                    "link": notification.link,
                    "icon": notification.icon,
                    "category": notification.category,
                    "action_type": notification.action_type,
                    "created_at": notification.created_at.isoformat()
                },
                aggregate_id=notification.id
            )
            event_bus.publish(event)

            logger.info(f"Notification créée - ID: {notification.id} pour {destinataire.id}")
            return notification

        except Exception as e:
            logger.error(f"Erreur lors de la création de la notification: {str(e)}")
            raise

    @staticmethod
    @transaction.atomic
    def marquer_comme_lue(acting_user: User, notification_id: UUID) -> bool:
        """Marque une notification comme lue par l'utilisateur"""
        try:
            notification = Notification.objects.get(
                id=notification_id,
                destinataire=acting_user.profil,
                deleted=False
            )
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            logger.warning(f"Notification {notification_id} introuvable pour {acting_user.id}")
            return False

    @staticmethod
    @transaction.atomic
    def marquer_tout_comme_lu(acting_user: User) -> int:
        """Marque toutes les notifications non lues comme lues"""
        from django.utils import timezone
        count = Notification.objects.filter(
            destinataire=acting_user.profil,
            is_read=False,
            deleted=False
        ).update(is_read=True, read_at=timezone.now())
        return count

    @staticmethod
    def obtenir_notifications(acting_user: User, page: int = 1, page_size: int = 20):
        """Obtient les notifications de l'utilisateur avec pagination"""
        from django.core.paginator import Paginator
        queryset = Notification.objects.filter(
            destinataire=acting_user.profil,
            deleted=False
        ).order_by('-created_at')

        paginator = Paginator(queryset, page_size)
        return paginator.get_page(page)
