"""
Nottorney Anki Addon - Streamlined Minimal Version
Main entry point with automatic progress syncing
"""

from aqt import mw, gui_hooks
from aqt.qt import QAction, QMenu
from aqt.utils import showInfo

# Import modules
try:
    from .ui.login_dialog import LoginDialog
    from .ui.single_dialog import MinimalNottorneyDialog
    from .ui.notifications_dialog import NotificationsDialog
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
    access_token = config.get_access_token()
    if not access_token:
        return False
    
    if config.is_token_expired():
        try:
            result = api.refresh_token()
            if result.get('success'):
                return True
            else:
                config.clear_tokens()
                return False
        except Exception as e:
            print(f"Token refresh exception: {e}")
            config.clear_tokens()
            return False
    
    return True


def check_notifications_background():
    """Background notification check (silent)"""
    if not config.is_logged_in():
        return
    
    if not config.should_check_notifications(interval_minutes=15):
        return
    
    try:
        result = api.check_notifications(mark_as_read=False, limit=5)
        
        if result.get('success'):
            unread_count = result.get('unread_count', 0)
            config.set_unread_notification_count(unread_count)
            config.update_last_notification_check()
            update_menu()
    except Exception as e:
        print(f"Background notification check failed: {e}")


def auto_sync_progress():
    """Automatically sync progress in background"""
    if not config.is_logged_in():
        return
    
    try:
        result = sync.sync_progress()
        if result:
            print(f"Auto-synced progress: {result.get('synced_count', 0)} deck(s)")
    except Exception as e:
        print(f"Auto-sync failed: {e}")


def show_notifications():
    """Show notifications dialog"""
    if not ensure_valid_token():
        showInfo("Your session has expired. Please login again.")
        show_login()
        return
    
    dialog = NotificationsDialog(mw)
    dialog.exec()
    update_menu()


def show_minimal_dialog():
    """Show the minimalist single-dialog interface"""
    dialog = MinimalNottorneyDialog(mw)
    dialog.exec()
    
    # Auto-sync progress after closing if logged in
    if config.is_logged_in():
        auto_sync_progress()


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
        
        check_notifications_background()
        update_menu()


def logout():
    """Logout the user"""
    config.clear_tokens()
    config.set_unread_notification_count(0)
    showInfo("Logged out successfully")
    update_menu()


def update_menu():
    """Update the menu based on login state"""
    global nottorney_menu
    
    if nottorney_menu is None:
        return
    
    # Clear all existing actions
    nottorney_menu.clear()
    
    is_logged_in = config.is_logged_in()
    
    # Main action
    main_action = QAction("🎯 Open Nottorney", mw)
    main_action.triggered.connect(show_minimal_dialog)
    nottorney_menu.addAction(main_action)
    
    # Notifications (if logged in)
    if is_logged_in:
        unread_count = config.get_unread_notification_count()
        if unread_count > 0:
            notif_text = f"🔔 Notifications ({unread_count})"
        else:
            notif_text = "🔔 Notifications"
        
        notif_action = QAction(notif_text, mw)
        notif_action.triggered.connect(show_notifications)
        nottorney_menu.addAction(notif_action)
        
        nottorney_menu.addSeparator()
        
        # Logout action
        logout_action = QAction("🚪 Logout", mw)
        logout_action.triggered.connect(logout)
        nottorney_menu.addAction(logout_action)
    else:
        nottorney_menu.addSeparator()
        
        # Login action
        login_action = QAction("🔑 Login", mw)
        login_action.triggered.connect(show_login)
        nottorney_menu.addAction(login_action)


def on_profile_loaded():
    """Hook that runs when Anki profile is loaded"""
    if config.is_logged_in():
        # Check notifications in background
        check_notifications_background()


def on_main_window_state_change(new_state, old_state):
    """Hook that runs when main window state changes"""
    # Auto-sync when user finishes a study session
    if config.is_logged_in() and new_state == "overview":
        auto_sync_progress()


def setup_menu():
    """Set up the addon menu in Anki"""
    global nottorney_menu
    
    nottorney_menu = mw.form.menuTools.addMenu("⚖️ Nottorney")
    update_menu()


def init_addon():
    """Initialize the addon when Anki starts"""
    print("=== Initializing Nottorney Addon (Minimal Mode) ===")
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
    
    # Register hooks
    gui_hooks.profile_did_open.append(on_profile_loaded)
    gui_hooks.main_window_did_init.append(lambda: check_notifications_background())
    
    # Auto-sync progress hook (when deck browser is shown)
    try:
        gui_hooks.state_did_change.append(on_main_window_state_change)
    except:
        pass  # Fallback if hook not available
    
    print("=== Nottorney Addon Initialized ===")


# Run initialization
init_addon()