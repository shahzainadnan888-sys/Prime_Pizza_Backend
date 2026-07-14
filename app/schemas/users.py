"""User module request / response schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.common.enums import NotificationType, UserRole
from app.utils.phone import is_valid_e164, normalize_phone


class UserProfileResponse(BaseModel):
    id: UUID
    full_name: str
    phone_number: str
    email: EmailStr | None = None
    avatar_url: str | None = None
    role: UserRole
    is_verified: bool
    is_active: bool
    created_at: datetime
    last_login: datetime | None = None

    model_config = {"from_attributes": True}


class UserProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None


class AddressCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    recipient_name: str = Field(..., min_length=2, max_length=150)
    phone_number: str = Field(..., min_length=8, max_length=20)
    street: str = Field(..., min_length=3, max_length=255)
    area: str | None = Field(default=None, max_length=150)
    city: str = Field(..., min_length=2, max_length=100)
    province: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., min_length=3, max_length=20)
    country: str = Field(default="Pakistan", min_length=2, max_length=100)
    latitude: Decimal | None = Field(default=None, ge=Decimal("-90"), le=Decimal("90"))
    longitude: Decimal | None = Field(default=None, ge=Decimal("-180"), le=Decimal("180"))
    delivery_notes: str | None = Field(default=None, max_length=1000)
    is_default: bool = False

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = normalize_phone(value)
        if not is_valid_e164(normalized):
            msg = "Address phone must be a valid E.164 number"
            raise ValueError(msg)
        return normalized


class AddressUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    recipient_name: str | None = Field(default=None, min_length=2, max_length=150)
    phone_number: str | None = Field(default=None, min_length=8, max_length=20)
    street: str | None = Field(default=None, min_length=3, max_length=255)
    area: str | None = Field(default=None, max_length=150)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    province: str | None = Field(default=None, min_length=2, max_length=100)
    postal_code: str | None = Field(default=None, min_length=3, max_length=20)
    country: str | None = Field(default=None, min_length=2, max_length=100)
    latitude: Decimal | None = Field(default=None, ge=Decimal("-90"), le=Decimal("90"))
    longitude: Decimal | None = Field(default=None, ge=Decimal("-180"), le=Decimal("180"))
    delivery_notes: str | None = Field(default=None, max_length=1000)
    is_default: bool | None = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = normalize_phone(value)
        if not is_valid_e164(normalized):
            msg = "Address phone must be a valid E.164 number"
            raise ValueError(msg)
        return normalized


class AddressResponse(BaseModel):
    id: UUID
    title: str
    recipient_name: str
    phone_number: str
    street: str
    area: str | None = None
    city: str
    province: str
    postal_code: str
    country: str
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    delivery_notes: str | None = None
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PreferenceResponse(BaseModel):
    dark_mode: bool
    language: str
    marketing_emails: bool
    marketing_sms: bool
    push_notifications: bool
    order_updates: bool
    promotional_notifications: bool
    preferred_currency: str
    preferred_timezone: str

    model_config = {"from_attributes": True}


class PreferenceUpdateRequest(BaseModel):
    dark_mode: bool | None = None
    language: str | None = Field(default=None, min_length=2, max_length=10)
    marketing_emails: bool | None = None
    marketing_sms: bool | None = None
    push_notifications: bool | None = None
    order_updates: bool | None = None
    promotional_notifications: bool | None = None
    preferred_currency: str | None = Field(default=None, min_length=3, max_length=10)
    preferred_timezone: str | None = Field(default=None, min_length=3, max_length=64)


class NotificationResponse(BaseModel):
    id: UUID
    title: str
    message: str
    notification_type: NotificationType
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AvatarUploadResponse(BaseModel):
    avatar_url: str
