"""Order repositories."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem, OrderNumberSequence, OrderTimelineEvent
from app.repositories.base import BaseRepository
from app.schemas.orders import OrderFilterParams


class OrderRepository(BaseRepository[Order]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Order)

    def _with_details(self, stmt: Select) -> Select:
        return stmt.options(
            selectinload(Order.items).selectinload(OrderItem.extras),
            selectinload(Order.timeline),
            selectinload(Order.coupon),
        )

    async def get_detail(self, order_id: UUID) -> Order | None:
        stmt = select(Order).where(Order.id == order_id, Order.deleted_at.is_(None))
        result = await self.session.execute(self._with_details(stmt))
        return result.scalar_one_or_none()

    async def get_for_user(self, order_id: UUID, user_id: UUID) -> Order | None:
        stmt = select(Order).where(
            Order.id == order_id,
            Order.user_id == user_id,
            Order.deleted_at.is_(None),
        )
        result = await self.session.execute(self._with_details(stmt))
        return result.scalar_one_or_none()

    def _apply_filters(self, stmt: Select, filters: OrderFilterParams) -> Select:
        stmt = stmt.where(Order.deleted_at.is_(None))
        if filters.status is not None:
            stmt = stmt.where(Order.status == filters.status)
        if filters.payment_status is not None:
            stmt = stmt.where(Order.payment_status == filters.payment_status)
        if filters.date_from is not None:
            stmt = stmt.where(Order.created_at >= filters.date_from)
        if filters.date_to is not None:
            stmt = stmt.where(Order.created_at <= filters.date_to)
        if filters.user_id is not None:
            stmt = stmt.where(Order.user_id == filters.user_id)
        if filters.q:
            stmt = stmt.where(Order.order_number.ilike(f"%{filters.q.strip()}%"))
        if filters.sort == "oldest":
            stmt = stmt.order_by(Order.created_at.asc())
        else:
            stmt = stmt.order_by(Order.created_at.desc())
        return stmt

    async def list_for_user(
        self,
        user_id: UUID,
        filters: OrderFilterParams,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[Order], int]:
        base = select(Order).where(Order.user_id == user_id)
        base = self._apply_filters(base, filters)
        count_stmt = select(func.count()).select_from(base.order_by(None).subquery())
        total = int((await self.session.execute(count_stmt)).scalar_one())
        result = await self.session.execute(
            base.options(selectinload(Order.items)).limit(limit).offset(offset)
        )
        return list(result.scalars().unique().all()), total

    async def list_all_filtered(
        self,
        filters: OrderFilterParams,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[Order], int]:
        base = select(Order)
        base = self._apply_filters(base, filters)
        count_stmt = select(func.count()).select_from(base.order_by(None).subquery())
        total = int((await self.session.execute(count_stmt)).scalar_one())
        result = await self.session.execute(
            base.options(selectinload(Order.items)).limit(limit).offset(offset)
        )
        return list(result.scalars().unique().all()), total


class OrderTimelineRepository(BaseRepository[OrderTimelineEvent]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, OrderTimelineEvent)

    async def list_for_order(self, order_id: UUID) -> list[OrderTimelineEvent]:
        stmt = (
            select(OrderTimelineEvent)
            .where(
                OrderTimelineEvent.order_id == order_id,
                OrderTimelineEvent.deleted_at.is_(None),
            )
            .order_by(OrderTimelineEvent.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class OrderNumberSequenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def next_value(self, year: int) -> int:
        """Allocate the next sequential value for ``PP-YYYY-######`` under row lock."""
        stmt = (
            select(OrderNumberSequence)
            .where(OrderNumberSequence.year == year, OrderNumberSequence.deleted_at.is_(None))
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            try:
                async with self.session.begin_nested():
                    self.session.add(OrderNumberSequence(year=year, last_value=0))
                    await self.session.flush()
            except IntegrityError:
                pass
            result = await self.session.execute(stmt)
            row = result.scalar_one()
        row.last_value += 1
        await self.session.flush()
        return int(row.last_value)
