# Nottorney Anki Addon - Fixed for PyQt6

**Version:** 1.0.2  
**Updated:** December 15, 2024  
**Compatible with:** Anki 24.x - 25.x (PyQt6)

---

## ✅ What's New in v1.0.2

This version adds critical backend compatibility fixes:

### Main Fixes:

1. **API browse_decks action parameter**
   - Added required `action: "list"` parameter to browse_decks endpoint
   - Location: `api_client.py`

2. **Response format handling**
   - Now handles both `{success: true, decks: [...]}` and `{decks: [...]}` response formats
   - Location: `ui/single_dialog.py`

3. **Deck field name compatibility**
   - Changed from `deck.name` to `deck.title` (backend field name)
   - Fallback to `name` for backward compatibility
   - Location: `ui/single_dialog.py`

4. **Enhanced .gitignore**
   - Added Python cache files (`__pycache__/`, `*.pyc`)
   - Added common Python build artifacts

---

## 📦 Installation

### Method 1: Complete Replacement (Recommended)

1. **Close Anki completely**

2. **Navigate to your Anki addons folder:**
   - **Windows:** `C:\Users\[YourUsername]\AppData\Roaming\Anki2\addons21\`
   - **Mac:** `~/Library/Application Support/Anki2/addons21/`
   - **Linux:** `~/.local/share/Anki2/addons21/`

3. **Backup your current addon (if you have one):**
   ```
   Rename "Nottorney_Addon" to "Nottorney_Addon_OLD"
   ```

4. **Copy the fixed addon:**
   - Copy the entire `Nottorney_Addon` folder from this package
   - Paste it into the `addons21` directory

5. **Restart Anki**

6. **Verify installation:**
   - Open Anki
   - Go to: Tools → ⚖️ Nottorney → Open Nottorney
   - The dialog should open without errors

---

## 🧪 Testing the Fix

After installation:

1. **Open Anki**
2. **Go to:** Tools → ⚖️ Nottorney → Open Nottorney
3. **The dialog should open without any errors** ✅
4. **Test login** (if you have an account)
5. **Test deck browsing** (after login) - Should now work properly!
6. **Test deck download** (select a deck and click Download)

If you see the login dialog without any error messages, and can browse decks after login, the fix is working! ✅

---

## 📋 File Structure

```
Nottorney_Addon/
├── __init__.py              # Main addon entry point (FIXED)
├── api_client.py            # API communication (FIXED v1.0.2)
├── config.py                # Configuration management (FIXED)
├── deck_importer.py         # Deck import functionality (FIXED)
├── sync.py                  # Progress sync (FIXED)
├── config.json              # Default configuration
├── manifest.json            # Addon metadata
├── .gitignore              # Git ignore rules (UPDATED v1.0.2)
├── .gitattributes          # Git attributes
└── ui/
    ├── __init__.py         # UI package init
    └── single_dialog.py    # Main dialog (FIXED v1.0.2 - Backend compatibility)
```

---

## 🔧 Technical Details

### v1.0.2 Backend Compatibility Fixes

| Component | Issue | Fix | File |
|-----------|-------|-----|------|
| browse_decks | Missing `action` parameter | Added `action: "list"` to request body | `api_client.py` |
| Response handling | Only checked `success` field | Now checks for `decks` key OR `success` | `ui/single_dialog.py` |
| Deck name | Used `deck.name` field | Changed to `deck.title` with `name` fallback | `ui/single_dialog.py` |

### PyQt5 vs PyQt6 Changes (v1.0.1)

All PyQt6 enum changes have been properly handled:

| Feature | PyQt5 (Old) | PyQt6 (New) |
|---------|-------------|-------------|
| Password field | `QLineEdit.Password` | `QLineEdit.EchoMode.Password` ✅ |
| User data role | `Qt.UserRole` | `Qt.ItemDataRole.UserRole` ✅ |
| Alignment | `Qt.AlignCenter` | `Qt.AlignmentFlag.AlignCenter` ✅ |
| Message box icons | `QMessageBox.Warning` | `QMessageBox.Icon.Warning` ✅ |
| Colors | `Qt.darkGreen` | `Qt.GlobalColor.darkGreen` ✅ |

### Key Improvements

**api_client.py (v1.0.2):**
- Added `action` parameter to `browse_decks()` method
- Ensures backend compatibility with default "list" action
- Supports optional `subject` and `search` parameters

**ui/single_dialog.py (v1.0.2):**
- Improved response format handling in `load_decks()`
- Changed deck field access from `name` to `title`
- Added fallback for backward compatibility
- Better error messages for API failures

**ui/single_dialog.py (v1.0.1):**
- Complete PyQt6 compatibility with all enum fixes
- Enhanced UI with better visual feedback
- Search functionality for deck filtering
- Download status indicators
- Better error messages
- Logout functionality

**deck_importer.py (v1.0.1):**
- Properly handles DeckNameId objects from `mw.col.decks.all_names_and_ids()`
- Extracts integer ID with `deck_info.id`
- Returns integer deck IDs consistently
- Better error handling and logging

**api_client.py (v1.0.1):**
- Custom `NottorneyAPIError` exception with status codes
- Improved error messages
- Better timeout handling
- Enhanced download validation
- Support for both `requests` and `urllib` fallback

**config.py (v1.0.1):**
- Configuration caching to reduce file I/O
- Better error handling
- Automatic default config creation
- Type-safe deck ID handling

**sync.py (v1.0.1):**
- Improved progress calculation
- Better retention rate tracking
- Streak calculation
- Automatic cleanup of deleted decks

---

## 🐛 Troubleshooting

### Issue: "No decks showing after login"
**Solution:** You're using v1.0.1. Upgrade to v1.0.2 which includes backend compatibility fixes.

### Issue: Deck names not displaying correctly
**Solution:** Upgrade to v1.0.2 which uses the correct `title` field.

### Issue: "AttributeError: type object 'QLineEdit' has no attribute 'Password'"
**Solution:** You're using the old version. Replace with this fixed version (v1.0.1+).

### Issue: "AttributeError: type object 'Qt' has no attribute 'UserRole'"
**Solution:** You're using the old version. Replace with this fixed version (v1.0.1+).

### Issue: "Module not found" errors
**Solution:** 
1. Make sure folder is named exactly `Nottorney_Addon`
2. Check that all files are present (see File Structure above)
3. Make sure the `ui` subfolder exists with both files
4. Restart Anki completely

### Issue: Dialog won't open
**Solution:**
1. Check Anki's console for errors: Help → View Console
2. Check errors log: Tools → Add-ons → View Files → addons21 → errors.log
3. Disable other addons temporarily to check for conflicts
4. Make sure you're using Anki 24.x or later

### Issue: "Config is None" warnings
**Solution:** This is normal on first run. The addon will create default config automatically.

### Issue: Login fails
**Solution:**
1. Check your internet connection
2. Verify your email and password are correct
3. Check the console for detailed error messages
4. Contact Nottorney support if the issue persists

### Issue: Deck download fails
**Solution:**
1. Make sure you've purchased the deck
2. Check your internet connection
3. Try logging out and back in
4. Check the console for detailed error messages

---

## 📝 Configuration

The addon stores configuration in Anki's addon manager. You can manually edit if needed:

1. Go to: Tools → Add-ons
2. Select "Nottorney"
3. Click "Config"

Key settings:
- `api_url`: API endpoint (default: Supabase function)
- `auto_sync_enabled`: Enable automatic progress sync
- `downloaded_decks`: Tracks downloaded decks (don't edit manually)
- `access_token`: Your login token (don't edit manually)

---

## 🆕 Version History

### v1.0.2 (December 15, 2024) - CURRENT
- ✅ Fixed browse_decks missing `action` parameter
- ✅ Fixed response format handling (checks for `decks` key)
- ✅ Fixed deck field names (`title` instead of `name`)
- ✅ Enhanced .gitignore for Python cache files
- ✅ Backward compatibility with old response formats

### v1.0.1 (December 15, 2024)
- Fixed all PyQt6 compatibility issues
- Complete enum updates for PyQt6
- Improved deck import handling
- Better error messages and handling
- Enhanced config management
- UI improvements (search, visual feedback)
- Better progress syncing

### v1.0.0 (Original)
- Initial release
- Basic deck download functionality
- Progress sync
- PyQt5 compatible only

---

## ⚠️ Known Limitations

1. **Anki 23.x and earlier:** Not compatible (uses PyQt5)
2. **Multiple decks:** API might have rate limits on batch downloads
3. **Network errors:** Limited retry logic (fails fast)
4. **Large decks:** May take time to download depending on connection

---

## 🔗 Support

- **Homepage:** https://nottorney.lovable.app
- **Issues:** Report via GitHub or contact support
- **Anki Version:** Check with Help → About Anki
- **Addon Version:** v1.0.2

---

## 📄 License

Copyright © 2024 Nottorney Team  
All rights reserved.

---

## 🎯 Quick Start Guide

1. **Install the addon** (see Installation above)
2. **Restart Anki**
3. **Open Nottorney:** Tools → ⚖️ Nottorney → Open Nottorney
4. **Login** with your Nottorney account
5. **Browse decks** in the catalog (now working properly! ✅)
6. **Search** using the search box if needed
7. **Download** decks you've purchased
8. **Study** normally in Anki
9. **Progress syncs** automatically

---

**Enjoy studying with Nottorney! 📚⚖️**