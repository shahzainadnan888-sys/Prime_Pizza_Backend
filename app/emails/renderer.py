"""Email template renderer registry — separates templates from delivery."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from loguru import logger

from app.common.enums import EmailTemplateKey
from app.core.exceptions import ValidationException
from app.emails.payloads import OrderEmailPayload, OwnerTestEmailPayload, RenderedEmail
from app.emails.templates.future_customer import (
    render_order_cancelled,
    render_order_confirmation,
    render_order_delivered,
)
from app.emails.templates.owner_new_order import render_owner_new_order
from app.emails.templates.owner_test import render_owner_test

Renderer = Callable[..., RenderedEmail]


class EmailRenderer:
    """Maps template keys to render functions (SOLID: open for extension)."""

    def __init__(self) -> None:
        self._registry: dict[EmailTemplateKey, Renderer] = {
            EmailTemplateKey.OWNER_NEW_ORDER: render_owner_new_order,
            EmailTemplateKey.OWNER_TEST: render_owner_test,
            EmailTemplateKey.ORDER_CONFIRMATION: render_order_confirmation,
            EmailTemplateKey.ORDER_CANCELLED: render_order_cancelled,
            EmailTemplateKey.ORDER_DELIVERED: render_order_delivered,
        }

    def register(self, key: EmailTemplateKey, renderer: Renderer) -> None:
        self._registry[key] = renderer

    def render(self, key: EmailTemplateKey, payload: Any) -> RenderedEmail:
        renderer = self._registry.get(key)
        if renderer is None:
            logger.error("Template errors | unknown template_key={}", key.value)
            raise ValidationException(f"Unknown email template: {key.value}")
        try:
            return renderer(payload)
        except ValidationException:
            raise
        except Exception as exc:
            logger.exception("Template errors | template_key={}", key.value)
            raise ValidationException("Email template rendering failed") from exc

    def render_owner_new_order(self, payload: OrderEmailPayload) -> RenderedEmail:
        return self.render(EmailTemplateKey.OWNER_NEW_ORDER, payload)

    def render_owner_test(self, payload: OwnerTestEmailPayload) -> RenderedEmail:
        return self.render(EmailTemplateKey.OWNER_TEST, payload)
