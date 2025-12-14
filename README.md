# Nottorney Anki Addon - Fixed for PyQt6

**Version:** 1.0.1  
**Fixed:** December 15, 2024  
**Compatible with:** Anki 24.x - 25.x (PyQt6)

---

## ✅ What Was Fixed

This version fixes **PyQt6 compatibility issues** that were causing the addon to crash on modern Anki versions.

### Main Fixes:

1. **QLineEdit.Password → QLineEdit.EchoMode.Password**
   - Fixed password field visibility in login dialog
   - Location: `ui/single_dialog.py`

2. **Qt.UserRole → Qt.ItemDataRole.UserRole**
   - Fixed deck list item data storage/retrieval
   - Locations: `ui/single_dialog.py`

3. **Qt.AlignCenter → Qt.AlignmentFlag.AlignCenter**
   - Fixed text alignment flags
   - Location: `ui/single_dialog.py`

4. **QMessageBox.Warning → QMessageBox.Icon.Warning**
   - Fixed message box icons
   - Location: `ui/single_dialog.py`

5. **DeckNameId handling**
   - Properly extracts integer deck IDs from Anki's DeckNameId objects
   - Location: `deck_importer.py`

6. **Enhanced error handling**
   - Better error messages throughout
   - Improved API client with NottorneyAPIError exception
   - Better config management with caching

7. **UI Improvements**
   - Better visual feedback for downloaded decks
   - Search functionality for deck list
   - Improved button layout and styling
   - Progress indicators during downloads

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
5. **Test deck browsing** (after login)
6. **Test deck download** (select a deck and click Download)

If you see the login dialog without any error messages, the fix is working! ✅

---

## 📋 File Structure

```
Nottorney_Addon/
├── __init__.py              # Main addon entry point (FIXED)
├── api_client.py            # API communication (FIXED)
├── config.py                # Configuration management (FIXED)
├── deck_importer.py         # Deck import functionality (FIXED)
├── sync.py                  # Progress sync (FIXED)
├── config.json              # Default configuration
├── manifest.json            # Addon metadata
├── .gitignore              # Git ignore rules
├── .gitattributes          # Git attributes
└── ui/
    ├── __init__.py         # UI package init
    └── single_dialog.py    # Main dialog (FIXED - Complete PyQt6)
```

---

## 🔧 Technical Details

### PyQt5 vs PyQt6 Changes

All PyQt6 enum changes have been properly handled:

| Feature | PyQt5 (Old) | PyQt6 (New) |
|---------|-------------|-------------|
| Password field | `QLineEdit.Password` | `QLineEdit.EchoMode.Password` ✅ |
| User data role | `Qt.UserRole` | `Qt.ItemDataRole.UserRole` ✅ |
| Alignment | `Qt.AlignCenter` | `Qt.AlignmentFlag.AlignCenter` ✅ |
| Message box icons | `QMessageBox.Warning` | `QMessageBox.Icon.Warning` ✅ |
| Colors | `Qt.darkGreen` | `Qt.GlobalColor.darkGreen` ✅ |

### Key Improvements

**ui/single_dialog.py:**
- Complete PyQt6 compatibility with all enum fixes
- Enhanced UI with better visual feedback
- Search functionality for deck filtering
- Download status indicators
- Better error messages
- Logout functionality

**deck_importer.py:**
- Properly handles DeckNameId objects from `mw.col.decks.all_names_and_ids()`
- Extracts integer ID with `deck_info.id`
- Returns integer deck IDs consistently
- Better error handling and logging

**api_client.py:**
- Custom `NottorneyAPIError` exception with status codes
- Improved error messages
- Better timeout handling
- Enhanced download validation
- Support for both `requests` and `urllib` fallback

**config.py:**
- Configuration caching to reduce file I/O
- Better error handling
- Automatic default config creation
- Type-safe deck ID handling

**sync.py:**
- Improved progress calculation
- Better retention rate tracking
- Streak calculation
- Automatic cleanup of deleted decks

---

## 🐛 Troubleshooting

### Issue: "AttributeError: type object 'QLineEdit' has no attribute 'Password'"
**Solution:** You're using the old version. Replace with this fixed version.

### Issue: "AttributeError: type object 'Qt' has no attribute 'UserRole'"
**Solution:** You're using the old version. Replace with this fixed version.

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

## 🆕 What's New in v1.0.1

- ✅ Full PyQt6 compatibility (all enums fixed)
- ✅ Fixed password field visibility
- ✅ Fixed deck list item data handling  
- ✅ Fixed text alignment
- ✅ Fixed message box icons
- ✅ Improved DeckNameId handling
- ✅ Better error messages throughout
- ✅ Enhanced API client with custom exceptions
- ✅ Improved config management with caching
- ✅ Better UI with search and visual feedback
- ✅ Improved deck cleanup on removal
- ✅ Enhanced progress syncing

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
- **Addon Version:** v1.0.1

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
5. **Browse decks** in the catalog
6. **Search** using the search box if needed
7. **Download** decks you've purchased
8. **Study** normally in Anki
9. **Progress syncs** automatically

---

## 🔍 Version History

### v1.0.1 (December 15, 2024) - CURRENT
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

**Enjoy studying with Nottorney! 📚⚖️**