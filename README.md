# AnkiPH Anki Addon

**Version:** 4.0.0  
**Updated:** December 21, 2025  
**Compatible with:** Anki 24.x - 25.x (PyQt6)

---

## Overview

AnkiPH is an AnkiHub-style deck syncing addon for Philippine students. It provides:

- **Deck subscription & syncing** - Subscribe to decks and receive updates automatically
- **Automatic updates** - Checks for deck updates on startup
- **Progress tracking** - Syncs study progress to server
- **Notifications** - Receive announcements from deck publishers
- **Subscription-only access** - Student (₱100/mo), Regular (₱149/mo), Lifetime plans

---

## Quick Start

1. **Install** the addon in Anki
2. **Restart** Anki
3. **Open** → ⚖️ AnkiPH (in top menu bar)
4. **Login** with your account
5. **Subscribe** to access all 33,709+ cards
6. **Browse** and download decks
7. **Study** - Updates sync automatically on startup

---

## File Structure

```
AnkiPH/
├── __init__.py              # Entry point
├── api_client.py            # API client (v4 compatible)
├── config.py                # Configuration management
├── deck_importer.py         # JSON import (DB Sync)
├── sync.py                  # Progress syncing
├── update_checker.py        # Database-driven update service
├── constants.py             # URLs and version
├── utils.py                 # Helper functions
├── logger.py                # Logging configuration
├── config.json              # Default config
├── manifest.json            # Addon metadata
└── ui/
    ├── __init__.py          # UI package exports
    ├── styles.py            # Shared COLORS and DARK_THEME
    ├── components.py        # Reusable widgets
    ├── main_dialog.py       # Main deck management UI
    ├── login_dialog.py      # Login form
    ├── settings_dialog.py   # Settings + Admin features
    ├── sync_dialog.py       # Push/Pull changes
    ├── history_dialog.py    # Card history viewer
    ├── suggestion_dialog.py # Card suggestions
    └── advanced_sync_dialog.py # Tags, suspend, media sync
```

---

## Features

### Core Features
- ✅ Authentication (login/logout with JWT)
- ✅ Deck browsing and download
- ✅ Batch download (up to 10 decks)
- ✅ Automatic update checking
- ✅ Manual update application
- ✅ Notifications system
- ✅ Progress syncing (v4 format)
- ✅ Access tiers: Admin, Collection Owner, Subscriber, Deck Subscriber, Legacy, Free, Public

### Advanced Features
- ⚠️ Push/Pull card changes
- ⚠️ Conflict resolution
- ⚠️ Protected fields
- ⚠️ Card suggestions
- ⚠️ Card history & rollback
- ⚠️ Tag/suspend/media/note type sync

### Admin Features
- 🔒 Push changes to database
- 🔒 Import full decks

---

## Configuration

Access via: **Tools → Add-ons → AnkiPH → Config**

```json
{
  "auto_check_updates": true,
  "update_check_interval_hours": 24,
  "auto_sync_enabled": true
}
```

---

## API v4 Migration Notes

This addon uses API v4 with:
- Unified access hierarchy (7 tiers)
- Rate limiting with 429 responses
- Global settings in responses
- Standardized error format

---

## Troubleshooting

### "Update check failed"
1. Check internet connection
2. Verify you're logged in
3. Try: ⚖️ AnkiPH → Check for Updates

### "Session expired"
1. Open AnkiPH
2. Click Logout then Login again

### "Rate limited"
Wait for the retry period shown in the error message.

---

## Version History

### v4.0.0 (December 21, 2025) - CURRENT
- 🎨 **UI Consolidation** - Shared styles.py and components.py
- 🗑️ **Removed tabbed_dialog.py** - Deleted unused duplicate (1338 lines)
- ✨ **Modern dark theme** - Consistent styling across all dialogs
- 🔧 **API v4 compatible** - Updated access tiers, rate limiting, progress format

### v3.3.0 (December 18, 2025)
- 🔄 Subscription-only model
- ✨ Lifetime Subscriber tier

### v3.0.0 (December 17, 2025)
- 🎨 Rebranded from Nottorney to AnkiPH
- ✨ Tiered access support

---

## Support

- **Homepage:** https://anki.lovable.app
- **API Docs:** See "API Documentation" below.

---

**Stay Updated. Study Smart! 📚⚖️**

---
---

# API Documentation

## Overview

This document describes the complete API interface between the AnkiPH Anki addon and the Nottorney backend. All endpoints are Supabase Edge Functions.

**Base URL:** `https://ladvckxztcleljbiomcf.supabase.co/functions/v1`

**Authentication:** All endpoints (except `addon-login`) require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Deck Browsing & Discovery](#2-deck-browsing--discovery)
3. [Deck Subscription Management](#3-deck-subscription-management)
4. [Deck Download & Sync](#4-deck-download--sync)
5. [Card Sync & Changes](#5-card-sync--changes)
6. [User Deck Creation (Premium)](#6-user-deck-creation-premium)
7. [Suggestions & Collaboration](#7-suggestions--collaboration)
8. [Media & Note Types](#8-media--note-types)
9. [Progress & Tags Sync](#9-progress--tags-sync)
10. [Notifications](#10-notifications)
11. [Data Models](#11-data-models)
12. [Error Handling](#12-error-handling)

---

## 1. Authentication

### POST `/addon-login`

Authenticates user and returns access token with user capabilities.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "userpassword"
}
```

**Response:**
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "refresh_token_here",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_admin": false
  },
  "access": {
    "has_active_subscription": true,
    "has_full_access": true,
    "subscription_tier": "student",
    "subscription_expires_at": "2025-02-01T00:00:00Z",
    "can_create_decks": true,
    "created_decks_count": 2,
    "max_decks_allowed": 10
  },
  "subscribed_decks": [
    {
      "deck_id": "uuid",
      "title": "Nottorney Collection",
      "version": "1.0.0",
      "last_synced_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

### POST `/addon-refresh-token`

Refreshes an expired access token.

**Request:**
```json
{
  "refresh_token": "refresh_token_here"
}
```

**Response:**
```json
{
  "success": true,
  "access_token": "new_access_token",
  "refresh_token": "new_refresh_token"
}
```

---

## 2. Deck Browsing & Discovery

### POST `/addon-browse-decks`

Browse available decks with filtering options.

**Request:**
```json
{
  "category": "all",
  "search": "constitutional",
  "page": 1,
  "limit": 20
}
```

**Parameters:**
- `category`: `"all"` | `"featured"` | `"community"` | `"subscribed"`
- `search`: Optional search term
- `page`: Page number (default: 1)
- `limit`: Results per page (default: 20, max: 100)

**Response:**
```json
{
  "success": true,
  "decks": [
    {
      "id": "uuid",
      "title": "Nottorney Collection",
      "description": "Complete Philippine Bar Exam preparation deck",
      "card_count": 33709,
      "subscriber_count": 150,
      "is_featured": true,
      "is_verified": true,
      "is_public": true,
      "bar_subject": "political_law",
      "version": "1.0.0",
      "image_url": "https://...",
      "creator": {
        "id": "uuid",
        "full_name": "Nottorney",
        "is_verified": true
      },
      "is_subscribed": true,
      "updated_at": "2025-01-15T10:00:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "total_pages": 3
}
```

---

## 3. Deck Subscription Management

### POST `/addon-manage-subscription`

Manage deck subscriptions (subscribe, unsubscribe, update settings, get status).

#### Subscribe to a Deck

**Request:**
```json
{
  "action": "subscribe",
  "deck_id": "uuid",
  "sync_enabled": true,
  "notify_updates": true
}
```

**Response:**
```json
{
  "success": true,
  "subscribed": true,
  "message": "Successfully subscribed to Nottorney Collection"
}
```

#### Unsubscribe from a Deck

**Request:**
```json
{
  "action": "unsubscribe",
  "deck_id": "uuid"
}
```

#### Update Subscription Settings

**Request:**
```json
{
  "action": "update",
  "deck_id": "uuid",
  "sync_enabled": true,
  "notify_updates": false
}
```

#### Get Subscription Status

**Request:**
```json
{
  "action": "get",
  "deck_id": "uuid"
}
```

**Response:**
```json
{
  "success": true,
  "subscription": {
    "id": "uuid",
    "deck_id": "uuid",
    "user_id": "uuid",
    "sync_enabled": true,
    "notify_updates": true,
    "last_synced_at": "2025-01-15T10:00:00Z",
    "subscribed_at": "2025-01-01T00:00:00Z"
  },
  "deck": {
    "id": "uuid",
    "title": "Nottorney Collection",
    "subscriber_count": 150
  },
  "access": {
    "has_active_subscription": true,
    "has_full_access": true,
    "subscription_tier": "student",
    "can_subscribe": true
  }
}
```

---

## 4. Deck Download & Sync

### POST `/addon-download-deck`

**Core Endpoint**: Performs the initial sync for a deck.
This endpoint retrieves the complete deck structure (Note Types, Cards, Notes, Media map) in JSON format. The client uses this data to reconstruct the deck in the local Anki database.

**Why Use This?**
It separates the "Initial Install" intent from subsequent "Sync Updates" (`pull_changes`).

**Request:**
```json
{
  "deck_id": "uuid",
  "include_media": true
}
```

**Response:**
```json
{
  "success": true,
  "deck": {
    "id": "uuid",
    "title": "Nottorney Collection",
    "description": "...",
    "version": "1.0.0",
    "card_count": 33709
  },
  "cards": [
    {
      "card_guid": "abc123",
      "note_type": "Basic",
      "fields": {
        "Front": "What is due process?",
        "Back": "Due process is..."
      },
      "tags": ["constitutional", "bill-of-rights"],
      "subdeck_path": "Political Law::Constitutional Law I"
    }
  ],
  "note_types": [
    {
      "name": "Basic",
      "note_type_id": "1234567890",
      "fields": ["Front", "Back"],
      "templates": [],
      "css": "..."
    }
  ],
  "media_files": [
    {
      "file_name": "image.png",
      "file_hash": "abc123...",
      "download_url": "https://..."
    }
  ],
  "subscribed": true
}
```

### POST `/addon-check-updates`

Check if deck has updates since last sync.

**Request:**
```json
{
  "deck_id": "uuid",
  "current_version": "1.0.0",
  "last_sync_timestamp": "2025-01-15T10:00:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "has_updates": true,
  "latest_version": "1.0.1",
  "changes_count": 25,
  "change_summary": {
    "cards_added": 10,
    "cards_modified": 12,
    "cards_deleted": 3
  }
}
```

> **BACKEND UPDATE REQUIRED**: The `check_deck_updates` endpoint effectively used this structure. Ensure the backend handles the `addon-check-updates` endpoint correctly for both global and single-deck checks if intended, or rely on this unified endpoint. The client now exclusively uses `check_updates` (global) or this structure.

---

## 5. Card Sync & Changes

### POST `/addon-pull-changes`

Pull card changes since last sync (incremental sync) or all cards (full sync with pagination).

**Request:**
```json
{
  "deck_id": "uuid",
  "last_change_id": "uuid",
  "full_sync": false,
  "offset": 0,
  "limit": 1000
}
```

**Parameters:**
- `deck_id`: Required. The deck UUID.
- `last_change_id`: Optional. For incremental sync, the last change ID received.
- `full_sync`: If `true`, returns all cards from `collaborative_deck_cards`.
- `offset`: Pagination offset (default: 0). Used with `full_sync=true`.
- `limit`: Cards per page (default: 1000, max: 1000). Used with `full_sync=true`.

**Response (incremental sync - full_sync=false):**
```json
{
  "success": true,
  "changes": [
    {
      "change_id": "uuid",
      "card_guid": "abc123",
      "change_type": "modify",
      "field_name": "Back",
      "old_value": "Old answer",
      "new_value": "Updated answer",
      "version": "1.0.1",
      "created_at": "2025-01-15T10:00:00Z"
    }
  ],
  "cards_updated": 15,
  "latest_change_id": "uuid",
  "deck_version": "1.0.1"
}
```

**Response (full sync - full_sync=true):**
```json
{
  "success": true,
  "cards": [
    {
      "card_guid": "abc123",
      "note_type": "Basic",
      "fields": { "Front": "...", "Back": "..." },
      "tags": ["tag1"],
      "subdeck_path": "DeckName::SubDeck"
    }
  ],
  "note_types": [...],
  "total_cards": 32435,
  "has_more": true,
  "next_offset": 1000,
  "latest_change_id": "uuid",
  "deck_version": "1.0.1"
}
```

> **Pagination Note:** For large decks (32,000+ cards), the addon fetches cards in batches of 1000. The backend MUST return `total_cards`, `has_more`, and `next_offset` to enable pagination.

### POST `/addon-push-changes` (User Suggestions)

Push user's local changes as suggestions for review.

**Request:**
```json
{
  "deck_id": "uuid",
  "changes": [
    {
      "card_guid": "abc123",
      "field_name": "Back",
      "old_value": "Current value",
      "new_value": "Suggested improvement",
      "reason": "Added citation to SC ruling"
    }
  ]
}
```

### POST `/addon-admin-push-changes` (Admin Only)

Push authoritative changes to deck (admin/deck owner only).

**Request:**
```json
{
  "deck_id": "uuid",
  "changes": [
    {
      "card_guid": "abc123",
      "field_name": "Back",
      "old_value": "Old value",
      "new_value": "New authoritative value"
    }
  ],
  "version": "1.0.1",
  "version_notes": "Updated constitutional law cards"
}
```

---

## 6. User Deck Creation (Premium)

> **Note**: These endpoints allow users to create their own collaborative decks.
> Free users cannot access these endpoints; they can only sync decks marked as "Free" or "Public" by admins.

### POST `/addon-create-deck`

Create a new collaborative deck (premium users only).

**Request:**
```json
{
  "title": "My Criminal Law Deck",
  "description": "Personal notes on Criminal Law",
  "bar_subject": "criminal_law",
  "is_public": true,
  "tags": ["criminal", "reviewer"]
}
```

### POST `/addon-update-deck`

Update deck metadata.

**Request:**
```json
{
  "deck_id": "uuid",
  "title": "Updated Title",
  "description": "Updated description",
  "is_public": true
}
```

### POST `/addon-delete-user-deck`

Delete a user-created deck.

**Request:**
```json
{
  "deck_id": "uuid",
  "confirm": true
}
```

### POST `/addon-push-deck-cards`

Push cards to a user-created deck.

**Request:**
```json
{
  "deck_id": "uuid",
  "cards": [
    {
      "card_guid": "local-guid-123",
      "note_type": "Basic",
      "fields": {
        "Front": "Question",
        "Back": "Answer"
      },
      "tags": ["tag1", "tag2"],
      "subdeck_path": "My Deck::Subtopic"
    }
  ],
  "deleted_guids": ["guid-to-delete-1"],
  "delete_missing": false,
  "version": "1.0.1"
}
```

### POST `/addon-get-my-decks`

Get list of user's created decks.

---

## 7. Suggestions & Collaboration

### POST `/addon-submit-suggestion`

Submit a card improvement suggestion.

### POST `/addon-get-protected-fields`

Get user's protected fields (fields that won't be overwritten during sync).

### POST `/addon-get-card-history`

Get version history for a specific card.

### POST `/addon-rollback-card`

Rollback a card to a previous version.

---

## 8. Media & Note Types

### POST `/addon-sync-media`

Sync media files for a deck.

### POST `/addon-sync-note-types`

Sync note type definitions.

---

## 9. Progress & Tags Sync

### POST `/addon-sync-progress`

Sync study progress (for leaderboard integration).

**Request:**
```json
{
  "deck_id": "uuid",
  "progress": {
    "total_cards_studied": 500,
    "cards_due_today": 25,
    "retention_rate": 92.5,
    "study_time_minutes": 45,
    "mature_cards": 300,
    "young_cards": 150,
    "learning_cards": 50,
    "avg_ease_factor": 2.5,
    "current_streak_days": 7,
    "total_reviews_today": 100
  }
}
```

### POST `/addon-sync-tags`

Sync card tags.

### POST `/addon-sync-suspend-state`

Sync card suspend/bury states.

---

## 10. Notifications

### POST `/addon-check-notifications`

Check for pending notifications.

### POST `/addon-get-changelog`

Get deck changelog/version history.

**Request:**
```json
{
  "deck_id": "uuid",
  "from_version": "1.0.0"
}
```

---

## 11. Data Models

### Card Object
```json
{
  "card_guid": "string (unique identifier from Anki)",
  "note_type": "string (note type name)",
  "fields": {
    "FieldName": "Field content (HTML allowed)"
  },
  "tags": ["array", "of", "tags"],
  "subdeck_path": "Parent::Child::Grandchild"
}
```

### Deck Object
```json
{
  "id": "uuid",
  "title": "string",
  "description": "string",
  "creator_id": "uuid",
  "card_count": 0,
  "subscriber_count": 0,
  "is_featured": false,
  "is_verified": false,
  "is_public": true,
  "bar_subject": "political_law | criminal_law | civil_law | labor_law | mercantile_taxation | remedial_law",
  "version": "1.0.0"
}
```

---

## 12. Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error message describing the issue",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid authorization token |
| `FORBIDDEN` | 403 | User lacks permission for this action |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `RATE_LIMITED` | 429 | Too many requests |
| `SUBSCRIPTION_REQUIRED` | 403 | Premium subscription required |
| `DECK_LIMIT_REACHED` | 403 | User has reached max deck creation limit |

---

## Version History

- **v3.0.0** (2025-01): Unified collaborative deck system, premium deck creation
- **v2.1.0** (2024-12): Standardized API responses, conflict handling
- **v2.0.0** (2024-11): Initial AnkiHub-parity implementation