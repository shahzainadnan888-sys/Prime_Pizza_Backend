# Chef Dashboard

Back to [`api.md`](../../api.md) · [`index`](README.md)

## `GET /api/v1/chef/orders`

**Summary:** Kitchen order boards

**Auth:** Bearer + chef

Returns pending/incoming, preparing, ready, completed, and cancelled orders for the chef kitchen dashboard.

**Success responses:** `200`

---

## `GET /api/v1/chef/orders/pending`

**Summary:** Pending kitchen orders

**Auth:** Bearer + chef

**Success responses:** `200`

---

## `GET /api/v1/chef/orders/incoming`

**Summary:** Incoming kitchen orders

**Auth:** Bearer + chef

**Success responses:** `200`

---

## `GET /api/v1/chef/orders/preparing`

**Summary:** Preparing kitchen orders

**Auth:** Bearer + chef

**Success responses:** `200`

---

## `GET /api/v1/chef/orders/ready`

**Summary:** Ready kitchen orders

**Auth:** Bearer + chef

**Success responses:** `200`

---

## `GET /api/v1/chef/orders/completed`

**Summary:** Completed kitchen orders

**Auth:** Bearer + chef

**Success responses:** `200`

---

## `GET /api/v1/chef/orders/cancelled`

**Summary:** Cancelled kitchen orders

**Auth:** Bearer + chef

**Success responses:** `200`

---

## `GET /api/v1/chef/orders/{order_id}`

**Summary:** Kitchen order details

**Auth:** Bearer + chef

**Path params**

- `order_id` (string, required)

**Success responses:** `200`

---

## `PATCH /api/v1/chef/orders/{order_id}/status`

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

## `POST /api/v1/chef/orders/{order_id}/accept`

**Summary:** Accept incoming order

**Auth:** Bearer + chef

**Path params**

- `order_id` (string, required)

**Body**

- Content-Type: `application/json`

**Success responses:** `200`

---

## `POST /api/v1/chef/orders/{order_id}/start-preparing`

**Summary:** Start preparing order

**Auth:** Bearer + chef

**Path params**

- `order_id` (string, required)

**Body**

- Content-Type: `application/json`

**Success responses:** `200`

---

## `POST /api/v1/chef/orders/{order_id}/mark-ready`

**Summary:** Mark order ready

**Auth:** Bearer + chef

**Path params**

- `order_id` (string, required)

**Body**

- Content-Type: `application/json`

**Success responses:** `200`

---

## `POST /api/v1/chef/orders/{order_id}/complete`

**Summary:** Complete order

**Auth:** Bearer + chef

**Path params**

- `order_id` (string, required)

**Body**

- Content-Type: `application/json`

**Success responses:** `200`

---

## `POST /api/v1/chef/orders/{order_id}/cancel`

**Summary:** Cancel order

**Auth:** Bearer + chef

**Path params**

- `order_id` (string, required)

**Body**

- Content-Type: `application/json`

**Success responses:** `200`

---

## `GET /api/v1/dashboard/chef/orders`

**Summary:** Kitchen order boards

**Auth:** Bearer + chef

Returns pending/incoming, preparing, ready, completed, and cancelled orders for the chef kitchen dashboard.

**Success responses:** `200`

---

## `GET /api/v1/dashboard/chef/orders/pending`

**Summary:** Pending kitchen orders

**Auth:** Bearer + chef

**Success responses:** `200`

---

## `GET /api/v1/dashboard/chef/orders/incoming`

**Summary:** Incoming kitchen orders

**Auth:** Bearer + chef

**Success responses:** `200`

---

## `GET /api/v1/dashboard/chef/orders/preparing`

**Summary:** Preparing kitchen orders

**Auth:** Bearer + chef

**Success responses:** `200`

---

## `GET /api/v1/dashboard/chef/orders/ready`

**Summary:** Ready kitchen orders

**Auth:** Bearer + chef

**Success responses:** `200`

---

## `GET /api/v1/dashboard/chef/orders/completed`

**Summary:** Completed kitchen orders

**Auth:** Bearer + chef

**Success responses:** `200`

---

## `GET /api/v1/dashboard/chef/orders/cancelled`

**Summary:** Cancelled kitchen orders

**Auth:** Bearer + chef

**Success responses:** `200`

---

## `GET /api/v1/dashboard/chef/orders/{order_id}`

**Summary:** Kitchen order details

**Auth:** Bearer + chef

**Path params**

- `order_id` (string, required)

**Success responses:** `200`

---

## `PATCH /api/v1/dashboard/chef/orders/{order_id}/status`

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

## `POST /api/v1/dashboard/chef/orders/{order_id}/accept`

**Summary:** Accept incoming order

**Auth:** Bearer + chef

**Path params**

- `order_id` (string, required)

**Body**

- Content-Type: `application/json`

**Success responses:** `200`

---

## `POST /api/v1/dashboard/chef/orders/{order_id}/start-preparing`

**Summary:** Start preparing order

**Auth:** Bearer + chef

**Path params**

- `order_id` (string, required)

**Body**

- Content-Type: `application/json`

**Success responses:** `200`

---

## `POST /api/v1/dashboard/chef/orders/{order_id}/mark-ready`

**Summary:** Mark order ready

**Auth:** Bearer + chef

**Path params**

- `order_id` (string, required)

**Body**

- Content-Type: `application/json`

**Success responses:** `200`

---

## `POST /api/v1/dashboard/chef/orders/{order_id}/complete`

**Summary:** Complete order

**Auth:** Bearer + chef

**Path params**

- `order_id` (string, required)

**Body**

- Content-Type: `application/json`

**Success responses:** `200`

---

## `POST /api/v1/dashboard/chef/orders/{order_id}/cancel`

**Summary:** Cancel order

**Auth:** Bearer + chef

**Path params**

- `order_id` (string, required)

**Body**

- Content-Type: `application/json`

**Success responses:** `200`

---
