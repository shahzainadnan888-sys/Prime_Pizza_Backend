"""Public catalog APIs: categories, products, deals."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.common.constants import APIMessages
from app.common.enums import ProductSort, ProductTag
from app.dependencies.catalog import (
    get_category_service,
    get_deal_service,
    get_product_filter_service,
    get_product_search_service,
    get_product_service,
)
from app.dependencies.pagination import get_pagination
from app.schemas.catalog import (
    CategoryResponse,
    DealResponse,
    ProductDetailResponse,
    ProductFilterParams,
    ProductListItemResponse,
)
from app.schemas.pagination import PaginationParams
from app.schemas.response import PaginatedResponse, SuccessResponse
from app.services.category import CategoryService
from app.services.deal import DealService
from app.services.product import ProductService
from app.services.search import ProductFilterService, ProductSearchService

router = APIRouter(tags=["Catalog"])


@router.get("/categories", response_model=SuccessResponse[list[CategoryResponse]])
async def list_categories(
    request: Request,
    service: CategoryService = Depends(get_category_service),
) -> SuccessResponse[list[CategoryResponse]]:
    data = await service.list_public()
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/categories/{slug}", response_model=SuccessResponse[CategoryResponse])
async def get_category(
    slug: str,
    request: Request,
    service: CategoryService = Depends(get_category_service),
) -> SuccessResponse[CategoryResponse]:
    data = await service.get_by_slug(slug)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/products", response_model=PaginatedResponse[ProductListItemResponse])
async def list_products(
    request: Request,
    pagination: PaginationParams = Depends(get_pagination),
    service: ProductFilterService = Depends(get_product_filter_service),
    category: str | None = Query(default=None),
    category_id: UUID | None = Query(default=None),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    is_available: bool | None = Query(default=None),
    is_featured: bool | None = Query(default=None),
    is_popular: bool | None = Query(default=None),
    is_best_seller: bool | None = Query(default=None),
    vegetarian: bool | None = Query(default=None),
    tag: ProductTag | None = Query(default=None),
    min_calories: int | None = Query(default=None, ge=0),
    max_calories: int | None = Query(default=None, ge=0),
    max_preparation_time: int | None = Query(default=None, ge=0),
    sort: ProductSort = Query(default=ProductSort.NEWEST),
    q: str | None = Query(default=None, min_length=1, max_length=200),
) -> PaginatedResponse[ProductListItemResponse]:
    filters = ProductFilterParams(
        category=category,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        is_available=is_available,
        is_featured=is_featured,
        is_popular=is_popular,
        is_best_seller=is_best_seller,
        vegetarian=vegetarian,
        tag=tag,
        min_calories=min_calories,
        max_calories=max_calories,
        max_preparation_time=max_preparation_time,
        sort=sort,
        q=q,
    )
    data, meta = await service.filter(filters, pagination)
    return PaginatedResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        meta=meta.model_dump(),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/products/search", response_model=PaginatedResponse[ProductListItemResponse])
async def search_products(
    request: Request,
    q: str = Query(..., min_length=1, max_length=200),
    pagination: PaginationParams = Depends(get_pagination),
    service: ProductSearchService = Depends(get_product_search_service),
) -> PaginatedResponse[ProductListItemResponse]:
    data, meta = await service.search(q, pagination)
    return PaginatedResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        meta=meta.model_dump(),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/products/featured", response_model=SuccessResponse[list[ProductListItemResponse]])
async def featured_products(
    request: Request,
    service: ProductService = Depends(get_product_service),
) -> SuccessResponse[list[ProductListItemResponse]]:
    data = await service.list_featured()
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/products/popular", response_model=SuccessResponse[list[ProductListItemResponse]])
async def popular_products(
    request: Request,
    service: ProductService = Depends(get_product_service),
) -> SuccessResponse[list[ProductListItemResponse]]:
    data = await service.list_popular()
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "/products/recommended",
    response_model=SuccessResponse[list[ProductListItemResponse]],
)
async def recommended_products(
    request: Request,
    service: ProductService = Depends(get_product_service),
    product_slug: str | None = Query(default=None),
    category: str | None = Query(default=None),
) -> SuccessResponse[list[ProductListItemResponse]]:
    data = await service.list_recommended(product_slug=product_slug, category=category)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/products/{slug}", response_model=SuccessResponse[ProductDetailResponse])
async def get_product(
    slug: str,
    request: Request,
    service: ProductService = Depends(get_product_service),
) -> SuccessResponse[ProductDetailResponse]:
    data = await service.get_by_slug(slug)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/deals", response_model=SuccessResponse[list[DealResponse]])
async def list_deals(
    request: Request,
    service: DealService = Depends(get_deal_service),
) -> SuccessResponse[list[DealResponse]]:
    data = await service.list_public()
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/deals/{slug}", response_model=SuccessResponse[DealResponse])
async def get_deal(
    slug: str,
    request: Request,
    service: DealService = Depends(get_deal_service),
) -> SuccessResponse[DealResponse]:
    data = await service.get_by_slug(slug)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )
