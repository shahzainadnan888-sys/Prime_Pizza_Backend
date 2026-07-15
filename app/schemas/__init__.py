"""Pydantic schema package."""

from app.schemas.auth import (
    AuthResponse,
    AuthUserResponse,
    LoginRequest,
    LogoutRequest,
    MeResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenPairResponse,
)
from app.schemas.pagination import PaginationMeta, PaginationParams
from app.schemas.response import (
    ErrorDetail,
    ErrorResponse,
    MessageResponse,
    PaginatedResponse,
    SuccessResponse,
)

__all__ = [
    "AuthResponse",
    "AuthUserResponse",
    "ErrorDetail",
    "ErrorResponse",
    "LoginRequest",
    "LogoutRequest",
    "MeResponse",
    "MessageResponse",
    "PaginatedResponse",
    "PaginationMeta",
    "PaginationParams",
    "RefreshTokenRequest",
    "RegisterRequest",
    "SuccessResponse",
    "TokenPairResponse",
]
