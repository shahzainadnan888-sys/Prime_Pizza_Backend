"""Role resolution and checks."""

from __future__ import annotations

from app.common.enums import UserRole
from app.config.settings import Settings


class RoleService:
    """Role predicate helpers used by dependencies and policies."""

    @staticmethod
    def normalize(role: str | UserRole) -> UserRole:
        if isinstance(role, UserRole):
            return role
        # Legacy DB / JWT values from the former owner role
        if role == "owner":
            return UserRole.CHEF
        return UserRole(role)

    @staticmethod
    def is_chef(role: str | UserRole) -> bool:
        return RoleService.normalize(role) == UserRole.CHEF

    @staticmethod
    def is_owner(role: str | UserRole) -> bool:
        """Backward-compatible alias — owner role was replaced by chef."""
        return RoleService.is_chef(role)

    @staticmethod
    def is_customer(role: str | UserRole) -> bool:
        return RoleService.normalize(role) == UserRole.CUSTOMER

    @staticmethod
    def is_staff_like(role: str | UserRole) -> bool:
        value = str(RoleService.normalize(role).value)
        return value in {"chef", "owner"}


class RoleAssignmentService:
    """
    Assign roles at authentication time.

    Register always creates customers. The chef account is bootstrapped at startup.
    """

    def __init__(self, settings: Settings) -> None:
        self._chef_email = str(settings.chef_email).strip().lower()

    @property
    def chef_email(self) -> str:
        return self._chef_email

    def resolve_role(self, email: str) -> UserRole:
        if email.strip().lower() == self._chef_email:
            return UserRole.CHEF
        return UserRole.CUSTOMER

    def is_chef_email(self, email: str) -> bool:
        return email.strip().lower() == self._chef_email
