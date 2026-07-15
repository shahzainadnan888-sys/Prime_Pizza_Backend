# Admin Notifications

## Create Notification

### Endpoint

`POST /api/v1/admin/notifications`

### Description

Create Notification

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `user_id` | string (uuid) | null | no | — |
| `title` | string | yes | minLength=1; maxLength=200 |
| `message` | string | yes | minLength=1; maxLength=5000 |
| `notification_type` | enum: `order` | `promo` | `system` | `account` | no | values: `order`, `promo`, `system`, `account` |
| `payload` | object | null | no | — |
| `scheduled_at` | string (date-time) | null | no | Preparation only — stored in payload until a scheduler ships |

### Example Request

```http
POST /api/v1/admin/notifications HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "message": "string",
  "title": "string",
  "user_id": null,
  "notification_type": "order",
  "payload": null,
  "scheduled_at": null
}
```

### Validation Rules

- Required body fields: `message`, `title`
- `title`: minLength=1, maxLength=200
- `message`: minLength=1, maxLength=5000
- `notification_type`: enum=order|promo|system|account

### Response Schema

Success status: **201**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `201` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `201` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Broadcast Notification

### Endpoint

`POST /api/v1/admin/notifications/broadcast`

### Description

Broadcast Notification

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `title` | string | yes | minLength=1; maxLength=200 |
| `message` | string | yes | minLength=1; maxLength=5000 |
| `notification_type` | enum: `order` | `promo` | `system` | `account` | no | values: `order`, `promo`, `system`, `account` |
| `payload` | object | null | no | — |
| `role_filter` | string | null | no | default=`"customer"` |
| `scheduled_at` | string (date-time) | null | no | — |

### Example Request

```http
POST /api/v1/admin/notifications/broadcast HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "message": "string",
  "title": "string",
  "notification_type": "order",
  "payload": null,
  "role_filter": null,
  "scheduled_at": null
}
```

### Validation Rules

- Required body fields: `message`, `title`
- `title`: minLength=1, maxLength=200
- `message`: minLength=1, maxLength=5000
- `notification_type`: enum=order|promo|system|account

### Response Schema

Success status: **201**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `201` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `201` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Delete Notification

### Endpoint

`DELETE /api/v1/admin/notifications/{notification_id}`

### Description

Delete Notification

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `notification_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `success` | boolean | no | default=`true` |
| `message` | string | yes | — |
| `request_id` | string | null | no | — |

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---
