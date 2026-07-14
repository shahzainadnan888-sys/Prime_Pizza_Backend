"""SQLAlchemy Enum column helpers for PostgreSQL."""

from __future__ import annotations

from enum import Enum
from typing import Any, TypeVar

from sqlalchemy import Enum as SAEnum

EnumT = TypeVar("EnumT", bound=Enum)


def pg_enum(enum_cls: type[EnumT], *, name: str, create_type: bool = True) -> SAEnum:
    """Create a PostgreSQL-native enum column type from a StrEnum."""
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=True,
        create_type=create_type,
        values_callable=lambda members: [member.value for member in members],
        validate_strings=True,
    )


def money_column_kwargs() -> dict[str, Any]:
    """Shared kwargs documentation helper for monetary Numeric columns."""
    return {"precision": 12, "scale": 2}
