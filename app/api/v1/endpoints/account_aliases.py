"""Frontend-compatible account/address aliases under /api/v1."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.common.constants import APIMessages
from app.dependencies.authorization import require_verified
from app.dependencies.users import get_address_service, get_user_service
from app.models.user import User
from app.schemas.response import SuccessResponse
from app.schemas.users import AddressResponse, UserProfileResponse
from app.services.address import AddressService
from app.services.user import UserService

router = APIRouter(tags=["Account"])


@router.get(
    "/account",
    response_model=SuccessResponse[UserProfileResponse],
    summary="Get account profile (alias of /users/me)",
)
async def get_account(
    request: Request,
    user: User = Depends(require_verified),
    service: UserService = Depends(get_user_service),
) -> SuccessResponse[UserProfileResponse]:
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=service.get_profile(user),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "/addresses",
    response_model=SuccessResponse[list[AddressResponse]],
    summary="List delivery addresses (alias of /users/addresses)",
)
async def list_account_addresses(
    request: Request,
    user: User = Depends(require_verified),
    service: AddressService = Depends(get_address_service),
) -> SuccessResponse[list[AddressResponse]]:
    data = await service.list_addresses(user)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )
