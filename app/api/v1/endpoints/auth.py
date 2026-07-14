"""Authentication API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status

from app.common.constants import APIMessages
from app.dependencies.auth import get_auth_service, get_current_user, get_token_payload
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LogoutRequest,
    MeResponse,
    RefreshTokenRequest,
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
)
from app.schemas.response import MessageResponse, SuccessResponse
from app.services.auth import AuthService
from app.utils.network import get_client_ip

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/send-otp",
    response_model=SuccessResponse[SendOTPResponse],
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    summary="Send OTP (local Redis provider)",
    description=(
        "Generates a cryptographically secure 6-digit OTP, stores it in Redis "
        "(TTL 5 minutes), prints it to the server terminal, and optionally "
        "echoes it in the response when APP_ENV=development. Rate limited per "
        "phone, IP, and globally."
    ),
    responses={
        200: {"description": "OTP challenge created"},
        422: {"description": "Invalid phone number"},
        429: {"description": "OTP or HTTP rate limit exceeded"},
    },
)
async def send_otp(
    body: SendOTPRequest,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
) -> SuccessResponse[SendOTPResponse]:
    data = await auth.send_otp(body.phone_number, client_ip=get_client_ip(request))
    return SuccessResponse(
        success=True,
        message=data.message,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/verify-otp",
    response_model=SuccessResponse[AuthResponse],
    status_code=status.HTTP_200_OK,
    summary="Verify OTP and issue tokens",
    description=(
        "Verifies the OTP, upserts the user (owner phone becomes owner role), "
        "mirrors identity to data/users.json, and returns JWT access + refresh tokens."
    ),
    responses={
        200: {"description": "Authenticated — returns token pair and user profile"},
        400: {"description": "Invalid or expired OTP"},
        422: {"description": "Validation error"},
        429: {"description": "Rate limited"},
    },
)
async def verify_otp(
    body: VerifyOTPRequest,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
) -> SuccessResponse[AuthResponse]:
    data = await auth.verify_otp(
        body.phone_number,
        body.code,
        client_ip=get_client_ip(request),
    )
    return SuccessResponse(
        success=True,
        message="Authentication successful",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/refresh",
    response_model=SuccessResponse[AuthResponse],
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
)
async def refresh_token(
    body: RefreshTokenRequest,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
) -> SuccessResponse[AuthResponse]:
    data = await auth.refresh(body.refresh_token)
    return SuccessResponse(
        success=True,
        message="Token refreshed",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout and revoke tokens",
)
async def logout(
    request: Request,
    body: LogoutRequest | None = None,
    auth: AuthService = Depends(get_auth_service),
    payload: dict = Depends(get_token_payload),
) -> MessageResponse:
    await auth.logout(
        access_payload=payload,
        refresh_token=(body.refresh_token if body else None),
    )
    return MessageResponse(
        success=True,
        message="Logged out successfully",
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "/me",
    response_model=SuccessResponse[MeResponse],
    status_code=status.HTTP_200_OK,
    summary="Current authenticated user",
)
async def me(
    request: Request,
    user: User = Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
) -> SuccessResponse[MeResponse]:
    data = await auth.get_me(user)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )
