# Authentication

Prime Pizza uses **email + password** authentication with JWT access/refresh tokens.

## Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/api/v1/auth/register` | Public | Create customer account |
| `POST` | `/api/v1/auth/login` | Public | Issue JWT pair |
| `POST` | `/api/v1/auth/refresh` | Public | Rotate refresh + access tokens |
| `POST` | `/api/v1/auth/logout` | Bearer | Revoke access (and optional refresh) |
| `GET` | `/api/v1/auth/me` | Bearer | Current user profile |

## Registration

Required fields: `first_name`, `last_name`, `email`, `password`, `confirm_password`.  
Optional: `phone_number` (E.164).

Passwords are bcrypt-hashed. Email must be unique. Accounts are written to PostgreSQL and mirrored to `data/users.json`.

## Login

Body: `{ "email", "password" }` → returns `user` + `tokens.access_token` / `tokens.refresh_token`.

## Roles

| Role | How assigned |
|------|----------------|
| `customer` | Default on registration |
| `chef` | Bootstrapped at startup from `CHEF_EMAIL` / `CHEF_PASSWORD` |

Default chef credentials (override via `.env`):

- Email: `Chef123@gmail.com`
- Password: `Chef123`

## JWT

- Algorithm: HS256
- Access TTL: `ACCESS_TOKEN_EXPIRE_MINUTES`
- Refresh TTL: `REFRESH_TOKEN_EXPIRE_DAYS`
- Refresh tokens are stored in Redis and rotated on use
- Authorization always uses the **database** role (JWT `role` claim is not trusted for privilege)

## Kitchen

Chef-protected kitchen APIs live under `/api/v1/kitchen/*`.
