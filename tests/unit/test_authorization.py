"""Authorization / RBAC unit tests."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.authorization.ownership import OwnershipService
from app.authorization.permissions import Permission, has_permission, permissions_for_role
from app.authorization.policy import AuthorizationService
from app.authorization.roles import RoleAssignmentService, RoleService
from app.common.enums import UserRole
from app.config.settings import get_settings
from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.user import User


def _user(*, role: UserRole, email: str = "user@example.com") -> User:
    return User(
        id=uuid4(),
        first_name="Test",
        last_name="User",
        phone_number=None,
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


def test_chef_email_resolves_to_chef_role() -> None:
    settings = get_settings()
    service = RoleAssignmentService(settings)
    assert service.resolve_role(settings.chef_email) == UserRole.CHEF
    assert service.resolve_role("customer@example.com") == UserRole.CUSTOMER


def test_customer_permissions_do_not_include_admin() -> None:
    perms = permissions_for_role(UserRole.CUSTOMER)
    assert Permission.PRODUCT_READ in perms
    assert Permission.CART_MANAGE_OWN in perms
    assert Permission.PRODUCT_CREATE not in perms
    assert Permission.DASHBOARD_READ not in perms
    assert Permission.KITCHEN_MANAGE not in perms
    assert Permission.ALL not in perms


def test_chef_has_wildcard_and_kitchen_permissions() -> None:
    assert has_permission(UserRole.CHEF, Permission.PRODUCT_DELETE)
    assert has_permission(UserRole.CHEF, Permission.DASHBOARD_READ)
    assert has_permission(UserRole.CHEF, Permission.KITCHEN_MANAGE)
    assert has_permission(UserRole.CHEF, Permission.ALL)
    assert has_permission(UserRole.CHEF, "analytics.read")


def test_require_chef_blocks_customer() -> None:
    authz = AuthorizationService()
    customer = _user(role=UserRole.CUSTOMER)
    with pytest.raises(ForbiddenException):
        authz.require_chef(customer)


def test_require_chef_allows_chef() -> None:
    authz = AuthorizationService()
    chef = _user(role=UserRole.CHEF)
    assert authz.require_chef(chef) is chef


def test_require_customer_blocks_chef() -> None:
    authz = AuthorizationService()
    chef = _user(role=UserRole.CHEF)
    with pytest.raises(ForbiddenException):
        authz.require_customer(chef)


def test_require_permission_blocks_customer_admin_action() -> None:
    authz = AuthorizationService()
    customer = _user(role=UserRole.CUSTOMER)
    with pytest.raises(ForbiddenException) as exc:
        authz.require_permission(customer, Permission.PRODUCT_CREATE)
    assert exc.value.status_code == 403


def test_ownership_allows_self() -> None:
    ownership = OwnershipService()
    customer = _user(role=UserRole.CUSTOMER)
    ownership.ensure_owner_or_self(customer, customer.id, resource_name="order")


def test_ownership_hides_foreign_resource_from_customer() -> None:
    ownership = OwnershipService()
    customer = _user(role=UserRole.CUSTOMER)
    with pytest.raises(NotFoundException):
        ownership.ensure_owner_or_self(customer, uuid4(), resource_name="order")


def test_ownership_chef_bypasses() -> None:
    ownership = OwnershipService()
    chef = _user(role=UserRole.CHEF)
    ownership.ensure_owner_or_self(chef, uuid4(), resource_name="order")


def test_role_service_predicates() -> None:
    assert RoleService.is_chef(UserRole.CHEF)
    assert RoleService.is_owner(UserRole.CHEF)  # alias
    assert RoleService.is_customer("customer")
    assert not RoleService.is_chef(UserRole.CUSTOMER)


def test_privilege_escalation_customer_cannot_gain_chef_permission() -> None:
    """Customers must not satisfy chef-only permission checks."""
    assert not has_permission(UserRole.CUSTOMER, Permission.SETTINGS_UPDATE)
    assert not has_permission(UserRole.CUSTOMER, Permission.CUSTOMER_READ)
    assert not has_permission(UserRole.CUSTOMER, Permission.AUDIT_LOG_READ)
    assert not has_permission(UserRole.CUSTOMER, Permission.KITCHEN_MANAGE)
