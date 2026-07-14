"""Email log repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_log import EmailLog
from app.repositories.base import BaseRepository


class EmailLogRepository(BaseRepository[EmailLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, EmailLog)

    async def get_by_id(self, email_log_id: UUID) -> EmailLog | None:
        stmt = select(EmailLog).where(
            EmailLog.id == email_log_id,
            EmailLog.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
