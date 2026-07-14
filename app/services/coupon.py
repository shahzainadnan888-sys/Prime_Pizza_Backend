"""Coupon validation service (no payment / no usage consumption)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import CouponType
from app.core.exceptions import NotFoundException, ValidationException
from app.models.coupon import Coupon
from app.repositories.coupon import CouponRepository, CouponUsageRepository
from app.schemas.cart import CouponValidationResponse
from app.services.base import BaseService
from app.services.pricing import money


class CouponService(BaseService):
    service_name = "coupon"

    def __init__(self, *, session: AsyncSession) -> None:
        self._session = session
        self._coupons = CouponRepository(session)
        self._usages = CouponUsageRepository(session)

    async def get_active_by_code(self, code: str) -> Coupon:
        coupon = await self._coupons.get_by_code(code.strip().upper())
        if coupon is None:
            raise NotFoundException("Coupon not found")
        return coupon

    def calculate_discount(self, coupon: Coupon, *, subtotal: Decimal) -> Decimal:
        if coupon.coupon_type == CouponType.PERCENTAGE:
            discount = money(subtotal * money(coupon.value) / Decimal("100"))
        else:
            discount = money(coupon.value)
        if coupon.maximum_discount is not None:
            discount = min(discount, money(coupon.maximum_discount))
        return min(discount, subtotal)

    async def validate_for_user(
        self,
        *,
        code: str,
        user_id: UUID,
        subtotal: Decimal,
    ) -> CouponValidationResponse:
        coupon = await self.get_active_by_code(code)
        now = datetime.now(UTC)

        if not coupon.is_active:
            raise ValidationException("Coupon is not active")
        if coupon.starts_at and coupon.starts_at > now:
            raise ValidationException("Coupon is not yet valid")
        if coupon.expires_at and coupon.expires_at < now:
            raise ValidationException("Coupon has expired")
        if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
            raise ValidationException("Coupon usage limit reached")
        if coupon.per_user_limit is not None:
            used = await self._usages.count_for_user(coupon.id, user_id)
            if used >= coupon.per_user_limit:
                raise ValidationException("You have already used this coupon the maximum times")
        if coupon.minimum_order_amount is not None and subtotal < money(coupon.minimum_order_amount):
            raise ValidationException(
                f"Minimum order amount of {coupon.minimum_order_amount} required",
            )

        discount = self.calculate_discount(coupon, subtotal=subtotal)
        return CouponValidationResponse(
            code=coupon.code,
            coupon_type=coupon.coupon_type,
            value=money(coupon.value),
            discount_amount=discount,
            is_valid=True,
            message="Coupon is valid",
        )
