# Product & Menu Module

Public and owner-managed catalog for Prime Pizza: categories, products, variants,
extras, gallery images, deals, search, filters, pagination, and Redis caching.

## Architecture

```
Public API  (/api/v1/categories|products|deals)
Admin API   (/api/v1/admin/...)
  → Services (Category, Product, Variant, Image, Deal, Search, Filter, Cache, Cloudinary)
  → Repositories
  → PostgreSQL (source of truth)
  → Redis catalog cache (best-effort, auto-invalidated on writes)
```

## Public endpoints

- `GET /categories`, `GET /categories/{slug}`
- `GET /products` (filters + sort + pagination)
- `GET /products/search?q=`
- `GET /products/featured`, `/popular`, `/recommended`
- `GET /products/{slug}`
- `GET /deals`, `GET /deals/{slug}`

## Admin endpoints (owner permissions)

- Categories / products / deals CRUD
- Product image upload, delete, reorder

## Cache keys

`catalog:categories`, `catalog:featured`, `catalog:popular`, `catalog:deals`,
`catalog:product:{slug}`, `catalog:search:{fingerprint}` — invalidated on any
catalog write.
