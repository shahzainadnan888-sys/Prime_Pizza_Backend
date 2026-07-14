"""Authentication request / response schemas (Pydantic v2)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.common.enums import UserRole
from app.utils.phone import is_valid_e164, normalize_phone


class SendOTPRequest(BaseModel):
    """Request body for sending a verification OTP."""

    phone_number: str = Field(..., min_length=8, max_length=20, examples=["+923001234567"])

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = normalize_phone(value)
        if not is_valid_e164(normalized):
            msg = "Phone number must be a valid E.164 number (e.g. +923001234567)"
            raise ValueError(msg)
        return normalized


class VerifyOTPRequest(BaseModel):
    """Request body for verifying an OTP and logging in."""

    phone_number: str = Field(..., min_length=8, max_length=20)
    code: str = Field(..., min_length=4, max_length=10, pattern=r"^\d+$")

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = normalize_phone(value)
        if not is_valid_e164(normalized):
            msg = "Phone number must be a valid E.164 number (e.g. +923001234567)"
            raise ValueError(msg)
        return normalized


class RefreshTokenRequest(BaseModel):
    """Request body for refreshing access tokens."""

    refresh_token: str = Field(..., min_length=20)


class LogoutRequest(BaseModel):
    """Optional refresh token to revoke on logout."""

    refresh_token: str | None = Field(default=None, min_length=20)


class TokenPairResponse(BaseModel):
    """Issued JWT pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token lifetime in seconds")


class AuthUserResponse(BaseModel):
    """Public user fields returned after authentication."""

    id: UUID
    phone_number: str
    full_name: str
    role: UserRole
    is_verified: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """Successful verify-otp / refresh response payload."""

    user: AuthUserResponse
    tokens: TokenPairResponse
    is_new_user: bool = False


class MeResponse(BaseModel):
    """Authenticated profile for GET /auth/me."""

    id: UUID
    phone_number: str
    role: UserRole
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SendOTPResponse(BaseModel):
    """Acknowledgement after OTP dispatch."""

    phone_number: str
    expires_in: int
    message: str = "Verification code sent"
    # Present only when APP_ENV=development — never set in staging/production.
    otp: str | None = Field(
        default=None,
        description="Development-only OTP echo. Omitted outside APP_ENV=development.",
    )
