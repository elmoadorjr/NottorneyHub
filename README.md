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
├── deck_importer.py         # .apkg import
├── sync.py                  # Progress syncing
├── update_checker.py        # Update service
├── constants.py             # URLs and version
├── utils.py                 # Helper functions
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

- **Homepage:** https://nottorney.com
- **API Docs:** See `ankiph_api_docs_Version3.md`

---

**Stay Updated. Study Smart! 📚⚖️**