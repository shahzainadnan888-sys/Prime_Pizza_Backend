"""order_management_checkout_timeline

Revision ID: 48fcbb9cf907
Revises: 89e7910d3eed
Create Date: 2026-07-13 23:58:07.350209
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "48fcbb9cf907"
down_revision: str | None = "89e7910d3eed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

order_status_enum = postgresql.ENUM(
    "pending",
    "confirmed",
    "preparing",
    "ready",
    "out_for_delivery",
    "delivered",
    "cancelled",
    "refunded",
    name="order_status",
    create_type=False,
)


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE order_status ADD VALUE IF NOT EXISTS 'ready'")
        op.execute("ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'cancelled'")

    op.create_table(
        "order_number_sequences",
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("last_value", sa.Integer(), server_default="0", nullable=False),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_order_number_sequences_created_at"),
        "order_number_sequences",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_order_number_sequences_deleted_at"),
        "order_number_sequences",
        ["deleted_at"],
        unique=False,
    )
    op.create_index("uq_order_number_sequences_year", "order_number_sequences", ["year"], unique=True)

    op.create_table(
        "order_timeline_events",
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("status", order_status_enum, nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("performed_by", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_timeline_events_created_at", "order_timeline_events", ["created_at"], unique=False)
    op.create_index(
        op.f("ix_order_timeline_events_deleted_at"),
        "order_timeline_events",
        ["deleted_at"],
        unique=False,
    )
    op.create_index("ix_order_timeline_events_order_id", "order_timeline_events", ["order_id"], unique=False)
    op.create_index("ix_order_timeline_events_status", "order_timeline_events", ["status"], unique=False)

    op.add_column("order_items", sa.Column("image_url", sa.String(length=500), nullable=True))
    op.add_column("order_items", sa.Column("discount_price", sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column("order_items", sa.Column("preparation_time_minutes", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "ck_order_items_discount_price_non_negative",
        "order_items",
        "discount_price IS NULL OR discount_price >= 0",
    )

    op.add_column("orders", sa.Column("currency", sa.String(length=10), server_default="PKR", nullable=False))
    op.add_column("orders", sa.Column("kitchen_notes", sa.Text(), nullable=True))
    op.add_column("orders", sa.Column("internal_notes", sa.Text(), nullable=True))
    op.add_column("orders", sa.Column("estimated_preparation_minutes", sa.Integer(), nullable=True))
    op.add_column("orders", sa.Column("coupon_code", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "coupon_code")
    op.drop_column("orders", "estimated_preparation_minutes")
    op.drop_column("orders", "internal_notes")
    op.drop_column("orders", "kitchen_notes")
    op.drop_column("orders", "currency")

    op.drop_constraint("ck_order_items_discount_price_non_negative", "order_items", type_="check")
    op.drop_column("order_items", "preparation_time_minutes")
    op.drop_column("order_items", "discount_price")
    op.drop_column("order_items", "image_url")

    op.drop_index("ix_order_timeline_events_status", table_name="order_timeline_events")
    op.drop_index("ix_order_timeline_events_order_id", table_name="order_timeline_events")
    op.drop_index(op.f("ix_order_timeline_events_deleted_at"), table_name="order_timeline_events")
    op.drop_index("ix_order_timeline_events_created_at", table_name="order_timeline_events")
    op.drop_table("order_timeline_events")

    op.drop_index("uq_order_number_sequences_year", table_name="order_number_sequences")
    op.drop_index(op.f("ix_order_number_sequences_deleted_at"), table_name="order_number_sequences")
    op.drop_index(op.f("ix_order_number_sequences_created_at"), table_name="order_number_sequences")
    op.drop_table("order_number_sequences")
