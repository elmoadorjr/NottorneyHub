"""
Nottorney Anki Addon
Main entry point with MINIMALIST dialog option
"""

from aqt import mw, gui_hooks
from aqt.qt import QAction, QMenu
from aqt.utils import showInfo

# Import all modules at the top to catch import errors early
try:
    from .ui.login_dialog import LoginDialog
    from .ui.deck_manager_dialog import DeckManagerDialog
    from .ui.sync_dialog import SyncDialog
    from .ui.single_dialog import MinimalNottorneyDialog  # NEW
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

# UI Mode Setting - Choose your preferred interface style
# Options: "minimal", "classic", "auto-sync"
UI_MODE = config.get_ui_mode() if hasattr(config, 'get_ui_mode') else "minimal"

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


def show_minimal_dialog():
    """Show the minimalist single-dialog interface (RECOMMENDED)"""
    print("=== Opening Minimal Dialog ===")
    dialog = MinimalNottorneyDialog(mw)
    dialog.exec()


def show_login():
    """Show the login dialog (CLASSIC)"""
    dialog = LoginDialog(mw)
    if dialog.exec():
        user = config.get_user()
        if user:
            email = user.get('email', 'User')
            showInfo(f"Login successful! Welcome, {email}.")
        else:
            showInfo("Login successful!")
        
        update_menu()


def show_sync_decks():
    """Show the auto-sync dialog for one-click deck syncing (CLASSIC)"""
    print("=== Opening Sync Decks Dialog ===")
    
    if not ensure_valid_token():
        print("Token validation failed, showing login")
        showInfo("Your session has expired. Please login again.")
        show_login()
        return
    
    print("Token valid, opening sync dialog")
    dialog = SyncDialog(mw)
    dialog.exec()


def show_deck_manager():
    """Show the deck manager dialog (CLASSIC - for advanced users)"""
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
    update_menu()


def switch_to_minimal_mode():
    """Switch to minimal UI mode"""
    global UI_MODE
    UI_MODE = "minimal"
    if hasattr(config, 'set_ui_mode'):
        config.set_ui_mode("minimal")
    showInfo("Switched to Minimal Mode! 🎯\n\nReopen Nottorney to use the simplified interface.")
    update_menu()


def switch_to_classic_mode():
    """Switch to classic UI mode"""
    global UI_MODE
    UI_MODE = "classic"
    if hasattr(config, 'set_ui_mode'):
        config.set_ui_mode("classic")
    showInfo("Switched to Classic Mode! 📚\n\nReopen Nottorney to use the full-featured interface.")
    update_menu()


def update_menu():
    """Update the menu based on login state and UI mode"""
    global nottorney_menu
    
    if nottorney_menu is None:
        return
    
    # Clear all existing actions
    nottorney_menu.clear()
    
    is_logged_in = config.is_logged_in()
    
    # === MINIMAL MODE ===
    if UI_MODE == "minimal":
        # Just one action - open the minimal dialog
        main_action = QAction("🎯 Open Nottorney", mw)
        main_action.triggered.connect(show_minimal_dialog)
        nottorney_menu.addAction(main_action)
        
        nottorney_menu.addSeparator()
        
        # Switch to classic mode option
        switch_action = QAction("📚 Switch to Classic Mode", mw)
        switch_action.triggered.connect(switch_to_classic_mode)
        nottorney_menu.addAction(switch_action)
        
        return
    
    # === CLASSIC MODE ===
    if is_logged_in:
        # Show logged-in menu options
        user = config.get_user()
        if user:
            email = user.get('email', 'User')
            user_label = QAction(f"👤 {email}", mw)
            user_label.setEnabled(False)
            nottorney_menu.addAction(user_label)
            nottorney_menu.addSeparator()
        
        # Sync Decks action (PRIMARY)
        sync_decks_action = QAction("🔄 Sync My Decks", mw)
        sync_decks_action.triggered.connect(show_sync_decks)
        sync_decks_action.setToolTip("Automatically download all your purchased decks")
        nottorney_menu.addAction(sync_decks_action)
        
        # Manage Decks action (SECONDARY)
        manage_action = QAction("📚 Browse & Download", mw)
        manage_action.triggered.connect(show_deck_manager)
        manage_action.setToolTip("Browse and selectively download decks")
        nottorney_menu.addAction(manage_action)
        
        # Sync Progress action
        sync_progress_action = QAction("📊 Sync Study Progress", mw)
        sync_progress_action.triggered.connect(on_sync_progress)
        sync_progress_action.setToolTip("Upload your study progress to Nottorney")
        nottorney_menu.addAction(sync_progress_action)
        
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
    
    # Add UI mode switcher in classic mode
    nottorney_menu.addSeparator()
    switch_action = QAction("🎯 Switch to Minimal Mode", mw)
    switch_action.triggered.connect(switch_to_minimal_mode)
    nottorney_menu.addAction(switch_action)


def show_about():
    """Show information about Nottorney"""
    mode_info = "Minimal Mode 🎯" if UI_MODE == "minimal" else "Classic Mode 📚"
    
    showInfo(
        f"<h2>Nottorney for Anki</h2>"
        f"<p>Version {ADDON_VERSION} - <b>{mode_info}</b></p>"
        f"<p>Automatically sync your Nottorney flashcard decks.</p>"
        f"<p><b>Please login to access your purchased decks.</b></p>"
        f"<br>"
        f"<p><small>💡 Tip: Switch between Minimal and Classic modes from the menu!</small></p>"
        f"<br>"
        f"<p>Visit: <a href='https://nottorney.lovable.app'>nottorney.lovable.app</a></p>"
    )


def setup_menu():
    """Set up the addon menu in Anki"""
    global nottorney_menu
    
    # Create main menu with mode indicator
    menu_title = "⚖️ Nottorney"
    if UI_MODE == "minimal":
        menu_title += " 🎯"  # Minimal mode indicator
    
    nottorney_menu = mw.form.menuTools.addMenu(menu_title)
    
    # Initial menu population
    update_menu()


def safe_auto_sync():
    """Safely attempt auto-sync without showing errors"""
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
    print(f"UI Mode: {UI_MODE}")
    
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