"""Product gallery image service (Cloudinary-backed)."""

from __future__ import annotations

from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.catalog import ProductImage
from app.repositories.image import ProductImageRepository
from app.repositories.product import ProductRepository
from app.schemas.catalog import ImageReorderRequest, ProductImageResponse
from app.services.base import BaseService
from app.services.catalog_cache import CatalogCacheService
from app.services.cloudinary_catalog import CatalogCloudinaryService


class ProductImageService(BaseService):
    service_name = "product_image"

    def __init__(
        self,
        *,
        session: AsyncSession,
        settings: Settings,
        cloudinary: CatalogCloudinaryService,
        cache: CatalogCacheService,
    ) -> None:
        self._session = session
        self._settings = settings
        self._cloudinary = cloudinary
        self._cache = cache
        self._products = ProductRepository(session)
        self._images = ProductImageRepository(session)

    async def upload(
        self,
        product_id: UUID,
        *,
        file_obj,
        filename: str,
        content_type: str | None,
        size: int,
        alt_text: str | None = None,
        is_primary: bool = False,
    ) -> ProductImageResponse:
        product = await self._products.get_by_id(product_id)
        if product is None:
            raise NotFoundException("Product not found")

        count = await self._images.count_for_product(product_id)
        if count >= self._settings.max_product_images:
            raise ValidationException(
                f"Maximum of {self._settings.max_product_images} images allowed per product",
            )

        uploaded = self._cloudinary.upload(
            file_obj=file_obj,
            folder=f"prime_pizza/products/{product_id}",
            public_id=None,
            filename=filename,
            content_type=content_type,
            size=size,
        )
        if await self._images.public_id_exists(uploaded.public_id):
            raise ConflictException("Duplicate image upload detected")

        if is_primary or count == 0:
            await self._images.clear_primary(product_id)
            is_primary = True

        image = ProductImage(
            product_id=product_id,
            image_url=uploaded.url,
            public_id=uploaded.public_id,
            alt_text=alt_text,
            is_primary=is_primary,
            display_order=await self._images.next_display_order(product_id),
        )
        await self._images.add(image)

        if is_primary:
            product.image_url = uploaded.url
            product.image_public_id = uploaded.public_id

        await self._session.commit()
        await self._session.refresh(image)
        await self._cache.invalidate_all()
        logger.info("Image uploaded | product_id={} | image_id={}", product_id, image.id)
        return ProductImageResponse.model_validate(image)

    async def delete(self, product_id: UUID, image_id: UUID) -> None:
        product = await self._products.get_by_id(product_id)
        if product is None:
            raise NotFoundException("Product not found")
        image = await self._images.get_for_product(product_id, image_id)
        if image is None:
            raise NotFoundException("Image not found")

        public_id = image.public_id
        was_primary = image.is_primary
        await self._images.soft_delete(image)
        await self._session.flush()

        if was_primary:
            remaining = await self._images.list_for_product(product_id)
            if remaining:
                remaining[0].is_primary = True
                product.image_url = remaining[0].image_url
                product.image_public_id = remaining[0].public_id
            else:
                product.image_url = None
                product.image_public_id = None

        await self._session.commit()
        self._cloudinary.delete(public_id)
        await self._cache.invalidate_all()
        logger.info("Image deleted | product_id={} | image_id={}", product_id, image_id)

    async def reorder(self, product_id: UUID, payload: ImageReorderRequest) -> list[ProductImageResponse]:
        product = await self._products.get_by_id(product_id)
        if product is None:
            raise NotFoundException("Product not found")
        images = await self._images.list_for_product(product_id)
        by_id = {img.id: img for img in images}
        if set(payload.image_ids) != set(by_id.keys()):
            raise ValidationException("image_ids must include every current product image exactly once")

        # Two-phase update avoids unique (product_id, display_order) collisions.
        for index, image_id in enumerate(payload.image_ids):
            by_id[image_id].display_order = 10_000 + index
        await self._session.flush()
        for index, image_id in enumerate(payload.image_ids):
            by_id[image_id].display_order = index
        await self._session.commit()
        await self._cache.invalidate_all()
        refreshed = await self._images.list_for_product(product_id)
        return [ProductImageResponse.model_validate(img) for img in refreshed]
