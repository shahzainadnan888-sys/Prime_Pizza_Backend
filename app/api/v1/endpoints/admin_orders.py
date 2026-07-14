"""Owner order management APIs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.authorization.permissions import Permission
from app.common.constants import APIMessages
from app.common.enums import OrderStatus, PaymentStatus
from app.dependencies.authorization import require_permission
from app.dependencies.orders import get_order_service
from app.dependencies.pagination import get_pagination
from app.models.user import User
from app.schemas.orders import (
    OrderDetailResponse,
    OrderFilterParams,
    OrderListItemResponse,
    UpdateOrderNotesRequest,
    UpdateOrderStatusRequest,
    UpdatePaymentStatusRequest,
)
from app.schemas.pagination import PaginationParams
from app.schemas.response import PaginatedResponse, SuccessResponse
from app.services.order import OrderService

router = APIRouter(prefix="/admin/orders", tags=["Admin Orders"])


@router.get("", response_model=PaginatedResponse[OrderListItemResponse])
async def list_orders(
    request: Request,
    pagination: PaginationParams = Depends(get_pagination),
    _: User = Depends(require_permission(Permission.ORDER_READ)),
    service: OrderService = Depends(get_order_service),
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    payment_status: PaymentStatus | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    sort: str = Query(default="newest", pattern="^(newest|oldest)$"),
    q: str | None = Query(default=None, max_length=80),
    user_id: UUID | None = Query(default=None),
) -> PaginatedResponse[OrderListItemResponse]:
    filters = OrderFilterParams(
        status=status_filter,
        payment_status=payment_status,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
        q=q,
        user_id=user_id,
    )
    data, meta = await service.list_admin_orders(filters, pagination)
    return PaginatedResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        meta=meta.model_dump(),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/{order_id}", response_model=SuccessResponse[OrderDetailResponse])
async def get_order(
    order_id: UUID,
    request: Request,
    _: User = Depends(require_permission(Permission.ORDER_READ)),
    service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderDetailResponse]:
    data = await service.get_admin_order(order_id)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/{order_id}/status", response_model=SuccessResponse[OrderDetailResponse])
async def update_order_status(
    order_id: UUID,
    body: UpdateOrderStatusRequest,
    request: Request,
    user: User = Depends(require_permission(Permission.ORDER_UPDATE)),
    service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderDetailResponse]:
    data = await service.update_status(user, order_id, body)
    return SuccessResponse(
        success=True,
        message="Order status updated",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/{order_id}/payment", response_model=SuccessResponse[OrderDetailResponse])
async def update_payment_status(
    order_id: UUID,
    body: UpdatePaymentStatusRequest,
    request: Request,
    user: User = Depends(require_permission(Permission.ORDER_UPDATE)),
    service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderDetailResponse]:
    data = await service.update_payment(user, order_id, body)
    return SuccessResponse(
        success=True,
        message="Payment status updated",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/{order_id}/notes", response_model=SuccessResponse[OrderDetailResponse])
async def update_order_notes(
    order_id: UUID,
    body: UpdateOrderNotesRequest,
    request: Request,
    user: User = Depends(require_permission(Permission.ORDER_UPDATE)),
    service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderDetailResponse]:
    data = await service.update_notes(user, order_id, body)
    return SuccessResponse(
        success=True,
        message="Order notes updated",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )
