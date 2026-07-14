"""Audit log recording and owner listing."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import AuditAction
from app.models.audit_log import AuditLog
from app.repositories.audit_log import AuditLogRepository
from app.schemas.admin_audit import AuditLogFilterParams, AuditLogResponse
from app.schemas.pagination import PaginationMeta, PaginationParams
from app.services.base import BaseService


class AuditService(BaseService):
    service_name = "audit"

    def __init__(self, *, session: AsyncSession) -> None:
        self._session = session
        self._logs = AuditLogRepository(session)

    async def record(
        self,
        *,
        action: AuditAction,
        resource_type: str,
        resource_id: str | None = None,
        user_id: UUID | None = None,
        message: str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        commit: bool = False,
    ) -> None:
        """Best-effort audit write — never breaks the calling business flow."""
        try:
            await self._logs.add(
                AuditLog(
                    user_id=user_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    message=message,
                    details=details,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            )
            if commit:
                await self._session.commit()
            else:
                await self._session.flush()
        except Exception:
            logger.exception("Audit log write failed | resource_type={}", resource_type)

    async def list_logs(
        self,
        filters: AuditLogFilterParams,
        pagination: PaginationParams,
    ) -> tuple[list[AuditLogResponse], PaginationMeta]:
        rows, total = await self._logs.list_filtered(
            filters,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        meta = PaginationMeta.from_totals(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total,
        )
        return [AuditLogResponse.model_validate(row) for row in rows], meta
