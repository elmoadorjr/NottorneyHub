# Nottorney Anki Add-on API Documentation

**Version:** 2.1.0  
**Base URL:** `https://ladvckxztcleljbiomcf.supabase.co/functions/v1`  
**Last Updated:** December 17, 2025

---

## Authentication

Uses JWT Bearer authentication. Include in all requests:
```
Authorization: Bearer <access_token>
```

| Token | Validity | Usage |
|-------|----------|-------|
| `access_token` | 1 hour | API requests |
| `refresh_token` | 7 days | Get new access tokens |

---

## Error Response Format

All errors return:
```json
{
  "success": false,
  "message": "Human-readable error message"
}
```

| HTTP Code | Meaning |
|-----------|---------|
| `401` | Invalid/expired token |
| `403` | No access (deck not owned) |
| `400` | Bad request |
| `500` | Server error |

---

## Endpoints

### 1. Login
**POST** `/addon-login`

Request:
```json
{ "email": "user@example.com", "password": "..." }
```

Response:
```json
{
  "success": true,
  "access_token": "jwt...",
  "refresh_token": "...",
  "expires_at": "ISO8601",
  "user": { "id": "uuid", "email": "...", "is_admin": false }
}
```

---

### 2. Refresh Token
**POST** `/addon-refresh-token`

Request:
```json
{ "refresh_token": "..." }
```

---

### 3. Get Purchases
**POST** `/addon-get-purchases`

Response:
```json
{
  "success": true,
  "decks": [
    { "id": "uuid", "name": "...", "version": "1.0.0" }
  ]
}
```

---

### 4. Download Deck
**POST** `/addon-download-deck`

Request:
```json
{ "deck_id": "uuid" }
```

---

### 5. Pull Changes
**POST** `/addon-pull-changes`

Request:
```json
{
  "deck_id": "uuid",
  "since": "ISO8601 (optional)",
  "last_change_id": "uuid (optional)",
  "full_sync": false
}
```

Response (incremental):
```json
{
  "success": true,
  "full_sync": false,
  "changes": [
    {
      "change_id": "uuid",
      "card_guid": "anki-note-guid",
      "field_name": "Front",
      "old_value": "...",
      "new_value": "...",
      "change_type": "modify",
      "is_protected": false
    }
  ],
  "conflicts": [
    {
      "card_guid": "guid",
      "field_name": "Back",
      "local_value": "User's version",
      "server_value": "Server's version",
      "is_protected": false
    }
  ],
  "protected_fields": ["Personal Notes"],
  "has_more": false
}
```

Response (full_sync=true):
```json
{
  "success": true,
  "full_sync": true,
  "cards": [...],
  "total_cards": 1000,
  "deck_version": "1.0.0"
}
```

---

### 6. Push Changes
**POST** `/addon-push-changes`

Request:
```json
{
  "deck_id": "uuid",
  "changes": [
    {
      "card_guid": "guid",
      "field_name": "Front",
      "old_value": "...",
      "new_value": "..."
    }
  ],
  "version": "1.0.1"
}
```

Response:
```json
{
  "success": true,
  "changes_pushed": 5,
  "last_change_id": "uuid"
}
```

---

### 7. Sync Tags
**POST** `/addon-sync-tags`

Request:
```json
{
  "deck_id": "uuid",
  "action": "pull" | "push",
  "changes": [{ "card_guid": "...", "tags": ["tag1"] }],
  "since": "ISO8601 (optional)"
}
```

Response:
```json
{
  "success": true,
  "tags_added": 5,
  "tags_removed": 2
}
```

---

### 8. Sync Suspend State
**POST** `/addon-sync-suspend-state`

Request:
```json
{
  "deck_id": "uuid",
  "action": "pull" | "push",
  "changes": [{ "card_guid": "...", "is_suspended": true, "is_buried": false }]
}
```

Response:
```json
{
  "success": true,
  "cards_updated": 10
}
```

---

### 9. Sync Media
**POST** `/addon-sync-media`

Request:
```json
{
  "deck_id": "uuid",
  "action": "list" | "download" | "upload" | "get_upload_url" | "confirm_upload",
  "file_name": "image.png",
  "file_hash": "sha256..."
}
```

Response (download):
```json
{
  "success": true,
  "files": [{ "file_name": "...", "url": "signed-url" }],
  "files_downloaded": 5,
  "files_uploaded": 0
}
```

---

### 10. Sync Note Types
**POST** `/addon-sync-note-types`

Request:
```json
{
  "deck_id": "uuid",
  "action": "get" | "push",
  "note_types": []
}
```

Response:
```json
{
  "success": true,
  "note_types": [...],
  "types_updated": 2
}
```

---

### 11. Submit Suggestion
**POST** `/addon-submit-suggestion`

Request:
```json
{
  "deck_id": "uuid",
  "card_guid": "guid",
  "field_name": "Front",
  "current_value": "...",
  "suggested_value": "...",
  "reason": "Typo fix"
}
```

---

### 12. Protected Fields
**GET/POST** `/addon-protected-fields`

Get:
```json
{ "deck_id": "uuid" }
```

Set:
```json
{
  "deck_id": "uuid",
  "fields": ["Personal Notes", "Extra"]
}
```

---

## Changelog v2.1.0

- `addon-pull-changes`: Returns `change_id` (was `id`), conflicts use `local_value`/`server_value`
- All sync endpoints: Use `action` parameter (not `direction`)
- All sync endpoints: Check collection access before individual deck purchase
- Response format standardized: `{ "success": bool, "message": "..." }`