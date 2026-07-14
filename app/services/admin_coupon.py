"""Owner coupon administration service."""

from __future__ import annotations

from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import AuditAction, CouponType
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.coupon import Coupon
from app.repositories.coupon import CouponRepository, CouponUsageRepository
from app.schemas.admin_coupons import (
    CouponCreateRequest,
    CouponFilterParams,
    CouponResponse,
    CouponUpdateRequest,
    CouponUsageReportResponse,
)
from app.schemas.pagination import PaginationMeta, PaginationParams
from app.services.audit import AuditService
from app.services.base import BaseService
from app.services.dashboard_cache import DashboardCacheService
from app.services.pricing import money


class AdminCouponService(BaseService):
    service_name = "admin_coupon"

    def __init__(
        self,
        *,
        session: AsyncSession,
        audit: AuditService,
        dashboard_cache: DashboardCacheService,
    ) -> None:
        self._session = session
        self._coupons = CouponRepository(session)
        self._usages = CouponUsageRepository(session)
        self._audit = audit
        self._dashboard_cache = dashboard_cache

    async def list_coupons(
        self,
        filters: CouponFilterParams,
        pagination: PaginationParams,
    ) -> tuple[list[CouponResponse], PaginationMeta]:
        rows, total = await self._coupons.list_filtered(
            filters,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        meta = PaginationMeta.from_totals(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total,
        )
        return [CouponResponse.model_validate(row) for row in rows], meta

    async def get_coupon(self, coupon_id: UUID) -> CouponResponse:
        coupon = await self._coupons.get_by_id(coupon_id)
        if coupon is None:
            raise NotFoundException("Coupon not found")
        return CouponResponse.model_validate(coupon)

    async def create(
        self,
        payload: CouponCreateRequest,
        *,
        actor_id: UUID,
    ) -> CouponResponse:
        code = payload.code.strip().upper()
        if await self._coupons.get_by_code(code) is not None:
            raise ConflictException("Coupon code already exists")
        coupon = Coupon(
            code=code,
            description=payload.description,
            coupon_type=payload.coupon_type,
            value=money(payload.value),
            minimum_order_amount=(
                money(payload.minimum_order_amount)
                if payload.minimum_order_amount is not None
                else None
            ),
            maximum_discount=(
                money(payload.maximum_discount) if payload.maximum_discount is not None else None
            ),
            usage_limit=payload.usage_limit,
            per_user_limit=payload.per_user_limit,
            is_active=payload.is_active,
            starts_at=payload.starts_at,
            expires_at=payload.expires_at,
            created_by=actor_id,
        )
        await self._coupons.add(coupon)
        await self._session.commit()
        await self._session.refresh(coupon)
        await self._audit.record(
            action=AuditAction.CREATE,
            resource_type="coupon",
            resource_id=str(coupon.id),
            user_id=actor_id,
            message="Coupon created",
            details={"code": coupon.code},
            commit=True,
        )
        await self._dashboard_cache.invalidate_all()
        logger.info("Coupon created | coupon_id={} | code={}", coupon.id, coupon.code)
        return CouponResponse.model_validate(coupon)

    async def update(
        self,
        coupon_id: UUID,
        payload: CouponUpdateRequest,
        *,
        actor_id: UUID,
    ) -> CouponResponse:
        coupon = await self._coupons.get_by_id(coupon_id)
        if coupon is None:
            raise NotFoundException("Coupon not found")
        data = payload.model_dump(exclude_unset=True)
        if not data:
            raise ValidationException("No coupon fields provided")
        coupon_type = data.get("coupon_type", coupon.coupon_type)
        value = data.get("value", coupon.value)
        if coupon_type == CouponType.PERCENTAGE and value > 100:
            raise ValidationException("Percentage coupons cannot exceed 100")
        starts = data.get("starts_at", coupon.starts_at)
        ends = data.get("expires_at", coupon.expires_at)
        if starts and ends and ends < starts:
            raise ValidationException("expires_at must be after starts_at")
        for key, value in data.items():
            if key in {"value", "minimum_order_amount", "maximum_discount"} and value is not None:
                setattr(coupon, key, money(value))
            else:
                setattr(coupon, key, value)
        await self._session.commit()
        await self._session.refresh(coupon)
        await self._audit.record(
            action=AuditAction.UPDATE,
            resource_type="coupon",
            resource_id=str(coupon.id),
            user_id=actor_id,
            message="Coupon updated",
            details={"fields": list(data.keys())},
            commit=True,
        )
        await self._dashboard_cache.invalidate_all()
        logger.info("Coupon updated | coupon_id={}", coupon_id)
        return CouponResponse.model_validate(coupon)

    async def set_active(
        self,
        coupon_id: UUID,
        *,
        is_active: bool,
        actor_id: UUID,
    ) -> CouponResponse:
        return await self.update(
            coupon_id,
            CouponUpdateRequest(is_active=is_active),
            actor_id=actor_id,
        )

    async def delete(self, coupon_id: UUID, *, actor_id: UUID) -> None:
        coupon = await self._coupons.get_by_id(coupon_id)
        if coupon is None:
            raise NotFoundException("Coupon not found")
        await self._coupons.soft_delete(coupon)
        await self._session.commit()
        await self._audit.record(
            action=AuditAction.DELETE,
            resource_type="coupon",
            resource_id=str(coupon_id),
            user_id=actor_id,
            message="Coupon deleted",
            commit=True,
        )
        await self._dashboard_cache.invalidate_all()
        logger.info("Coupon deleted | coupon_id={}", coupon_id)

    async def usage_report(self, coupon_id: UUID) -> CouponUsageReportResponse:
        coupon = await self._coupons.get_by_id(coupon_id)
        if coupon is None:
            raise NotFoundException("Coupon not found")
        total_discount, unique_users = await self._usages.usage_report(coupon_id)
        remaining = None
        if coupon.usage_limit is not None:
            remaining = max(coupon.usage_limit - int(coupon.used_count or 0), 0)
        return CouponUsageReportResponse(
            coupon_id=coupon.id,
            code=coupon.code,
            used_count=int(coupon.used_count or 0),
            usage_limit=coupon.usage_limit,
            total_discount_applied=money(total_discount),
            unique_users=unique_users,
            remaining_uses=remaining,
        )
