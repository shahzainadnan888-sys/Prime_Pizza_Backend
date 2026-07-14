"""Owner audit log listing APIs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.authorization.permissions import Permission
from app.common.constants import APIMessages
from app.common.enums import AuditAction
from app.dependencies.admin import get_audit_service
from app.dependencies.authorization import require_permission
from app.dependencies.pagination import get_pagination
from app.models.user import User
from app.schemas.admin_audit import AuditLogFilterParams, AuditLogResponse
from app.schemas.pagination import PaginationParams
from app.schemas.response import PaginatedResponse
from app.services.audit import AuditService

router = APIRouter(prefix="/admin/audit-logs", tags=["Admin Audit"])


@router.get("", response_model=PaginatedResponse[AuditLogResponse])
async def list_audit_logs(
    request: Request,
    pagination: PaginationParams = Depends(get_pagination),
    _: User = Depends(require_permission(Permission.AUDIT_LOG_READ)),
    service: AuditService = Depends(get_audit_service),
    q: str | None = Query(default=None, max_length=200),
    user_id: UUID | None = Query(default=None),
    action: AuditAction | None = Query(default=None),
    resource_type: str | None = Query(default=None, max_length=100),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    sort: str = Query(default="newest", pattern="^(newest|oldest)$"),
) -> PaginatedResponse[AuditLogResponse]:
    filters = AuditLogFilterParams(
        q=q,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
    )
    data, meta = await service.list_logs(filters, pagination)
    return PaginatedResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        meta=meta.model_dump(),
        request_id=getattr(request.state, "request_id", None),
    )
