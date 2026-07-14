"""Owner console enterprise search API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.authorization.permissions import Permission
from app.common.constants import APIMessages
from app.dependencies.admin import get_admin_search_service
from app.dependencies.authorization import require_permission
from app.models.user import User
from app.schemas.admin_search import AdminSearchRequest, AdminSearchResponse
from app.schemas.response import SuccessResponse
from app.services.admin_search import AdminSearchService

router = APIRouter(prefix="/admin/search", tags=["Admin Search"])


@router.post("", response_model=SuccessResponse[AdminSearchResponse])
async def admin_search(
    body: AdminSearchRequest,
    request: Request,
    _: User = Depends(require_permission(Permission.DASHBOARD_READ)),
    service: AdminSearchService = Depends(get_admin_search_service),
) -> SuccessResponse[AdminSearchResponse]:
    data = await service.search(body)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )
