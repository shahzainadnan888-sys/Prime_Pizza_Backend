"""Orders JSON mirror — dual-write companion to PostgreSQL."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

from app.data_mirror.base import BaseJsonMirror

DEFAULT_ORDERS_JSON_PATH = Path("data") / "order.json"


class OrdersJsonMirror(BaseJsonMirror):
    """
    Append/upsert order snapshots into `data/order.json` after Postgres writes.

    PostgreSQL remains the source of truth. Mirror failures are logged and
    re-raised so callers can decide whether to surface them.
    """

    def __init__(self, file_path: Path | None = None) -> None:
        super().__init__(file_path or DEFAULT_ORDERS_JSON_PATH)

    def serialize(self, entity: Any) -> dict[str, Any]:
        status = getattr(entity, "status", None)
        payment_method = getattr(entity, "payment_method", None)
        user = getattr(entity, "user", None)
        snapshot = getattr(entity, "delivery_address_snapshot", None) or {}

        customer: dict[str, Any]
        if user is not None:
            customer = {
                "id": str(getattr(user, "id", "")),
                "name": getattr(user, "full_name", None)
                or " ".join(
                    filter(
                        None,
                        [
                            getattr(user, "first_name", None),
                            getattr(user, "last_name", None),
                        ],
                    )
                ).strip()
                or None,
                "email": getattr(user, "email", None),
                "phone_number": getattr(user, "phone_number", None),
            }
        else:
            customer = {
                "id": str(getattr(entity, "user_id", "")),
                "name": snapshot.get("recipient_name"),
                "email": snapshot.get("email"),
                "phone_number": snapshot.get("phone_number"),
            }

        items: list[dict[str, Any]] = []
        for item in getattr(entity, "items", None) or []:
            if getattr(item, "deleted_at", None) is not None:
                continue
            extras = [
                {
                    "option_id": str(getattr(extra, "option_id", "")),
                    "name": getattr(extra, "option_name", None),
                    "quantity": getattr(extra, "quantity", 1),
                    "unit_price": str(getattr(extra, "unit_price", "0")),
                }
                for extra in getattr(item, "extras", None) or []
                if getattr(extra, "deleted_at", None) is None
            ]
            items.append(
                {
                    "id": str(getattr(item, "id", "")),
                    "product_id": str(getattr(item, "product_id", "")),
                    "product_name": getattr(item, "product_name", None),
                    "variant_name": getattr(item, "variant_name", None),
                    "quantity": getattr(item, "quantity", 0),
                    "unit_price": str(getattr(item, "unit_price", "0")),
                    "subtotal": str(getattr(item, "subtotal", "0")),
                    "extras": extras,
                }
            )

        return {
            "id": str(getattr(entity, "id", "")),
            "order_number": getattr(entity, "order_number", None),
            "customer": customer,
            "items": items,
            "subtotal": str(getattr(entity, "subtotal", "0")),
            "delivery_fee": str(getattr(entity, "delivery_fee", "0")),
            "tax": str(getattr(entity, "tax", "0")),
            "discount": str(getattr(entity, "discount", "0")),
            "total": str(getattr(entity, "grand_total", "0")),
            "status": getattr(status, "value", str(status) if status is not None else None),
            "payment_method": getattr(
                payment_method,
                "value",
                str(payment_method) if payment_method is not None else None,
            ),
            "payment_status": str(
                getattr(getattr(entity, "payment_status", None), "value", getattr(entity, "payment_status", None))
            ),
            "currency": getattr(entity, "currency", None),
            "notes": getattr(entity, "notes", None),
            "latitude": (
                str(getattr(entity, "latitude"))
                if getattr(entity, "latitude", None) is not None
                else snapshot.get("latitude")
            ),
            "longitude": (
                str(getattr(entity, "longitude"))
                if getattr(entity, "longitude", None) is not None
                else snapshot.get("longitude")
            ),
            "gps_accuracy": (
                str(getattr(entity, "gps_accuracy"))
                if getattr(entity, "gps_accuracy", None) is not None
                else snapshot.get("gps_accuracy")
            ),
            "delivery_address": snapshot,
            "created_at": getattr(entity, "created_at", None),
            "updated_at": getattr(entity, "updated_at", None),
        }

    async def upsert(self, entity: Any) -> None:
        try:
            rows = await self.read_all_async()
            serialized = self.serialize(entity)
            entity_id = serialized["id"]
            replaced = False
            for index, row in enumerate(rows):
                if str(row.get("id")) == entity_id:
                    rows[index] = serialized
                    replaced = True
                    break
            if not replaced:
                rows.append(serialized)
            await self.write_all_async(rows)
            logger.info(
                "Order mirrored to order.json | id={} | order_number={} | appended={}",
                entity_id,
                serialized.get("order_number"),
                not replaced,
            )
        except Exception:
            logger.exception(
                "Failed to mirror order to order.json | id={}",
                getattr(entity, "id", None),
            )
            raise

    async def remove(self, entity_id: str) -> None:
        try:
            rows = await self.read_all_async()
            filtered = [row for row in rows if str(row.get("id")) != entity_id]
            await self.write_all_async(filtered)
            logger.info("Order removed from order.json | id={}", entity_id)
        except Exception:
            logger.exception("Failed to remove order from order.json | id={}", entity_id)
            raise
