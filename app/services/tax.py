"""Tax calculation preparation service."""

from __future__ import annotations

from decimal import Decimal

from app.config.settings import Settings
from app.services.base import BaseService
from app.services.commerce_config import CommerceConfig
from app.services.pricing import money


class TaxService(BaseService):
    """Flat percentage tax (regional VAT/GST rules prepared for later)."""

    service_name = "tax"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def calculate(
        self,
        *,
        taxable_amount: Decimal,
        commerce: CommerceConfig | None = None,
    ) -> Decimal:
        rate = (
            commerce.tax_percent
            if commerce is not None
            else Decimal(str(self._settings.tax_rate_percent))
        )
        if rate <= 0 or taxable_amount <= 0:
            return money(0)
        return money(taxable_amount * rate / Decimal("100"))
