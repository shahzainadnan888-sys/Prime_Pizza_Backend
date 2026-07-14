"""Category service."""

from __future__ import annotations

from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.catalog import Category
from app.repositories.category import CategoryRepository
from app.schemas.catalog import CategoryCreateRequest, CategoryResponse, CategoryUpdateRequest
from app.services.base import BaseService
from app.services.catalog_cache import CatalogCacheService
from app.utils.slug import slugify


class CategoryService(BaseService):
    service_name = "category"

    def __init__(
        self,
        *,
        session: AsyncSession,
        cache: CatalogCacheService,
    ) -> None:
        self._session = session
        self._categories = CategoryRepository(session)
        self._cache = cache

    async def list_public(self) -> list[CategoryResponse]:
        cached = await self._cache.get_json(self._cache.categories_key())
        if cached is not None:
            return [CategoryResponse.model_validate(item) for item in cached]

        rows = await self._categories.list_visible()
        data = [CategoryResponse.model_validate(row) for row in rows]
        await self._cache.set_json(
            self._cache.categories_key(),
            [item.model_dump(mode="json") for item in data],
        )
        return data

    async def get_by_slug(self, slug: str) -> CategoryResponse:
        category = await self._categories.get_by_slug(slug, visible_only=True)
        if category is None:
            raise NotFoundException("Category not found")
        return CategoryResponse.model_validate(category)

    async def create(self, payload: CategoryCreateRequest) -> CategoryResponse:
        slug = payload.slug or slugify(payload.name, max_length=180)
        if await self._categories.slug_exists(slug):
            raise ConflictException("Category slug already exists")
        category = Category(
            name=payload.name.strip(),
            slug=slug,
            description=payload.description,
            image_url=payload.image_url,
            display_order=payload.display_order,
            is_visible=payload.is_visible,
            seo_title=payload.seo_title,
            seo_description=payload.seo_description,
            seo_keywords=payload.seo_keywords,
        )
        await self._categories.add(category)
        await self._session.commit()
        await self._session.refresh(category)
        await self._cache.invalidate_all()
        logger.info("Category created | category_id={} | slug={}", category.id, category.slug)
        return CategoryResponse.model_validate(category)

    async def update(self, category_id: UUID, payload: CategoryUpdateRequest) -> CategoryResponse:
        category = await self._categories.get_by_id(category_id)
        if category is None:
            raise NotFoundException("Category not found")
        data = payload.model_dump(exclude_unset=True)
        if not data:
            raise ValidationException("No category fields provided")
        if "slug" in data and data["slug"] and await self._categories.slug_exists(
            data["slug"],
            exclude_id=category_id,
        ):
            raise ConflictException("Category slug already exists")
        if "name" in data and data["name"]:
            data["name"] = str(data["name"]).strip()
        for key, value in data.items():
            setattr(category, key, value)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(category)
        await self._cache.invalidate_all()
        logger.info("Category updated | category_id={}", category.id)
        return CategoryResponse.model_validate(category)

    async def delete(self, category_id: UUID) -> None:
        category = await self._categories.get_by_id(category_id)
        if category is None:
            raise NotFoundException("Category not found")
        await self._categories.soft_delete(category)
        await self._session.commit()
        await self._cache.invalidate_all()
        logger.info("Category deleted | category_id={}", category_id)

    async def list_admin(self) -> list[CategoryResponse]:
        rows = await self._categories.list_all_active()
        return [CategoryResponse.model_validate(row) for row in rows]

    async def hide(self, category_id: UUID) -> CategoryResponse:
        return await self.update(category_id, CategoryUpdateRequest(is_visible=False))

    async def restore(self, category_id: UUID) -> CategoryResponse:
        category = await self._categories.get_by_id(category_id, include_deleted=True)
        if category is None:
            raise NotFoundException("Category not found")
        if category.deleted_at is not None:
            category.deleted_at = None
            category.is_visible = True
            await self._session.commit()
            await self._session.refresh(category)
            await self._cache.invalidate_all()
            logger.info("Category restored | category_id={}", category_id)
            return CategoryResponse.model_validate(category)
        return await self.update(category_id, CategoryUpdateRequest(is_visible=True))

    async def reorder(self, items: list[tuple[UUID, int]]) -> list[CategoryResponse]:
        for category_id, display_order in items:
            category = await self._categories.get_by_id(category_id)
            if category is None:
                raise NotFoundException(f"Category not found: {category_id}")
            category.display_order = display_order
        await self._session.commit()
        await self._cache.invalidate_all()
        logger.info("Category reorder | count={}", len(items))
        return await self.list_admin()
