# core/api/notifications.py
from typing import List
from uuid import UUID
from ninja import Router, Query
from core.services.auth_service import jwt_auth
from core.services.notification_service import NotificationService
from core.api.schemas import NotificationOut, NotificationListOut
from core.models import Notification

notifications_router = Router(tags=["Notifications"])

@notifications_router.get("/", response=NotificationListOut, auth=jwt_auth)
def list_notifications(request, page: int = 1, page_size: int = 20):
    """Liste les notifications de l'utilisateur"""
    notifications_page = NotificationService.obtenir_notifications(
        acting_user=request.user,
        page=page,
        page_size=page_size
    )

    unread_count = Notification.objects.filter(
        destinataire=request.user.profil,
        is_read=False,
        deleted=False
    ).count()

    return {
        "items": list(notifications_page.object_list),
        "total_count": notifications_page.paginator.count,
        "unread_count": unread_count
    }

@notifications_router.patch("/{notification_id}/read/", response={200: dict}, auth=jwt_auth)
def mark_notification_as_read(request, notification_id: UUID):
    """Marque une notification comme lue"""
    success = NotificationService.marquer_comme_lue(
        acting_user=request.user,
        notification_id=notification_id
    )
    return 200, {"success": success}

@notifications_router.post("/read-all/", response={200: dict}, auth=jwt_auth)
def mark_all_notifications_as_read(request):
    """Marque toutes les notifications comme lues"""
    count = NotificationService.marquer_tout_comme_lu(acting_user=request.user)
    return 200, {"success": True, "marked_count": count}
