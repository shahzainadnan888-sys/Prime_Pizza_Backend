"""Pydantic schema package."""

from app.schemas.auth import (
    AuthResponse,
    AuthUserResponse,
    LogoutRequest,
    MeResponse,
    RefreshTokenRequest,
    SendOTPRequest,
    SendOTPResponse,
    TokenPairResponse,
    VerifyOTPRequest,
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
    "LogoutRequest",
    "MeResponse",
    "MessageResponse",
    "PaginatedResponse",
    "PaginationMeta",
    "PaginationParams",
    "RefreshTokenRequest",
    "SendOTPRequest",
    "SendOTPResponse",
    "SuccessResponse",
    "TokenPairResponse",
    "VerifyOTPRequest",
]
