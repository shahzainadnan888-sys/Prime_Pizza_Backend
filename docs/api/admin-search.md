# Admin Search

## Admin Search

### Endpoint

`POST /api/v1/admin/search`

### Description

Admin Search

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
| `q` | string | yes | minLength=1; maxLength=200 |
| `entities` | array<enum: `customers` | `orders` | `products` | `coupons` | `deals` | `categories` | `audit_logs`> | null | no | — |
| `limit_per_entity` | integer | no | min=1.0; max=50.0; default=`10` |

### Example Request

```http
POST /api/v1/admin/search HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "q": "string",
  "entities": null,
  "limit_per_entity": 10
}
```

### Validation Rules

- Required body fields: `q`
- `q`: minLength=1, maxLength=200
- `limit_per_entity`: min=1.0, max=50.0

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

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
