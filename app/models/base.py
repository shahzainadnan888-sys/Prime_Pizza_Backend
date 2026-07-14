"""Abstract ORM base model for all domain tables."""

from __future__ import annotations

from app.database.base import Base
from app.database.mixins import BaseModelMixin


class BaseModel(Base, BaseModelMixin):
    """
    Common base for every Prime Pizza domain model.

    Provides: UUID PK, timestamps, soft delete, audit actors, optimistic locking.
    """

    __abstract__ = True
