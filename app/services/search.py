"""Search and filtering facades over ProductService."""

from __future__ import annotations

from app.schemas.catalog import ProductFilterParams, ProductListItemResponse
from app.schemas.pagination import PaginationMeta, PaginationParams
from app.services.base import BaseService
from app.services.product import ProductService


class ProductSearchService(BaseService):
    service_name = "product_search"

    def __init__(self, product_service: ProductService) -> None:
        self._products = product_service

    async def search(
        self,
        query: str,
        pagination: PaginationParams,
    ) -> tuple[list[ProductListItemResponse], PaginationMeta]:
        return await self._products.search(query, pagination)


class ProductFilterService(BaseService):
    service_name = "product_filter"

    def __init__(self, product_service: ProductService) -> None:
        self._products = product_service

    async def filter(
        self,
        filters: ProductFilterParams,
        pagination: PaginationParams,
    ) -> tuple[list[ProductListItemResponse], PaginationMeta]:
        return await self._products.list_products(filters, pagination)
