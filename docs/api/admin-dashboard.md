# Admin Dashboard

Back to [`api.md`](../../api.md) · [`index`](README.md)

## `GET /api/v1/admin/dashboard`

**Summary:** Get Dashboard

**Auth:** Bearer + owner

**Success responses:** `200`

---

## `GET /api/v1/admin/analytics`

**Summary:** Get Analytics

**Auth:** Bearer + owner

**Query params**

- `period` (string, default=`daily`)
- `limit` (integer, default=`10`)

**Success responses:** `200`

---

## `GET /api/v1/admin/charts`

**Summary:** Get Charts

**Auth:** Bearer + owner

**Query params**

- `period` (string, default=`daily`)

**Success responses:** `200`

---
