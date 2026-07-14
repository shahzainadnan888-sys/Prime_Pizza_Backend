"""Unit tests for JWT and phone validation."""

from __future__ import annotations

from uuid import uuid4

import pytest
from app.config.settings import get_settings
from app.core.exceptions import InvalidPhoneException, InvalidTokenException
from app.security.jwt import JWTService
from app.services.phone import PhoneValidationService


def test_phone_validation_accepts_e164() -> None:
    service = PhoneValidationService()
    assert service.normalize_and_validate("+923001234567") == "+923001234567"


def test_phone_validation_rejects_invalid() -> None:
    service = PhoneValidationService()
    with pytest.raises(InvalidPhoneException):
        service.normalize_and_validate("03001234567")


def test_jwt_token_pair_roundtrip() -> None:
    settings = get_settings()
    jwt_service = JWTService(settings)
    user_id = uuid4()
    access, refresh, access_jti, refresh_jti = jwt_service.create_token_pair(
        user_id=user_id,
        phone_number="+923001234567",
        role="customer",
    )
    access_payload = jwt_service.decode_token(access, expected_type="access")
    refresh_payload = jwt_service.decode_token(refresh, expected_type="refresh")
    assert access_payload["user_id"] == str(user_id)
    assert access_payload["phone_number"] == "+923001234567"
    assert access_payload["role"] == "customer"
    assert access_payload["token_type"] == "access"
    assert access_payload["jti"] == access_jti
    assert refresh_payload["token_type"] == "refresh"
    assert refresh_payload["jti"] == refresh_jti


def test_jwt_rejects_wrong_type() -> None:
    settings = get_settings()
    jwt_service = JWTService(settings)
    access, _, _, _ = jwt_service.create_token_pair(
        user_id=uuid4(),
        phone_number="+923001234567",
        role="customer",
    )
    with pytest.raises(InvalidTokenException):
        jwt_service.decode_token(access, expected_type="refresh")
