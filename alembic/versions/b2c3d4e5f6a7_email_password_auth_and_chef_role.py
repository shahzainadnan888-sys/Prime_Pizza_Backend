"""email_password_auth_and_chef_role

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-15 02:30:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# bcrypt hash of a random impossible password (placeholder for legacy rows)
_PLACEHOLDER_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G2oQzqKxqKxqKx"


def upgrade() -> None:
    # Rename owner → chef in PostgreSQL enum
    op.execute("ALTER TYPE user_role RENAME VALUE 'owner' TO 'chef'")

    op.add_column("users", sa.Column("first_name", sa.String(length=80), server_default="", nullable=False))
    op.add_column("users", sa.Column("last_name", sa.String(length=80), server_default="", nullable=False))
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))

    # Backfill names from full_name
    op.execute(
        """
        UPDATE users
        SET first_name = COALESCE(NULLIF(split_part(full_name, ' ', 1), ''), 'User'),
            last_name = COALESCE(
                NULLIF(substring(full_name from position(' ' in full_name) + 1), ''),
                ''
            )
        WHERE coalesce(first_name, '') = ''
        """
    )

    # Placeholder hash for any legacy OTP-era rows without passwords
    op.execute(f"UPDATE users SET password_hash = '{_PLACEHOLDER_HASH}' WHERE password_hash IS NULL")
    op.alter_column("users", "password_hash", nullable=False)

    # Email required — synthesize unique emails for orphan phone-only rows
    op.execute(
        """
        UPDATE users
        SET email = lower(concat('legacy+', replace(id::text, '-', ''), '@primepizza.local'))
        WHERE email IS NULL OR btrim(email) = ''
        """
    )
    op.alter_column("users", "email", existing_type=sa.String(length=255), nullable=False)

    # Phone optional
    op.alter_column("users", "phone_number", existing_type=sa.String(length=20), nullable=True)

    # Rebuild unique indexes for new nullability / email rules
    op.drop_index("uq_users_phone_active", table_name="users")
    op.drop_index("uq_users_email_active", table_name="users")
    op.create_index(
        "uq_users_phone_active",
        "users",
        ["phone_number"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND phone_number IS NOT NULL"),
    )
    op.create_index(
        "uq_users_email_active",
        "users",
        ["email"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # Drop OTP audit table + enum
    op.drop_table("otp_logs")
    otp_status = postgresql.ENUM(
        "pending",
        "verified",
        "expired",
        "failed",
        name="otp_verification_status",
        create_type=False,
    )
    otp_status.drop(op.get_bind(), checkfirst=True)

    op.alter_column("users", "first_name", server_default=None)
    op.alter_column("users", "last_name", server_default=None)


def downgrade() -> None:
    otp_status = postgresql.ENUM(
        "pending",
        "verified",
        "expired",
        "failed",
        name="otp_verification_status",
    )
    otp_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "otp_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("phone_number", sa.String(length=20), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "verified",
                "expired",
                "failed",
                name="otp_verification_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_sid", sa.String(length=64), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )

    op.drop_index("uq_users_email_active", table_name="users")
    op.drop_index("uq_users_phone_active", table_name="users")
    op.create_index(
        "uq_users_email_active",
        "users",
        ["email"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND email IS NOT NULL"),
    )
    op.create_index(
        "uq_users_phone_active",
        "users",
        ["phone_number"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.alter_column("users", "phone_number", existing_type=sa.String(length=20), nullable=False)
    op.alter_column("users", "email", existing_type=sa.String(length=255), nullable=True)
    op.drop_column("users", "password_hash")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")

    op.execute("ALTER TYPE user_role RENAME VALUE 'chef' TO 'owner'")
