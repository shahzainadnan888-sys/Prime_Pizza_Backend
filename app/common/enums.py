"""Shared enumerations."""

from __future__ import annotations

from enum import StrEnum


class AppEnvironment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class UserRole(StrEnum):
    CUSTOMER = "customer"
    CHEF = "chef"


class OrderStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(StrEnum):
    CASH_ON_DELIVERY = "cash_on_delivery"
    CARD = "card"
    ONLINE = "online"
    WALLET = "wallet"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    CANCELLED = "cancelled"


class CouponType(StrEnum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class CartStatus(StrEnum):
    ACTIVE = "active"
    CHECKOUT_READY = "checkout_ready"
    ABANDONED = "abandoned"
    CONVERTED = "converted"


class NotificationType(StrEnum):
    ORDER = "order"
    PROMO = "promo"
    SYSTEM = "system"
    ACCOUNT = "account"


class DealType(StrEnum):
    COMBO = "combo"
    FAMILY = "family"
    LIMITED = "limited"
    TIME_BASED = "time_based"
    WEEKEND = "weekend"
    FESTIVAL = "festival"


class VariantSize(StrEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    FAMILY = "family"
    CUSTOM = "custom"


class VariantOptionType(StrEnum):
    TOPPING = "topping"
    SAUCE = "sauce"
    CRUST = "crust"
    EXTRA = "extra"
    OTHER = "other"


class StockStatus(StrEnum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    LIMITED = "limited"


class ProductTag(StrEnum):
    POPULAR = "popular"
    FEATURED = "featured"
    NEW = "new"
    LIMITED = "limited"
    SPICY = "spicy"
    VEGETARIAN = "vegetarian"
    BEST_SELLER = "best_seller"
    CHEF_SPECIAL = "chef_special"
    KIDS_FAVORITE = "kids_favorite"


class ProductSort(StrEnum):
    NEWEST = "newest"
    OLDEST = "oldest"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    POPULARITY = "popularity"
    ALPHABETICAL = "alphabetical"
    PREPARATION_TIME = "preparation_time"


class AuditAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    VIEW = "view"
    OTHER = "other"


class EmailDeliveryStatus(StrEnum):
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


class EmailTemplateKey(StrEnum):
    """Transactional template keys — marketing keys intentionally omitted."""

    WELCOME = "welcome"
    ORDER_NOTIFICATION = "order_notification"
    CONTACT_NOTIFICATION = "contact_notification"
    CONTACT_CONFIRMATION = "contact_confirmation"
    ADMIN_TEST = "admin_test"
    # Legacy keys retained for existing email_logs rows
    OWNER_NEW_ORDER = "owner_new_order"
    OWNER_TEST = "owner_test"
    ORDER_CONFIRMATION = "order_confirmation"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_DELIVERED = "order_delivered"
