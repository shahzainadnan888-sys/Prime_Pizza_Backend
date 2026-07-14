# Orders

Back to [`api.md`](../../api.md) · [`index`](README.md)

## `POST /api/v1/orders`

**Summary:** Place Order

**Auth:** Bearer

**Body**

- Content-Type: `application/json`
- Schema: `PlaceOrderRequest`

| Field | Type | Required |
|-------|------|----------|
| `address_id` | `nullable` | no |
| `payment_method` | `PaymentMethod` | no |
| `notes` | `nullable` | no |
| `idempotency_key` | `nullable` | no |

**Success responses:** `201`

---

## `GET /api/v1/orders`

**Summary:** List My Orders

**Auth:** Bearer

**Query params**

- `status` (object, default=``)
- `payment_status` (object, default=``)
- `date_from` (object, default=``)
- `date_to` (object, default=``)
- `sort` (string, default=`newest`)
- `page` (integer, default=`1`)
- `page_size` (integer, default=`20`)

**Success responses:** `200`

---

## `GET /api/v1/orders/{order_id}`

**Summary:** Get My Order

**Auth:** Bearer

**Path params**

- `order_id` (string, required)

**Success responses:** `200`

---

## `GET /api/v1/orders/{order_id}/tracking`

**Summary:** Track My Order

**Auth:** Bearer

**Path params**

- `order_id` (string, required)

**Success responses:** `200`

---

## `PATCH /api/v1/orders/{order_id}/cancel`

**Summary:** Cancel My Order

**Auth:** Bearer

**Path params**

- `order_id` (string, required)

**Body**

- Content-Type: `application/json`

**Success responses:** `200`

---
