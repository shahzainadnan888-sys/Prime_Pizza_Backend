"""Catalog request / response schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.common.enums import DealType, ProductSort, ProductTag, StockStatus, VariantOptionType, VariantSize
from app.utils.slug import slugify


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None = None
    image_url: str | None = None
    display_order: int
    is_visible: bool
    seo_title: str | None = None
    seo_description: str | None = None
    seo_keywords: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    slug: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = Field(default=None, max_length=5000)
    image_url: str | None = Field(default=None, max_length=500)
    display_order: int = Field(default=0, ge=0)
    is_visible: bool = True
    seo_title: str | None = Field(default=None, max_length=200)
    seo_description: str | None = Field(default=None, max_length=500)
    seo_keywords: str | None = Field(default=None, max_length=500)

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return slugify(value, max_length=180)


class CategoryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    slug: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = Field(default=None, max_length=5000)
    image_url: str | None = Field(default=None, max_length=500)
    display_order: int | None = Field(default=None, ge=0)
    is_visible: bool | None = None
    seo_title: str | None = Field(default=None, max_length=200)
    seo_description: str | None = Field(default=None, max_length=500)
    seo_keywords: str | None = Field(default=None, max_length=500)

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return slugify(value, max_length=180)


class ProductImageResponse(BaseModel):
    id: UUID
    image_url: str
    public_id: str | None = None
    alt_text: str | None = None
    is_primary: bool
    display_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class VariantResponse(BaseModel):
    id: UUID
    size: VariantSize
    name: str
    price: Decimal
    discount_price: Decimal | None = None
    preparation_time_minutes: int | None = None
    is_available: bool
    display_order: int

    model_config = {"from_attributes": True}


class VariantCreateRequest(BaseModel):
    size: VariantSize
    name: str = Field(..., min_length=1, max_length=100)
    price: Decimal = Field(..., ge=0)
    discount_price: Decimal | None = Field(default=None, ge=0)
    preparation_time_minutes: int | None = Field(default=None, ge=0)
    is_available: bool = True
    display_order: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_discount(self) -> VariantCreateRequest:
        if self.discount_price is not None and self.discount_price > self.price:
            msg = "Variant discount_price cannot exceed price"
            raise ValueError(msg)
        return self


class ExtraOptionResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    option_type: VariantOptionType
    price: Decimal
    is_available: bool
    display_order: int
    is_default: bool = False

    model_config = {"from_attributes": True}


class ProductListItemResponse(BaseModel):
    id: UUID
    category_id: UUID
    name: str
    slug: str
    short_description: str | None = None
    base_price: Decimal
    discount_price: Decimal | None = None
    image_url: str | None = None
    is_available: bool
    stock_status: StockStatus
    preparation_time_minutes: int | None = None
    calories: int | None = None
    is_featured: bool
    is_popular: bool
    is_best_seller: bool
    tags: list[str] = Field(default_factory=list)
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductDetailResponse(ProductListItemResponse):
    description: str | None = None
    is_visible: bool
    seo_title: str | None = None
    seo_description: str | None = None
    seo_keywords: str | None = None
    updated_at: datetime
    images: list[ProductImageResponse] = Field(default_factory=list)
    variants: list[VariantResponse] = Field(default_factory=list)
    extras: list[ExtraOptionResponse] = Field(default_factory=list)
    category: CategoryResponse | None = None


class ProductCreateRequest(BaseModel):
    category_id: UUID
    name: str = Field(..., min_length=2, max_length=200)
    slug: str | None = Field(default=None, min_length=2, max_length=220)
    description: str | None = None
    short_description: str | None = Field(default=None, max_length=500)
    base_price: Decimal = Field(..., ge=0)
    discount_price: Decimal | None = Field(default=None, ge=0)
    image_url: str | None = Field(default=None, max_length=500)
    is_available: bool = True
    stock_status: StockStatus = StockStatus.IN_STOCK
    preparation_time_minutes: int | None = Field(default=None, ge=0)
    calories: int | None = Field(default=None, ge=0)
    is_featured: bool = False
    is_popular: bool = False
    is_best_seller: bool = False
    is_visible: bool = True
    sort_order: int = Field(default=0, ge=0)
    tags: list[ProductTag] = Field(default_factory=list)
    seo_title: str | None = Field(default=None, max_length=200)
    seo_description: str | None = Field(default=None, max_length=500)
    seo_keywords: str | None = Field(default=None, max_length=500)
    variants: list[VariantCreateRequest] = Field(default_factory=list)
    extra_option_ids: list[UUID] = Field(default_factory=list)

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return slugify(value, max_length=220)

    @model_validator(mode="after")
    def validate_prices(self) -> ProductCreateRequest:
        if self.discount_price is not None and self.discount_price > self.base_price:
            msg = "discount_price cannot exceed base_price"
            raise ValueError(msg)
        return self


class ProductUpdateRequest(BaseModel):
    category_id: UUID | None = None
    name: str | None = Field(default=None, min_length=2, max_length=200)
    slug: str | None = Field(default=None, min_length=2, max_length=220)
    description: str | None = None
    short_description: str | None = Field(default=None, max_length=500)
    base_price: Decimal | None = Field(default=None, ge=0)
    discount_price: Decimal | None = Field(default=None, ge=0)
    image_url: str | None = Field(default=None, max_length=500)
    is_available: bool | None = None
    stock_status: StockStatus | None = None
    preparation_time_minutes: int | None = Field(default=None, ge=0)
    calories: int | None = Field(default=None, ge=0)
    is_featured: bool | None = None
    is_popular: bool | None = None
    is_best_seller: bool | None = None
    is_visible: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)
    tags: list[ProductTag] | None = None
    seo_title: str | None = Field(default=None, max_length=200)
    seo_description: str | None = Field(default=None, max_length=500)
    seo_keywords: str | None = Field(default=None, max_length=500)
    variants: list[VariantCreateRequest] | None = None
    extra_option_ids: list[UUID] | None = None

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return slugify(value, max_length=220)


class ProductFilterParams(BaseModel):
    category: str | None = None
    category_id: UUID | None = None
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    is_available: bool | None = None
    is_featured: bool | None = None
    is_popular: bool | None = None
    is_best_seller: bool | None = None
    vegetarian: bool | None = None
    tag: ProductTag | None = None
    min_calories: int | None = Field(default=None, ge=0)
    max_calories: int | None = Field(default=None, ge=0)
    max_preparation_time: int | None = Field(default=None, ge=0)
    sort: ProductSort = ProductSort.NEWEST
    q: str | None = Field(default=None, min_length=1, max_length=200)

    @model_validator(mode="after")
    def validate_ranges(self) -> ProductFilterParams:
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            msg = "min_price cannot exceed max_price"
            raise ValueError(msg)
        if (
            self.min_calories is not None
            and self.max_calories is not None
            and self.min_calories > self.max_calories
        ):
            msg = "min_calories cannot exceed max_calories"
            raise ValueError(msg)
        return self


class ImageReorderRequest(BaseModel):
    image_ids: list[UUID] = Field(..., min_length=1)


class DealProductItem(BaseModel):
    product_id: UUID
    quantity: int = Field(default=1, ge=1)


class DealProductResponse(BaseModel):
    product_id: UUID
    quantity: int
    product_name: str | None = None
    product_slug: str | None = None

    model_config = {"from_attributes": True}


class DealResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None = None
    deal_type: DealType
    deal_price: Decimal
    discount_percent: Decimal | None = None
    image_url: str | None = None
    is_active: bool
    is_visible: bool
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    products: list[DealProductResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DealCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    slug: str | None = Field(default=None, min_length=2, max_length=220)
    description: str | None = None
    deal_type: DealType
    deal_price: Decimal = Field(..., ge=0)
    discount_percent: Decimal | None = Field(default=None, ge=0, le=100)
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool = True
    is_visible: bool = True
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    products: list[DealProductItem] = Field(default_factory=list)

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return slugify(value, max_length=220)

    @model_validator(mode="after")
    def validate_window(self) -> DealCreateRequest:
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            msg = "ends_at must be greater than or equal to starts_at"
            raise ValueError(msg)
        return self


class DealUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    slug: str | None = Field(default=None, min_length=2, max_length=220)
    description: str | None = None
    deal_type: DealType | None = None
    deal_price: Decimal | None = Field(default=None, ge=0)
    discount_percent: Decimal | None = Field(default=None, ge=0, le=100)
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None
    is_visible: bool | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    products: list[DealProductItem] | None = None

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return slugify(value, max_length=220)
