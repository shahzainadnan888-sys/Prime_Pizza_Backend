"""Coupon repository."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coupon import Coupon, CouponUsage
from app.repositories.base import BaseRepository
from app.schemas.admin_coupons import CouponFilterParams


class CouponRepository(BaseRepository[Coupon]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Coupon)

    async def get_by_code(self, code: str) -> Coupon | None:
        stmt = select(Coupon).where(
            Coupon.code == code.upper(),
            Coupon.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_update(self, coupon_id: UUID) -> Coupon | None:
        """Row-lock coupon for atomic usage_count increments during checkout."""
        stmt = (
            select(Coupon)
            .where(Coupon.id == coupon_id, Coupon.deleted_at.is_(None))
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _apply_filters(self, stmt: Select, filters: CouponFilterParams) -> Select:
        stmt = stmt.where(Coupon.deleted_at.is_(None))
        if filters.is_active is not None:
            stmt = stmt.where(Coupon.is_active.is_(filters.is_active))
        if filters.coupon_type is not None:
            stmt = stmt.where(Coupon.coupon_type == filters.coupon_type)
        if filters.q:
            pattern = f"%{filters.q.strip()}%"
            stmt = stmt.where(
                or_(Coupon.code.ilike(pattern), Coupon.description.ilike(pattern))
            )
        if filters.sort == "oldest":
            stmt = stmt.order_by(Coupon.created_at.asc())
        elif filters.sort == "usage":
            stmt = stmt.order_by(Coupon.used_count.desc(), Coupon.created_at.desc())
        else:
            stmt = stmt.order_by(Coupon.created_at.desc())
        return stmt

    async def list_filtered(
        self,
        filters: CouponFilterParams,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[Coupon], int]:
        base = select(Coupon)
        base = self._apply_filters(base, filters)
        count_stmt = select(func.count()).select_from(base.order_by(None).subquery())
        total = int((await self.session.execute(count_stmt)).scalar_one())
        result = await self.session.execute(base.limit(limit).offset(offset))
        return list(result.scalars().all()), total


class CouponUsageRepository(BaseRepository[CouponUsage]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CouponUsage)

    async def count_for_user(self, coupon_id: UUID, user_id: UUID) -> int:
        stmt = select(func.count()).select_from(CouponUsage).where(
            CouponUsage.coupon_id == coupon_id,
            CouponUsage.user_id == user_id,
            CouponUsage.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def usage_report(self, coupon_id: UUID) -> tuple[Decimal, int]:
        stmt = select(
            func.coalesce(func.sum(CouponUsage.discount_applied), 0),
            func.count(func.distinct(CouponUsage.user_id)),
        ).where(
            CouponUsage.coupon_id == coupon_id,
            CouponUsage.deleted_at.is_(None),
        )
        row = (await self.session.execute(stmt)).one()
        return Decimal(str(row[0])), int(row[1])
