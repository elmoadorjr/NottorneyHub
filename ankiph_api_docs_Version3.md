# NottorneyHub Tiered Access API Documentation (v3.0)

## Overview

NottorneyHub implements a tiered access model for the Anki addon:

| Tier | Access | Price | Sync Updates |
|------|--------|-------|--------------|
| **Collection Owner** | ALL decks + full sync | ₱1,000 one-time | ✅ Yes |
| **NottorneyHub Subscriber** | ALL decks + full sync | ₱149/month | ✅ Yes |
| **Free Tier** | Only `is_free=true` subdecks | Free | ❌ No updates |
| **Legacy Purchase** | Individual purchased decks only | Varies | ✅ Yes |

---

## Authentication

### POST `/addon-login`

**New Fields in v3.0:**
- `owns_collection` (boolean): User has purchased the ₱1,000 collection
- `has_subscription` (boolean): User has active NottorneyHub subscription
- `subscription_expires_at` (string|null): ISO timestamp of subscription expiry
- `subscription_tier` (string): `"free"`, `"standard"`, or `"premium"`

---

## Deck Access

### POST `/addon-get-purchases`

**`access_type` Values:**
| Value | Description |
|-------|-------------|
| `collection_owner` | User owns the ₱1,000 collection |
| `subscriber` | User has active NottorneyHub subscription |
| `free_tier` | Free subdeck (is_free=true) |
| `legacy_purchase` | Individual deck purchase |

---

## Access Control Logic

```python
class AccessTier(Enum):
    COLLECTION_OWNER = "collection_owner"  # Full access, owns decks
    SUBSCRIBER = "subscriber"              # Full access, subscription
    FREE_TIER = "free_tier"                # Limited to is_free decks
    LEGACY = "legacy_purchase"             # Individual purchases only

def check_access(user_data: dict, deck: dict) -> AccessTier:
    """Determine user's access tier for a specific deck."""
    
    # Tier 1: Collection owners get everything
    if user_data.get("owns_collection"):
        return AccessTier.COLLECTION_OWNER
    
    # Tier 2: Active subscribers get everything
    if user_data.get("has_subscription"):
        expires = user_data.get("subscription_expires_at")
        if expires and datetime.fromisoformat(expires) > datetime.now():
            return AccessTier.SUBSCRIBER
    
    # Tier 3: Free tier - only is_free subdecks
    if deck.get("access_type") == "free_tier":
        return AccessTier.FREE_TIER
    
    # Tier 4: Legacy individual purchases
    if deck.get("access_type") == "legacy_purchase":
        return AccessTier.LEGACY
    
    return None  # No access

def can_sync_updates(tier: AccessTier) -> bool:
    """Free tier users cannot sync updates."""
    return tier in [AccessTier.COLLECTION_OWNER, AccessTier.SUBSCRIBER, AccessTier.LEGACY]
```

---

## Error Codes

| HTTP | Code | Description |
|------|------|-------------|
| 401 | `UNAUTHORIZED` | Invalid or expired token |
| 403 | `NO_ACCESS` | User doesn't have access to this deck |
| 403 | `SUBSCRIPTION_EXPIRED` | Subscription has expired |
| 429 | `RATE_LIMITED` | Too many requests |

---

## Pricing Summary

| Product | Price | What You Get |
|---------|-------|--------------|
| **Nottorney Collection** | ₱1,000 one-time | Own all 33,709 cards forever, full sync |
| **NottorneyHub** | ₱149/month | Access all decks, full sync, cancel anytime |
| **Free Tier** | ₱0 | Access to is_free subdecks only, no updates |
