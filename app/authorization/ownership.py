"""Resource ownership validation (horizontal privilege prevention)."""

from __future__ import annotations

from uuid import UUID

from loguru import logger

from app.authorization.roles import RoleService
from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.user import User


class OwnershipService:
    """
    Validate that a customer may only access their own resources.

    Owner role bypasses ownership checks (vertical privilege by design).
    """

    def ensure_owner_or_self(
        self,
        actor: User,
        resource_owner_id: UUID | None,
        *,
        resource_name: str = "resource",
        hide_existence: bool = True,
    ) -> None:
        """
        Allow access when actor is platform owner OR owns the resource.

        When `hide_existence` is True, customers get 404 (not 403) for foreign
        resources to avoid leaking existence of other users' data.
        """
        if RoleService.is_owner(actor.role):
            logger.info(
                "Owner access granted | user_id={} | resource={}",
                actor.id,
                resource_name,
            )
            return

        if resource_owner_id is None or actor.id != resource_owner_id:
            logger.warning(
                "Ownership denied | user_id={} | resource={} | target_owner={}",
                actor.id,
                resource_name,
                resource_owner_id,
            )
            if hide_existence:
                raise NotFoundException(f"{resource_name} not found")
            raise ForbiddenException(f"You do not have access to this {resource_name}")

    def is_self(self, actor: User, resource_owner_id: UUID) -> bool:
        return actor.id == resource_owner_id

    def owner_bypasses(self, actor: User) -> bool:
        return RoleService.is_owner(actor.role)
