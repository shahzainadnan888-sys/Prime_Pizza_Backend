"""cart_wishlist_checkout_preparation

Revision ID: 89e7910d3eed
Revises: cb465f3c33d6
Create Date: 2026-07-13 23:48:00.421213
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "89e7910d3eed"
down_revision: str | None = "cb465f3c33d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

cart_status_enum = postgresql.ENUM(
    "active",
    "checkout_ready",
    "abandoned",
    "converted",
    name="cart_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    cart_status_enum.create(bind, checkfirst=True)

    op.add_column("cart_items", sa.Column("discount_price", sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column("cart_items", sa.Column("special_instructions", sa.String(length=500), nullable=True))
    op.execute(sa.text("UPDATE cart_items SET special_instructions = notes WHERE notes IS NOT NULL"))
    op.drop_column("cart_items", "notes")
    op.create_check_constraint(
        "ck_cart_items_discount_price_non_negative",
        "cart_items",
        "discount_price IS NULL OR discount_price >= 0",
    )

    op.add_column(
        "carts",
        sa.Column("status", cart_status_enum, server_default="active", nullable=False),
    )
    op.add_column("carts", sa.Column("currency", sa.String(length=10), server_default="PKR", nullable=False))
    op.add_column("carts", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("carts", sa.Column("last_activity", sa.DateTime(timezone=True), nullable=True))
    op.add_column("carts", sa.Column("coupon_id", sa.UUID(), nullable=True))
    op.add_column(
        "carts",
        sa.Column("subtotal", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False),
    )
    op.add_column(
        "carts",
        sa.Column("discount", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False),
    )
    op.add_column(
        "carts",
        sa.Column("delivery_fee", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False),
    )
    op.add_column(
        "carts",
        sa.Column("tax", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False),
    )
    op.add_column(
        "carts",
        sa.Column("grand_total", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False),
    )
    op.create_index("ix_carts_coupon_id", "carts", ["coupon_id"], unique=False)
    op.create_index("ix_carts_status", "carts", ["status"], unique=False)
    op.create_foreign_key(
        "fk_carts_coupon_id_coupons",
        "carts",
        "coupons",
        ["coupon_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_check_constraint("ck_carts_subtotal_non_negative", "carts", "subtotal >= 0")
    op.create_check_constraint("ck_carts_discount_non_negative", "carts", "discount >= 0")
    op.create_check_constraint("ck_carts_delivery_fee_non_negative", "carts", "delivery_fee >= 0")
    op.create_check_constraint("ck_carts_tax_non_negative", "carts", "tax >= 0")
    op.create_check_constraint("ck_carts_grand_total_non_negative", "carts", "grand_total >= 0")


def downgrade() -> None:
    op.drop_constraint("ck_carts_grand_total_non_negative", "carts", type_="check")
    op.drop_constraint("ck_carts_tax_non_negative", "carts", type_="check")
    op.drop_constraint("ck_carts_delivery_fee_non_negative", "carts", type_="check")
    op.drop_constraint("ck_carts_discount_non_negative", "carts", type_="check")
    op.drop_constraint("ck_carts_subtotal_non_negative", "carts", type_="check")
    op.drop_constraint("fk_carts_coupon_id_coupons", "carts", type_="foreignkey")
    op.drop_index("ix_carts_status", table_name="carts")
    op.drop_index("ix_carts_coupon_id", table_name="carts")
    op.drop_column("carts", "grand_total")
    op.drop_column("carts", "tax")
    op.drop_column("carts", "delivery_fee")
    op.drop_column("carts", "discount")
    op.drop_column("carts", "subtotal")
    op.drop_column("carts", "coupon_id")
    op.drop_column("carts", "last_activity")
    op.drop_column("carts", "notes")
    op.drop_column("carts", "currency")
    op.drop_column("carts", "status")

    op.drop_constraint("ck_cart_items_discount_price_non_negative", "cart_items", type_="check")
    op.add_column("cart_items", sa.Column("notes", sa.VARCHAR(length=500), autoincrement=False, nullable=True))
    op.execute(sa.text("UPDATE cart_items SET notes = special_instructions WHERE special_instructions IS NOT NULL"))
    op.drop_column("cart_items", "special_instructions")
    op.drop_column("cart_items", "discount_price")

    cart_status_enum.drop(op.get_bind(), checkfirst=True)
