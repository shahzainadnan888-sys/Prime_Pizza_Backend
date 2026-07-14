"""user_module_profile_addresses_preferences

Revision ID: 6335ba01e31c
Revises: 7e1e98e95ace
Create Date: 2026-07-13 22:32:38.456978
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "6335ba01e31c"
down_revision: str | None = "7e1e98e95ace"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_preferences",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("dark_mode", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("language", sa.String(length=10), server_default="en", nullable=False),
        sa.Column("marketing_emails", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("marketing_sms", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("push_notifications", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("order_updates", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("promotional_notifications", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("preferred_currency", sa.String(length=10), server_default="PKR", nullable=False),
        sa.Column("preferred_timezone", sa.String(length=64), server_default="Asia/Karachi", nullable=False),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_preferences_created_at"), "user_preferences", ["created_at"], unique=False)
    op.create_index(op.f("ix_user_preferences_deleted_at"), "user_preferences", ["deleted_at"], unique=False)
    op.create_index(
        "uq_user_preferences_user_active",
        "user_preferences",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # Preserve channel flags from the legacy notification_preferences table.
    op.execute(
        sa.text(
            """
            INSERT INTO user_preferences (
                user_id,
                marketing_emails,
                marketing_sms,
                push_notifications,
                promotional_notifications,
                id,
                created_at,
                updated_at,
                deleted_at,
                created_by,
                updated_by,
                version
            )
            SELECT
                user_id,
                email_enabled,
                sms_enabled,
                push_enabled,
                marketing_enabled,
                id,
                created_at,
                updated_at,
                deleted_at,
                created_by,
                updated_by,
                version
            FROM notification_preferences
            """
        )
    )

    op.drop_index(
        op.f("ix_notification_preferences_created_at"),
        table_name="notification_preferences",
    )
    op.drop_index(
        op.f("ix_notification_preferences_deleted_at"),
        table_name="notification_preferences",
    )
    op.drop_index(
        op.f("uq_notification_preferences_user_active"),
        table_name="notification_preferences",
        postgresql_where="(deleted_at IS NULL)",
    )
    op.drop_table("notification_preferences")

    op.add_column(
        "addresses",
        sa.Column("recipient_name", sa.String(length=150), server_default="", nullable=False),
    )
    op.add_column(
        "addresses",
        sa.Column("phone_number", sa.String(length=20), server_default="", nullable=False),
    )
    op.add_column("addresses", sa.Column("area", sa.String(length=150), nullable=True))
    op.add_column("addresses", sa.Column("delivery_notes", sa.Text(), nullable=True))
    op.execute(sa.text("UPDATE addresses SET delivery_notes = notes WHERE notes IS NOT NULL"))
    op.drop_column("addresses", "notes")

    op.add_column("users", sa.Column("avatar_public_id", sa.String(length=255), nullable=True))
    op.create_index("ix_users_full_name", "users", ["full_name"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_full_name", table_name="users")
    op.drop_column("users", "avatar_public_id")

    op.add_column("addresses", sa.Column("notes", sa.TEXT(), autoincrement=False, nullable=True))
    op.execute(sa.text("UPDATE addresses SET notes = delivery_notes WHERE delivery_notes IS NOT NULL"))
    op.drop_column("addresses", "delivery_notes")
    op.drop_column("addresses", "area")
    op.drop_column("addresses", "phone_number")
    op.drop_column("addresses", "recipient_name")

    op.create_table(
        "notification_preferences",
        sa.Column("user_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("sms_enabled", sa.BOOLEAN(), server_default=sa.text("true"), autoincrement=False, nullable=False),
        sa.Column("email_enabled", sa.BOOLEAN(), server_default=sa.text("true"), autoincrement=False, nullable=False),
        sa.Column("push_enabled", sa.BOOLEAN(), server_default=sa.text("true"), autoincrement=False, nullable=False),
        sa.Column(
            "marketing_enabled",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), autoincrement=False, nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("deleted_at", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
        sa.Column("created_by", sa.UUID(), autoincrement=False, nullable=True),
        sa.Column("updated_by", sa.UUID(), autoincrement=False, nullable=True),
        sa.Column("version", sa.INTEGER(), server_default=sa.text("1"), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("notification_preferences_user_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("notification_preferences_pkey")),
    )
    op.create_index(
        op.f("uq_notification_preferences_user_active"),
        "notification_preferences",
        ["user_id"],
        unique=True,
        postgresql_where="(deleted_at IS NULL)",
    )
    op.create_index(
        op.f("ix_notification_preferences_deleted_at"),
        "notification_preferences",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_preferences_created_at"),
        "notification_preferences",
        ["created_at"],
        unique=False,
    )

    op.execute(
        sa.text(
            """
            INSERT INTO notification_preferences (
                user_id,
                sms_enabled,
                email_enabled,
                push_enabled,
                marketing_enabled,
                id,
                created_at,
                updated_at,
                deleted_at,
                created_by,
                updated_by,
                version
            )
            SELECT
                user_id,
                marketing_sms,
                marketing_emails,
                push_notifications,
                promotional_notifications,
                id,
                created_at,
                updated_at,
                deleted_at,
                created_by,
                updated_by,
                version
            FROM user_preferences
            """
        )
    )

    op.drop_index(
        "uq_user_preferences_user_active",
        table_name="user_preferences",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_index(op.f("ix_user_preferences_deleted_at"), table_name="user_preferences")
    op.drop_index(op.f("ix_user_preferences_created_at"), table_name="user_preferences")
    op.drop_table("user_preferences")
