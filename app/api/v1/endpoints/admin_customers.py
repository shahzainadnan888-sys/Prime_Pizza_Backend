"""Owner customer management APIs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.authorization.permissions import Permission
from app.common.constants import APIMessages
from app.common.enums import UserRole
from app.dependencies.admin import get_admin_customer_service
from app.dependencies.authorization import require_permission
from app.dependencies.pagination import get_pagination
from app.models.user import User
from app.schemas.admin_customers import (
    AdminCustomerDetailResponse,
    AdminCustomerFilterParams,
    AdminCustomerStatusRequest,
    AdminCustomerUpdateRequest,
)
from app.schemas.pagination import PaginationParams
from app.schemas.response import PaginatedResponse, SuccessResponse
from app.schemas.users import UserProfileResponse
from app.services.admin_customer import AdminCustomerService

router = APIRouter(prefix="/admin/customers", tags=["Admin Customers"])


@router.get("", response_model=PaginatedResponse[UserProfileResponse])
async def list_customers(
    request: Request,
    pagination: PaginationParams = Depends(get_pagination),
    _: User = Depends(require_permission(Permission.CUSTOMER_READ)),
    service: AdminCustomerService = Depends(get_admin_customer_service),
    q: str | None = Query(default=None, max_length=150),
    name: str | None = Query(default=None, max_length=150),
    phone: str | None = Query(default=None, max_length=30),
    email: str | None = Query(default=None, max_length=255),
    role: UserRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    is_verified: bool | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    sort: str = Query(default="newest", pattern="^(newest|oldest|name)$"),
) -> PaginatedResponse[UserProfileResponse]:
    filters = AdminCustomerFilterParams(
        q=q,
        name=name,
        phone=phone,
        email=email,
        role=role,
        is_active=is_active,
        is_verified=is_verified,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
    )
    data, meta = await service.list_customers(filters, pagination)
    return PaginatedResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        meta=meta.model_dump(),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/{customer_id}", response_model=SuccessResponse[AdminCustomerDetailResponse])
async def get_customer(
    customer_id: UUID,
    request: Request,
    _: User = Depends(require_permission(Permission.CUSTOMER_READ)),
    service: AdminCustomerService = Depends(get_admin_customer_service),
) -> SuccessResponse[AdminCustomerDetailResponse]:
    data = await service.get_customer(customer_id)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/{customer_id}", response_model=SuccessResponse[AdminCustomerDetailResponse])
async def update_customer(
    customer_id: UUID,
    body: AdminCustomerUpdateRequest,
    request: Request,
    user: User = Depends(require_permission(Permission.CUSTOMER_UPDATE)),
    service: AdminCustomerService = Depends(get_admin_customer_service),
) -> SuccessResponse[AdminCustomerDetailResponse]:
    data = await service.update_customer(customer_id, body, actor_id=user.id)
    return SuccessResponse(
        success=True,
        message="Customer updated",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch(
    "/{customer_id}/status",
    response_model=SuccessResponse[AdminCustomerDetailResponse],
)
async def update_customer_status(
    customer_id: UUID,
    body: AdminCustomerStatusRequest,
    request: Request,
    user: User = Depends(require_permission(Permission.CUSTOMER_UPDATE)),
    service: AdminCustomerService = Depends(get_admin_customer_service),
) -> SuccessResponse[AdminCustomerDetailResponse]:
    data = await service.update_status(customer_id, body, actor_id=user.id)
    return SuccessResponse(
        success=True,
        message="Customer status updated",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )
