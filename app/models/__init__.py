"""ORM models package — import all models for Alembic metadata discovery."""

from app.database.base import Base
from app.models.audit_log import AuditLog
from app.models.base import BaseModel
from app.models.cart import Cart, CartItem, CartItemExtra
from app.models.catalog import (
    Category,
    Product,
    ProductImage,
    ProductOption,
    ProductVariant,
    VariantOption,
)
from app.models.coupon import Coupon, CouponUsage
from app.models.deal import Deal, DealProduct
from app.models.email_log import EmailLog
from app.models.notification import Notification, NotificationPreference, UserPreference
from app.models.order import (
    Order,
    OrderItem,
    OrderItemExtra,
    OrderNumberSequence,
    OrderTimelineEvent,
)
from app.models.otp_log import OTPLog
from app.models.system_setting import SystemSetting
from app.models.user import Address, User
from app.models.wishlist import Wishlist, WishlistItem

__all__ = [
    "Address",
    "AuditLog",
    "Base",
    "BaseModel",
    "Cart",
    "CartItem",
    "CartItemExtra",
    "Category",
    "Coupon",
    "CouponUsage",
    "Deal",
    "DealProduct",
    "EmailLog",
    "Notification",
    "NotificationPreference",
    "OTPLog",
    "Order",
    "OrderItem",
    "OrderItemExtra",
    "OrderNumberSequence",
    "OrderTimelineEvent",
    "Product",
    "ProductImage",
    "ProductOption",
    "ProductVariant",
    "SystemSetting",
    "User",
    "UserPreference",
    "VariantOption",
    "Wishlist",
    "WishlistItem",
]
