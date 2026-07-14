# Authorization (RBAC)

## Roles

| Role | Source |
|------|--------|
| `customer` | Default for all verified phones |
| `owner` | Phone matches `OWNER_PHONE_NUMBER` from `.env` |

Future roles (`manager`, `staff`, `delivery`, `support`) can be added by:
1. Extending `UserRole` + Alembic enum migration
2. Adding an entry to `_FUTURE_ROLE_PERMISSIONS` / `_role_matrix`
3. No dependency code changes required

## Permissions

Defined in `app/authorization/permissions.py` as `{resource}.{action}`.

Owner receives `Permission.ALL` (wildcard) plus explicit admin permissions.
Customer receives self-service + catalog browse permissions only.

## Dependencies

| Dependency | Use |
|------------|-----|
| `require_authenticated` | Any logged-in user |
| `require_verified` | Verified phone |
| `require_customer` | Storefront (owner also allowed) |
| `require_owner` | Owner-only |
| `require_permission(...)` | Fine-grained |
| `require_self_or_owner` | Path `{user_id}` self-access |
| `ensure_resource_owner(...)` | After loading an entity |

## Ownership

`OwnershipService.ensure_owner_or_self`:
- Owner bypasses
- Customers: only own resources (404 for foreign to avoid leakage)

## Security invariants

- DB role is authoritative; JWT `role` claim is never used for authorization
- Owner phone is never hardcoded — always from settings
- Role re-synced on every successful OTP verify
