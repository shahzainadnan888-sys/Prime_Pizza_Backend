"""Unit tests for order number formatting and status titles."""

from __future__ import annotations

from app.common.enums import OrderStatus, PaymentStatus
from app.services.order import ALLOWED_STATUS_TRANSITIONS, STATUS_TITLES


def test_order_status_includes_ready() -> None:
    assert OrderStatus.READY.value == "ready"
    assert "ready" in {s.value for s in OrderStatus}


def test_payment_status_includes_cancelled() -> None:
    assert PaymentStatus.CANCELLED.value == "cancelled"


def test_timeline_titles_cover_statuses() -> None:
    for status in OrderStatus:
        assert status in STATUS_TITLES
        assert STATUS_TITLES[status]


def test_status_transition_graph_is_acyclic_for_happy_path() -> None:
    assert OrderStatus.CONFIRMED in ALLOWED_STATUS_TRANSITIONS[OrderStatus.PENDING]
    assert OrderStatus.PREPARING in ALLOWED_STATUS_TRANSITIONS[OrderStatus.CONFIRMED]
    assert OrderStatus.READY in ALLOWED_STATUS_TRANSITIONS[OrderStatus.PREPARING]
    assert OrderStatus.OUT_FOR_DELIVERY in ALLOWED_STATUS_TRANSITIONS[OrderStatus.READY]
    assert OrderStatus.DELIVERED in ALLOWED_STATUS_TRANSITIONS[OrderStatus.OUT_FOR_DELIVERY]
    assert ALLOWED_STATUS_TRANSITIONS[OrderStatus.REFUNDED] == set()
    assert OrderStatus.DELIVERED not in ALLOWED_STATUS_TRANSITIONS[OrderStatus.PENDING]
