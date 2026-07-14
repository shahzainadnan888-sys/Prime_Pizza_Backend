"""Unit tests for pricing, delivery, tax, and coupons."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from app.common.enums import CouponType, StockStatus, VariantSize
from app.config.settings import get_settings
from app.core.exceptions import ValidationException
from app.models.catalog import Product, ProductVariant, VariantOption
from app.models.coupon import Coupon
from app.services.coupon import CouponService
from app.services.delivery import DeliveryService
from app.services.pricing import PricingService, money
from app.services.tax import TaxService


def test_pricing_uses_variant_discount() -> None:
    pricing = PricingService()
    product = Product(
        id=uuid4(),
        category_id=uuid4(),
        name="Pizza",
        slug="pizza",
        base_price=Decimal("1000"),
        discount_price=Decimal("900"),
        is_available=True,
        is_visible=True,
        stock_status=StockStatus.IN_STOCK,
        tags=[],
    )
    variant = ProductVariant(
        id=uuid4(),
        product_id=product.id,
        size=VariantSize.LARGE,
        name="Large",
        price=Decimal("1200"),
        discount_price=Decimal("1100"),
        is_available=True,
    )
    extra = VariantOption(
        id=uuid4(),
        name="Extra Cheese",
        slug="extra-cheese",
        price=Decimal("100"),
        is_available=True,
    )
    line = pricing.price_line(
        product=product,
        variant=variant,
        quantity=2,
        extras=[(extra, 1)],
    )
    assert line.effective_unit_price == Decimal("1100.00")
    assert line.line_subtotal == Decimal("2400.00")


def test_delivery_free_threshold() -> None:
    settings = get_settings()
    delivery = DeliveryService(settings)
    fee = delivery.calculate_fee(subtotal_after_discount=money(settings.free_delivery_threshold))
    assert fee == Decimal("0.00")
    fee2 = delivery.calculate_fee(subtotal_after_discount=Decimal("100.00"))
    assert fee2 == money(settings.delivery_fee_flat)


def test_tax_calculation() -> None:
    settings = get_settings()
    tax = TaxService(settings)
    expected = money(Decimal("1000") * Decimal(str(settings.tax_rate_percent)) / Decimal("100"))
    assert tax.calculate(taxable_amount=Decimal("1000")) == expected


def test_coupon_discount_percentage_with_cap() -> None:
    service = CouponService.__new__(CouponService)
    coupon = Coupon(
        id=uuid4(),
        code="SAVE20",
        coupon_type=CouponType.PERCENTAGE,
        value=Decimal("20"),
        maximum_discount=Decimal("50"),
        is_active=True,
        used_count=0,
    )
    discount = CouponService.calculate_discount(service, coupon, subtotal=Decimal("1000"))
    assert discount == Decimal("50.00")


@pytest.mark.asyncio
async def test_coupon_expired_raises() -> None:
    class _Repo:
        async def get_by_code(self, code: str):
            return Coupon(
                id=uuid4(),
                code="OLD",
                coupon_type=CouponType.FIXED,
                value=Decimal("100"),
                is_active=True,
                used_count=0,
                expires_at=datetime.now(UTC) - timedelta(days=1),
            )

    class _Usage:
        async def count_for_user(self, coupon_id, user_id):
            return 0

    service = CouponService.__new__(CouponService)
    service._coupons = _Repo()
    service._usages = _Usage()

    with pytest.raises(ValidationException):
        await service.validate_for_user(code="OLD", user_id=uuid4(), subtotal=Decimal("500"))
