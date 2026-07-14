"""Helpers to map catalog ORM entities to response schemas."""

from __future__ import annotations

from app.models.catalog import Product, ProductOption
from app.models.deal import Deal
from app.schemas.catalog import (
    CategoryResponse,
    DealProductResponse,
    DealResponse,
    ExtraOptionResponse,
    ProductDetailResponse,
    ProductImageResponse,
    ProductListItemResponse,
    VariantResponse,
)


def to_product_list_item(product: Product) -> ProductListItemResponse:
    return ProductListItemResponse.model_validate(product)


def to_extra(link: ProductOption) -> ExtraOptionResponse:
    option = link.option
    return ExtraOptionResponse(
        id=option.id,
        name=option.name,
        slug=option.slug,
        option_type=option.option_type,
        price=option.price,
        is_available=option.is_available,
        display_order=option.display_order,
        is_default=link.is_default,
    )


def to_product_detail(product: Product) -> ProductDetailResponse:
    images = [
        ProductImageResponse.model_validate(img)
        for img in product.images
        if img.deleted_at is None
    ]
    variants = [
        VariantResponse.model_validate(variant)
        for variant in product.variants
        if variant.deleted_at is None
    ]
    extras = [
        to_extra(link)
        for link in product.available_options
        if link.deleted_at is None and link.option is not None and link.option.deleted_at is None
    ]
    category = CategoryResponse.model_validate(product.category) if product.category else None
    base = ProductDetailResponse.model_validate(product)
    return base.model_copy(
        update={
            "images": images,
            "variants": variants,
            "extras": extras,
            "category": category,
        }
    )


def to_deal_response(deal: Deal) -> DealResponse:
    products = []
    for link in deal.deal_products:
        if link.deleted_at is not None:
            continue
        product = link.product
        products.append(
            DealProductResponse(
                product_id=link.product_id,
                quantity=link.quantity,
                product_name=product.name if product else None,
                product_slug=product.slug if product else None,
            )
        )
    base = DealResponse.model_validate(deal)
    return base.model_copy(update={"products": products})
