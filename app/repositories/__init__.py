"""Repository layer for domain aggregates."""

from app.repositories.address import AddressRepository
from app.repositories.base import BaseRepository
from app.repositories.cart import CartItemExtraRepository, CartItemRepository, CartRepository
from app.repositories.category import CategoryRepository
from app.repositories.coupon import CouponRepository, CouponUsageRepository
from app.repositories.deal import DealProductRepository, DealRepository
from app.repositories.email_log import EmailLogRepository
from app.repositories.extra import ExtraOptionRepository, ProductOptionRepository
from app.repositories.image import ProductImageRepository
from app.repositories.notification import NotificationRepository
from app.repositories.order import (
    OrderNumberSequenceRepository,
    OrderRepository,
    OrderTimelineRepository,
)
from app.repositories.preference import PreferenceRepository
from app.repositories.product import ProductRepository
from app.repositories.redis_auth import RedisAuthRepository
from app.repositories.user import UserRepository
from app.repositories.variant import VariantRepository
from app.repositories.wishlist import WishlistItemRepository, WishlistRepository

__all__ = [
    "AddressRepository",
    "BaseRepository",
    "CartItemExtraRepository",
    "CartItemRepository",
    "CartRepository",
    "CategoryRepository",
    "CouponRepository",
    "CouponUsageRepository",
    "DealProductRepository",
    "DealRepository",
    "EmailLogRepository",
    "ExtraOptionRepository",
    "NotificationRepository",
    "OrderNumberSequenceRepository",
    "OrderRepository",
    "OrderTimelineRepository",
    "PreferenceRepository",
    "ProductImageRepository",
    "ProductOptionRepository",
    "ProductRepository",
    "RedisAuthRepository",
    "UserRepository",
    "VariantRepository",
    "WishlistItemRepository",
    "WishlistRepository",
]
