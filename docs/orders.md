# Order Management & Checkout

Transactional order placement from an authenticated customer's cart.
No email/Resend integration in this phase — owner new-order emails are sent
post-commit via the Email Notification module (`docs/emails.md`).

## Checkout flow

1. Optional idempotency lookup (`orders:idempotency:{user}:{key}`)
2. Acquire Redis checkout lock (`orders:checkout_lock:{user_id}`)
3. `SELECT … FOR UPDATE` on active cart
4. Checkout validation **without commit** (availability, address, coupon, stock)
5. Recalculate all prices from PostgreSQL
6. Resolve delivery address → snapshot onto order
7. Allocate `PP-YYYY-######` via `order_number_sequences` (`FOR UPDATE` + savepoint insert)
8. Insert order + item/extra snapshots + timeline (“Order Created”)
9. Lock coupon row, re-validate, increment `used_count`, insert `coupon_usages`
10. Convert/clear cart (`status=converted`, `is_active=false`)
11. Commit — on any failure: rollback + release lock

## Transactions

One SQLAlchemy session transaction owns create order → items → coupon → timeline → cart conversion.
`CheckoutValidationService.validate(commit=False)` only flushes pricing; it never commits mid-checkout.
Failures call `session.rollback()` so no partial order rows remain.

## Order creation

- Order number: unique partial index + sequential yearly counter
- Line items store name, variant, extras, qty, unit/discount/subtotal, prep time, image URL, snapshots
- Address copied into `delivery_address_snapshot` JSONB
- Payment defaults to COD + `payment_status=pending`
- Online payment rejected until payment module ships

## Tracking & timeline

- `GET /orders/{id}/tracking` returns status, timeline, ETA prep/delivery, last updated
- Timeline events: status, title, performed_by, notes, timestamp
- Owner status changes append timeline; illegal transitions are rejected

## Customer APIs

| Method | Path | Permission |
|--------|------|------------|
| POST | `/api/v1/orders` | `order.create` |
| GET | `/api/v1/orders` | `order.read_own` |
| GET | `/api/v1/orders/{id}` | `order.read_own` |
| GET | `/api/v1/orders/{id}/tracking` | `order.track_own` |
| PATCH | `/api/v1/orders/{id}/cancel` | `order.create` |

Scoped by `user_id`. Cancel only while Pending/Confirmed inside cancel window.

## Owner APIs

| Method | Path | Permission |
|--------|------|------------|
| GET | `/api/v1/admin/orders` | `order.read` |
| GET | `/api/v1/admin/orders/{id}` | `order.read` |
| PATCH | `/api/v1/admin/orders/{id}/status` | `order.update` |
| PATCH | `/api/v1/admin/orders/{id}/payment` | `order.update` |
| PATCH | `/api/v1/admin/orders/{id}/notes` | `order.update` |

Internal/kitchen notes visible only on admin detail responses.

## Redis

Cached: tracking, detail, customer list, recent orders.
Invalidated on place / status / payment / notes / cancel.
Checkout lock + idempotency keys prevent double submit.

## Security

- JWT + permission + ownership checks
- Never trust client prices
- Checkout lock + cart row lock + coupon row lock
- Idempotency key (optional)
- Customers cannot see other users' orders or internal notes
