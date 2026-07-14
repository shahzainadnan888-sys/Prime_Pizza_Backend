"""Order summary preparation (pre-order)."""

from __future__ import annotations

from app.config.settings import Settings
from app.models.cart import Cart
from app.schemas.cart import (
    CartItemExtraResponse,
    OrderSummaryLineResponse,
    OrderSummaryResponse,
)
from app.services.base import BaseService


class OrderSummaryService(BaseService):
    service_name = "order_summary"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def build(self, cart: Cart) -> OrderSummaryResponse:
        lines: list[OrderSummaryLineResponse] = []
        prep_times: list[int] = []
        for item in cart.items:
            if item.deleted_at is not None:
                continue
            product = item.product
            variant = item.variant
            extras = [
                CartItemExtraResponse(
                    option_id=extra.option_id,
                    name=extra.option.name if extra.option else None,
                    quantity=extra.quantity,
                    unit_price=extra.unit_price,
                )
                for extra in item.extras
                if extra.deleted_at is None
            ]
            prep = None
            if variant and variant.preparation_time_minutes is not None:
                prep = variant.preparation_time_minutes
            elif product and product.preparation_time_minutes is not None:
                prep = product.preparation_time_minutes
            if prep is not None:
                prep_times.append(prep * item.quantity)

            lines.append(
                OrderSummaryLineResponse(
                    product_id=item.product_id,
                    product_name=product.name if product else "Product",
                    variant_name=variant.name if variant else None,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    discount_price=item.discount_price,
                    extras=extras,
                    line_total=item.subtotal,
                    preparation_time_minutes=prep,
                )
            )

        estimated_prep = self._settings.estimated_prep_buffer_minutes
        if prep_times:
            estimated_prep = max(prep_times) + self._settings.estimated_prep_buffer_minutes
        return OrderSummaryResponse(
            currency=cart.currency,
            products=lines,
            subtotal=cart.subtotal,
            discount=cart.discount,
            tax=cart.tax,
            delivery_fee=cart.delivery_fee,
            grand_total=cart.grand_total,
            coupon_code=cart.coupon.code if cart.coupon else None,
            estimated_preparation_time_minutes=estimated_prep,
            estimated_delivery_time_minutes=self._settings.estimated_delivery_minutes,
            item_count=sum(item.quantity for item in cart.items if item.deleted_at is None),
        )
