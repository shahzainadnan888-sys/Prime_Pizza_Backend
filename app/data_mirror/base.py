"""Base JSON mirror contract — implementation deferred to auth/user phases."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseJsonMirror(ABC):
    """
    Dual-write helper contract.

    Future flow after a successful PostgreSQL write:
      1. Persist entity in Postgres (source of truth)
      2. Call `upsert()` / `remove()` to mirror into `data/*.json`
      3. Failures in the mirror layer must be logged, not silently ignored
    """

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("[]\n", encoding="utf-8")

    def read_all(self) -> list[dict[str, Any]]:
        raw = self.file_path.read_text(encoding="utf-8").strip() or "[]"
        data = json.loads(raw)
        if not isinstance(data, list):
            msg = f"Expected a JSON array in {self.file_path}"
            raise TypeError(msg)
        return data

    def write_all(self, rows: list[dict[str, Any]]) -> None:
        self.file_path.write_text(
            json.dumps(rows, indent=2, ensure_ascii=False, default=str) + "\n",
            encoding="utf-8",
        )

    @abstractmethod
    def serialize(self, entity: Any) -> dict[str, Any]:
        """Convert an ORM entity into a JSON-safe dict."""

    @abstractmethod
    async def upsert(self, entity: Any) -> None:
        """Insert or replace a mirrored row — implement in a later phase."""

    @abstractmethod
    async def remove(self, entity_id: str) -> None:
        """Remove a mirrored row — implement in a later phase."""
