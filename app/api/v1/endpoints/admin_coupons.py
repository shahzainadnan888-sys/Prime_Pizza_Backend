"""Owner coupon management APIs."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.authorization.permissions import Permission
from app.common.constants import APIMessages
from app.common.enums import CouponType
from app.dependencies.admin import get_admin_coupon_service
from app.dependencies.authorization import require_permission
from app.dependencies.pagination import get_pagination
from app.models.user import User
from app.schemas.admin_coupons import (
    CouponCreateRequest,
    CouponFilterParams,
    CouponResponse,
    CouponUpdateRequest,
    CouponUsageReportResponse,
)
from app.schemas.pagination import PaginationParams
from app.schemas.response import MessageResponse, PaginatedResponse, SuccessResponse
from app.services.admin_coupon import AdminCouponService

router = APIRouter(prefix="/admin/coupons", tags=["Admin Coupons"])


@router.get("", response_model=PaginatedResponse[CouponResponse])
async def list_coupons(
    request: Request,
    pagination: PaginationParams = Depends(get_pagination),
    _: User = Depends(require_permission(Permission.COUPON_READ)),
    service: AdminCouponService = Depends(get_admin_coupon_service),
    q: str | None = Query(default=None, max_length=50),
    is_active: bool | None = Query(default=None),
    coupon_type: CouponType | None = Query(default=None),
    sort: str = Query(default="newest", pattern="^(newest|oldest|usage)$"),
) -> PaginatedResponse[CouponResponse]:
    filters = CouponFilterParams(
        q=q,
        is_active=is_active,
        coupon_type=coupon_type,
        sort=sort,
    )
    data, meta = await service.list_coupons(filters, pagination)
    return PaginatedResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        meta=meta.model_dump(),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "",
    response_model=SuccessResponse[CouponResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_coupon(
    body: CouponCreateRequest,
    request: Request,
    user: User = Depends(require_permission(Permission.COUPON_CREATE)),
    service: AdminCouponService = Depends(get_admin_coupon_service),
) -> SuccessResponse[CouponResponse]:
    data = await service.create(body, actor_id=user.id)
    return SuccessResponse(
        success=True,
        message="Coupon created",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/{coupon_id}", response_model=SuccessResponse[CouponResponse])
async def get_coupon(
    coupon_id: UUID,
    request: Request,
    _: User = Depends(require_permission(Permission.COUPON_READ)),
    service: AdminCouponService = Depends(get_admin_coupon_service),
) -> SuccessResponse[CouponResponse]:
    data = await service.get_coupon(coupon_id)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/{coupon_id}", response_model=SuccessResponse[CouponResponse])
async def update_coupon(
    coupon_id: UUID,
    body: CouponUpdateRequest,
    request: Request,
    user: User = Depends(require_permission(Permission.COUPON_UPDATE)),
    service: AdminCouponService = Depends(get_admin_coupon_service),
) -> SuccessResponse[CouponResponse]:
    data = await service.update(coupon_id, body, actor_id=user.id)
    return SuccessResponse(
        success=True,
        message="Coupon updated",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/{coupon_id}/enable", response_model=SuccessResponse[CouponResponse])
async def enable_coupon(
    coupon_id: UUID,
    request: Request,
    user: User = Depends(require_permission(Permission.COUPON_UPDATE)),
    service: AdminCouponService = Depends(get_admin_coupon_service),
) -> SuccessResponse[CouponResponse]:
    data = await service.set_active(coupon_id, is_active=True, actor_id=user.id)
    return SuccessResponse(
        success=True,
        message="Coupon enabled",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/{coupon_id}/disable", response_model=SuccessResponse[CouponResponse])
async def disable_coupon(
    coupon_id: UUID,
    request: Request,
    user: User = Depends(require_permission(Permission.COUPON_UPDATE)),
    service: AdminCouponService = Depends(get_admin_coupon_service),
) -> SuccessResponse[CouponResponse]:
    data = await service.set_active(coupon_id, is_active=False, actor_id=user.id)
    return SuccessResponse(
        success=True,
        message="Coupon disabled",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/{coupon_id}", response_model=MessageResponse)
async def delete_coupon(
    coupon_id: UUID,
    request: Request,
    user: User = Depends(require_permission(Permission.COUPON_DELETE)),
    service: AdminCouponService = Depends(get_admin_coupon_service),
) -> MessageResponse:
    await service.delete(coupon_id, actor_id=user.id)
    return MessageResponse(
        success=True,
        message="Coupon deleted",
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/{coupon_id}/usage", response_model=SuccessResponse[CouponUsageReportResponse])
async def get_coupon_usage(
    coupon_id: UUID,
    request: Request,
    _: User = Depends(require_permission(Permission.COUPON_READ)),
    service: AdminCouponService = Depends(get_admin_coupon_service),
) -> SuccessResponse[CouponUsageReportResponse]:
    data = await service.usage_report(coupon_id)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )
