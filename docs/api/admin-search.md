# Admin Search

Back to [`api.md`](../../api.md) · [`index`](README.md)

## `POST /api/v1/admin/search`

**Summary:** Admin Search

**Auth:** Bearer + owner

**Body**

- Content-Type: `application/json`
- Schema: `AdminSearchRequest`

| Field | Type | Required |
|-------|------|----------|
| `q` | `string` | yes |
| `entities` | `nullable` | no |
| `limit_per_entity` | `integer` | no |

**Success responses:** `200`

---
