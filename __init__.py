"""
Nottorney Anki Addon
Main entry point for the addon
"""

from aqt import mw, gui_hooks
from aqt.qt import QAction, QMenu
from aqt.utils import showInfo

# Import all modules at the top to catch import errors early
try:
    from .ui.login_dialog import LoginDialog
    from .ui.deck_manager_dialog import DeckManagerDialog
    from .config import config
    from . import sync
    from .api_client import api
except ImportError as e:
    def show_import_error():
        showInfo(f"Nottorney addon import error: {str(e)}\n\nPlease reinstall the addon.")
    
    def setup_error_menu():
        menu = mw.form.menuTools.addMenu("Nottorney (Error)")
        error_action = QAction("Show Error", mw)
        error_action.triggered.connect(show_import_error)
        menu.addAction(error_action)
    
    setup_error_menu()
    raise

# Addon metadata
ADDON_NAME = "Nottorney"
ADDON_VERSION = "1.0.0"

# Global menu reference
nottorney_menu = None


def ensure_valid_token():
    """Ensure we have a valid token, refresh if needed"""
    print("=== Checking token validity ===")
    
    access_token = config.get_access_token()
    if not access_token:
        print("No access token found")
        return False
    
    if config.is_token_expired():
        try:
            print("Token expired, attempting refresh...")
            result = api.refresh_token()
            if result.get('success'):
                print("Token refresh successful!")
                return True
            else:
                print(f"Token refresh failed: {result}")
                config.clear_tokens()
                return False
        except Exception as e:
            print(f"Token refresh exception: {e}")
            config.clear_tokens()
            return False
    
    print("Token is valid")
    return True


def show_login():
    """Show the login dialog"""
    dialog = LoginDialog(mw)
    if dialog.exec():
        user = config.get_user()
        if user:
            email = user.get('email', 'User')
            showInfo(f"Login successful! Welcome, {email}.")
        else:
            showInfo("Login successful!")
        
        # Update menu after successful login
        update_menu()


def show_deck_manager():
    """Show the deck manager dialog"""
    print("=== Opening Deck Manager ===")
    
    if not ensure_valid_token():
        print("Token validation failed, showing login")
        showInfo("Your session has expired. Please login again.")
        show_login()
        return
    
    print("Token valid, opening deck manager")
    dialog = DeckManagerDialog(mw)
    dialog.exec()


def on_sync_progress():
    """Sync progress to server"""
    print("=== Manual Sync Progress ===")
    
    if not ensure_valid_token():
        print("Token validation failed, showing login")
        showInfo("Your session has expired. Please login again.")
        show_login()
        return
    
    try:
        result = sync.sync_progress()
        if result:
            synced_count = result.get('synced_count', 0)
            showInfo(f"Progress synced successfully! {synced_count} deck(s) updated.")
        else:
            showInfo("No decks to sync. Download some decks first!")
    except Exception as e:
        print(f"Sync error: {e}")
        showInfo(f"Error syncing progress: {str(e)}")


def logout():
    """Logout the user"""
    print("=== Logging out ===")
    config.clear_tokens()
    showInfo("Logged out successfully")
    
    # Update menu after logout
    update_menu()


def update_menu():
    """Update the menu based on login state"""
    global nottorney_menu
    
    if nottorney_menu is None:
        return
    
    # Clear all existing actions
    nottorney_menu.clear()
    
    is_logged_in = config.is_logged_in()
    
    if is_logged_in:
        # Show logged-in menu options
        user = config.get_user()
        if user:
            email = user.get('email', 'User')
            user_label = QAction(f"👤 {email}", mw)
            user_label.setEnabled(False)  # Make it non-clickable
            nottorney_menu.addAction(user_label)
            nottorney_menu.addSeparator()
        
        # Manage Decks action
        manage_action = QAction("📚 Manage Decks", mw)
        manage_action.triggered.connect(show_deck_manager)
        nottorney_menu.addAction(manage_action)
        
        # Sync Progress action
        sync_action = QAction("🔄 Sync Progress", mw)
        sync_action.triggered.connect(on_sync_progress)
        nottorney_menu.addAction(sync_action)
        
        nottorney_menu.addSeparator()
        
        # Logout action
        logout_action = QAction("🚪 Logout", mw)
        logout_action.triggered.connect(logout)
        nottorney_menu.addAction(logout_action)
    else:
        # Show logged-out menu options
        login_action = QAction("🔑 Login", mw)
        login_action.triggered.connect(show_login)
        nottorney_menu.addAction(login_action)
        
        nottorney_menu.addSeparator()
        
        # Info action
        info_action = QAction("ℹ️ About Nottorney", mw)
        info_action.triggered.connect(show_about)
        nottorney_menu.addAction(info_action)


def show_about():
    """Show information about Nottorney"""
    showInfo(
        f"<h2>Nottorney for Anki</h2>"
        f"<p>Version {ADDON_VERSION}</p>"
        f"<p>Manage and sync your Nottorney flashcard decks.</p>"
        f"<p><b>Please login to access your purchased decks.</b></p>"
        f"<br>"
        f"<p>Visit: <a href='https://nottorney.lovable.app'>nottorney.lovable.app</a></p>"
    )


def setup_menu():
    """Set up the addon menu in Anki"""
    global nottorney_menu
    
    # Create main menu
    nottorney_menu = mw.form.menuTools.addMenu(f"⚖️ {ADDON_NAME}")
    
    # Initial menu population
    update_menu()


def safe_auto_sync():
    """Safely attempt auto-sync without showing errors"""
    # Disabled for now to avoid login interruptions
    return
    
    print("=== Auto-sync triggered ===")
    try:
        if ensure_valid_token():
            sync.sync_progress()
            print("Auto-sync completed")
        else:
            print("Auto-sync skipped: not logged in")
    except Exception as e:
        print(f"Auto-sync failed: {e}")


def init_addon():
    """Initialize the addon when Anki starts"""
    print("=== Initializing Nottorney Addon ===")
    print(f"Addon name: {config.addon_name}")
    
    # Check initial login state
    if config.is_logged_in():
        user = config.get_user()
        if user:
            print(f"User logged in: {user.get('email', 'unknown')}")
        else:
            print("Token exists but no user data")
    else:
        print("User not logged in")
    
    setup_menu()
    
    print("=== Nottorney Addon Initialized ===")


# Run initialization
init_addon()