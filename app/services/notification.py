"""User notification inbox service."""

from __future__ import annotations

from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.authorization.ownership import OwnershipService
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.repositories.notification import NotificationRepository
from app.schemas.users import NotificationResponse
from app.services.base import BaseService


class UserNotificationService(BaseService):
    service_name = "user_notification"

    def __init__(
        self,
        *,
        session: AsyncSession,
        ownership: OwnershipService | None = None,
    ) -> None:
        self._session = session
        self._notifications = NotificationRepository(session)
        self._ownership = ownership or OwnershipService()

    async def list_notifications(self, user: User) -> list[NotificationResponse]:
        rows = await self._notifications.list_for_user(user.id)
        return [NotificationResponse.model_validate(row) for row in rows]

    async def mark_read(self, user: User, notification_id: UUID) -> NotificationResponse:
        notification = await self._notifications.get_for_user(notification_id, user.id)
        if notification is None:
            raise NotFoundException("Notification not found")
        self._ownership.ensure_owner_or_self(
            user,
            notification.user_id,
            resource_name="notification",
        )
        await self._notifications.mark_read(notification)
        await self._session.commit()
        await self._session.refresh(notification)
        logger.info("Notification read | user_id={} | notification_id={}", user.id, notification_id)
        return NotificationResponse.model_validate(notification)

    async def mark_all_read(self, user: User) -> int:
        count = await self._notifications.mark_all_read(user.id)
        await self._session.commit()
        logger.info("Notifications read-all | user_id={} | count={}", user.id, count)
        return count

    async def delete_notification(self, user: User, notification_id: UUID) -> None:
        notification = await self._notifications.get_for_user(notification_id, user.id)
        if notification is None:
            raise NotFoundException("Notification not found")
        self._ownership.ensure_owner_or_self(
            user,
            notification.user_id,
            resource_name="notification",
        )
        await self._notifications.soft_delete(notification)
        await self._session.commit()
        logger.info(
            "Notification deleted | user_id={} | notification_id={}",
            user.id,
            notification_id,
        )
