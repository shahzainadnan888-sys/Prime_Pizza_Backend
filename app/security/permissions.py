"""Permission helpers — re-export canonical authorization catalog."""

from app.authorization.permissions import (
    Permission,
    ProtectedResource,
    has_permission,
    permissions_for_role,
)
from app.authorization.policy import AuthorizationService

__all__ = [
    "AuthorizationService",
    "Permission",
    "ProtectedResource",
    "has_permission",
    "permissions_for_role",
]
