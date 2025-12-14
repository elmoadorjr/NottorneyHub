"""
Nottorney Anki Addon - Fixed Version
PyQt6 Compatible - v1.0.1
"""

from aqt import mw, gui_hooks
from aqt.qt import QAction
from aqt.utils import showInfo

# Global reference to prevent garbage collection
_dialog_instance = None

try:
    from .ui.single_dialog import MinimalNottorneyDialog
    from .config import config
    from . import sync
    from .api_client import api, set_access_token
except ImportError as e:
    def show_error():
        showInfo(f"Nottorney addon import error: {str(e)}\n\nPlease check that all files are present.")
    show_error()
    raise

ADDON_NAME = "Nottorney"
ADDON_VERSION = "1.0.1"


def show_main_dialog():
    """Show main dialog"""
    global _dialog_instance
    
    try:
        # Create new dialog instance
        _dialog_instance = MinimalNottorneyDialog(mw)
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
    finally:
        _dialog_instance = None


def setup_menu():
    """Setup menu in Anki"""
    try:
        # Create Nottorney menu
        menu = mw.form.menuTools.addMenu("⚖️ Nottorney")
        
        # Add "Open" action
        action = QAction("Open Nottorney", mw)
        action.triggered.connect(show_main_dialog)
        menu.addAction(action)
        
        print(f"✓ Nottorney addon v{ADDON_VERSION} loaded successfully")
    except Exception as e:
        print(f"✗ Error setting up Nottorney menu: {e}")
        showInfo(f"Nottorney addon failed to load:\n{str(e)}")


# Setup menu when Anki loads
try:
    setup_menu()
except Exception as e:
    print(f"✗ Fatal error loading Nottorney addon: {e}")
    showInfo(f"Fatal error loading Nottorney addon:\n{str(e)}")