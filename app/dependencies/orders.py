"""FastAPI dependencies for order management."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.dependencies.admin import get_dashboard_cache
from app.dependencies.cart import (
    get_cart_cache,
    get_cart_service,
    get_checkout_validation_service,
    get_coupon_service,
    get_order_summary_service,
)
from app.dependencies.database import get_db_session
from app.dependencies.email import get_email_service
from app.dependencies.redis import get_cache_service
from app.dependencies.settings import get_app_settings
from app.integrations.redis.cache import CacheService
from app.services.cart import CartService
from app.services.cart_cache import CartCacheService
from app.services.checkout import CheckoutValidationService
from app.services.coupon import CouponService
from app.services.dashboard_cache import DashboardCacheService
from app.services.email import EmailService
from app.services.order import OrderService
from app.services.order_cache import OrderCacheService
from app.services.order_summary import OrderSummaryService


def get_order_cache(
    cache: CacheService = Depends(get_cache_service),
    settings: Settings = Depends(get_app_settings),
) -> OrderCacheService:
    return OrderCacheService(cache, settings)


def get_order_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
    cart_service: CartService = Depends(get_cart_service),
    checkout_validation: CheckoutValidationService = Depends(get_checkout_validation_service),
    coupon_service: CouponService = Depends(get_coupon_service),
    summary_service: OrderSummaryService = Depends(get_order_summary_service),
    order_cache: OrderCacheService = Depends(get_order_cache),
    cart_cache: CartCacheService = Depends(get_cart_cache),
    email_service: EmailService = Depends(get_email_service),
    dashboard_cache: DashboardCacheService = Depends(get_dashboard_cache),
) -> OrderService:
    return OrderService(
        session=session,
        settings=settings,
        cart_service=cart_service,
        checkout_validation=checkout_validation,
        coupon_service=coupon_service,
        summary_service=summary_service,
        order_cache=order_cache,
        cart_cache=cart_cache,
        email_service=email_service,
        dashboard_cache=dashboard_cache,
    )
