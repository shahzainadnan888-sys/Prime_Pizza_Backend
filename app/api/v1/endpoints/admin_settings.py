"""Owner system settings APIs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.authorization.permissions import Permission
from app.common.constants import APIMessages
from app.dependencies.admin import get_system_settings_service
from app.dependencies.authorization import require_permission
from app.models.user import User
from app.schemas.admin_settings import (
    RestaurantSettingsResponse,
    SystemSettingResponse,
    SystemSettingsBulkUpdateRequest,
    SystemSettingUpsertRequest,
)
from app.schemas.response import SuccessResponse
from app.services.system_settings import SystemSettingsService

router = APIRouter(prefix="/admin/settings", tags=["Admin Settings"])


@router.get("", response_model=SuccessResponse[list[SystemSettingResponse]])
async def list_settings(
    request: Request,
    _: User = Depends(require_permission(Permission.SETTINGS_READ)),
    service: SystemSettingsService = Depends(get_system_settings_service),
) -> SuccessResponse[list[SystemSettingResponse]]:
    data = await service.list_settings()
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.put("", response_model=SuccessResponse[list[SystemSettingResponse]])
async def bulk_update_settings(
    body: SystemSettingsBulkUpdateRequest,
    request: Request,
    user: User = Depends(require_permission(Permission.SETTINGS_UPDATE)),
    service: SystemSettingsService = Depends(get_system_settings_service),
) -> SuccessResponse[list[SystemSettingResponse]]:
    data = await service.bulk_upsert(body, actor_id=user.id)
    return SuccessResponse(
        success=True,
        message="Settings updated",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/restaurant", response_model=SuccessResponse[RestaurantSettingsResponse])
async def get_restaurant_settings(
    request: Request,
    _: User = Depends(require_permission(Permission.SETTINGS_READ)),
    service: SystemSettingsService = Depends(get_system_settings_service),
) -> SuccessResponse[RestaurantSettingsResponse]:
    data = await service.restaurant_view()
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/{key}", response_model=SuccessResponse[SystemSettingResponse])
async def get_setting(
    key: str,
    request: Request,
    _: User = Depends(require_permission(Permission.SETTINGS_READ)),
    service: SystemSettingsService = Depends(get_system_settings_service),
) -> SuccessResponse[SystemSettingResponse]:
    data = await service.get_setting(key)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.put("/{key}", response_model=SuccessResponse[SystemSettingResponse])
async def upsert_setting(
    key: str,
    body: SystemSettingUpsertRequest,
    request: Request,
    user: User = Depends(require_permission(Permission.SETTINGS_UPDATE)),
    service: SystemSettingsService = Depends(get_system_settings_service),
) -> SuccessResponse[SystemSettingResponse]:
    data = await service.upsert(key, body, actor_id=user.id)
    return SuccessResponse(
        success=True,
        message="Setting updated",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )
