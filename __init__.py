"""
Nottorney Anki Addon
Main entry point for the addon
"""

from aqt import mw, gui_hooks
from aqt.qt import QAction
from aqt.utils import showInfo

# Import all modules at the top to catch import errors early
try:
    from .ui.login_dialog import LoginDialog
    from .ui.deck_manager_dialog import DeckManagerDialog
    from .config import config
    from . import sync  # Import the sync module
except ImportError as e:
    # If imports fail, show error and exit gracefully
    def show_import_error():
        showInfo(f"Nottorney addon import error: {str(e)}\n\nPlease reinstall the addon.")
    
    # Set up a minimal menu that shows the error
    def setup_error_menu():
        menu = mw.form.menuTools.addMenu("Nottorney (Error)")
        error_action = QAction("Show Error", mw)
        error_action.triggered.connect(show_import_error)
        menu.addAction(error_action)
    
    setup_error_menu()
    raise  # Re-raise to see full traceback

# Addon metadata
ADDON_NAME = "Nottorney"
ADDON_VERSION = "1.0.0"


def show_login():
    """Show the login dialog"""
    dialog = LoginDialog(mw)
    if dialog.exec():
        # Don't show deck manager automatically after login
        # This prevents multiple dialogs from appearing
        showInfo("Login successful! You can now manage your decks from the Tools > Nottorney menu.")


def show_deck_manager():
    """Show the deck manager dialog"""
    if not config.is_logged_in():
        showInfo("Please login first")
        show_login()
        return
    
    dialog = DeckManagerDialog(mw)
    dialog.exec()


def on_sync_progress():
    """Sync progress to server"""
    if not config.is_logged_in():
        showInfo("Please login first")
        return
    
    try:
        result = sync.sync_progress()
        if result:
            showInfo("Progress synced successfully!")
        else:
            showInfo("No decks to sync")
    except Exception as e:
        showInfo(f"Error syncing progress: {str(e)}")


def setup_menu():
    """Set up the addon menu in Anki"""
    # Create main menu
    menu = mw.form.menuTools.addMenu(ADDON_NAME)
    
    # Login action
    login_action = QAction("Login", mw)
    login_action.triggered.connect(show_login)
    menu.addAction(login_action)
    
    # Manage Decks action
    manage_action = QAction("Manage Decks", mw)
    manage_action.triggered.connect(show_deck_manager)
    menu.addAction(manage_action)
    
    # Sync Progress action
    sync_action = QAction("Sync Progress", mw)
    sync_action.triggered.connect(on_sync_progress)
    menu.addAction(sync_action)
    
    # Separator
    menu.addSeparator()
    
    # Logout action
    logout_action = QAction("Logout", mw)
    logout_action.triggered.connect(logout)
    menu.addAction(logout_action)


def logout():
    """Logout the user"""
    config.clear_tokens()
    showInfo("Logged out successfully")


def safe_auto_sync():
    """Safely attempt auto-sync without showing errors"""
    # Temporarily disabled to debug login issues
    # Will re-enable once we confirm login is stable
    return
    
    try:
        if config.is_logged_in():
            sync.sync_progress()
            print("Auto-sync completed")
    except Exception as e:
        # Silently fail for auto-sync
        print(f"Auto-sync failed: {e}")


# Initialize the addon
def init_addon():
    """Initialize the addon when Anki starts"""
    setup_menu()
    
    # Auto-sync progress on profile load (currently disabled)
    # gui_hooks.profile_did_open.append(safe_auto_sync)


# Run initialization
init_addon()