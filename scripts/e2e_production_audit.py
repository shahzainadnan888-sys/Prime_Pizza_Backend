"""End-to-end production audit: latency + dual-write + chef + contact.

Run: uv run python scripts/e2e_production_audit.py
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def _ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 1)


def main() -> None:
    app = create_app()
    report: dict = {"checks": {}, "timings_ms": {}, "remaining": []}

    with TestClient(app) as client:
        # Health / DB
        t0 = time.perf_counter()
        health = client.get("/health")
        report["timings_ms"]["GET /health"] = _ms(t0)
        report["checks"]["health"] = health.status_code == 200

        t0 = time.perf_counter()
        db = client.get("/health/database")
        report["timings_ms"]["GET /health/database"] = _ms(t0)
        report["checks"]["database_health"] = db.status_code == 200
        if db.status_code == 200:
            body = db.json()
            report["database"] = body.get("data") or body

        # Contact route existence + submit
        t0 = time.perf_counter()
        missing = client.post("/api/v1/contact", json={})
        report["timings_ms"]["POST /contact empty"] = _ms(t0)
        report["checks"]["contact_route_exists"] = missing.status_code == 422

        t0 = time.perf_counter()
        contact = client.post(
            "/api/v1/contact",
            json={
                "name": "Audit Bot",
                "email": "audit.bot@example.com",
                "phone": "+923001112233",
                "subject": "E2E audit",
                "message": "Production audit contact test",
            },
        )
        report["timings_ms"]["POST /contact"] = _ms(t0)
        report["checks"]["contact_submit"] = contact.status_code == 201

        # Register customer
        email = f"audit_{uuid.uuid4().hex[:10]}@example.com"
        password = "AuditTest123!"
        t0 = time.perf_counter()
        reg = client.post(
            "/api/v1/auth/register",
            json={
                "first_name": "Audit",
                "last_name": "Customer",
                "email": email,
                "password": password,
                "confirm_password": password,
                "phone_number": f"+92300{uuid.uuid4().int % 10_000_000:07d}",
            },
        )
        report["timings_ms"]["POST /auth/register"] = _ms(t0)
        report["checks"]["register"] = reg.status_code in {200, 201}
        if reg.status_code not in {200, 201}:
            report["register_error"] = (reg.text or "")[:500]
        reg_body = reg.json() if reg.content else {}
        customer_token = (
            (reg_body.get("data") or {}).get("access_token")
            or (reg_body.get("data") or {}).get("tokens", {}).get("access_token")
        )
        report["checks"]["customer_jwt"] = bool(customer_token)
        report["checks"]["user_json_after_register"] = Path("data/user.json").exists()

        # Login customer
        t0 = time.perf_counter()
        login = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        report["timings_ms"]["POST /auth/login customer"] = _ms(t0)
        report["checks"]["customer_login"] = login.status_code == 200
        if login.status_code == 200:
            data = login.json().get("data") or {}
            customer_token = data.get("access_token") or (data.get("tokens") or {}).get(
                "access_token"
            )
            role = data.get("role") or ((data.get("user") or {}).get("role"))
            report["checks"]["customer_role"] = role == "customer"

        headers = {"Authorization": f"Bearer {customer_token}"} if customer_token else {}

        # Fast GET paths that were timing out
        for path in (
            "/api/v1/cart",
            "/api/v1/account",
            "/api/v1/addresses",
            "/api/v1/users/me",
            "/api/v1/users/addresses",
        ):
            t0 = time.perf_counter()
            resp = client.get(path, headers=headers)
            report["timings_ms"][f"GET {path}"] = _ms(t0)
            report["checks"][f"ok {path}"] = resp.status_code == 200

        # Chef login + JWT role
        t0 = time.perf_counter()
        chef = client.post(
            "/api/v1/auth/login",
            json={"email": "Chef123@gmail.com", "password": "Chef123"},
        )
        report["timings_ms"]["POST /auth/login chef"] = _ms(t0)
        report["checks"]["chef_login"] = chef.status_code == 200
        chef_token = None
        if chef.status_code == 200:
            data = chef.json().get("data") or {}
            chef_token = data.get("access_token") or (data.get("tokens") or {}).get(
                "access_token"
            )
            role = data.get("role") or ((data.get("user") or {}).get("role"))
            report["checks"]["chef_jwt_role"] = role == "chef"
        chef_headers = {"Authorization": f"Bearer {chef_token}"} if chef_token else {}

        t0 = time.perf_counter()
        kitchen = client.get("/api/v1/kitchen/orders", headers=chef_headers)
        report["timings_ms"]["GET /kitchen/orders"] = _ms(t0)
        report["checks"]["kitchen_boards"] = kitchen.status_code == 200
        if kitchen.status_code == 200:
            board = (kitchen.json().get("data") or {})
            report["checks"]["kitchen_has_pending_key"] = "pending" in board
            report["checks"]["kitchen_has_preparing_key"] = "preparing" in board
            report["checks"]["kitchen_has_ready_key"] = "ready" in board
            report["checks"]["kitchen_has_completed_key"] = "completed" in board
            report["checks"]["kitchen_has_cancelled_key"] = "cancelled" in board

        # Catalog product for cart/order if available
        products = client.get("/api/v1/products")
        report["checks"]["catalog_products"] = products.status_code == 200
        product_id = None
        if products.status_code == 200:
            payload = products.json().get("data")
            items = payload if isinstance(payload, list) else (payload or {}).get("items") or []
            if items:
                product_id = items[0].get("id")

        # Add address if needed
        addr = client.post(
            "/api/v1/users/addresses",
            headers=headers,
            json={
                "title": "Home",
                "recipient_name": "Audit Customer",
                "phone_number": "+923001112233",
                "street": "Street 1 Block A",
                "area": "Clifton",
                "city": "Karachi",
                "province": "Sindh",
                "postal_code": "75600",
                "country": "Pakistan",
                "is_default": True,
            },
        )
        report["checks"]["create_address"] = addr.status_code in {200, 201}
        address_id = None
        if addr.status_code in {200, 201}:
            address_id = (addr.json().get("data") or {}).get("id")

        order_ok = False
        if product_id and address_id and customer_token:
            add = client.post(
                "/api/v1/cart/items",
                headers=headers,
                json={"product_id": product_id, "quantity": 1},
            )
            report["checks"]["add_cart_item"] = add.status_code in {200, 201}
            t0 = time.perf_counter()
            order = client.post(
                "/api/v1/orders",
                headers=headers,
                json={
                    "address_id": address_id,
                    "payment_method": "cash_on_delivery",
                    "notes": "E2E audit order",
                },
            )
            report["timings_ms"]["POST /orders"] = _ms(t0)
            order_ok = order.status_code in {200, 201}
            report["checks"]["place_order"] = order_ok
            if order_ok:
                order_data = order.json().get("data") or {}
                report["order_number"] = order_data.get("order_number")
                report["checks"]["order_json_exists"] = Path("data/order.json").exists()
                if Path("data/order.json").exists():
                    rows = json.loads(Path("data/order.json").read_text(encoding="utf-8") or "[]")
                    report["checks"]["order_json_appended"] = any(
                        str(r.get("id")) == str(order_data.get("id")) for r in rows
                    )

                # Kitchen should include new pending order
                kitchen2 = client.get("/api/v1/kitchen/orders", headers=chef_headers)
                pending = ((kitchen2.json().get("data") or {}).get("pending") or [])
                report["checks"]["order_visible_in_kitchen"] = any(
                    str(o.get("id")) == str(order_data.get("id")) for o in pending
                )

        # OpenAPI route list sanity
        openapi = client.get("/openapi.json").json()
        paths = openapi.get("paths") or {}
        report["checks"]["openapi_has_contact"] = "/api/v1/contact" in paths
        report["checks"]["openapi_has_account"] = "/api/v1/account" in paths
        report["checks"]["openapi_has_addresses"] = "/api/v1/addresses" in paths
        report["checks"]["openapi_has_cart"] = "/api/v1/cart" in paths

    # Slow endpoint threshold report
    slow = {k: v for k, v in report["timings_ms"].items() if v >= 5000}
    if slow:
        report["remaining"].append(f"Slow responses (>=5s): {slow}")

    failed = [k for k, v in report["checks"].items() if v is False]
    report["failed_checks"] = failed
    report["summary"] = "PASS" if not failed else "PARTIAL"

    out = Path("data") / "e2e_audit_report.json"
    out.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
