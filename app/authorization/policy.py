"""Central authorization policy evaluator."""

from __future__ import annotations

from uuid import UUID

from loguru import logger

from app.authorization.ownership import OwnershipService
from app.authorization.permissions import Permission, has_permission, permissions_for_role
from app.authorization.roles import RoleService
from app.core.exceptions import ForbiddenException
from app.models.user import User
from app.services.base import BaseService


class AuthorizationService(BaseService):
    """
    Single place for role / permission / ownership decisions.

    Dependencies call into this service so route handlers never duplicate checks.
    """

    service_name = "authorization"

    def __init__(self, ownership: OwnershipService | None = None) -> None:
        self._ownership = ownership or OwnershipService()

    def permissions_for(self, user: User) -> frozenset[Permission]:
        return permissions_for_role(user.role)

    def require_role(self, user: User, *roles: str) -> User:
        current = str(user.role.value if hasattr(user.role, "value") else user.role)
        allowed = {str(role) for role in roles}
        # Accept legacy "owner" token as chef
        if current == "chef":
            allowed = allowed | {"chef"} if "owner" in allowed or "chef" in allowed else allowed
        if "owner" in allowed:
            allowed.add("chef")
        if current not in allowed and not (current == "chef" and "owner" in allowed):
            logger.warning(
                "Forbidden role | user_id={} | role={} | required={}",
                user.id,
                current,
                sorted(allowed),
            )
            raise ForbiddenException("Insufficient role privileges")
        return user

    def require_chef(self, user: User) -> User:
        if not RoleService.is_chef(user.role):
            logger.warning("Chef-only access denied | user_id={} | role={}", user.id, user.role)
            raise ForbiddenException("Chef access required")
        logger.info("Chef access | user_id={}", user.id)
        return user

    def require_owner(self, user: User) -> User:
        """Backward-compatible alias for require_chef."""
        return self.require_chef(user)

    def require_customer(self, user: User) -> User:
        if not RoleService.is_customer(user.role):
            logger.warning("Customer access denied | user_id={} | role={}", user.id, user.role)
            raise ForbiddenException("Customer access required")
        return user

    def require_permission(self, user: User, *permissions: Permission | str) -> User:
        missing = [
            str(permission)
            for permission in permissions
            if not has_permission(user.role, permission)
        ]
        if missing:
            logger.warning(
                "Permission failure | user_id={} | role={} | missing={}",
                user.id,
                user.role,
                missing,
            )
            raise ForbiddenException(
                "Insufficient permissions",
                details={"missing_permissions": missing},
            )
        return user

    def require_any_permission(self, user: User, *permissions: Permission | str) -> User:
        if any(has_permission(user.role, permission) for permission in permissions):
            return user
        logger.warning(
            "Permission failure (any) | user_id={} | role={} | required_any={}",
            user.id,
            user.role,
            [str(p) for p in permissions],
        )
        raise ForbiddenException("Insufficient permissions")

    def require_ownership(
        self,
        user: User,
        resource_owner_id: UUID | None,
        *,
        resource_name: str = "resource",
    ) -> User:
        self._ownership.ensure_owner_or_self(
            user,
            resource_owner_id,
            resource_name=resource_name,
        )
        return user
