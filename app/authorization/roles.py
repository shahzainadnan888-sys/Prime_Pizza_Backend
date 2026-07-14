"""Role resolution and checks."""

from __future__ import annotations

from app.common.enums import UserRole
from app.config.settings import Settings
from app.utils.phone import normalize_phone


class RoleService:
    """Role predicate helpers used by dependencies and policies."""

    @staticmethod
    def normalize(role: str | UserRole) -> UserRole:
        return role if isinstance(role, UserRole) else UserRole(role)

    @staticmethod
    def is_owner(role: str | UserRole) -> bool:
        return RoleService.normalize(role) == UserRole.OWNER

    @staticmethod
    def is_customer(role: str | UserRole) -> bool:
        return RoleService.normalize(role) == UserRole.CUSTOMER

    @staticmethod
    def is_staff_like(role: str | UserRole) -> bool:
        """Prepared for future manager/staff/support roles."""
        value = str(role)
        return value in {"owner", "manager", "staff", "support"}


class RoleAssignmentService:
    """
    Assign roles at authentication time.

    Owner is identified solely by OWNER_PHONE_NUMBER from settings/.env.
    """

    def __init__(self, settings: Settings) -> None:
        self._owner_phone = normalize_phone(settings.owner_phone_number)

    @property
    def owner_phone_number(self) -> str:
        return self._owner_phone

    def resolve_role(self, phone_number: str) -> UserRole:
        phone = normalize_phone(phone_number)
        if phone == self._owner_phone:
            return UserRole.OWNER
        return UserRole.CUSTOMER

    def is_owner_phone(self, phone_number: str) -> bool:
        return normalize_phone(phone_number) == self._owner_phone
