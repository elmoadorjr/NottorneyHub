"""
Nottorney Anki Addon - Simplified Version
PyQt6 Compatible - v2.1.0
SIMPLIFIED: Removed minimal UI mode, added auto-sync on startup
"""

from aqt import mw, gui_hooks
from aqt.qt import QAction
from aqt.utils import showInfo, tooltip

# Global reference to prevent garbage collection
_dialog_instance = None

try:
    from .config import config
    from . import sync
    from .api_client import api, set_access_token
    from .update_checker import update_checker
    
    # Use simplified main dialog (v2.2.0)
    from .ui.main_dialog import NottorneyMainDialog as MainDialog
        
except ImportError as e:
    # Defer error display until Anki is ready (mw might not be initialized yet)
    _import_error = str(e)
    
    def show_startup_error():
        from aqt.utils import showInfo
        showInfo(f"Nottorney addon import error: {_import_error}\n\nPlease check that all files are present.")
    
    from aqt import gui_hooks
    gui_hooks.main_window_did_init.append(show_startup_error)
    raise

ADDON_NAME = "Nottorney"
ADDON_VERSION = "2.2.0"


def show_settings_dialog():
    """Show settings dialog"""
    try:
        from .ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(mw)
        dialog.exec()
    except Exception as e:
        showInfo(f"Error opening settings:\n{str(e)}")
        print(f"Settings dialog error: {e}")
        import traceback
        traceback.print_exc()


def show_main_dialog():
    """Show main dialog"""
    global _dialog_instance
    
    try:
        # Create new dialog instance
        _dialog_instance = MainDialog(mw)
        _dialog_instance.exec()
        
        # Sync progress after dialog closes if logged in
        if config.is_logged_in():
            try:
                # Set the access token before syncing
                token = config.get_access_token()
                if token:
                    set_access_token(token)
                sync.sync_progress()
                print("✓ Progress synced successfully")
            except Exception as e: 
                print(f"Sync failed (non-critical): {e}")
    except Exception as e:
        showInfo(f"Error opening Nottorney dialog:\n{str(e)}")
        print(f"Dialog error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        _dialog_instance = None


def on_main_window_did_init():
    """Called when Anki's main window finishes initializing"""
    if not config.is_logged_in():
        return
    
    try:
        # Set access token
        token = config.get_access_token()
        if token:
            set_access_token(token)
        
        # Check for updates
        updates = update_checker.check_for_updates(silent=True)
        
        # Auto-apply updates if any available
        if updates and len(updates) > 0:
            count = len(updates)
            tooltip(f"⚖️ Nottorney: {count} deck update(s) available")
            
            # Try to auto-apply updates silently
            try:
                update_checker.auto_apply_updates()
            except Exception as e:
                print(f"Auto-apply updates failed (non-critical): {e}")
                
    except Exception as e:
        print(f"Nottorney startup check failed (non-critical): {e}")


def setup_menu():
    """Setup menu in Anki - single action opens main dialog"""
    try:
        # Add single Nottorney action to Tools menu (no submenu)
        action = QAction("⚖️ Nottorney", mw)
        action.triggered.connect(show_main_dialog)
        mw.form.menuTools.addAction(action)
        
        print(f"✓ Nottorney addon v{ADDON_VERSION} loaded successfully")
        print(f"  Auto-update check: {config.get_auto_check_updates()}")
        
    except Exception as e:
        print(f"✗ Error setting up Nottorney menu: {e}")
        showInfo(f"Nottorney addon failed to load:\n{str(e)}")


# Setup hooks
try:
    setup_menu()
    gui_hooks.main_window_did_init.append(on_main_window_did_init)
except Exception as e:
    print(f"✗ Fatal error loading Nottorney addon: {e}")
    showInfo(f"Fatal error loading Nottorney addon:\n{str(e)}")

