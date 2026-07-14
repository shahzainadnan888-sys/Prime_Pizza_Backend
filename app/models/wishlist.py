"""Wishlist models."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.catalog import Product
    from app.models.user import User


class Wishlist(BaseModel):
    """One wishlist per customer."""

    __tablename__ = "wishlists"
    __table_args__ = (
        Index(
            "uq_wishlists_user_active",
            "user_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_wishlists_user_id", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="wishlist")
    items: Mapped[list[WishlistItem]] = relationship(
        back_populates="wishlist",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class WishlistItem(BaseModel):
    """Product saved to a wishlist."""

    __tablename__ = "wishlist_items"
    __table_args__ = (
        Index(
            "uq_wishlist_items_wishlist_product_active",
            "wishlist_id",
            "product_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_wishlist_items_wishlist_id", "wishlist_id"),
        Index("ix_wishlist_items_product_id", "product_id"),
    )

    wishlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("wishlists.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )

    wishlist: Mapped[Wishlist] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()
