"""Authentication request / response schemas (Pydantic v2)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, computed_field, field_validator, model_validator

from app.common.enums import UserRole
from app.security.passwords import validate_password_strength
from app.utils.phone import is_valid_e164, normalize_phone


class RegisterRequest(BaseModel):
    """Customer registration payload."""

    first_name: str = Field(..., min_length=1, max_length=80)
    last_name: str = Field(..., min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    phone_number: str | None = Field(default=None, max_length=20)

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_names(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name cannot be empty")
        return cleaned

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, value: str) -> str:
        return validate_password_strength(value)

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None or not str(value).strip():
            return None
        normalized = normalize_phone(value)
        if not is_valid_e164(normalized):
            raise ValueError("Phone number must be a valid E.164 number (e.g. +923001234567)")
        return normalized

    @model_validator(mode="after")
    def passwords_match(self) -> RegisterRequest:
        if self.password != self.confirm_password:
            raise ValueError("Password and confirm password do not match")
        return self


class LoginRequest(BaseModel):
    """Email + password login payload."""

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


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
    first_name: str
    last_name: str
    email: str
    phone_number: str | None
    full_name: str
    role: UserRole
    is_verified: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def name(self) -> str:
        """Frontend-friendly display name alias."""
        return self.full_name or f"{self.first_name} {self.last_name}".strip()


class AuthResponse(BaseModel):
    """Successful register / login / refresh response payload."""

    user: AuthUserResponse
    tokens: TokenPairResponse
    is_new_user: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def access_token(self) -> str:
        """Flattened token for frontends that read data.access_token."""
        return self.tokens.access_token

    @computed_field  # type: ignore[prop-decorator]
    @property
    def refresh_token(self) -> str:
        """Flattened token for frontends that read data.refresh_token."""
        return self.tokens.refresh_token

    @computed_field  # type: ignore[prop-decorator]
    @property
    def token_type(self) -> str:
        return self.tokens.token_type

    @computed_field  # type: ignore[prop-decorator]
    @property
    def expires_in(self) -> int:
        return self.tokens.expires_in

    @computed_field  # type: ignore[prop-decorator]
    @property
    def role(self) -> UserRole:
        """Top-level role mirror so UIs can route without digging into user."""
        return self.user.role


class MeResponse(BaseModel):
    """Authenticated profile for GET /auth/me."""

    id: UUID
    first_name: str
    last_name: str
    email: str
    phone_number: str | None
    full_name: str
    role: UserRole
    is_verified: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def name(self) -> str:
        return self.full_name or f"{self.first_name} {self.last_name}".strip()
