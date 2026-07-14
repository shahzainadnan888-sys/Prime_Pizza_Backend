"""Variant and extras repositories."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import ProductOption, ProductVariant, VariantOption
from app.repositories.base import BaseRepository


class VariantRepository(BaseRepository[ProductVariant]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ProductVariant)

    async def list_for_product(self, product_id: UUID) -> list[ProductVariant]:
        stmt = (
            select(ProductVariant)
            .where(ProductVariant.product_id == product_id, ProductVariant.deleted_at.is_(None))
            .order_by(ProductVariant.display_order.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def soft_delete_for_product(self, product_id: UUID) -> None:
        rows = await self.list_for_product(product_id)
        for row in rows:
            await self.soft_delete(row)


class ExtraOptionRepository(BaseRepository[VariantOption]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, VariantOption)

    async def list_available(self) -> list[VariantOption]:
        stmt = (
            select(VariantOption)
            .where(VariantOption.deleted_at.is_(None), VariantOption.is_available.is_(True))
            .order_by(VariantOption.display_order.asc(), VariantOption.name.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_ids(self, option_ids: list[UUID]) -> list[VariantOption]:
        if not option_ids:
            return []
        stmt = select(VariantOption).where(
            VariantOption.id.in_(option_ids),
            VariantOption.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def slug_exists(self, slug: str, *, exclude_id: UUID | None = None) -> bool:
        stmt = select(VariantOption.id).where(
            VariantOption.slug == slug,
            VariantOption.deleted_at.is_(None),
        )
        if exclude_id is not None:
            stmt = stmt.where(VariantOption.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None


class ProductOptionRepository(BaseRepository[ProductOption]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ProductOption)

    async def list_for_product(self, product_id: UUID) -> list[ProductOption]:
        stmt = select(ProductOption).where(
            ProductOption.product_id == product_id,
            ProductOption.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def soft_delete_for_product(self, product_id: UUID) -> None:
        rows = await self.list_for_product(product_id)
        for row in rows:
            await self.soft_delete(row)
