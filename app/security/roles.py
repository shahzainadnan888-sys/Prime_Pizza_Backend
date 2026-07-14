"""Role service — re-export canonical authorization RoleService."""

from app.authorization.roles import RoleAssignmentService, RoleService

__all__ = ["RoleAssignmentService", "RoleService"]
