# Authorization

Roles are stored in PostgreSQL and reloaded on every authenticated request. JWT `role` claims are never trusted for privilege decisions.

## Roles

| Role | Assignment | Access |
|------|------------|--------|
| `customer` | Default on `/auth/register` | Storefront: profile, addresses, cart, wishlist, checkout, own orders |
| `chef` | Startup bootstrap (`CHEF_EMAIL` / `CHEF_PASSWORD`) | Kitchen dashboard + restaurant ops (`/api/v1/kitchen/*`, `/api/v1/admin/*`) |

There is no `owner` or `admin` role.

## Enforcement

- FastAPI dependencies: `require_customer`, `require_chef` / `require_owner` (alias), `require_permission(...)`
- Permission matrix: `app/authorization/permissions.py`
- Ownership checks hide foreign customer resources with 404

## Kitchen

Chef-only board + actions under `/api/v1/kitchen/orders*`. Customer order placement writes to PostgreSQL immediately; kitchen polls the same tables.
