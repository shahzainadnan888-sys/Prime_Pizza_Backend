"""Permission catalog and role → permission matrix (RBAC)."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from app.common.enums import UserRole


class ProtectedResource(StrEnum):
    """Logical resources protected by the authorization layer."""

    PRODUCT = "product"
    CATEGORY = "category"
    DEAL = "deal"
    COUPON = "coupon"
    ORDER = "order"
    CUSTOMER = "customer"
    CART = "cart"
    WISHLIST = "wishlist"
    ADDRESS = "address"
    PROFILE = "profile"
    NOTIFICATION = "notification"
    IMAGE = "image"
    DASHBOARD = "dashboard"
    ANALYTICS = "analytics"
    SETTINGS = "settings"
    AUDIT_LOG = "audit_log"


class Permission(StrEnum):
    """
    Fine-grained permissions.

    Naming: `{resource}.{action}` — extend freely for future roles.
    """

    # Catalog / customer browse
    PRODUCT_READ = "product.read"
    PRODUCT_CREATE = "product.create"
    PRODUCT_UPDATE = "product.update"
    PRODUCT_DELETE = "product.delete"

    CATEGORY_READ = "category.read"
    CATEGORY_CREATE = "category.create"
    CATEGORY_UPDATE = "category.update"
    CATEGORY_DELETE = "category.delete"

    DEAL_READ = "deal.read"
    DEAL_CREATE = "deal.create"
    DEAL_UPDATE = "deal.update"
    DEAL_DELETE = "deal.delete"

    COUPON_READ = "coupon.read"
    COUPON_CREATE = "coupon.create"
    COUPON_UPDATE = "coupon.update"
    COUPON_DELETE = "coupon.delete"

    # Orders
    ORDER_READ_OWN = "order.read_own"
    ORDER_READ = "order.read"
    ORDER_CREATE = "order.create"
    ORDER_UPDATE = "order.update"
    ORDER_DELETE = "order.delete"
    ORDER_TRACK_OWN = "order.track_own"

    # Customers (admin)
    CUSTOMER_READ = "customer.read"
    CUSTOMER_UPDATE = "customer.update"

    # Self-service
    PROFILE_READ_OWN = "profile.read_own"
    PROFILE_UPDATE_OWN = "profile.update_own"
    ADDRESS_MANAGE_OWN = "address.manage_own"
    CART_MANAGE_OWN = "cart.manage_own"
    WISHLIST_MANAGE_OWN = "wishlist.manage_own"
    NOTIFICATION_READ_OWN = "notification.read_own"
    SETTINGS_UPDATE_OWN = "settings.update_own"

    # Media / ops
    IMAGE_UPLOAD = "image.upload"
    IMAGE_MANAGE = "image.manage"
    NOTIFICATION_MANAGE = "notification.manage"
    EMAIL_TEST = "email.test"

    # Owner console
    DASHBOARD_READ = "dashboard.read"
    ANALYTICS_READ = "analytics.read"
    SETTINGS_UPDATE = "settings.update"
    SETTINGS_READ = "settings.read"
    AUDIT_LOG_READ = "audit_log.read"

    # Super-capability (owner)
    ALL = "*"


# Customer baseline — self-service + catalog browse / checkout
_CUSTOMER_PERMISSIONS: frozenset[Permission] = frozenset(
    {
        Permission.PRODUCT_READ,
        Permission.CATEGORY_READ,
        Permission.DEAL_READ,
        Permission.COUPON_READ,
        Permission.CART_MANAGE_OWN,
        Permission.WISHLIST_MANAGE_OWN,
        Permission.ORDER_CREATE,
        Permission.ORDER_READ_OWN,
        Permission.ORDER_TRACK_OWN,
        Permission.PROFILE_READ_OWN,
        Permission.PROFILE_UPDATE_OWN,
        Permission.ADDRESS_MANAGE_OWN,
        Permission.NOTIFICATION_READ_OWN,
        Permission.SETTINGS_UPDATE_OWN,
    }
)

# Owner = customer capabilities + full administrative surface
_OWNER_PERMISSIONS: frozenset[Permission] = frozenset(
    {
        *_CUSTOMER_PERMISSIONS,
        Permission.PRODUCT_CREATE,
        Permission.PRODUCT_UPDATE,
        Permission.PRODUCT_DELETE,
        Permission.CATEGORY_CREATE,
        Permission.CATEGORY_UPDATE,
        Permission.CATEGORY_DELETE,
        Permission.DEAL_CREATE,
        Permission.DEAL_UPDATE,
        Permission.DEAL_DELETE,
        Permission.COUPON_CREATE,
        Permission.COUPON_UPDATE,
        Permission.COUPON_DELETE,
        Permission.ORDER_READ,
        Permission.ORDER_UPDATE,
        Permission.ORDER_DELETE,
        Permission.CUSTOMER_READ,
        Permission.CUSTOMER_UPDATE,
        Permission.NOTIFICATION_MANAGE,
        Permission.EMAIL_TEST,
        Permission.IMAGE_UPLOAD,
        Permission.IMAGE_MANAGE,
        Permission.DASHBOARD_READ,
        Permission.ANALYTICS_READ,
        Permission.SETTINGS_UPDATE,
        Permission.SETTINGS_READ,
        Permission.AUDIT_LOG_READ,
        Permission.ALL,
    }
)

# Future role stubs — add permissions here without touching dependency code.
_FUTURE_ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    # "manager": frozenset({...}),
    # "staff": frozenset({...}),
    # "delivery": frozenset({...}),
    # "support": frozenset({...}),
}


@lru_cache
def _role_matrix() -> dict[UserRole, frozenset[Permission]]:
    return {
        UserRole.CUSTOMER: _CUSTOMER_PERMISSIONS,
        UserRole.OWNER: _OWNER_PERMISSIONS,
    }


def permissions_for_role(role: UserRole | str) -> frozenset[Permission]:
    """Resolve the permission set for a role (DB roles + future stubs)."""
    if isinstance(role, str):
        future = _FUTURE_ROLE_PERMISSIONS.get(role)
        if future is not None:
            return future
        role = UserRole(role)
    return _role_matrix().get(role, frozenset())


def has_permission(role: UserRole | str, permission: Permission | str) -> bool:
    """Return True when the role grants the permission (or wildcard ALL)."""
    granted = permissions_for_role(role)
    if Permission.ALL in granted:
        return True
    target = Permission(permission) if isinstance(permission, str) else permission
    return target in granted
