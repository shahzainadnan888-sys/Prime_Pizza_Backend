# Admin Audit

## List Audit Logs

### Endpoint

`GET /api/v1/admin/audit-logs`

### Description

List Audit Logs

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `q` | no | string | null | — |
| `user_id` | no | string (uuid) | null | — |
| `action` | no | enum: `create` | `update` | `delete` | `login` | `logout` | `view` | `other` | null | — |
| `resource_type` | no | string | null | — |
| `date_from` | no | string (date-time) | null | — |
| `date_to` | no | string (date-time) | null | — |
| `sort` | no | string | — |
| `page` | no | integer | Page number |
| `page_size` | no | integer | Items per page |

### Request Body Schema

_No request body._

### Validation Rules

- `page`: min=1
- `page_size`: min=1, max=100

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Example Response

```json
{
  "success": true,
  "message": "Success",
  "data": [
    {
      "resource_type": "string",
      "created_at": "2026-07-15T12:00:00Z",
      "user_id": null,
      "id": "00000000-0000-4000-8000-000000000001",
      "message": null,
      "user_agent": null,
      "resource_id": null,
      "ip_address": null,
      "details": null,
      "action": "create"
    }
  ],
  "request_id": "00000000-0000-4000-8000-000000000099",
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 1,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  }
}
```

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
