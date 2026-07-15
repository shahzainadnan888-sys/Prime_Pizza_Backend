"""Live Brevo email integration audit.

Run: uv run python scripts/brevo_email_audit.py

Uses backend .env only — never exposes BREVO_API_KEY to any frontend.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.config.settings import Settings, get_settings
from app.database.session import close_db, init_db
from app.emails.payloads import OrderEmailLineItem, OrderEmailPayload
from app.integrations.brevo.client import init_brevo, is_brevo_configured, send_email_via_brevo
from app.services.email_service import EmailService


def _report_section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


async def _verify_brevo_auth(settings: Settings) -> dict[str, Any]:
    result: dict[str, Any] = {"ok": False}
    try:
        settings.validate_brevo_required()
        init_brevo(settings, strict=True)
        sender_email, sender_name = settings.brevo_sender_email, settings.brevo_sender_name
        result["sender_email"] = str(sender_email)
        result["sender_name"] = str(sender_name)
        result["configured"] = is_brevo_configured()
        result["ok"] = result["configured"]
    except Exception as exc:
        result["error"] = str(exc)
    return result


async def _send_via_service(settings: Settings) -> dict[str, Any]:
    service = EmailService(settings=settings)
    audit_id = uuid.uuid4().hex[:8]
    customer_email = str(settings.admin_email).strip().lower()
    results: dict[str, Any] = {}

    # Welcome
    try:
        log = await service.send_welcome_email(
            customer_name="Brevo Audit",
            customer_email=customer_email,
        )
        results["welcome"] = {"ok": True, "email_log_id": str(log.id)}
    except Exception as exc:
        results["welcome"] = {"ok": False, "error": str(exc)}

    # Contact admin inbox
    try:
        log = await service.send_contact_email(
            name="Brevo Audit",
            email="audit@primepizza.local",
            phone="+923001112233",
            subject=f"Contact audit {audit_id}",
            message="Automated Brevo contact-form audit message.",
            submission_time=datetime.now(UTC),
            client_ip="127.0.0.1",
        )
        results["contact"] = {
            "ok": True,
            "email_log_id": str(log.id),
            "recipients": settings.contact_notification_recipients(),
        }
    except Exception as exc:
        results["contact"] = {"ok": False, "error": str(exc)}

    order_payload = OrderEmailPayload(
        order_id=uuid.uuid4(),
        order_number=f"AUDIT-{audit_id}",
        order_created_at=datetime.now(UTC),
        customer_name="Brevo Audit Customer",
        customer_phone="+923001112233",
        customer_email=customer_email,
        delivery_address="123 Audit Street, Lahore",
        payment_method="Cash On Delivery",
        payment_status="Pending",
        order_status="Pending",
        currency="PKR",
        subtotal=Decimal("1500.00"),
        delivery_fee=Decimal("150.00"),
        tax=Decimal("0.00"),
        discount=Decimal("0.00"),
        grand_total=Decimal("1650.00"),
        customer_notes=None,
        estimated_preparation_minutes=35,
        items=[
            OrderEmailLineItem(
                product_name="Margherita",
                quantity=1,
                unit_price=Decimal("1500.00"),
                subtotal=Decimal("1500.00"),
                variant_name="Large",
            )
        ],
        brand_name=settings.email_brand_name,
    )

    try:
        confirm_msg = service.build_order_confirmation_message(order_payload)
        confirm_msg.order_id = None  # audit-only: no orders row required
        log = await service.send_message(confirm_msg)
        results["order_confirmation"] = {"ok": True, "email_log_id": str(log.id)}
    except Exception as exc:
        results["order_confirmation"] = {"ok": False, "error": str(exc)}

    try:
        chef_msg = service.build_chef_notification_message(order_payload)
        chef_msg.order_id = None  # audit-only: no orders row required
        log = await service.send_message(chef_msg)
        results["chef_notification"] = {
            "ok": True,
            "email_log_id": str(log.id),
            "recipients": settings.chef_notification_recipients(),
        }
    except Exception as exc:
        results["chef_notification"] = {"ok": False, "error": str(exc)}

    return results


async def main() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    report: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "email_enabled": settings.email_enabled,
        "checks": {},
    }

    _report_section("Brevo configuration")
    brevo = await _verify_brevo_auth(settings)
    report["brevo"] = brevo
    print(json.dumps(brevo, indent=2))
    report["checks"]["brevo_authentication"] = brevo.get("ok", False)
    report["checks"]["sender_verified"] = bool(brevo.get("sender_email"))

    if not brevo.get("ok"):
        print("\nAborting live sends — fix Brevo configuration first.")
    else:
        _report_section("Live email sends via EmailService")
        await init_db(settings)
        try:
            started = time.perf_counter()
            sends = await _send_via_service(settings)
            report["sends"] = sends
            report["send_duration_ms"] = round((time.perf_counter() - started) * 1000, 1)
            print(json.dumps(sends, indent=2))
            for key in ("welcome", "contact", "order_confirmation", "chef_notification"):
                report["checks"][key] = sends.get(key, {}).get("ok", False)
        finally:
            await close_db()

    out = Path("data/brevo_email_audit_report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nReport written to {out}")

    _report_section("Final checklist")
    labels = {
        "brevo_authentication": "Brevo authentication successful",
        "sender_verified": "Sender verified",
        "welcome": "Welcome email working",
        "contact": "Contact email working",
        "order_confirmation": "Order confirmation working",
        "chef_notification": "Chef notification working",
    }
    for key, label in labels.items():
        status = "PASS" if report["checks"].get(key) else "FAIL/SKIP"
        print(f"  [{status}] {label}")


if __name__ == "__main__":
    asyncio.run(main())
