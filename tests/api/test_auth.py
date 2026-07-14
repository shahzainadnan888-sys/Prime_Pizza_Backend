"""Authentication API tests (AuthService mocked at the boundary)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.common.enums import UserRole
from app.config.settings import Settings, get_settings
from app.core.exceptions import InvalidOTPException, RateLimitException
from app.main import create_app
from app.models.user import User
from app.schemas.auth import AuthResponse, AuthUserResponse, TokenPairResponse
from fastapi.testclient import TestClient


@pytest.fixture
def settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture
def app(settings: Settings):
    return create_app(settings=settings)


def _mock_user(*, phone: str = "+923001234567", is_new: bool = False) -> User:
    user = User(
        id=uuid4(),
        phone_number=phone,
        full_name="Customer 4567",
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        version=1,
    )
    return user


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


def test_send_otp_success(client, monkeypatch) -> None:
    async def _send(self, phone_number: str, **_kwargs):
        from app.schemas.auth import SendOTPResponse

        return SendOTPResponse(phone_number=phone_number, expires_in=300)

    monkeypatch.setattr("app.services.auth.AuthService.send_otp", _send)
    response = client.post("/api/v1/auth/send-otp", json={"phone_number": "+923001234567"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["phone_number"] == "+923001234567"


def test_send_otp_invalid_phone(client) -> None:
    response = client.post("/api/v1/auth/send-otp", json={"phone_number": "12345"})
    assert response.status_code == 422


def test_verify_otp_first_login(client, monkeypatch) -> None:
    user = _mock_user(is_new=True)

    async def _verify(self, phone_number: str, code: str, **_kwargs):
        return AuthResponse(
            user=AuthUserResponse.model_validate(user),
            tokens=TokenPairResponse(
                access_token="access",
                refresh_token="refresh",
                expires_in=1800,
            ),
            is_new_user=True,
        )

    monkeypatch.setattr("app.services.auth.AuthService.verify_otp", _verify)
    response = client.post(
        "/api/v1/auth/verify-otp",
        json={"phone_number": "+923001234567", "code": "123456"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["is_new_user"] is True
    assert body["data"]["tokens"]["access_token"] == "access"


def test_verify_otp_invalid(client, monkeypatch) -> None:
    async def _verify(self, phone_number: str, code: str, **_kwargs):
        raise InvalidOTPException("Invalid verification code")

    monkeypatch.setattr("app.services.auth.AuthService.verify_otp", _verify)
    response = client.post(
        "/api/v1/auth/verify-otp",
        json={"phone_number": "+923001234567", "code": "000000"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_otp"


def test_me_unauthorized(client) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_refresh_and_logout_flow(client, monkeypatch) -> None:
    user = _mock_user()

    async def _refresh(self, refresh_token: str):
        return AuthResponse(
            user=AuthUserResponse.model_validate(user),
            tokens=TokenPairResponse(
                access_token="new-access",
                refresh_token="new-refresh",
                expires_in=1800,
            ),
            is_new_user=False,
        )

    async def _logout(self, *, access_payload, refresh_token):
        return None

    monkeypatch.setattr("app.services.auth.AuthService.refresh", _refresh)
    monkeypatch.setattr("app.services.auth.AuthService.logout", _logout)

    # Bypass token dependency for logout by mocking get_token_payload
    async def _payload():
        return {"jti": "abc", "user_id": str(user.id), "token_type": "access", "exp": 9999999999}

    from app.dependencies import auth as auth_deps

    app = client.app
    app.dependency_overrides[auth_deps.get_token_payload] = _payload

    refresh_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "x" * 40})
    assert refresh_resp.status_code == 200
    assert refresh_resp.json()["data"]["tokens"]["access_token"] == "new-access"

    logout_resp = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "y" * 40},
        headers={"Authorization": "Bearer unused"},
    )
    assert logout_resp.status_code == 200
    app.dependency_overrides.clear()


def test_send_otp_rate_limited(client, monkeypatch) -> None:
    async def _send(self, phone_number: str, **_kwargs):
        raise RateLimitException("Too many OTP requests. Please try again later.")

    monkeypatch.setattr("app.services.auth.AuthService.send_otp", _send)
    response = client.post("/api/v1/auth/send-otp", json={"phone_number": "+923001234567"})
    assert response.status_code == 429
