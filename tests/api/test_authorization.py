"""API-level authorization dependency tests."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.authorization.permissions import Permission
from app.common.enums import UserRole
from app.dependencies.authorization import require_owner, require_permission
from app.main import create_app
from app.models.user import User
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient


def _user(role: UserRole) -> User:
    return User(
        id=uuid4(),
        phone_number="+923001234567",
        full_name="API User",
        role=role,
        is_active=True,
        is_verified=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        version=1,
    )


def _build_protected_app() -> FastAPI:
    from app.config.settings import get_settings

    settings = get_settings()
    app = create_app(settings=settings)

    @app.get("/__test/owner-only")
    async def owner_only(user: User = Depends(require_owner)) -> dict:
        return {"ok": True, "role": str(user.role)}

    @app.get("/__test/product-create")
    async def product_create(
        user: User = Depends(require_permission(Permission.PRODUCT_CREATE)),
    ) -> dict:
        return {"ok": True, "user_id": str(user.id)}

    return app


def test_owner_dependency_allows_owner(monkeypatch) -> None:
    app = _build_protected_app()
    owner = _user(UserRole.OWNER)

    async def _current_user():
        return owner

    from app.dependencies import auth as auth_deps

    app.dependency_overrides[auth_deps.get_current_user] = _current_user
    app.dependency_overrides[auth_deps.get_verified_user] = _current_user

    with TestClient(app) as client:
        response = client.get("/__test/owner-only")
        assert response.status_code == 200
        assert response.json()["ok"] is True
    app.dependency_overrides.clear()


def test_owner_dependency_forbids_customer() -> None:
    app = _build_protected_app()
    customer = _user(UserRole.CUSTOMER)

    async def _current_user():
        return customer

    from app.dependencies import auth as auth_deps

    app.dependency_overrides[auth_deps.get_current_user] = _current_user
    app.dependency_overrides[auth_deps.get_verified_user] = _current_user

    with TestClient(app) as client:
        response = client.get("/__test/owner-only")
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "forbidden"
    app.dependency_overrides.clear()


def test_permission_dependency_forbids_customer_product_create() -> None:
    app = _build_protected_app()
    customer = _user(UserRole.CUSTOMER)

    async def _current_user():
        return customer

    from app.dependencies import auth as auth_deps

    app.dependency_overrides[auth_deps.get_current_user] = _current_user
    app.dependency_overrides[auth_deps.get_verified_user] = _current_user

    with TestClient(app) as client:
        response = client.get("/__test/product-create")
        assert response.status_code == 403
    app.dependency_overrides.clear()


def test_permission_dependency_allows_owner_product_create() -> None:
    app = _build_protected_app()
    owner = _user(UserRole.OWNER)

    async def _current_user():
        return owner

    from app.dependencies import auth as auth_deps

    app.dependency_overrides[auth_deps.get_current_user] = _current_user
    app.dependency_overrides[auth_deps.get_verified_user] = _current_user

    with TestClient(app) as client:
        response = client.get("/__test/product-create")
        assert response.status_code == 200
    app.dependency_overrides.clear()


def test_unauthenticated_owner_route_returns_401() -> None:
    app = _build_protected_app()
    with TestClient(app) as client:
        response = client.get("/__test/owner-only")
        assert response.status_code == 401
