"""Future customer transactional templates — stubs only for this phase."""

from __future__ import annotations

from app.common.enums import EmailTemplateKey
from app.core.exceptions import ValidationException
from app.emails.payloads import OrderEmailPayload, RenderedEmail


def render_order_confirmation(_payload: OrderEmailPayload) -> RenderedEmail:
    raise ValidationException(
        "Order confirmation emails are prepared for a future customer-email phase",
        details={"template": EmailTemplateKey.ORDER_CONFIRMATION.value},
    )


def render_order_cancelled(_payload: OrderEmailPayload) -> RenderedEmail:
    raise ValidationException(
        "Order cancelled emails are prepared for a future customer-email phase",
        details={"template": EmailTemplateKey.ORDER_CANCELLED.value},
    )


def render_order_delivered(_payload: OrderEmailPayload) -> RenderedEmail:
    raise ValidationException(
        "Order delivered emails are prepared for a future customer-email phase",
        details={"template": EmailTemplateKey.ORDER_DELIVERED.value},
    )
