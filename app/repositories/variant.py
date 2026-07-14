"""Variant repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import ProductVariant
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
