"""Authentication API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status

from app.common.constants import APIMessages
from app.dependencies.auth import get_auth_service, get_current_user, get_token_payload
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    MeResponse,
    RefreshTokenRequest,
    RegisterRequest,
)
from app.schemas.response import MessageResponse, SuccessResponse
from app.services.auth import AuthService
from app.utils.network import get_client_ip

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=SuccessResponse[AuthResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a customer account",
    description=(
        "Creates a customer with email/password (bcrypt), persists to PostgreSQL, "
        "mirrors to data/users.json, and returns a JWT access + refresh pair."
    ),
    responses={
        201: {"description": "Registered — returns token pair and user profile"},
        409: {"description": "Email or phone already registered"},
        422: {"description": "Validation error"},
        429: {"description": "Rate limited"},
    },
)
async def register(
    body: RegisterRequest,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
) -> SuccessResponse[AuthResponse]:
    data = await auth.register(body, client_ip=get_client_ip(request))
    return SuccessResponse(
        success=True,
        message="Registration successful",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/login",
    response_model=SuccessResponse[AuthResponse],
    status_code=status.HTTP_200_OK,
    summary="Login with email and password",
    description="Validates credentials and issues a JWT access + refresh pair.",
    responses={
        200: {"description": "Authenticated"},
        401: {"description": "Invalid credentials"},
        429: {"description": "Rate limited"},
    },
)
async def login(
    body: LoginRequest,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
) -> SuccessResponse[AuthResponse]:
    data = await auth.login(body, client_ip=get_client_ip(request))
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
