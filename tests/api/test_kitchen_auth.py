"""API authorization tests for chef kitchen vs customer."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.common.enums import UserRole
from app.config.settings import get_settings
from app.core.exceptions import ForbiddenException
from app.main import create_app
from app.models.user import User
from app.schemas.auth import AuthResponse, AuthUserResponse, TokenPairResponse
from app.schemas.kitchen import KitchenBoardResponse
from fastapi.testclient import TestClient


def _user(*, role: UserRole, email: str = "user@example.com") -> User:
    return User(
        id=uuid4(),
        first_name="Test",
        last_name="User",
        phone_number="+923001234567",
        full_name="Test User",
        email=email,
        password_hash="hashed",
        role=role,
        is_active=True,
        is_verified=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        version=1,
    )


def test_customer_forbidden_on_kitchen_aliases() -> None:
    from app.api.v1.endpoints import kitchen as kitchen_ep
    from app.dependencies import auth as auth_deps

    app = create_app(settings=get_settings())
    customer = _user(role=UserRole.CUSTOMER)

    async def _current() -> User:
        return customer

    async def _deny_chef() -> User:
        raise ForbiddenException("Chef access required")

    class _FakeKitchen:
        async def get_board(self) -> KitchenBoardResponse:
            return KitchenBoardResponse()

    app.dependency_overrides[auth_deps.get_current_user] = _current
    app.dependency_overrides[auth_deps.get_verified_user] = _current
    app.dependency_overrides[auth_deps.get_current_chef] = _deny_chef
    app.dependency_overrides[kitchen_ep.get_kitchen_service] = lambda: _FakeKitchen()

    with TestClient(app) as client:
        for path in (
            "/api/v1/kitchen/orders",
            "/api/v1/chef/orders",
            "/api/v1/orders/kitchen/orders",
            "/api/v1/dashboard/chef/orders",
        ):
            resp = client.get(path)
            assert resp.status_code == 403, path


def test_chef_can_access_kitchen_aliases() -> None:
    from app.api.v1.endpoints import kitchen as kitchen_ep
    from app.dependencies import auth as auth_deps

    app = create_app(settings=get_settings())
    chef = _user(role=UserRole.CHEF, email="chef123@gmail.com")

    async def _current() -> User:
        return chef

    class _FakeKitchen:
        async def get_board(self) -> KitchenBoardResponse:
            return KitchenBoardResponse()

    app.dependency_overrides[auth_deps.get_current_user] = _current
    app.dependency_overrides[auth_deps.get_verified_user] = _current
    app.dependency_overrides[auth_deps.get_current_chef] = _current
    app.dependency_overrides[kitchen_ep.get_kitchen_service] = lambda: _FakeKitchen()

    with TestClient(app) as client:
        for path in (
            "/api/v1/kitchen/orders",
            "/api/v1/chef/orders",
            "/api/v1/orders/kitchen/orders",
            "/api/v1/dashboard/chef/orders",
        ):
            resp = client.get(path)
            assert resp.status_code == 200, (path, resp.text)
            body = resp.json()
            assert body["success"] is True
            assert "incoming" in body["data"]
            assert "pending" in body["data"]
            assert "preparing" in body["data"]
            assert "ready" in body["data"]
            assert "completed" in body["data"]


def test_login_payload_exposes_role_for_frontend_routing() -> None:
    user = AuthUserResponse(
        id=uuid4(),
        first_name="Kitchen",
        last_name="Chef",
        email="chef123@gmail.com",
        phone_number=None,
        full_name="Kitchen Chef",
        role=UserRole.CHEF,
        is_verified=True,
        is_active=True,
        created_at=datetime.now(UTC),
    )
    tokens = TokenPairResponse(
        access_token="access.jwt",
        refresh_token="refresh.jwt",
        token_type="bearer",
        expires_in=1800,
    )
    payload = AuthResponse(user=user, tokens=tokens).model_dump(mode="json")
    assert payload["role"] == "chef"
    assert payload["user"]["role"] == "chef"
    assert payload["user"]["name"] == "Kitchen Chef"
    assert payload["access_token"] == "access.jwt"
    assert payload["tokens"]["access_token"] == "access.jwt"
