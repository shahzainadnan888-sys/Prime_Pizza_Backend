"""order_gps_coordinates

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-16 00:10:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("latitude", sa.Numeric(10, 7), nullable=True))
    op.add_column("orders", sa.Column("longitude", sa.Numeric(10, 7), nullable=True))
    op.add_column("orders", sa.Column("gps_accuracy", sa.Numeric(10, 2), nullable=True))
    op.create_check_constraint(
        "ck_orders_latitude_range",
        "orders",
        "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
    )
    op.create_check_constraint(
        "ck_orders_longitude_range",
        "orders",
        "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
    )
    op.create_check_constraint(
        "ck_orders_gps_accuracy_non_negative",
        "orders",
        "gps_accuracy IS NULL OR gps_accuracy >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_orders_gps_accuracy_non_negative", "orders", type_="check")
    op.drop_constraint("ck_orders_longitude_range", "orders", type_="check")
    op.drop_constraint("ck_orders_latitude_range", "orders", type_="check")
    op.drop_column("orders", "gps_accuracy")
    op.drop_column("orders", "longitude")
    op.drop_column("orders", "latitude")
