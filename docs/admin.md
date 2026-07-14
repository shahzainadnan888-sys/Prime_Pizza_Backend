# Owner Admin Console

Owner-facing APIs for dashboard metrics, customer and coupon management,
notifications, system settings, audit logs, and console search. Catalog and
order admin routes live in the existing Admin Catalog / Admin Orders modules
with additional bulk and lifecycle helpers.

## Surfaces

| Area | Prefix | Permissions |
|------|--------|-------------|
| Dashboard / analytics / charts | `/api/v1/admin` | `dashboard.read`, `analytics.read` |
| Customers | `/api/v1/admin/customers` | `customer.read`, `customer.update` |
| Coupons | `/api/v1/admin/coupons` | `coupon.read` / `create` / `update` / `delete` |
| Notifications | `/api/v1/admin/notifications` | `notification.manage` |
| Settings | `/api/v1/admin/settings` | `settings.read`, `settings.update` |
| Audit logs | `/api/v1/admin/audit-logs` | `audit_log.read` |
| Search | `/api/v1/admin/search` | `dashboard.read` |

All routes use `SuccessResponse` / `PaginatedResponse`, `require_permission`, and
`request_id` from request state.

## Caching

Dashboard stats, analytics, and charts are cached via Redis. Set
`DASHBOARD_CACHE_TTL_SECONDS` (default `60` in `.env.example`). Customer,
coupon, and settings mutations invalidate the dashboard cache.

## Catalog ops (Admin Catalog)

Extra owner helpers on `/api/v1/admin`:

- Category list, reorder, hide, restore
- Product bulk visibility / featured / availability / category / delete
- Deal activate, deactivate, schedule

## Notes

- Notification broadcast can target `customer`, `owner`, or `all`; scheduling is
  stored in payload only until a delivery worker exists.
- Settings expose a typed restaurant view at `GET /admin/settings/restaurant`
  plus key-level and bulk upserts.
- Admin order list accepts optional `q` and `user_id` filters.
