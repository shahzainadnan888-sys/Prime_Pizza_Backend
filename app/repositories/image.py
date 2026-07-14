"""Product image repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import ProductImage
from app.repositories.base import BaseRepository


class ProductImageRepository(BaseRepository[ProductImage]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ProductImage)

    async def list_for_product(self, product_id: UUID) -> list[ProductImage]:
        stmt = (
            select(ProductImage)
            .where(ProductImage.product_id == product_id, ProductImage.deleted_at.is_(None))
            .order_by(ProductImage.display_order.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_product(self, product_id: UUID, image_id: UUID) -> ProductImage | None:
        stmt = select(ProductImage).where(
            ProductImage.id == image_id,
            ProductImage.product_id == product_id,
            ProductImage.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_for_product(self, product_id: UUID) -> int:
        stmt = select(func.count()).select_from(ProductImage).where(
            ProductImage.product_id == product_id,
            ProductImage.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def public_id_exists(self, public_id: str) -> bool:
        stmt = select(ProductImage.id).where(
            ProductImage.public_id == public_id,
            ProductImage.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def clear_primary(self, product_id: UUID) -> None:
        stmt = (
            update(ProductImage)
            .where(
                ProductImage.product_id == product_id,
                ProductImage.deleted_at.is_(None),
                ProductImage.is_primary.is_(True),
            )
            .values(is_primary=False)
        )
        await self.session.execute(stmt)

    async def next_display_order(self, product_id: UUID) -> int:
        stmt = select(func.coalesce(func.max(ProductImage.display_order), -1)).where(
            ProductImage.product_id == product_id,
            ProductImage.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one()) + 1
