"""Catalog models: categories, products, images, variants, and options."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import StockStatus, VariantOptionType, VariantSize
from app.database.types import pg_enum
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.deal import DealProduct


class Category(BaseModel):
    """Menu category."""

    __tablename__ = "categories"
    __table_args__ = (
        Index(
            "uq_categories_slug_active",
            "slug",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_categories_display_order", "display_order"),
        Index("ix_categories_is_visible", "is_visible"),
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_public_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    seo_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    seo_keywords: Mapped[str | None] = mapped_column(String(500), nullable=True)

    products: Mapped[list[Product]] = relationship(
        back_populates="category",
        passive_deletes=True,
    )


class Product(BaseModel):
    """Sellable menu product."""

    __tablename__ = "products"
    __table_args__ = (
        Index(
            "uq_products_slug_active",
            "slug",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_products_category_id", "category_id"),
        Index("ix_products_is_available", "is_available"),
        Index("ix_products_is_featured", "is_featured"),
        Index("ix_products_is_popular", "is_popular"),
        Index("ix_products_is_best_seller", "is_best_seller"),
        Index("ix_products_is_visible", "is_visible"),
        Index("ix_products_sort_order", "sort_order"),
        Index("ix_products_stock_status", "stock_status"),
        Index("ix_products_tags", "tags", postgresql_using="gin"),
        Index(
            "ix_products_visible_featured_sort",
            "is_visible",
            "is_featured",
            "sort_order",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "ix_products_visible_popular",
            "is_visible",
            "is_popular",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        CheckConstraint("base_price >= 0", name="ck_products_base_price_non_negative"),
        CheckConstraint(
            "discount_price IS NULL OR discount_price >= 0",
            name="ck_products_discount_price_non_negative",
        ),
        CheckConstraint(
            "discount_price IS NULL OR discount_price <= base_price",
            name="ck_products_discount_lte_base",
        ),
        CheckConstraint(
            "preparation_time_minutes IS NULL OR preparation_time_minutes >= 0",
            name="ck_products_prep_time_non_negative",
        ),
        CheckConstraint(
            "calories IS NULL OR calories >= 0",
            name="ck_products_calories_non_negative",
        ),
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(220), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    base_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_public_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    stock_status: Mapped[StockStatus] = mapped_column(
        pg_enum(StockStatus, name="stock_status"),
        nullable=False,
        default=StockStatus.IN_STOCK,
        server_default=StockStatus.IN_STOCK.value,
    )
    preparation_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_popular: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_best_seller: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)),
        nullable=False,
        server_default=text("'{}'"),
    )
    seo_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    seo_keywords: Mapped[str | None] = mapped_column(String(500), nullable=True)

    category: Mapped[Category] = relationship(back_populates="products")
    images: Mapped[list[ProductImage]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ProductImage.display_order",
    )
    variants: Mapped[list[ProductVariant]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    available_options: Mapped[list[ProductOption]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    deal_products: Mapped[list[DealProduct]] = relationship(
        back_populates="product",
        passive_deletes=True,
    )


class ProductImage(BaseModel):
    """Additional product gallery images."""

    __tablename__ = "product_images"
    __table_args__ = (
        Index("ix_product_images_product_id", "product_id"),
        Index(
            "uq_product_images_primary",
            "product_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL AND is_primary IS TRUE"),
        ),
        Index(
            "uq_product_images_product_order_active",
            "product_id",
            "display_order",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "uq_product_images_public_id_active",
            "public_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL AND public_id IS NOT NULL"),
        ),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    public_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    product: Mapped[Product] = relationship(back_populates="images")


class ProductVariant(BaseModel):
    """Size / portion variant with custom pricing."""

    __tablename__ = "product_variants"
    __table_args__ = (
        Index("ix_product_variants_product_id", "product_id"),
        Index(
            "uq_product_variants_product_size_active",
            "product_id",
            "size",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        CheckConstraint("price >= 0", name="ck_product_variants_price_non_negative"),
        CheckConstraint(
            "discount_price IS NULL OR discount_price >= 0",
            name="ck_product_variants_discount_non_negative",
        ),
        CheckConstraint(
            "discount_price IS NULL OR discount_price <= price",
            name="ck_product_variants_discount_lte_price",
        ),
        CheckConstraint(
            "preparation_time_minutes IS NULL OR preparation_time_minutes >= 0",
            name="ck_product_variants_prep_time_non_negative",
        ),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    size: Mapped[VariantSize] = mapped_column(pg_enum(VariantSize, name="variant_size"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    preparation_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    product: Mapped[Product] = relationship(back_populates="variants")


class VariantOption(BaseModel):
    """Global catalog of toppings, sauces, crusts, and extras."""

    __tablename__ = "variant_options"
    __table_args__ = (
        Index(
            "uq_variant_options_slug_active",
            "slug",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_variant_options_option_type", "option_type"),
        CheckConstraint("price >= 0", name="ck_variant_options_price_non_negative"),
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), nullable=False)
    option_type: Mapped[VariantOptionType] = mapped_column(
        pg_enum(VariantOptionType, name="variant_option_type"),
        nullable=False,
        default=VariantOptionType.TOPPING,
        server_default=VariantOptionType.TOPPING.value,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    product_links: Mapped[list[ProductOption]] = relationship(
        back_populates="option",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ProductOption(BaseModel):
    """Which variant options are available for a given product."""

    __tablename__ = "product_options"
    __table_args__ = (
        Index(
            "uq_product_options_product_option_active",
            "product_id",
            "option_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_product_options_product_id", "product_id"),
        Index("ix_product_options_option_id", "option_id"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    option_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("variant_options.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    product: Mapped[Product] = relationship(back_populates="available_options")
    option: Mapped[VariantOption] = relationship(back_populates="product_links")
