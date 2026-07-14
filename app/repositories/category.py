"""Category repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Category)

    async def list_visible(self) -> list[Category]:
        stmt = (
            select(Category)
            .where(Category.deleted_at.is_(None), Category.is_visible.is_(True))
            .order_by(Category.display_order.asc(), Category.name.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all_active(self) -> list[Category]:
        stmt = (
            select(Category)
            .where(Category.deleted_at.is_(None))
            .order_by(Category.display_order.asc(), Category.name.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str, *, visible_only: bool = True) -> Category | None:
        stmt = select(Category).where(Category.slug == slug, Category.deleted_at.is_(None))
        if visible_only:
            stmt = stmt.where(Category.is_visible.is_(True))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_active(self, category_id: UUID) -> Category | None:
        return await self.get_by_id(category_id)

    async def slug_exists(self, slug: str, *, exclude_id: UUID | None = None) -> bool:
        stmt = select(Category.id).where(Category.slug == slug, Category.deleted_at.is_(None))
        if exclude_id is not None:
            stmt = stmt.where(Category.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
