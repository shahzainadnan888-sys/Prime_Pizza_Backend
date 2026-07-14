"""Owner notification create / broadcast / delete."""

from __future__ import annotations

from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import AuditAction, UserRole
from app.core.exceptions import NotFoundException, ValidationException
from app.models.notification import Notification
from app.repositories.notification import NotificationRepository
from app.repositories.user import UserRepository
from app.schemas.admin_notifications import (
    AdminNotificationResponse,
    NotificationBroadcastRequest,
    NotificationBroadcastResult,
    NotificationCreateRequest,
)
from app.services.audit import AuditService
from app.services.base import BaseService


class AdminNotificationService(BaseService):
    service_name = "admin_notification"

    def __init__(
        self,
        *,
        session: AsyncSession,
        audit: AuditService,
    ) -> None:
        self._session = session
        self._notifications = NotificationRepository(session)
        self._users = UserRepository(session)
        self._audit = audit

    def _payload_with_schedule(self, payload: dict | None, scheduled_at) -> dict | None:
        if scheduled_at is None and payload is None:
            return None
        data = dict(payload or {})
        if scheduled_at is not None:
            data["scheduled_at"] = scheduled_at.isoformat()
            data["delivery_status"] = "scheduled_pending"
        return data

    async def create_individual(
        self,
        payload: NotificationCreateRequest,
        *,
        actor_id: UUID,
    ) -> AdminNotificationResponse:
        if payload.user_id is None:
            raise ValidationException("user_id is required for individual notifications")
        user = await self._users.get_by_id(payload.user_id)
        if user is None:
            raise NotFoundException("User not found")
        row = Notification(
            user_id=payload.user_id,
            title=payload.title.strip(),
            message=payload.message.strip(),
            notification_type=payload.notification_type,
            payload=self._payload_with_schedule(payload.payload, payload.scheduled_at),
            created_by=actor_id,
        )
        await self._notifications.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        await self._audit.record(
            action=AuditAction.CREATE,
            resource_type="notification",
            resource_id=str(row.id),
            user_id=actor_id,
            message="Notification created",
            commit=True,
        )
        logger.info("Notification created | notification_id={} | user_id={}", row.id, row.user_id)
        return AdminNotificationResponse.model_validate(row)

    async def broadcast(
        self,
        payload: NotificationBroadcastRequest,
        *,
        actor_id: UUID,
    ) -> NotificationBroadcastResult:
        role = None
        if payload.role_filter == "customer":
            role = UserRole.CUSTOMER
        elif payload.role_filter == "owner":
            role = UserRole.OWNER
        user_ids = await self._users.list_ids_by_role(role)
        body_payload = self._payload_with_schedule(payload.payload, payload.scheduled_at)
        for user_id in user_ids:
            await self._notifications.add(
                Notification(
                    user_id=user_id,
                    title=payload.title.strip(),
                    message=payload.message.strip(),
                    notification_type=payload.notification_type,
                    payload=body_payload,
                    created_by=actor_id,
                )
            )
        await self._session.commit()
        await self._audit.record(
            action=AuditAction.CREATE,
            resource_type="notification",
            resource_id=None,
            user_id=actor_id,
            message="Notification broadcast",
            details={"created_count": len(user_ids), "role_filter": payload.role_filter},
            commit=True,
        )
        logger.info("Notification broadcast | count={}", len(user_ids))
        return NotificationBroadcastResult(
            created_count=len(user_ids),
            scheduled=payload.scheduled_at is not None,
        )

    async def delete(self, notification_id: UUID, *, actor_id: UUID) -> None:
        row = await self._notifications.get_by_id(notification_id)
        if row is None:
            raise NotFoundException("Notification not found")
        await self._notifications.soft_delete(row)
        await self._session.commit()
        await self._audit.record(
            action=AuditAction.DELETE,
            resource_type="notification",
            resource_id=str(notification_id),
            user_id=actor_id,
            message="Notification deleted",
            commit=True,
        )
