"""product_module_catalog_extensions

Revision ID: cb465f3c33d6
Revises: 6335ba01e31c
Create Date: 2026-07-13 23:19:48.805843
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "cb465f3c33d6"
down_revision: str | None = "6335ba01e31c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

stock_status_enum = postgresql.ENUM(
    "in_stock",
    "out_of_stock",
    "limited",
    name="stock_status",
    create_type=False,
)


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE deal_type ADD VALUE IF NOT EXISTS 'weekend'")
        op.execute("ALTER TYPE deal_type ADD VALUE IF NOT EXISTS 'festival'")

    bind = op.get_bind()
    stock_status_enum.create(bind, checkfirst=True)

    op.add_column("categories", sa.Column("image_public_id", sa.String(length=255), nullable=True))
    op.add_column("categories", sa.Column("seo_title", sa.String(length=200), nullable=True))
    op.add_column("categories", sa.Column("seo_description", sa.String(length=500), nullable=True))
    op.add_column("categories", sa.Column("seo_keywords", sa.String(length=500), nullable=True))

    op.add_column("deals", sa.Column("discount_percent", sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column("deals", sa.Column("image_public_id", sa.String(length=255), nullable=True))
    op.add_column(
        "deals",
        sa.Column("is_visible", sa.Boolean(), server_default="true", nullable=False),
    )
    op.create_index("ix_deals_is_visible", "deals", ["is_visible"], unique=False)
    op.create_check_constraint(
        "ck_deals_discount_percent_range",
        "deals",
        "discount_percent IS NULL OR (discount_percent >= 0 AND discount_percent <= 100)",
    )

    op.add_column("product_images", sa.Column("public_id", sa.String(length=255), nullable=True))
    op.create_index(
        "uq_product_images_public_id_active",
        "product_images",
        ["public_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND public_id IS NOT NULL"),
    )

    op.add_column(
        "product_variants",
        sa.Column("discount_price", sa.Numeric(precision=12, scale=2), nullable=True),
    )
    op.add_column("product_variants", sa.Column("preparation_time_minutes", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "ck_product_variants_discount_non_negative",
        "product_variants",
        "discount_price IS NULL OR discount_price >= 0",
    )
    op.create_check_constraint(
        "ck_product_variants_discount_lte_price",
        "product_variants",
        "discount_price IS NULL OR discount_price <= price",
    )
    op.create_check_constraint(
        "ck_product_variants_prep_time_non_negative",
        "product_variants",
        "preparation_time_minutes IS NULL OR preparation_time_minutes >= 0",
    )

    op.add_column("products", sa.Column("short_description", sa.String(length=500), nullable=True))
    op.add_column("products", sa.Column("image_public_id", sa.String(length=255), nullable=True))
    op.add_column(
        "products",
        sa.Column(
            "stock_status",
            stock_status_enum,
            server_default="in_stock",
            nullable=False,
        ),
    )
    op.add_column(
        "products",
        sa.Column("is_best_seller", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "products",
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "products",
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.String(length=50)),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
    )
    op.add_column("products", sa.Column("seo_title", sa.String(length=200), nullable=True))
    op.add_column("products", sa.Column("seo_description", sa.String(length=500), nullable=True))
    op.add_column("products", sa.Column("seo_keywords", sa.String(length=500), nullable=True))
    op.create_index("ix_products_is_best_seller", "products", ["is_best_seller"], unique=False)
    op.create_index("ix_products_sort_order", "products", ["sort_order"], unique=False)
    op.create_index("ix_products_stock_status", "products", ["stock_status"], unique=False)
    op.create_index("ix_products_tags", "products", ["tags"], unique=False, postgresql_using="gin")


def downgrade() -> None:
    op.drop_index("ix_products_tags", table_name="products", postgresql_using="gin")
    op.drop_index("ix_products_stock_status", table_name="products")
    op.drop_index("ix_products_sort_order", table_name="products")
    op.drop_index("ix_products_is_best_seller", table_name="products")
    op.drop_column("products", "seo_keywords")
    op.drop_column("products", "seo_description")
    op.drop_column("products", "seo_title")
    op.drop_column("products", "tags")
    op.drop_column("products", "sort_order")
    op.drop_column("products", "is_best_seller")
    op.drop_column("products", "stock_status")
    op.drop_column("products", "image_public_id")
    op.drop_column("products", "short_description")

    op.drop_constraint("ck_product_variants_prep_time_non_negative", "product_variants", type_="check")
    op.drop_constraint("ck_product_variants_discount_lte_price", "product_variants", type_="check")
    op.drop_constraint("ck_product_variants_discount_non_negative", "product_variants", type_="check")
    op.drop_column("product_variants", "preparation_time_minutes")
    op.drop_column("product_variants", "discount_price")

    op.drop_index(
        "uq_product_images_public_id_active",
        table_name="product_images",
        postgresql_where=sa.text("deleted_at IS NULL AND public_id IS NOT NULL"),
    )
    op.drop_column("product_images", "public_id")

    op.drop_constraint("ck_deals_discount_percent_range", "deals", type_="check")
    op.drop_index("ix_deals_is_visible", table_name="deals")
    op.drop_column("deals", "is_visible")
    op.drop_column("deals", "image_public_id")
    op.drop_column("deals", "discount_percent")

    op.drop_column("categories", "seo_keywords")
    op.drop_column("categories", "seo_description")
    op.drop_column("categories", "seo_title")
    op.drop_column("categories", "image_public_id")

    stock_status_enum.drop(op.get_bind(), checkfirst=True)
