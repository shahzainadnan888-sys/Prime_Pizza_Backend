# Admin Audit

Back to [`api.md`](../../api.md) · [`index`](README.md)

## `GET /api/v1/admin/audit-logs`

**Summary:** List Audit Logs

**Auth:** Bearer + owner

**Query params**

- `q` (object, default=``)
- `user_id` (object, default=``)
- `action` (object, default=``)
- `resource_type` (object, default=``)
- `date_from` (object, default=``)
- `date_to` (object, default=``)
- `sort` (string, default=`newest`)
- `page` (integer, default=`1`)
- `page_size` (integer, default=`20`)

**Success responses:** `200`

---
