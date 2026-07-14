"""Unit tests for ORM model metadata registration."""

from __future__ import annotations

import app.models  # noqa: F401 — register all models on Base.metadata
from app.database.base import Base

EXPECTED_TABLES = {
    "users",
    "addresses",
    "categories",
    "products",
    "product_images",
    "product_variants",
    "variant_options",
    "product_options",
    "deals",
    "deal_products",
    "carts",
    "cart_items",
    "cart_item_extras",
    "wishlists",
    "wishlist_items",
    "orders",
    "order_items",
    "order_item_extras",
    "order_timeline_events",
    "order_number_sequences",
    "coupons",
    "coupon_usages",
    "notifications",
    "user_preferences",
    "otp_logs",
    "audit_logs",
    "system_settings",
    "email_logs",
}


def test_all_domain_tables_registered() -> None:
    assert set(Base.metadata.tables.keys()) == EXPECTED_TABLES


def test_user_has_soft_delete_and_version() -> None:
    table = Base.metadata.tables["users"]
    assert "deleted_at" in table.c
    assert "version" in table.c
    assert "created_by" in table.c
    assert "phone_number" in table.c
    assert "avatar_public_id" in table.c


def test_address_has_delivery_fields() -> None:
    table = Base.metadata.tables["addresses"]
    assert "recipient_name" in table.c
    assert "phone_number" in table.c
    assert "area" in table.c
    assert "delivery_notes" in table.c
    assert "notes" not in table.c


def test_user_preferences_table_shape() -> None:
    table = Base.metadata.tables["user_preferences"]
    assert "dark_mode" in table.c
    assert "preferred_currency" in table.c
    assert "preferred_timezone" in table.c


def test_product_catalog_extensions() -> None:
    products = Base.metadata.tables["products"]
    assert "short_description" in products.c
    assert "stock_status" in products.c
    assert "is_best_seller" in products.c
    assert "tags" in products.c
    assert "seo_title" in products.c

    images = Base.metadata.tables["product_images"]
    assert "public_id" in images.c

    variants = Base.metadata.tables["product_variants"]
    assert "discount_price" in variants.c
    assert "preparation_time_minutes" in variants.c

    deals = Base.metadata.tables["deals"]
    assert "is_visible" in deals.c
    assert "discount_percent" in deals.c


def test_cart_checkout_preparation_columns() -> None:
    carts = Base.metadata.tables["carts"]
    assert "status" in carts.c
    assert "currency" in carts.c
    assert "coupon_id" in carts.c
    assert "subtotal" in carts.c
    assert "grand_total" in carts.c
    assert "last_activity" in carts.c

    items = Base.metadata.tables["cart_items"]
    assert "discount_price" in items.c
    assert "special_instructions" in items.c
    assert "notes" not in items.c


def test_order_management_tables() -> None:
    assert "order_timeline_events" in Base.metadata.tables
    assert "order_number_sequences" in Base.metadata.tables
    orders = Base.metadata.tables["orders"]
    assert "kitchen_notes" in orders.c
    assert "internal_notes" in orders.c
    assert "coupon_code" in orders.c
    assert "estimated_preparation_minutes" in orders.c
    items = Base.metadata.tables["order_items"]
    assert "image_url" in items.c
    assert "discount_price" in items.c
    assert "preparation_time_minutes" in items.c


def test_email_logs_table() -> None:
    table = Base.metadata.tables["email_logs"]
    assert "recipient" in table.c
    assert "subject" in table.c
    assert "template_key" in table.c
    assert "status" in table.c
    assert "retry_count" in table.c
    assert "failure_reason" in table.c
    assert "sent_at" in table.c
    assert "order_id" in table.c


def test_order_item_has_snapshot_columns() -> None:
    table = Base.metadata.tables["order_items"]
    assert "product_name" in table.c
    assert "product_snapshot" in table.c
    assert "extras_snapshot" in table.c
