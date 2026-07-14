"""Checkout preparation APIs — validation only, no order creation."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.authorization.permissions import Permission
from app.dependencies.authorization import require_permission
from app.dependencies.cart import get_checkout_validation_service
from app.models.user import User
from app.schemas.cart import CheckoutValidationResponse
from app.schemas.response import SuccessResponse
from app.services.checkout import CheckoutValidationService

router = APIRouter(prefix="/checkout", tags=["Checkout"])


@router.post("/validate", response_model=SuccessResponse[CheckoutValidationResponse])
async def validate_checkout(
    request: Request,
    user: User = Depends(require_permission(Permission.CART_MANAGE_OWN)),
    service: CheckoutValidationService = Depends(get_checkout_validation_service),
) -> SuccessResponse[CheckoutValidationResponse]:
    data = await service.validate(user)
    return SuccessResponse(
        success=True,
        message="Checkout validation completed" if data.is_valid else "Checkout validation failed",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )
