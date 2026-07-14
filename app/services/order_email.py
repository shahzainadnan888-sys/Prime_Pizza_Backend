"""Build serializable email payloads from committed order aggregates."""

from __future__ import annotations

from app.emails.payloads import OrderEmailLineExtra, OrderEmailLineItem, OrderEmailPayload
from app.models.order import Order
from app.models.user import User


def _format_address(snapshot: dict | None) -> str:
    if not snapshot:
        return "—"
    parts = [
        snapshot.get("recipient_name"),
        snapshot.get("street"),
        snapshot.get("area"),
        snapshot.get("city"),
        snapshot.get("province"),
        snapshot.get("postal_code"),
        snapshot.get("country"),
        snapshot.get("phone_number"),
        snapshot.get("delivery_notes"),
    ]
    return ", ".join(str(p) for p in parts if p)


def build_order_email_payload(
    order: Order,
    user: User,
    *,
    brand_name: str = "Prime Pizza",
    logo_url: str | None = None,
) -> OrderEmailPayload:
    """Snapshot order + customer fields for post-commit email delivery."""
    items: list[OrderEmailLineItem] = []
    for item in order.items:
        if item.deleted_at is not None:
            continue
        extras = [
            OrderEmailLineExtra(
                name=extra.option_name,
                quantity=extra.quantity,
                unit_price=extra.unit_price,
            )
            for extra in item.extras
            if extra.deleted_at is None
        ]
        items.append(
            OrderEmailLineItem(
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
                variant_name=item.variant_name,
                image_url=item.image_url,
                extras=extras,
                notes=item.notes,
            )
        )

    return OrderEmailPayload(
        order_id=order.id,
        order_number=order.order_number,
        order_created_at=order.created_at,
        customer_name=user.full_name or "Customer",
        customer_phone=user.phone_number,
        customer_email=user.email,
        delivery_address=_format_address(order.delivery_address_snapshot),
        payment_method=order.payment_method.value.replace("_", " ").title(),
        payment_status=order.payment_status.value.replace("_", " ").title(),
        order_status=order.status.value.replace("_", " ").title(),
        currency=order.currency or "PKR",
        subtotal=order.subtotal,
        delivery_fee=order.delivery_fee,
        tax=order.tax,
        discount=order.discount,
        grand_total=order.grand_total,
        customer_notes=order.notes,
        estimated_preparation_minutes=order.estimated_preparation_minutes,
        items=items,
        brand_name=brand_name,
        logo_url=logo_url,
    )
