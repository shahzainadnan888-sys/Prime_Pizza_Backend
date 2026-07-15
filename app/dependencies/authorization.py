"""Reusable authorization FastAPI dependencies."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from fastapi import Depends

from app.authorization.permissions import Permission
from app.authorization.policy import AuthorizationService
from app.dependencies.auth import get_current_user, get_verified_user
from app.models.user import User


def get_authorization_service() -> AuthorizationService:
    return AuthorizationService()


async def require_authenticated(user: User = Depends(get_current_user)) -> User:
    """Any valid authenticated principal."""
    return user


async def require_verified(user: User = Depends(get_verified_user)) -> User:
    """Authenticated + phone-verified user."""
    return user


async def require_customer(
    user: User = Depends(get_verified_user),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> User:
    """Customer storefront access (owners allowed for shopping flows)."""
    return authz.require_customer(user)


async def require_owner(
    user: User = Depends(get_verified_user),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> User:
    """Chef-only access (legacy owner name)."""
    return authz.require_owner(user)


async def require_chef(
    user: User = Depends(get_verified_user),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> User:
    """Kitchen chef only — customers receive HTTP 403 Forbidden."""
    return authz.require_chef(user)


def require_permission(*permissions: Permission | str) -> Callable[..., User]:
    """
    Dependency factory requiring ALL listed permissions.

    Example:
        user: User = Depends(require_permission(Permission.PRODUCT_CREATE))
    """

    async def _dependency(
        user: User = Depends(get_verified_user),
        authz: AuthorizationService = Depends(get_authorization_service),
    ) -> User:
        return authz.require_permission(user, *permissions)

    _dependency.__name__ = f"require_permission_{'_'.join(str(p) for p in permissions)}"
    return _dependency


def require_any_permission(*permissions: Permission | str) -> Callable[..., User]:
    """Dependency factory requiring at least one listed permission."""

    async def _dependency(
        user: User = Depends(get_verified_user),
        authz: AuthorizationService = Depends(get_authorization_service),
    ) -> User:
        return authz.require_any_permission(user, *permissions)

    _dependency.__name__ = f"require_any_permission_{'_'.join(str(p) for p in permissions)}"
    return _dependency


async def require_self_or_owner(
    user_id: UUID,
    user: User = Depends(get_verified_user),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> User:
    """
    Path `{user_id}` must match the caller unless the caller is the platform owner.

    Use on routes like `GET /users/{user_id}/profile`.
    """
    return authz.require_ownership(user, user_id, resource_name="user")


def ensure_resource_owner(
    user: User,
    resource_owner_id: UUID | None,
    *,
    resource_name: str = "resource",
    authz: AuthorizationService | None = None,
) -> None:
    """Service/endpoint helper after a resource has been loaded."""
    service = authz or AuthorizationService()
    service.require_ownership(user, resource_owner_id, resource_name=resource_name)
