# Cart, Wishlist & Checkout Preparation

Authenticated shopping cart, wishlist, coupon validation, delivery/tax preparation,
and checkout readiness checks. **No orders are created in this phase.**

## Architecture

```
API (/cart, /wishlist, /checkout/validate)
  → require_verified + CART_MANAGE_OWN / WISHLIST_MANAGE_OWN
  → CartService / WishlistService / CheckoutValidationService
  → PricingService + CouponService + DeliveryService + TaxService + OrderSummaryService
  → Repositories → PostgreSQL (authoritative prices)
  → CartCacheService (Redis) invalidated on every cart mutation
```

## Security

- Client cannot supply `unit_price` / totals — all prices loaded from catalog tables.
- Cart mutations use `SELECT … FOR UPDATE` on the active cart row.
- Coupons validated for active/expiry/usage/min-order/max-discount without consuming usage.
- Checkout validate returns issues only; never inserts into `orders`.
