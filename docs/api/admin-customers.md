# Admin Customers

Back to [`api.md`](../../api.md) · [`index`](README.md)

## `GET /api/v1/admin/customers`

**Summary:** List Customers

**Auth:** Bearer + owner

**Query params**

- `q` (object, default=``)
- `name` (object, default=``)
- `phone` (object, default=``)
- `email` (object, default=``)
- `role` (object, default=``)
- `is_active` (object, default=``)
- `is_verified` (object, default=``)
- `date_from` (object, default=``)
- `date_to` (object, default=``)
- `sort` (string, default=`newest`)
- `page` (integer, default=`1`)
- `page_size` (integer, default=`20`)

**Success responses:** `200`

---

## `GET /api/v1/admin/customers/{customer_id}`

**Summary:** Get Customer

**Auth:** Bearer + owner

**Path params**

- `customer_id` (string, required)

**Success responses:** `200`

---

## `PATCH /api/v1/admin/customers/{customer_id}`

**Summary:** Update Customer

**Auth:** Bearer + owner

**Path params**

- `customer_id` (string, required)

**Body**

- Content-Type: `application/json`
- Schema: `AdminCustomerUpdateRequest`

| Field | Type | Required |
|-------|------|----------|
| `full_name` | `nullable` | no |
| `email` | `nullable` | no |

**Success responses:** `200`

---

## `PATCH /api/v1/admin/customers/{customer_id}/status`

**Summary:** Update Customer Status

**Auth:** Bearer + owner

**Path params**

- `customer_id` (string, required)

**Body**

- Content-Type: `application/json`
- Schema: `AdminCustomerStatusRequest`

| Field | Type | Required |
|-------|------|----------|
| `is_active` | `boolean` | yes |

**Success responses:** `200`

---
