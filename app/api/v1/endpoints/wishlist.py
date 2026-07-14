"""Authenticated wishlist APIs."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.authorization.permissions import Permission
from app.common.constants import APIMessages
from app.dependencies.authorization import require_permission
from app.dependencies.cart import get_wishlist_service
from app.models.user import User
from app.schemas.cart import WishlistAddRequest, WishlistResponse
from app.schemas.response import SuccessResponse
from app.services.wishlist import WishlistService

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])


@router.get("", response_model=SuccessResponse[WishlistResponse])
async def get_wishlist(
    request: Request,
    user: User = Depends(require_permission(Permission.WISHLIST_MANAGE_OWN)),
    service: WishlistService = Depends(get_wishlist_service),
) -> SuccessResponse[WishlistResponse]:
    data = await service.list_wishlist(user)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("", response_model=SuccessResponse[WishlistResponse], status_code=status.HTTP_201_CREATED)
async def add_wishlist_item(
    body: WishlistAddRequest,
    request: Request,
    user: User = Depends(require_permission(Permission.WISHLIST_MANAGE_OWN)),
    service: WishlistService = Depends(get_wishlist_service),
) -> SuccessResponse[WishlistResponse]:
    data = await service.add(user, body.product_id)
    return SuccessResponse(
        success=True,
        message="Product added to wishlist",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/clear", response_model=SuccessResponse[WishlistResponse])
async def clear_wishlist(
    request: Request,
    user: User = Depends(require_permission(Permission.WISHLIST_MANAGE_OWN)),
    service: WishlistService = Depends(get_wishlist_service),
) -> SuccessResponse[WishlistResponse]:
    data = await service.clear(user)
    return SuccessResponse(
        success=True,
        message="Wishlist cleared",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/{product_id}", response_model=SuccessResponse[WishlistResponse])
async def remove_wishlist_item(
    product_id: UUID,
    request: Request,
    user: User = Depends(require_permission(Permission.WISHLIST_MANAGE_OWN)),
    service: WishlistService = Depends(get_wishlist_service),
) -> SuccessResponse[WishlistResponse]:
    data = await service.remove(user, product_id)
    return SuccessResponse(
        success=True,
        message="Product removed from wishlist",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )
