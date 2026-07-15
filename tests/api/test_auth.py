"""API tests for email/password authentication endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from app.common.enums import UserRole
from app.core.exceptions import ConflictException, RateLimitException, UnauthorizedException
from app.schemas.auth import AuthResponse, AuthUserResponse, TokenPairResponse


def _auth_response(*, is_new: bool = False) -> AuthResponse:
    user = AuthUserResponse(
        id=uuid4(),
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        phone_number=None,
        full_name="Ada Lovelace",
        role=UserRole.CUSTOMER,
        is_verified=True,
        is_active=True,
        created_at=datetime.now(UTC),
    )
    tokens = TokenPairResponse(
        access_token="access.jwt.token",
        refresh_token="refresh.jwt.token",
        token_type="bearer",
        expires_in=1800,
    )
    return AuthResponse(user=user, tokens=tokens, is_new_user=is_new)


def test_register_success(client, monkeypatch) -> None:
    async def _register(self, payload, *, client_ip=None):
        return _auth_response(is_new=True)

    monkeypatch.setattr("app.services.auth.AuthService.register", _register)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "password": "SecurePass1",
            "confirm_password": "SecurePass1",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["is_new_user"] is True
    assert body["data"]["tokens"]["access_token"]


def test_register_password_mismatch(client) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "password": "SecurePass1",
            "confirm_password": "SecurePass2",
        },
    )
    assert response.status_code == 422


def test_register_weak_password(client) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "password": "weak",
            "confirm_password": "weak",
        },
    )
    assert response.status_code == 422


def test_register_duplicate_email(client, monkeypatch) -> None:
    async def _register(self, payload, *, client_ip=None):
        raise ConflictException("An account with this email already exists")

    monkeypatch.setattr("app.services.auth.AuthService.register", _register)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "password": "SecurePass1",
            "confirm_password": "SecurePass1",
        },
    )
    assert response.status_code == 409


def test_login_success(client, monkeypatch) -> None:
    async def _login(self, payload, *, client_ip=None):
        return _auth_response(is_new=False)

    monkeypatch.setattr("app.services.auth.AuthService.login", _login)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ada@example.com", "password": "SecurePass1"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["tokens"]["refresh_token"]


def test_login_invalid(client, monkeypatch) -> None:
    async def _login(self, payload, *, client_ip=None):
        raise UnauthorizedException("Invalid email or password")

    monkeypatch.setattr("app.services.auth.AuthService.login", _login)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ada@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


def test_refresh_success(client, monkeypatch) -> None:
    async def _refresh(self, refresh_token: str):
        return _auth_response()

    monkeypatch.setattr("app.services.auth.AuthService.refresh", _refresh)
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "x" * 40},
    )
    assert response.status_code == 200


def test_register_rate_limited(client, monkeypatch) -> None:
    async def _register(self, payload, *, client_ip=None):
        raise RateLimitException("Too many registration attempts. Please try again later.")

    monkeypatch.setattr("app.services.auth.AuthService.register", _register)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "password": "SecurePass1",
            "confirm_password": "SecurePass1",
        },
    )
    assert response.status_code == 429
