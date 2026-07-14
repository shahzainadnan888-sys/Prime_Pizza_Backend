"""Template package exports."""

from app.emails.templates.future_customer import (
    render_order_cancelled,
    render_order_confirmation,
    render_order_delivered,
)
from app.emails.templates.owner_new_order import render_owner_new_order
from app.emails.templates.owner_test import render_owner_test

__all__ = [
    "render_order_cancelled",
    "render_order_confirmation",
    "render_order_delivered",
    "render_owner_new_order",
    "render_owner_test",
]
