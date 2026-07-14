"""FastAPI dependencies for the catalog / product module."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.dependencies.database import get_db_session
from app.dependencies.redis import get_cache_service
from app.dependencies.settings import get_app_settings
from app.integrations.redis.cache import CacheService
from app.services.catalog_cache import CatalogCacheService
from app.services.category import CategoryService
from app.services.cloudinary_catalog import CatalogCloudinaryService
from app.services.deal import DealService
from app.services.product import ProductService
from app.services.product_image import ProductImageService
from app.services.search import ProductFilterService, ProductSearchService
from app.services.variant import VariantService


def get_catalog_cache(
    cache: CacheService = Depends(get_cache_service),
    settings: Settings = Depends(get_app_settings),
) -> CatalogCacheService:
    return CatalogCacheService(cache, settings)


def get_catalog_cloudinary(
    settings: Settings = Depends(get_app_settings),
) -> CatalogCloudinaryService:
    return CatalogCloudinaryService(settings)


def get_variant_service(
    session: AsyncSession = Depends(get_db_session),
) -> VariantService:
    return VariantService(session=session)


def get_category_service(
    session: AsyncSession = Depends(get_db_session),
    cache: CatalogCacheService = Depends(get_catalog_cache),
) -> CategoryService:
    return CategoryService(session=session, cache=cache)


def get_product_service(
    session: AsyncSession = Depends(get_db_session),
    cache: CatalogCacheService = Depends(get_catalog_cache),
    variant_service: VariantService = Depends(get_variant_service),
) -> ProductService:
    return ProductService(session=session, cache=cache, variant_service=variant_service)


def get_product_image_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
    cloudinary: CatalogCloudinaryService = Depends(get_catalog_cloudinary),
    cache: CatalogCacheService = Depends(get_catalog_cache),
) -> ProductImageService:
    return ProductImageService(
        session=session,
        settings=settings,
        cloudinary=cloudinary,
        cache=cache,
    )


def get_deal_service(
    session: AsyncSession = Depends(get_db_session),
    cache: CatalogCacheService = Depends(get_catalog_cache),
) -> DealService:
    return DealService(session=session, cache=cache)


def get_product_search_service(
    product_service: ProductService = Depends(get_product_service),
) -> ProductSearchService:
    return ProductSearchService(product_service)


def get_product_filter_service(
    product_service: ProductService = Depends(get_product_service),
) -> ProductFilterService:
    return ProductFilterService(product_service)
