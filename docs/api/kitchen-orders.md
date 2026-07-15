# Kitchen Orders

Back to [`api.md`](../../api.md) · [`index`](README.md)

## `GET /api/v1/orders/kitchen/orders`

**Summary:** Kitchen order boards

**Auth:** Bearer + chef

Returns pending/incoming, preparing, ready, completed, and cancelled orders for the chef kitchen dashboard.

**Success responses:** `200`

---

## `GET /api/v1/orders/kitchen/orders/pending`

**Summary:** Pending kitchen orders

**Auth:** Bearer + chef

**Success responses:** `200`

---

## `GET /api/v1/orders/kitchen/orders/incoming`

**Summary:** Incoming kitchen orders

**Auth:** Bearer + chef

**Success responses:** `200`

---

## `GET /api/v1/orders/kitchen/orders/preparing`

**Summary:** Preparing kitchen orders

**Auth:** Bearer + chef

**Success responses:** `200`

---

## `GET /api/v1/orders/kitchen/orders/ready`

**Summary:** Ready kitchen orders

**Auth:** Bearer + chef

**Success responses:** `200`

---

## `GET /api/v1/orders/kitchen/orders/completed`

**Summary:** Completed kitchen orders

**Auth:** Bearer + chef

**Success responses:** `200`

---

## `GET /api/v1/orders/kitchen/orders/cancelled`

**Summary:** Cancelled kitchen orders

**Auth:** Bearer + chef

**Success responses:** `200`

---

## `GET /api/v1/orders/kitchen/orders/{order_id}`

**Summary:** Kitchen order details

**Auth:** Bearer + chef

**Path params**

- `order_id` (string, required)

**Success responses:** `200`

---

## `PATCH /api/v1/orders/kitchen/orders/{order_id}/status`

**Summary:** Update kitchen order status

**Auth:** Bearer + chef

Chef-only status updates: pending, preparing, ready, completed.

**Path params**

- `order_id` (string, required)

**Body**

- Content-Type: `application/json`
- Schema: `KitchenStatusUpdateRequest`

| Field | Type | Required |
|-------|------|----------|
| `status` | `string` | yes |
| `notes` | `nullable` | no |

**Success responses:** `200`

---

## `POST /api/v1/orders/kitchen/orders/{order_id}/accept`

**Summary:** Accept incoming order

**Auth:** Bearer + chef

**Path params**

- `order_id` (string, required)

**Body**

- Content-Type: `application/json`

**Success responses:** `200`

---

## `POST /api/v1/orders/kitchen/orders/{order_id}/start-preparing`

**Summary:** Start preparing order

**Auth:** Bearer + chef

**Path params**

- `order_id` (string, required)

**Body**

- Content-Type: `application/json`

**Success responses:** `200`

---

## `POST /api/v1/orders/kitchen/orders/{order_id}/mark-ready`

**Summary:** Mark order ready

**Auth:** Bearer + chef

**Path params**

- `order_id` (string, required)

**Body**

- Content-Type: `application/json`

**Success responses:** `200`

---

## `POST /api/v1/orders/kitchen/orders/{order_id}/complete`

**Summary:** Complete order

**Auth:** Bearer + chef

**Path params**

- `order_id` (string, required)

**Body**

- Content-Type: `application/json`

**Success responses:** `200`

---

## `POST /api/v1/orders/kitchen/orders/{order_id}/cancel`

**Summary:** Cancel order

**Auth:** Bearer + chef

**Path params**

- `order_id` (string, required)

**Body**

- Content-Type: `application/json`

**Success responses:** `200`

---
