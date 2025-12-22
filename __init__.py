"""
AnkiPH Anki Addon - DEBUG VERSION 3
Adds back full main dialog with aggressive error catching
"""

from aqt import mw
from aqt.qt import QAction
from aqt.utils import showInfo

# Lazy-loaded
logger = None
config = None
_initialized = False


def _init():
    """Load dependencies"""
    global logger, config, _initialized
    
    if _initialized:
        return True
    
    try:
        from .logger import logger as _log
        from .config import config as _cfg
        from .constants import ADDON_VERSION
        from .api_client import set_access_token
        
        logger, config = _log, _cfg
        
        if token := config.get_access_token():
            set_access_token(token)
        
        logger.info(f"AnkiPH v{ADDON_VERSION} ready")
        _initialized = True
        return True
        
    except Exception as e:
        import traceback
        print(f"✗ AnkiPH init failed:\n{traceback.format_exc()}")
        showInfo(f"AnkiPH failed to load:\n{e}")
        return False


def _on_menu_click(*_):
    """Show the main dialog with error catching"""
    if not _init():
        return
    
    try:
        # Check login first
        if not config.is_logged_in():
            from .ui.login_dialog import show_login_dialog
            if not show_login_dialog(mw):
                return
        
        # Now show main dialog
        from .ui.main_dialog import AnkiPHMainDialog
        
        dialog = AnkiPHMainDialog(mw)
        dialog.show()
        
    except Exception as e:
        import traceback
        print(f"✗ Dialog error:\n{traceback.format_exc()}")
        showInfo(f"Error opening dialog:\n{e}")


def _setup_menu():
    from .constants import ADDON_VERSION
    action = QAction("⚖️ AnkiPH", mw)
    action.triggered.connect(_on_menu_click)
    mw.form.menubar.insertAction(mw.form.menuHelp.menuAction(), action)
    print(f"✓ AnkiPH v{ADDON_VERSION} loaded (DEBUG 3)")


try:
    _setup_menu()
except Exception as e:
    print(f"✗ AnkiPH setup failed: {e}")