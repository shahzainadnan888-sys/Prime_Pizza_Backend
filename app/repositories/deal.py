"""Deal repository."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.deal import Deal, DealProduct
from app.repositories.base import BaseRepository


class DealRepository(BaseRepository[Deal]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Deal)

    def _with_products(self, stmt):
        return stmt.options(
            selectinload(Deal.deal_products).selectinload(DealProduct.product),
        )

    async def list_public(self) -> list[Deal]:
        now = datetime.now(UTC)
        stmt = (
            select(Deal)
            .where(
                Deal.deleted_at.is_(None),
                Deal.is_active.is_(True),
                Deal.is_visible.is_(True),
                or_(Deal.starts_at.is_(None), Deal.starts_at <= now),
                or_(Deal.ends_at.is_(None), Deal.ends_at >= now),
            )
            .order_by(Deal.created_at.desc())
        )
        result = await self.session.execute(self._with_products(stmt))
        return list(result.scalars().unique().all())

    async def get_by_slug(self, slug: str, *, public_only: bool = True) -> Deal | None:
        now = datetime.now(UTC)
        stmt = select(Deal).where(Deal.slug == slug, Deal.deleted_at.is_(None))
        if public_only:
            stmt = stmt.where(
                Deal.is_active.is_(True),
                Deal.is_visible.is_(True),
                or_(Deal.starts_at.is_(None), Deal.starts_at <= now),
                or_(Deal.ends_at.is_(None), Deal.ends_at >= now),
            )
        result = await self.session.execute(self._with_products(stmt))
        return result.scalar_one_or_none()

    async def get_detail(self, deal_id: UUID) -> Deal | None:
        stmt = select(Deal).where(Deal.id == deal_id, Deal.deleted_at.is_(None))
        result = await self.session.execute(self._with_products(stmt))
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str, *, exclude_id: UUID | None = None) -> bool:
        stmt = select(Deal.id).where(Deal.slug == slug, Deal.deleted_at.is_(None))
        if exclude_id is not None:
            stmt = stmt.where(Deal.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None


class DealProductRepository(BaseRepository[DealProduct]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, DealProduct)

    async def list_for_deal(self, deal_id: UUID) -> list[DealProduct]:
        stmt = select(DealProduct).where(
            DealProduct.deal_id == deal_id,
            DealProduct.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def soft_delete_for_deal(self, deal_id: UUID) -> None:
        rows = await self.list_for_deal(deal_id)
        for row in rows:
            await self.soft_delete(row)
