"""Authorization package — RBAC permissions, roles, and ownership."""

from app.authorization.ownership import OwnershipService
from app.authorization.permissions import (
    Permission,
    ProtectedResource,
    permissions_for_role,
)
from app.authorization.policy import AuthorizationService
from app.authorization.roles import RoleAssignmentService, RoleService

__all__ = [
    "AuthorizationService",
    "OwnershipService",
    "Permission",
    "ProtectedResource",
    "RoleAssignmentService",
    "RoleService",
    "permissions_for_role",
]
