"""Customer order APIs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.authorization.permissions import Permission
from app.common.constants import APIMessages
from app.common.enums import OrderStatus, PaymentStatus
from app.dependencies.authorization import require_permission
from app.dependencies.orders import get_order_service
from app.dependencies.pagination import get_pagination
from app.models.user import User
from app.schemas.orders import (
    CancelOrderRequest,
    OrderDetailResponse,
    OrderFilterParams,
    OrderListItemResponse,
    OrderTrackingResponse,
    PlaceOrderRequest,
)
from app.schemas.pagination import PaginationParams
from app.schemas.response import PaginatedResponse, SuccessResponse
from app.services.order import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=SuccessResponse[OrderDetailResponse], status_code=status.HTTP_201_CREATED)
async def place_order(
    body: PlaceOrderRequest,
    request: Request,
    user: User = Depends(require_permission(Permission.ORDER_CREATE)),
    service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderDetailResponse]:
    data = await service.place_order(user, body)
    return SuccessResponse(
        success=True,
        message="Order placed successfully",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("", response_model=PaginatedResponse[OrderListItemResponse])
async def list_my_orders(
    request: Request,
    pagination: PaginationParams = Depends(get_pagination),
    user: User = Depends(require_permission(Permission.ORDER_READ_OWN)),
    service: OrderService = Depends(get_order_service),
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    payment_status: PaymentStatus | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    sort: str = Query(default="newest", pattern="^(newest|oldest)$"),
) -> PaginatedResponse[OrderListItemResponse]:
    filters = OrderFilterParams(
        status=status_filter,
        payment_status=payment_status,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
    )
    data, meta = await service.list_my_orders(user, filters, pagination)
    return PaginatedResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        meta=meta.model_dump(),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/{order_id}", response_model=SuccessResponse[OrderDetailResponse])
async def get_my_order(
    order_id: UUID,
    request: Request,
    user: User = Depends(require_permission(Permission.ORDER_READ_OWN)),
    service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderDetailResponse]:
    data = await service.get_my_order(user, order_id)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/{order_id}/tracking", response_model=SuccessResponse[OrderTrackingResponse])
async def track_my_order(
    order_id: UUID,
    request: Request,
    user: User = Depends(require_permission(Permission.ORDER_TRACK_OWN)),
    service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderTrackingResponse]:
    data = await service.track_my_order(user, order_id)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/{order_id}/cancel", response_model=SuccessResponse[OrderDetailResponse])
async def cancel_my_order(
    order_id: UUID,
    request: Request,
    body: CancelOrderRequest | None = None,
    user: User = Depends(require_permission(Permission.ORDER_CREATE)),
    service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderDetailResponse]:
    data = await service.cancel_my_order(user, order_id, body or CancelOrderRequest())
    return SuccessResponse(
        success=True,
        message="Order cancelled",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )
