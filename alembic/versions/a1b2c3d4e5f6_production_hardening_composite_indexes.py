"""production_hardening_composite_indexes

Revision ID: a1b2c3d4e5f6
Revises: d789ba8517ef
Create Date: 2026-07-14 00:40:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "d789ba8517ef"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_orders_user_created",
        "orders",
        ["user_id", "created_at"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_orders_status_created",
        "orders",
        ["status", "created_at"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_notifications_user_created",
        "notifications",
        ["user_id", "created_at"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_products_visible_featured_sort",
        "products",
        ["is_visible", "is_featured", "sort_order"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_products_visible_popular",
        "products",
        ["is_visible", "is_popular"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_products_visible_popular", table_name="products")
    op.drop_index("ix_products_visible_featured_sort", table_name="products")
    op.drop_index("ix_notifications_user_created", table_name="notifications")
    op.drop_index("ix_orders_status_created", table_name="orders")
    op.drop_index("ix_orders_user_created", table_name="orders")
