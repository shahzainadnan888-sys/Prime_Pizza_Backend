"""Pricing helpers — all amounts derived from catalog DB values."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.models.catalog import Product, ProductVariant, VariantOption
from app.services.base import BaseService

TWOPLACES = Decimal("0.01")


def money(value: Decimal | int | float | str) -> Decimal:
    return Decimal(value).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class LinePrice:
    unit_price: Decimal
    discount_price: Decimal | None
    effective_unit_price: Decimal
    extras_unit_total: Decimal
    line_subtotal: Decimal


class PricingService(BaseService):
    """Compute cart line and cart totals from authoritative catalog prices."""

    service_name = "pricing"

    def effective_product_unit_price(
        self,
        product: Product,
        variant: ProductVariant | None,
    ) -> tuple[Decimal, Decimal | None]:
        if variant is not None:
            unit = money(variant.price)
            discount = money(variant.discount_price) if variant.discount_price is not None else None
            if discount is None and product.discount_price is not None and variant.size:
                # Prefer variant discount; fall back only when variant has none.
                pass
            return unit, discount

        unit = money(product.base_price)
        discount = money(product.discount_price) if product.discount_price is not None else None
        return unit, discount

    def price_line(
        self,
        *,
        product: Product,
        variant: ProductVariant | None,
        quantity: int,
        extras: list[tuple[VariantOption, int]],
    ) -> LinePrice:
        unit_price, discount_price = self.effective_product_unit_price(product, variant)
        effective = discount_price if discount_price is not None else unit_price
        extras_total = money(sum((money(option.price) * qty for option, qty in extras), Decimal("0")))
        line_subtotal = money((effective + extras_total) * quantity)
        return LinePrice(
            unit_price=unit_price,
            discount_price=discount_price,
            effective_unit_price=effective,
            extras_unit_total=extras_total,
            line_subtotal=line_subtotal,
        )

    def cart_subtotal(self, line_subtotals: list[Decimal]) -> Decimal:
        return money(sum(line_subtotals, Decimal("0")))
