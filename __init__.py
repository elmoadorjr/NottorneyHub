"""
AnkiPH Anki Addon - Simplified Version
PyQt6 Compatible - v3.3.2
SIMPLIFIED: Subscription-only model, auto-sync on startup
"""

from aqt import mw, gui_hooks
from aqt.qt import QAction
from aqt.utils import showInfo, tooltip
import threading

# Global reference to prevent garbage collection
_dialog_instance = None
_dialog_lock = threading.Lock()

# Initialize logger as None first
logger = None

try:
    # Import logger FIRST before anything else
    from .logger import logger
    
    from .config import config
    from . import sync
    from .api_client import api, set_access_token
    from .update_checker import update_checker
    from .constants import ADDON_NAME, ADDON_VERSION
    
    # Use simplified main dialog (v3.0.0)
    from .ui.main_dialog import AnkiPHMainDialog as MainDialog
    from .ui.login_dialog import show_login_dialog
        
except ImportError as e:
    _import_error = str(e)
    
    def show_startup_error():
        try:
            from aqt.utils import showInfo
            showInfo(f"AnkiPH addon import error: {_import_error}\n\nPlease check that all files are present.")
        except Exception:
            print(f"✗ AnkiPH import error: {_import_error}")
    
    try:
        from aqt import gui_hooks
        gui_hooks.main_window_did_init.append(show_startup_error)
    except Exception:
        print(f"✗ Fatal AnkiPH import error: {_import_error}")


def show_settings_dialog():
    """Show settings dialog"""
    try:
        from .ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(mw)
        dialog.exec()
    except Exception as e:
        showInfo(f"Error opening settings:\n{str(e)}")
        if logger:
            logger.exception(f"Settings dialog error: {e}")


def on_menu_action(*args):
    """Smart menu action: Login -> Main Dialog"""
    try:
        if not config.is_logged_in():
            if show_login_dialog(mw):
                show_main_dialog()
        else:
            show_main_dialog()
            
    except Exception as e:
        showInfo(f"Error opening AnkiPH:\n{str(e)}")
        if logger:
            logger.exception(f"Menu action error: {e}")


def show_main_dialog():
    """Show main dialog (thread-safe)"""
    global _dialog_instance
    
    with _dialog_lock:
        # Check if dialog already exists and is visible
        if _dialog_instance and not _dialog_instance.isHidden():
            _dialog_instance.raise_()
            _dialog_instance.activateWindow()
            return

        try:
            _dialog_instance = MainDialog(mw)
            _dialog_instance.finished.connect(lambda: _on_dialog_finished())
            _dialog_instance.show()
            
        except Exception as e:
            showInfo(f"Error opening AnkiPH dialog:\n{str(e)}")
            if logger:
                logger.exception(f"Dialog error: {e}")
            _dialog_instance = None


def _on_dialog_finished():
    """Cleanup when dialog is closed"""
    global _dialog_instance
    _dialog_instance = None
    
    if config.is_logged_in():
        try:
            token = config.get_access_token()
            if token:
                set_access_token(token)
            sync.sync_progress()
            if logger:
                logger.info("Progress synced successfully after dialog close")
        except Exception as e: 
            if logger:
                logger.warning(f"Sync failed (non-critical): {e}")


def _auto_apply_updates_background():
    """Auto-apply updates in background thread"""
    try:
        update_checker.auto_apply_updates()
    except Exception as e:
        if logger:
            logger.warning(f"Auto-apply updates failed (non-critical): {e}")


def on_main_window_did_init():
    """Called when Anki's main window finishes initializing"""
    if not config.is_logged_in():
        if logger:
            logger.debug("Skipping startup tasks - user not logged in")
        return
    
    try:
        token = config.get_access_token()
        if token:
            set_access_token(token)
        
        updates = update_checker.check_for_updates(silent=True)
        
        if updates and len(updates) > 0:
            count = len(updates)
            tooltip(f"⚖️ AnkiPH: {count} deck update(s) available")
            
            # Apply updates in background thread to avoid blocking UI
            threading.Thread(
                target=_auto_apply_updates_background,
                daemon=True,
                name="AnkiPH-AutoUpdate"
            ).start()
                
    except Exception as e:
        if logger:
            logger.warning(f"AnkiPH startup check failed (non-critical): {e}")


def setup_menu():
    """Setup menu in Anki - direct action in menu bar next to Help"""
    try:
        action = QAction(f"⚖️ AnkiPH", mw)
        action.triggered.connect(on_menu_action)
        
        menubar = mw.form.menubar
        help_menu = mw.form.menuHelp
        menubar.insertAction(help_menu.menuAction(), action)
        
        if logger:
            logger.info(f"AnkiPH addon v{ADDON_VERSION} loaded successfully")
            logger.info(f"Auto-update check: {config.get_auto_check_updates()}")
        
    except Exception as e:
        if logger:
            logger.error(f"Error setting up AnkiPH menu: {e}")
        showInfo(f"AnkiPH addon failed to load:\n{str(e)}")


# Setup hooks
try:
    setup_menu()
    gui_hooks.main_window_did_init.append(on_main_window_did_init)
except Exception as e:
    print(f"✗ Fatal error loading AnkiPH addon: {e}")
    if logger:
        logger.exception("Fatal addon load error")
    showInfo(f"Fatal error loading AnkiPH addon:\n{str(e)}")