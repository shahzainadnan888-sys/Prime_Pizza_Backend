# Admin Orders

Back to [`api.md`](../../api.md) · [`index`](README.md)

## `GET /api/v1/admin/orders`

**Summary:** List Orders

**Auth:** Bearer + owner

**Query params**

- `status` (object, default=``)
- `payment_status` (object, default=``)
- `date_from` (object, default=``)
- `date_to` (object, default=``)
- `sort` (string, default=`newest`)
- `q` (object, default=``)
- `user_id` (object, default=``)
- `page` (integer, default=`1`)
- `page_size` (integer, default=`20`)

**Success responses:** `200`

---

## `GET /api/v1/admin/orders/{order_id}`

**Summary:** Get Order

**Auth:** Bearer + owner

**Path params**

- `order_id` (string, required)

**Success responses:** `200`

---

## `PATCH /api/v1/admin/orders/{order_id}/status`

**Summary:** Update Order Status

**Auth:** Bearer + owner

**Path params**

- `order_id` (string, required)

**Body**

- Content-Type: `application/json`
- Schema: `UpdateOrderStatusRequest`

| Field | Type | Required |
|-------|------|----------|
| `status` | `OrderStatus` | yes |
| `notes` | `nullable` | no |

**Success responses:** `200`

---

## `PATCH /api/v1/admin/orders/{order_id}/payment`

**Summary:** Update Payment Status

**Auth:** Bearer + owner

**Path params**

- `order_id` (string, required)

**Body**

- Content-Type: `application/json`
- Schema: `UpdatePaymentStatusRequest`

| Field | Type | Required |
|-------|------|----------|
| `payment_status` | `PaymentStatus` | yes |
| `notes` | `nullable` | no |

**Success responses:** `200`

---

## `PATCH /api/v1/admin/orders/{order_id}/notes`

**Summary:** Update Order Notes

**Auth:** Bearer + owner

**Path params**

- `order_id` (string, required)

**Body**

- Content-Type: `application/json`
- Schema: `UpdateOrderNotesRequest`

| Field | Type | Required |
|-------|------|----------|
| `notes` | `nullable` | no |
| `kitchen_notes` | `nullable` | no |
| `internal_notes` | `nullable` | no |

**Success responses:** `200`

---
