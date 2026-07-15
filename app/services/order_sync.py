"""Order synchronization between PostgreSQL and order.json."""

from __future__ import annotations

from loguru import logger

from app.data_mirror.orders import OrdersJsonMirror
from app.models.order import Order
from app.services.base import BaseService


class OrderSyncService(BaseService):
    """Keep `data/order.json` synchronized after Postgres order writes."""

    service_name = "order_sync"

    def __init__(self, mirror: OrdersJsonMirror | None = None) -> None:
        self._mirror = mirror or OrdersJsonMirror()

    async def sync_order(self, order: Order) -> None:
        await self._mirror.upsert(order)
        self.log_info(
            "Order sync completed | order_id={} | order_number={}",
            order.id,
            order.order_number,
        )

    async def sync_order_best_effort(self, order: Order) -> None:
        """Sync without failing the HTTP response. Postgres remains source of truth."""
        try:
            await self.sync_order(order)
        except Exception:
            logger.exception(
                "Order JSON mirror failed after Postgres commit | order_id={}",
                order.id,
            )
