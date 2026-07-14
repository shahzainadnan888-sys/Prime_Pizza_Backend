"""Product catalog service (public reads + owner writes)."""

from __future__ import annotations

from hashlib import sha1
from uuid import UUID

from loguru import logger
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.catalog import Product
from app.repositories.category import CategoryRepository
from app.repositories.product import ProductRepository
from app.schemas.catalog import (
    ProductCreateRequest,
    ProductDetailResponse,
    ProductFilterParams,
    ProductListItemResponse,
    ProductUpdateRequest,
)
from app.schemas.pagination import PaginationMeta, PaginationParams
from app.services.base import BaseService
from app.services.catalog_cache import CatalogCacheService
from app.services.catalog_mapper import to_product_detail, to_product_list_item
from app.services.variant import VariantService
from app.utils.slug import slugify


class ProductService(BaseService):
    service_name = "product"

    def __init__(
        self,
        *,
        session: AsyncSession,
        cache: CatalogCacheService,
        variant_service: VariantService,
    ) -> None:
        self._session = session
        self._products = ProductRepository(session)
        self._categories = CategoryRepository(session)
        self._cache = cache
        self._variants = variant_service

    async def list_products(
        self,
        filters: ProductFilterParams,
        pagination: PaginationParams,
    ) -> tuple[list[ProductListItemResponse], PaginationMeta]:
        rows, total = await self._products.list_filtered(
            filters,
            limit=pagination.limit,
            offset=pagination.offset,
            public_only=True,
        )
        meta = PaginationMeta.from_totals(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total,
        )
        return [to_product_list_item(row) for row in rows], meta

    async def get_by_slug(self, slug: str) -> ProductDetailResponse:
        cache_key = self._cache.product_key(slug)
        cached = await self._cache.get_json(cache_key)
        if cached is not None:
            return ProductDetailResponse.model_validate(cached)

        product = await self._products.get_by_slug(slug, public_only=True)
        if product is None:
            raise NotFoundException("Product not found")
        data = to_product_detail(product)
        await self._cache.set_json(cache_key, data.model_dump(mode="json"))
        return data

    async def list_featured(self) -> list[ProductListItemResponse]:
        cached = await self._cache.get_json(self._cache.featured_key())
        if cached is not None:
            return [ProductListItemResponse.model_validate(item) for item in cached]
        rows = await self._products.list_featured()
        data = [to_product_list_item(row) for row in rows]
        await self._cache.set_json(
            self._cache.featured_key(),
            [item.model_dump(mode="json") for item in data],
        )
        return data

    async def list_popular(self) -> list[ProductListItemResponse]:
        cached = await self._cache.get_json(self._cache.popular_key())
        if cached is not None:
            return [ProductListItemResponse.model_validate(item) for item in cached]
        rows = await self._products.list_popular()
        data = [to_product_list_item(row) for row in rows]
        await self._cache.set_json(
            self._cache.popular_key(),
            [item.model_dump(mode="json") for item in data],
        )
        return data

    async def list_recommended(
        self,
        *,
        product_slug: str | None = None,
        category: str | None = None,
    ) -> list[ProductListItemResponse]:
        category_id = None
        exclude_id = None
        if product_slug:
            product = await self._products.get_by_slug(product_slug, public_only=True)
            if product is not None:
                category_id = product.category_id
                exclude_id = product.id
        elif category:
            cat = await self._categories.get_by_slug(category, visible_only=True)
            if cat is not None:
                category_id = cat.id
        rows = await self._products.list_recommended(
            category_id=category_id,
            exclude_id=exclude_id,
        )
        return [to_product_list_item(row) for row in rows]

    async def search(
        self,
        query: str,
        pagination: PaginationParams,
    ) -> tuple[list[ProductListItemResponse], PaginationMeta]:
        fingerprint = sha1(
            f"{query.strip().lower()}:{pagination.page}:{pagination.page_size}".encode()
        ).hexdigest()
        cache_key = self._cache.search_key(fingerprint)
        cached = await self._cache.get_json(cache_key)
        if cached is not None:
            items = [ProductListItemResponse.model_validate(i) for i in cached["items"]]
            meta = PaginationMeta.model_validate(cached["meta"])
            return items, meta

        rows, total = await self._products.search(
            query,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        meta = PaginationMeta.from_totals(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total,
        )
        items = [to_product_list_item(row) for row in rows]
        await self._cache.set_json(
            cache_key,
            {
                "items": [item.model_dump(mode="json") for item in items],
                "meta": meta.model_dump(mode="json"),
            },
        )
        return items, meta

    async def create(self, payload: ProductCreateRequest) -> ProductDetailResponse:
        category = await self._categories.get_by_id(payload.category_id)
        if category is None:
            raise NotFoundException("Category not found")
        slug = payload.slug or slugify(payload.name, max_length=220)
        if await self._products.slug_exists(slug):
            raise ConflictException("Product slug already exists")

        tags = [tag.value for tag in payload.tags]
        product = Product(
            category_id=payload.category_id,
            name=payload.name.strip(),
            slug=slug,
            description=payload.description,
            short_description=payload.short_description,
            base_price=payload.base_price,
            discount_price=payload.discount_price,
            image_url=payload.image_url,
            is_available=payload.is_available,
            stock_status=payload.stock_status,
            preparation_time_minutes=payload.preparation_time_minutes,
            calories=payload.calories,
            is_featured=payload.is_featured,
            is_popular=payload.is_popular,
            is_best_seller=payload.is_best_seller,
            is_visible=payload.is_visible,
            sort_order=payload.sort_order,
            tags=tags,
            seo_title=payload.seo_title,
            seo_description=payload.seo_description,
            seo_keywords=payload.seo_keywords,
        )
        await self._products.add(product)
        await self._session.flush()
        await self._variants.replace_variants(product.id, payload.variants)
        await self._variants.replace_extras(product.id, payload.extra_option_ids)
        await self._session.commit()

        detail = await self._products.get_detail(product.id)
        assert detail is not None
        await self._cache.invalidate_all()
        logger.info("Product created | product_id={} | slug={}", product.id, product.slug)
        return to_product_detail(detail)

    async def update(self, product_id: UUID, payload: ProductUpdateRequest) -> ProductDetailResponse:
        product = await self._products.get_by_id(product_id)
        if product is None:
            raise NotFoundException("Product not found")

        data = payload.model_dump(exclude_unset=True, exclude={"variants", "extra_option_ids", "tags"})
        if "tags" in payload.model_fields_set:
            data["tags"] = [tag.value for tag in (payload.tags or [])]
        if not data and payload.variants is None and payload.extra_option_ids is None:
            raise ValidationException("No product fields provided")

        if "category_id" in data:
            category = await self._categories.get_by_id(data["category_id"])
            if category is None:
                raise NotFoundException("Category not found")
        if "slug" in data and data["slug"] and await self._products.slug_exists(
            data["slug"],
            exclude_id=product_id,
        ):
            raise ConflictException("Product slug already exists")
        if "name" in data and data["name"]:
            data["name"] = str(data["name"]).strip()

        base_price = data.get("base_price", product.base_price)
        discount = data.get("discount_price", product.discount_price)
        if discount is not None and base_price is not None and discount > base_price:
            raise ValidationException("discount_price cannot exceed base_price")

        for key, value in data.items():
            setattr(product, key, value)

        if payload.variants is not None:
            await self._variants.replace_variants(product_id, payload.variants)
        if payload.extra_option_ids is not None:
            await self._variants.replace_extras(product_id, payload.extra_option_ids)

        await self._session.commit()
        detail = await self._products.get_detail(product_id)
        assert detail is not None
        await self._cache.invalidate_all()
        logger.info("Product updated | product_id={}", product_id)
        return to_product_detail(detail)

    async def delete(self, product_id: UUID) -> None:
        product = await self._products.get_by_id(product_id)
        if product is None:
            raise NotFoundException("Product not found")
        await self._products.soft_delete(product)
        await self._session.commit()
        await self._cache.invalidate_all()
        logger.info("Product deleted | product_id={}", product_id)

    async def bulk_update_fields(
        self,
        product_ids: list[UUID],
        *,
        fields: dict,
    ) -> tuple[int, int]:
        if not product_ids:
            raise ValidationException("product_ids is required")
        allowed = {
            "is_visible",
            "is_featured",
            "is_available",
            "category_id",
            "deleted_at",
        }
        data = {k: v for k, v in fields.items() if k in allowed}
        if not data:
            raise ValidationException("No bulk fields provided")
        matched = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(Product).where(
                        Product.id.in_(product_ids),
                        Product.deleted_at.is_(None),
                    )
                )
            ).scalar_one()
        )
        result = await self._session.execute(
            update(Product)
            .where(Product.id.in_(product_ids), Product.deleted_at.is_(None))
            .values(**data)
        )
        await self._session.commit()
        await self._cache.invalidate_all()
        updated = int(result.rowcount or 0)
        logger.info("Product bulk update | matched={} | updated={}", matched, updated)
        return matched, updated

    async def bulk_delete(self, product_ids: list[UUID]) -> tuple[int, int]:
        from datetime import UTC, datetime

        return await self.bulk_update_fields(
            product_ids,
            fields={"deleted_at": datetime.now(UTC)},
        )
