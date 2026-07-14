"""Product repository with search, filter, and sort support."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.enums import ProductSort, ProductTag
from app.models.catalog import Category, Product, ProductOption
from app.repositories.base import BaseRepository
from app.schemas.catalog import ProductFilterParams


class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Product)

    def _with_details(self, stmt: Select) -> Select:
        return stmt.options(
            selectinload(Product.images),
            selectinload(Product.variants),
            selectinload(Product.available_options).selectinload(ProductOption.option),
            selectinload(Product.category),
        )

    async def get_by_slug(self, slug: str, *, public_only: bool = True) -> Product | None:
        stmt = select(Product).where(Product.slug == slug, Product.deleted_at.is_(None))
        if public_only:
            stmt = stmt.where(Product.is_visible.is_(True))
        result = await self.session.execute(self._with_details(stmt))
        return result.scalar_one_or_none()

    async def get_detail(self, product_id: UUID, *, public_only: bool = False) -> Product | None:
        stmt = select(Product).where(Product.id == product_id, Product.deleted_at.is_(None))
        if public_only:
            stmt = stmt.where(Product.is_visible.is_(True))
        result = await self.session.execute(self._with_details(stmt))
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str, *, exclude_id: UUID | None = None) -> bool:
        stmt = select(Product.id).where(Product.slug == slug, Product.deleted_at.is_(None))
        if exclude_id is not None:
            stmt = stmt.where(Product.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    def _apply_filters(self, stmt: Select, filters: ProductFilterParams, *, public_only: bool) -> Select:
        stmt = stmt.where(Product.deleted_at.is_(None))
        if public_only:
            stmt = stmt.where(Product.is_visible.is_(True))

        if filters.category_id is not None:
            stmt = stmt.where(Product.category_id == filters.category_id)
        if filters.category:
            stmt = stmt.join(Category, Category.id == Product.category_id).where(
                Category.slug == filters.category,
                Category.deleted_at.is_(None),
            )
        if filters.min_price is not None:
            stmt = stmt.where(Product.base_price >= filters.min_price)
        if filters.max_price is not None:
            stmt = stmt.where(Product.base_price <= filters.max_price)
        if filters.is_available is not None:
            stmt = stmt.where(Product.is_available.is_(filters.is_available))
        if filters.is_featured is not None:
            stmt = stmt.where(Product.is_featured.is_(filters.is_featured))
        if filters.is_popular is not None:
            stmt = stmt.where(Product.is_popular.is_(filters.is_popular))
        if filters.is_best_seller is not None:
            stmt = stmt.where(Product.is_best_seller.is_(filters.is_best_seller))
        if filters.vegetarian is True:
            stmt = stmt.where(Product.tags.contains([ProductTag.VEGETARIAN.value]))
        if filters.tag is not None:
            stmt = stmt.where(Product.tags.contains([filters.tag.value]))
        if filters.min_calories is not None:
            stmt = stmt.where(Product.calories >= filters.min_calories)
        if filters.max_calories is not None:
            stmt = stmt.where(Product.calories <= filters.max_calories)
        if filters.max_preparation_time is not None:
            stmt = stmt.where(Product.preparation_time_minutes <= filters.max_preparation_time)
        if filters.q:
            pattern = f"%{filters.q.strip()}%"
            stmt = stmt.where(
                or_(
                    Product.name.ilike(pattern),
                    Product.slug.ilike(pattern),
                    Product.description.ilike(pattern),
                    Product.short_description.ilike(pattern),
                    func.array_to_string(Product.tags, ",").ilike(pattern),
                )
            )
        return stmt

    def _apply_sort(self, stmt: Select, sort: ProductSort) -> Select:
        mapping = {
            ProductSort.NEWEST: Product.created_at.desc(),
            ProductSort.OLDEST: Product.created_at.asc(),
            ProductSort.PRICE_ASC: Product.base_price.asc(),
            ProductSort.PRICE_DESC: Product.base_price.desc(),
            ProductSort.POPULARITY: Product.is_popular.desc(),
            ProductSort.ALPHABETICAL: Product.name.asc(),
            ProductSort.PREPARATION_TIME: Product.preparation_time_minutes.asc().nulls_last(),
        }
        return stmt.order_by(mapping[sort], Product.sort_order.asc(), Product.name.asc())

    async def list_filtered(
        self,
        filters: ProductFilterParams,
        *,
        limit: int,
        offset: int,
        public_only: bool = True,
    ) -> tuple[list[Product], int]:
        base = select(Product)
        base = self._apply_filters(base, filters, public_only=public_only)
        count_stmt = select(func.count()).select_from(base.order_by(None).subquery())
        total = int((await self.session.execute(count_stmt)).scalar_one())

        stmt = self._apply_sort(base, filters.sort).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all()), total

    async def list_featured(self, *, limit: int = 20) -> list[Product]:
        stmt = (
            select(Product)
            .where(
                Product.deleted_at.is_(None),
                Product.is_visible.is_(True),
                Product.is_featured.is_(True),
            )
            .order_by(Product.sort_order.asc(), Product.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_popular(self, *, limit: int = 20) -> list[Product]:
        stmt = (
            select(Product)
            .where(
                Product.deleted_at.is_(None),
                Product.is_visible.is_(True),
                or_(Product.is_popular.is_(True), Product.is_best_seller.is_(True)),
            )
            .order_by(Product.is_best_seller.desc(), Product.is_popular.desc(), Product.name.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_recommended(
        self,
        *,
        category_id: UUID | None = None,
        exclude_id: UUID | None = None,
        limit: int = 12,
    ) -> list[Product]:
        conditions = [
            Product.deleted_at.is_(None),
            Product.is_visible.is_(True),
            Product.is_available.is_(True),
        ]
        if category_id is not None:
            conditions.append(Product.category_id == category_id)
        if exclude_id is not None:
            conditions.append(Product.id != exclude_id)
        stmt = (
            select(Product)
            .where(and_(*conditions))
            .order_by(
                Product.is_featured.desc(),
                Product.is_popular.desc(),
                Product.is_best_seller.desc(),
                Product.created_at.desc(),
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search(
        self,
        query: str,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[Product], int]:
        filters = ProductFilterParams(q=query, sort=ProductSort.POPULARITY)
        return await self.list_filtered(filters, limit=limit, offset=offset, public_only=True)
