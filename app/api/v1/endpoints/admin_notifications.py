"""Owner notification create, broadcast, and delete APIs."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.authorization.permissions import Permission
from app.dependencies.admin import get_admin_notification_service
from app.dependencies.authorization import require_permission
from app.models.user import User
from app.schemas.admin_notifications import (
    AdminNotificationResponse,
    NotificationBroadcastRequest,
    NotificationBroadcastResult,
    NotificationCreateRequest,
)
from app.schemas.response import MessageResponse, SuccessResponse
from app.services.admin_notification import AdminNotificationService

router = APIRouter(prefix="/admin/notifications", tags=["Admin Notifications"])


@router.post(
    "",
    response_model=SuccessResponse[AdminNotificationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_notification(
    body: NotificationCreateRequest,
    request: Request,
    user: User = Depends(require_permission(Permission.NOTIFICATION_MANAGE)),
    service: AdminNotificationService = Depends(get_admin_notification_service),
) -> SuccessResponse[AdminNotificationResponse]:
    data = await service.create_individual(body, actor_id=user.id)
    return SuccessResponse(
        success=True,
        message="Notification created",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/broadcast",
    response_model=SuccessResponse[NotificationBroadcastResult],
    status_code=status.HTTP_201_CREATED,
)
async def broadcast_notification(
    body: NotificationBroadcastRequest,
    request: Request,
    user: User = Depends(require_permission(Permission.NOTIFICATION_MANAGE)),
    service: AdminNotificationService = Depends(get_admin_notification_service),
) -> SuccessResponse[NotificationBroadcastResult]:
    data = await service.broadcast(body, actor_id=user.id)
    return SuccessResponse(
        success=True,
        message="Notification broadcast",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/{notification_id}", response_model=MessageResponse)
async def delete_notification(
    notification_id: UUID,
    request: Request,
    user: User = Depends(require_permission(Permission.NOTIFICATION_MANAGE)),
    service: AdminNotificationService = Depends(get_admin_notification_service),
) -> MessageResponse:
    await service.delete(notification_id, actor_id=user.id)
    return MessageResponse(
        success=True,
        message="Notification deleted",
        request_id=getattr(request.state, "request_id", None),
    )
