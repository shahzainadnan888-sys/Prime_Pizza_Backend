"""Authenticated cart APIs."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.authorization.permissions import Permission
from app.common.constants import APIMessages
from app.dependencies.authorization import require_permission
from app.dependencies.cart import get_cart_service
from app.models.user import User
from app.schemas.cart import (
    AddCartItemRequest,
    ApplyCouponRequest,
    CartResponse,
    OrderSummaryResponse,
    UpdateCartItemRequest,
)
from app.schemas.response import SuccessResponse
from app.services.cart import CartService

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("", response_model=SuccessResponse[CartResponse])
async def get_cart(
    request: Request,
    user: User = Depends(require_permission(Permission.CART_MANAGE_OWN)),
    service: CartService = Depends(get_cart_service),
) -> SuccessResponse[CartResponse]:
    data = await service.get_cart(user)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/summary", response_model=SuccessResponse[OrderSummaryResponse])
async def get_cart_summary(
    request: Request,
    user: User = Depends(require_permission(Permission.CART_MANAGE_OWN)),
    service: CartService = Depends(get_cart_service),
) -> SuccessResponse[OrderSummaryResponse]:
    data = await service.get_summary(user)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/items",
    response_model=SuccessResponse[CartResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_cart_item(
    body: AddCartItemRequest,
    request: Request,
    user: User = Depends(require_permission(Permission.CART_MANAGE_OWN)),
    service: CartService = Depends(get_cart_service),
) -> SuccessResponse[CartResponse]:
    data = await service.add_item(user, body)
    return SuccessResponse(
        success=True,
        message="Product added to cart",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/items/{item_id}", response_model=SuccessResponse[CartResponse])
async def update_cart_item(
    item_id: UUID,
    body: UpdateCartItemRequest,
    request: Request,
    user: User = Depends(require_permission(Permission.CART_MANAGE_OWN)),
    service: CartService = Depends(get_cart_service),
) -> SuccessResponse[CartResponse]:
    data = await service.update_item(user, item_id, body)
    return SuccessResponse(
        success=True,
        message="Cart item updated",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/items/{item_id}", response_model=SuccessResponse[CartResponse])
async def remove_cart_item(
    item_id: UUID,
    request: Request,
    user: User = Depends(require_permission(Permission.CART_MANAGE_OWN)),
    service: CartService = Depends(get_cart_service),
) -> SuccessResponse[CartResponse]:
    data = await service.remove_item(user, item_id)
    return SuccessResponse(
        success=True,
        message="Product removed from cart",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/clear", response_model=SuccessResponse[CartResponse])
async def clear_cart(
    request: Request,
    user: User = Depends(require_permission(Permission.CART_MANAGE_OWN)),
    service: CartService = Depends(get_cart_service),
) -> SuccessResponse[CartResponse]:
    data = await service.clear(user)
    return SuccessResponse(
        success=True,
        message="Cart cleared",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/apply-coupon", response_model=SuccessResponse[CartResponse])
async def apply_coupon(
    body: ApplyCouponRequest,
    request: Request,
    user: User = Depends(require_permission(Permission.CART_MANAGE_OWN)),
    service: CartService = Depends(get_cart_service),
) -> SuccessResponse[CartResponse]:
    data = await service.apply_coupon(user, body)
    return SuccessResponse(
        success=True,
        message="Coupon applied",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/remove-coupon", response_model=SuccessResponse[CartResponse])
async def remove_coupon(
    request: Request,
    user: User = Depends(require_permission(Permission.CART_MANAGE_OWN)),
    service: CartService = Depends(get_cart_service),
) -> SuccessResponse[CartResponse]:
    data = await service.remove_coupon(user)
    return SuccessResponse(
        success=True,
        message="Coupon removed",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )
