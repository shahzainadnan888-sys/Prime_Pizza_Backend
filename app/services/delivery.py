"""Delivery fee preparation service."""

from __future__ import annotations

from decimal import Decimal

from app.config.settings import Settings
from app.services.base import BaseService
from app.services.commerce_config import CommerceConfig
from app.services.pricing import money


class DeliveryService(BaseService):
    """Flat fee + free-delivery threshold (distance-based pricing prepared later)."""

    service_name = "delivery"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def calculate_fee(
        self,
        *,
        subtotal_after_discount: Decimal,
        commerce: CommerceConfig | None = None,
    ) -> Decimal:
        if commerce is not None:
            threshold = commerce.free_delivery_threshold
            flat = commerce.delivery_fee
        else:
            threshold = money(self._settings.free_delivery_threshold)
            flat = money(self._settings.delivery_fee_flat)
        if threshold > 0 and subtotal_after_discount >= threshold:
            return money(0)
        return flat
