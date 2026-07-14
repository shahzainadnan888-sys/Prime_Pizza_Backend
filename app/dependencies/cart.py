"""FastAPI dependencies for cart, wishlist, and checkout preparation."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.dependencies.database import get_db_session
from app.dependencies.redis import get_cache_service
from app.dependencies.settings import get_app_settings
from app.integrations.redis.cache import CacheService
from app.services.cart import CartService
from app.services.cart_cache import CartCacheService
from app.services.checkout import CheckoutValidationService
from app.services.commerce_config import CommerceConfigService
from app.services.coupon import CouponService
from app.services.delivery import DeliveryService
from app.services.order_summary import OrderSummaryService
from app.services.pricing import PricingService
from app.services.tax import TaxService
from app.services.wishlist import WishlistService


def get_cart_cache(
    cache: CacheService = Depends(get_cache_service),
    settings: Settings = Depends(get_app_settings),
) -> CartCacheService:
    return CartCacheService(cache, settings)


def get_pricing_service() -> PricingService:
    return PricingService()


def get_delivery_service(settings: Settings = Depends(get_app_settings)) -> DeliveryService:
    return DeliveryService(settings)


def get_tax_service(settings: Settings = Depends(get_app_settings)) -> TaxService:
    return TaxService(settings)


def get_commerce_config_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
    cache: CacheService = Depends(get_cache_service),
) -> CommerceConfigService:
    return CommerceConfigService(session=session, settings=settings, cache=cache)


def get_coupon_service(session: AsyncSession = Depends(get_db_session)) -> CouponService:
    return CouponService(session=session)


def get_order_summary_service(
    settings: Settings = Depends(get_app_settings),
) -> OrderSummaryService:
    return OrderSummaryService(settings)


def get_cart_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
    cache: CartCacheService = Depends(get_cart_cache),
    pricing: PricingService = Depends(get_pricing_service),
    delivery: DeliveryService = Depends(get_delivery_service),
    tax: TaxService = Depends(get_tax_service),
    coupon: CouponService = Depends(get_coupon_service),
    summary: OrderSummaryService = Depends(get_order_summary_service),
    commerce: CommerceConfigService = Depends(get_commerce_config_service),
) -> CartService:
    return CartService(
        session=session,
        settings=settings,
        cache=cache,
        pricing=pricing,
        delivery=delivery,
        tax=tax,
        coupon=coupon,
        summary=summary,
        commerce=commerce,
    )


def get_wishlist_service(
    session: AsyncSession = Depends(get_db_session),
) -> WishlistService:
    return WishlistService(session=session)


def get_checkout_validation_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
    cart_service: CartService = Depends(get_cart_service),
    summary: OrderSummaryService = Depends(get_order_summary_service),
    cache: CartCacheService = Depends(get_cart_cache),
) -> CheckoutValidationService:
    return CheckoutValidationService(
        session=session,
        settings=settings,
        cart_service=cart_service,
        summary=summary,
        cache=cache,
    )
