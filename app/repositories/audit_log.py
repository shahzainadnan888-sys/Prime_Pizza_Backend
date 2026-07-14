"""Audit log repository."""

from __future__ import annotations

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository
from app.schemas.admin_audit import AuditLogFilterParams


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AuditLog)

    def _apply_filters(self, stmt: Select, filters: AuditLogFilterParams) -> Select:
        stmt = stmt.where(AuditLog.deleted_at.is_(None))
        if filters.user_id is not None:
            stmt = stmt.where(AuditLog.user_id == filters.user_id)
        if filters.action is not None:
            stmt = stmt.where(AuditLog.action == filters.action)
        if filters.resource_type:
            stmt = stmt.where(AuditLog.resource_type == filters.resource_type)
        if filters.date_from is not None:
            stmt = stmt.where(AuditLog.created_at >= filters.date_from)
        if filters.date_to is not None:
            stmt = stmt.where(AuditLog.created_at <= filters.date_to)
        if filters.q:
            pattern = f"%{filters.q.strip()}%"
            stmt = stmt.where(
                or_(
                    AuditLog.message.ilike(pattern),
                    AuditLog.resource_type.ilike(pattern),
                    AuditLog.resource_id.ilike(pattern),
                )
            )
        if filters.sort == "oldest":
            stmt = stmt.order_by(AuditLog.created_at.asc())
        else:
            stmt = stmt.order_by(AuditLog.created_at.desc())
        return stmt

    async def list_filtered(
        self,
        filters: AuditLogFilterParams,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[AuditLog], int]:
        base = select(AuditLog)
        base = self._apply_filters(base, filters)
        count_stmt = select(func.count()).select_from(base.order_by(None).subquery())
        total = int((await self.session.execute(count_stmt)).scalar_one())
        result = await self.session.execute(base.limit(limit).offset(offset))
        return list(result.scalars().all()), total
