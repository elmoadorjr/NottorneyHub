"""
Enhanced Minimal Dialog with Batch Download & Changelog Support
Now uses /addon-batch-download and /addon-get-changelog endpoints
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, Qt, QWidget, QTextEdit, QScrollArea
)
from aqt import mw
from ..api_client import api, NottorneyAPIError
from ..config import config
from ..deck_importer import import_deck

# Minimalist stylesheet (same as before)
MINIMAL_STYLE = """
QDialog { background-color: #1a1a1a; color: #e0e0e0; }
QLabel { color: #e0e0e0; font-size: 14px; }
QLabel#title { font-size: 24px; font-weight: bold; color: #ffffff; }
QLabel#status { color: #888; font-size: 13px; }
QPushButton {
    background-color: #2a2a2a; border: 1px solid #404040;
    border-radius: 6px; padding: 12px 24px; color: #e0e0e0; font-size: 14px;
}
QPushButton:hover { background-color: #333; border-color: #555; }
QPushButton:disabled { background-color: #1a1a1a; color: #555; }
QPushButton#primary {
    background-color: #4caf50; border: none; color: white; font-weight: bold;
}
QPushButton#primary:hover { background-color: #45a049; }
QPushButton#primary:disabled { background-color: #2a4a2b; color: #666; }
QPushButton#secondary {
    background-color: transparent; border: none; color: #888;
    padding: 8px 16px; font-size: 13px;
}
QPushButton#secondary:hover { color: #aaa; }
QPushButton#notification {
    background-color: #ff5722; border: none; color: white;
    padding: 8px 16px; font-size: 13px; font-weight: bold;
}
QPushButton#notification:hover { background-color: #f4511e; }
QLineEdit {
    background-color: #2a2a2a; border: 1px solid #404040;
    border-radius: 6px; padding: 10px; color: #e0e0e0; font-size: 14px;
}
QLineEdit:focus { border-color: #4caf50; }
QProgressBar {
    border: 1px solid #404040; border-radius: 6px;
    background-color: #2a2a2a; text-align: center;
    color: #e0e0e0; height: 24px;
}
QProgressBar::chunk { background-color: #4caf50; border-radius: 5px; }
QListWidget {
    background-color: #2a2a2a; border: 1px solid #404040;
    border-radius: 6px; outline: none; color: #e0e0e0;
}
QListWidget::item { padding: 12px; border-bottom: 1px solid #333; }
QListWidget::item:hover { background-color: #333; }
QListWidget::item:selected { background-color: #4caf50; color: white; }
QTextEdit {
    background-color: #1a1a1a; color: #00ff00;
    border: 1px solid #404040; border-radius: 6px;
    font-family: monospace; font-size: 11px;
}
"""


class MinimalNottorneyDialog(QDialog):
    """Enhanced minimal dialog with batch download & changelog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nottorney")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(MINIMAL_STYLE)
        
        self.decks = []
        self.is_syncing = False
        self.show_advanced = False
        self.show_log = False
        
        self.setup_ui()
        self.run_startup_cleanup()
        self.check_login()
    
    def setup_ui(self):
        """Minimal UI setup"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        self.title_label = QLabel("Nottorney")
        self.title_label.setObjectName("title")
        layout.addWidget(self.title_label)
        
        # Status
        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Login section
        self.login_widget = self.create_login_section()
        layout.addWidget(self.login_widget)
        
        # Sync section
        self.sync_widget = self.create_sync_section()
        layout.addWidget(self.sync_widget)
        
        # Advanced section
        self.advanced_widget = self.create_advanced_section()
        layout.addWidget(self.advanced_widget)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.hide()
        layout.addWidget(self.progress)
        
        # Debug log
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setMaximumHeight(150)
        self.log_widget.hide()
        layout.addWidget(self.log_widget)
        
        # Bottom actions
        bottom = QHBoxLayout()
        
        # Notification button (hidden by default)
        self.notif_btn = QPushButton("🔔")
        self.notif_btn.setObjectName("notification")
        self.notif_btn.clicked.connect(self.show_notifications)
        self.notif_btn.setToolTip("View notifications")
        self.notif_btn.hide()
        
        self.cleanup_btn = QPushButton("Clean Tracking")
        self.cleanup_btn.setObjectName("secondary")
        self.cleanup_btn.clicked.connect(self.manual_cleanup)
        self.cleanup_btn.setToolTip("Remove tracking for deleted decks")
        
        self.advanced_btn = QPushButton("Browse Decks")
        self.advanced_btn.setObjectName("secondary")
        self.advanced_btn.clicked.connect(self.toggle_advanced)
        self.advanced_btn.hide()
        
        self.log_btn = QPushButton("Show Log")
        self.log_btn.setObjectName("secondary")
        self.log_btn.clicked.connect(self.toggle_log)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.setObjectName("secondary")
        self.close_btn.clicked.connect(self.accept)
        
        bottom.addWidget(self.notif_btn)
        bottom.addWidget(self.cleanup_btn)
        bottom.addWidget(self.log_btn)
        bottom.addWidget(self.advanced_btn)
        bottom.addStretch()
        bottom.addWidget(self.close_btn)
        layout.addLayout(bottom)
        
        self.setLayout(layout)
    
    def create_login_section(self):
        """Login section"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.returnPressed.connect(self.handle_login)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.handle_login)
        
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setObjectName("primary")
        self.login_btn.clicked.connect(self.handle_login)
        
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_btn)
        
        widget.setLayout(layout)
        widget.hide()
        return widget
    
    def create_sync_section(self):
        """Sync section"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        self.sync_status = QLabel("")
        
        self.sync_btn = QPushButton("Download All")
        self.sync_btn.setObjectName("primary")
        self.sync_btn.clicked.connect(self.sync_all)
        
        self.refresh_btn = QPushButton("Refresh Status")
        self.refresh_btn.setObjectName("secondary")
        self.refresh_btn.clicked.connect(self.load_deck_status)
        
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setObjectName("secondary")
        self.logout_btn.clicked.connect(self.handle_logout)
        
        layout.addWidget(self.sync_status)
        layout.addWidget(self.sync_btn)
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.logout_btn)
        
        widget.setLayout(layout)
        widget.hide()
        return widget
    
    def create_advanced_section(self):
        """Advanced section"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search decks...")
        self.search_input.textChanged.connect(self.filter_decks)
        
        self.deck_list = QListWidget()
        self.deck_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.deck_list.itemDoubleClicked.connect(self.show_deck_changelog)
        
        btn_layout = QHBoxLayout()
        
        download_btn = QPushButton("Download Selected")
        download_btn.setObjectName("primary")
        download_btn.clicked.connect(self.download_selected)
        
        changelog_btn = QPushButton("View Changelog")
        changelog_btn.setObjectName("secondary")
        changelog_btn.clicked.connect(lambda: self.show_deck_changelog(self.deck_list.currentItem()))
        
        btn_layout.addWidget(download_btn)
        btn_layout.addWidget(changelog_btn)
        
        layout.addWidget(self.search_input)
        layout.addWidget(self.deck_list)
        layout.addLayout(btn_layout)
        
        widget.setLayout(layout)
        widget.hide()
        return widget
    
    def log(self, message):
        """Add to debug log"""
        self.log_widget.append(message)
        print(message)
    
    def log_api_response(self, response_dict):
        """Log API response in a readable format"""
        import json
        try:
            formatted = json.dumps(response_dict, indent=2)
            self.log(f"API Response:\n{formatted}")
        except:
            self.log(f"API Response: {response_dict}")
    
    def log_api_response(self, response_dict):
        """Log API response in a readable format"""
        import json
        try:
            formatted = json.dumps(response_dict, indent=2)
            self.log(f"API Response:\n{formatted}")
        except:
            self.log(f"API Response: {response_dict}")
    
    def toggle_log(self):
        """Toggle log visibility"""
        self.show_log = not self.show_log
        self.log_widget.setVisible(self.show_log)
        self.log_btn.setText("Hide Log" if self.show_log else "Show Log")
        self.setMinimumHeight(600 if self.show_log else 400)
    
    def run_startup_cleanup(self):
        """Run automatic cleanup on startup"""
        self.log("\n=== STARTUP CLEANUP ===")
        try:
            cleaned, total = config.cleanup_deleted_decks()
            if cleaned > 0:
                self.log(f"✓ Cleaned up {cleaned} deleted deck(s)")
            else:
                self.log(f"✓ All {total} tracked deck(s) are valid")
        except Exception as e:
            self.log(f"✗ Cleanup error: {e}")
    
    def manual_cleanup(self):
        """Manual cleanup trigger"""
        reply = QMessageBox.question(
            self, "Clean Tracking",
            "Remove tracking for decks that no longer exist in Anki?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            cleaned, total = config.cleanup_deleted_decks()
            if cleaned > 0:
                QMessageBox.information(
                    self, "Cleanup Complete",
                    f"Removed tracking for {cleaned} deleted deck(s).\n\nRemaining: {total - cleaned} deck(s)"
                )
            else:
                QMessageBox.information(
                    self, "No Cleanup Needed",
                    f"All {total} tracked deck(s) exist in Anki."
                )
            
            if config.is_logged_in():
                self.load_deck_status()
        except Exception as e:
            QMessageBox.warning(self, "Cleanup Error", f"Error during cleanup:\n\n{str(e)}")
    
    def check_notifications_silent(self):
        """Silently check for notifications"""
        if not config.is_logged_in():
            return
        
        try:
            self.log("Checking notifications...")
            result = api.check_notifications(mark_as_read=False, limit=5)
            
            if result.get('success'):
                unread_count = result.get('unread_count', 0)
                config.set_unread_notification_count(unread_count)
                config.update_last_notification_check()
                self.log(f"Found {unread_count} unread notification(s)")
                
                if unread_count > 0:
                    self.notif_btn.setText(f"🔔 {unread_count}")
                    self.notif_btn.show()
                else:
                    self.notif_btn.setText("🔔")
                    self.notif_btn.show()
        except Exception as e:
            self.log(f"Notification check failed: {e}")
    
    def show_notifications(self):
        """Show notifications dialog"""
        from .notifications_dialog import NotificationsDialog
        dialog = NotificationsDialog(mw)
        dialog.exec()
        self.check_notifications_silent()
    
    def show_deck_changelog(self, item):
        """Show changelog for a deck (NEW!)"""
        if not item:
            return
        
        deck = item.data(Qt.ItemDataRole.UserRole)
        deck_id = self.get_deck_id(deck)
        deck_title = deck.get('title', 'Unknown')
        
        try:
            self.log(f"Fetching changelog for {deck_title}...")
            changelog = api.get_changelog(deck_id)
            
            if changelog.get('success'):
                self.show_changelog_dialog(changelog)
            else:
                QMessageBox.warning(self, "Error", "Failed to fetch changelog")
        except Exception as e:
            self.log(f"Changelog error: {e}")
            QMessageBox.warning(self, "Error", f"Failed to fetch changelog:\n\n{str(e)}")
    
    def show_changelog_dialog(self, changelog):
        """Display changelog in a dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Changelog: {changelog.get('title', 'Deck')}")
        dialog.setMinimumSize(500, 400)
        dialog.setStyleSheet(MINIMAL_STYLE)
        
        layout = QVBoxLayout()
        
        # Header info
        current_ver = changelog.get('current_version', '')
        synced_ver = changelog.get('user_synced_version', '')
        is_updated = changelog.get('is_up_to_date', True)
        
        header = QLabel(f"<b>Current:</b> v{current_ver} | <b>Your version:</b> v{synced_ver or 'Not downloaded'}")
        if not is_updated:
            header.setText(header.text() + " | <span style='color: #ff5722;'><b>⟳ Update Available</b></span>")
        layout.addWidget(header)
        
        # Version list
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        for version in changelog.get('versions', []):
            ver_num = version.get('version', '')
            notes = version.get('version_notes', 'No notes')
            card_count = version.get('card_count', 0)
            is_current = version.get('is_current', False)
            is_synced = version.get('is_synced', False)
            
            status = ""
            if is_current:
                status = " <b style='color: #4caf50;'>[LATEST]</b>"
            if is_synced:
                status += " <b style='color: #2196f3;'>[YOUR VERSION]</b>"
            
            ver_label = QLabel(f"<h3>v{ver_num}{status}</h3><p>{card_count} cards</p><p>{notes}</p><hr>")
            ver_label.setWordWrap(True)
            scroll_layout.addWidget(ver_label)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def check_login(self):
        """Check login state"""
        is_logged_in = config.is_logged_in()
        self.log(f"Login check: {'Logged in' if is_logged_in else 'Not logged in'}")
        
        if is_logged_in:
            self.show_sync_interface()
            self.check_notifications_silent()
        else:
            self.show_login_interface()
    
    def show_login_interface(self):
        """Show login"""
        self.title_label.setText("Nottorney")
        self.status_label.setText("Sign in to sync your decks")
        self.login_widget.show()
        self.sync_widget.hide()
        self.advanced_widget.hide()
        self.advanced_btn.hide()
        self.notif_btn.hide()
        self.email_input.setFocus()
    
    def show_sync_interface(self):
        """Show sync interface"""
        user = config.get_user()
        if user:
            email = user.get('email', 'User')
            self.title_label.setText(f"Nottorney\n{email}")
        else:
            self.title_label.setText("Nottorney")
        
        self.login_widget.hide()
        self.sync_widget.show()
        self.advanced_btn.show()
        self.load_deck_status()
    
    def handle_login(self):
        """Handle login"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            self.status_label.setText("❌ Enter email and password")
            return
        
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Signing in...")
        self.status_label.setText("⏳ Authenticating...")
        
        try:
            self.log(f"Attempting login for: {email}")
            result = api.login(email, password)
            
            if result.get('success'):
                self.log("Login successful")
                self.show_sync_interface()
                self.check_notifications_silent()
            else:
                error = result.get('error', 'Login failed')
                self.log(f"Login failed: {error}")
                self.status_label.setText(f"❌ {error}")
        except NottorneyAPIError as e:
            error_msg = str(e)
            self.log(f"Login error: {error_msg}")
            
            if "connection" in error_msg.lower():
                self.status_label.setText("❌ Connection error")
            elif "401" in error_msg or "unauthorized" in error_msg.lower():
                self.status_label.setText("❌ Incorrect email or password")
            else:
                self.status_label.setText(f"❌ {error_msg}")
        except Exception as e:
            self.log(f"Unexpected error: {e}")
            self.status_label.setText(f"❌ Error: {str(e)}")
        finally:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Sign In")
    
    def handle_logout(self):
        """Handle logout"""
        reply = QMessageBox.question(
            self, "Logout", "Logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            config.clear_tokens()
            config.set_unread_notification_count(0)
            self.log("Logged out")
            self.check_login()
    
    def load_deck_status(self):
        """Load deck status"""
        try:
            self.status_label.setText("⏳ Loading decks...")
            self.log("Fetching purchased decks...")
            
            # CRITICAL: Clean up deleted decks first
            self.log("Running cleanup before status check...")
            cleaned, total_tracked = config.cleanup_deleted_decks()
            if cleaned > 0:
                self.log(f"✓ Cleaned up {cleaned} deleted deck(s) from tracking")
            
            self.log("Calling API to get purchased decks...")
            try:
                self.decks = api.get_purchased_decks()
                self.log(f"API returned {len(self.decks)} deck(s)")
                
                # Debug: Log the raw response structure
                if len(self.decks) > 0:
                    self.log(f"First deck structure: {list(self.decks[0].keys())}")
                    self.log(f"First deck sample: {self.decks[0]}")
                else:
                    self.log("⚠ API returned empty list - checking if this is expected")
                    
            except NottorneyAPIError as e:
                self.log(f"❌ API Error: {e}")
                self.status_label.setText("❌ Failed to load decks")
                self.sync_status.setText(f"API Error: {str(e)}")
                self.sync_btn.setEnabled(False)
                return
            except Exception as e:
                self.log(f"❌ Unexpected error fetching decks: {e}")
                import traceback
                self.log(traceback.format_exc())
                self.status_label.setText("❌ Error loading decks")
                self.sync_status.setText(f"Error: {str(e)}")
                self.sync_btn.setEnabled(False)
                return
            
            total = len(self.decks)
            
<<<<<<< HEAD
            if total == 0:
                self.status_label.setText("No purchased decks found")
                self.sync_status.setText("You don't have any purchased decks")
                self.sync_btn.setText("No Decks")
                self.sync_btn.setEnabled(False)
                self.log("⚠ No decks found - this might be a data issue")
                return
            
=======
            # Count new and updated decks
>>>>>>> parent of acc9c8d (wewe)
            new = 0
            updates = 0
            
            for deck in self.decks:
                deck_id = self.get_deck_id(deck)
                deck_title = deck.get('title', 'Unknown')
                
                if not deck_id:
                    self.log(f"⚠ Deck '{deck_title}' has no ID, treating as new")
                    new += 1
                    continue
                
                self.log(f"Checking deck '{deck_title}' (ID: {deck_id})...")
                
                if not config.is_deck_downloaded(deck_id):
                    self.log(f"  → Not downloaded")
                    new += 1
                else:
                    current_version = self.get_deck_version(deck)
                    saved_version = config.get_deck_version(deck_id)
                    self.log(f"  → Downloaded (saved: {saved_version}, current: {current_version})")
                    if current_version != saved_version:
                        self.log(f"  → Update available")
                        updates += 1
            
            self.log(f"Found {total} decks: {new} new, {updates} updates")
            
            if new + updates == 0:
                self.status_label.setText(f"✓ All {total} decks synced")
                self.sync_status.setText("Everything is up to date")
                self.sync_btn.setText("✓ All Synced")
                self.sync_btn.setEnabled(False)
            else:
                parts = []
                if new > 0:
                    parts.append(f"{new} new")
                if updates > 0:
                    parts.append(f"{updates} updates")
                
                status_text = " + ".join(parts)
                self.status_label.setText(f"{total} total decks")
                self.sync_status.setText(f"{status_text} available")
                self.sync_btn.setText(f"Download ({new + updates})")
                self.sync_btn.setEnabled(True)
        except Exception as e:
            self.log(f"Error loading decks: {e}")
            self.status_label.setText("❌ Failed to load decks")
            self.sync_status.setText(str(e))
            self.sync_btn.setEnabled(False)
<<<<<<< HEAD
        except Exception as e:
            self.log(f"Unexpected error: {e}")
            import traceback
            self.log(traceback.format_exc())
            self.status_label.setText("❌ Error")
            self.sync_status.setText(str(e))
            self.sync_btn.setEnabled(False)
=======
>>>>>>> parent of acc9c8d (wewe)
    
    def sync_all(self):
        """Download all new/updated decks using BATCH DOWNLOAD (NEW!)"""
        if self.is_syncing:
            self.log("⚠ Already syncing, ignoring request")
            return
        
        if not self.decks:
            self.log("⚠ No decks loaded, cannot sync")
            self.status_label.setText("⚠ No decks loaded")
            return
        
        self.log(f"\n=== Starting sync for {len(self.decks)} deck(s) ===")
        decks_to_sync = []
        
        for deck in self.decks:
            deck_id = self.get_deck_id(deck)
            deck_title = deck.get('title', 'Unknown')
            
            if not deck_id:
                self.log(f"⚠ '{deck_title}': No ID, skipping")
                continue
            
            if not config.is_deck_downloaded(deck_id):
                self.log(f"✓ '{deck_title}': Not downloaded, adding to sync")
                decks_to_sync.append(deck)
            else:
                current_version = self.get_deck_version(deck)
                saved_version = config.get_deck_version(deck_id)
                self.log(f"  '{deck_title}': Downloaded (saved: {saved_version}, current: {current_version})")
                if current_version != saved_version:
                    self.log(f"✓ '{deck_title}': Update available, adding to sync")
                    decks_to_sync.append(deck)
        
        self.log(f"Total decks to sync: {len(decks_to_sync)}")
        
        if not decks_to_sync:
            self.log("⚠ No decks need syncing")
            self.status_label.setText("✓ All decks are up to date")
            return
        
        reply = QMessageBox.question(
            self, "Confirm",
            f"Download {len(decks_to_sync)} deck(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.is_syncing = True
        self.sync_btn.setEnabled(False)
        self.progress.show()
        
        # Use BATCH DOWNLOAD API (max 10 per request)
        self.batch_download_decks(decks_to_sync)
    
    def batch_download_decks(self, decks):
        """Download decks using batch API (NEW!)"""
        success_count = 0
        failed = []
        
<<<<<<< HEAD
        if not decks:
            self.log("⚠ No decks to download")
            self.is_syncing = False
            self.progress.hide()
            self.sync_btn.setEnabled(True)
            return
        
=======
        # Split into batches of 10
>>>>>>> parent of acc9c8d (wewe)
        batch_size = 10
        total_batches = (len(decks) + batch_size - 1) // batch_size
        
        self.progress.setMaximum(len(decks))
        
        for batch_idx in range(0, len(decks), batch_size):
            batch = decks[batch_idx:batch_idx + batch_size]
            batch_num = (batch_idx // batch_size) + 1
            
            self.log(f"\n=== Batch {batch_num}/{total_batches} ({len(batch)} decks) ===")
            
<<<<<<< HEAD
            # Extract deck IDs with validation
            deck_ids = []
            for deck in batch:
                deck_id = self.get_deck_id(deck)
                deck_title = deck.get('title', 'Unknown')
                if deck_id:
                    deck_ids.append(deck_id)
                    self.log(f"  Deck '{deck_title}': ID = {deck_id}")
                else:
                    failed.append(f"{deck_title}: No deck ID found")
                    self.log(f"  ✗ Deck '{deck_title}': No ID found")
            
            if not deck_ids:
                self.log("⚠ No valid deck IDs in this batch, skipping")
                continue
            
            self.log(f"Requesting batch download for {len(deck_ids)} deck(s)...")
            
            try:
                self.log(f"Calling batch_download_decks API with {len(deck_ids)} deck ID(s)...")
                try:
                    result = api.batch_download_decks(deck_ids)
                except NottorneyAPIError as api_err:
                    # Log the full error before re-raising
                    self.log(f"✗ API Error caught: {api_err}")
                    self.log(f"Error message: {str(api_err)}")
                    # The API client already logs the full response, but we'll try to capture it here too
                    raise
                
                self.log(f"Batch API response received: success={result.get('success')}")
                self.log(f"Response keys: {list(result.keys())}")
                self.log_api_response(result)
=======
            # Get deck IDs for this batch
            deck_ids = [self.get_deck_id(d) for d in batch]
            
            try:
                # Call BATCH DOWNLOAD API
                result = api.batch_download_decks(deck_ids)
>>>>>>> parent of acc9c8d (wewe)
                
                if result.get('success'):
                    downloads = result.get('downloads', [])
                    self.log(f"Received {len(downloads)} download response(s)")
                    
                    if not downloads:
                        self.log("⚠ No downloads in response, checking failed list...")
                        failed_items = result.get('failed', [])
                        if failed_items:
                            self.log(f"Found {len(failed_items)} failed items")
                        else:
                            self.log("⚠ No downloads and no failed items - unexpected response")
                            self.log(f"Full response: {result}")
                    
                    # Process successful downloads
                    for i, download in enumerate(downloads):
                        if download.get('success'):
                            deck_id = download.get('deck_id')
                            title = download.get('title', 'Unknown')
                            version = download.get('version', '1.0')
                            download_url = download.get('download_url')
                            
                            if not download_url:
                                error_msg = "No download URL in response"
                                failed.append(f"{title}: {error_msg}")
                                self.log(f"✗ {title}: {error_msg}")
                                continue
                            
                            self.progress.setValue(batch_idx + i)
                            self.progress.setFormat(f"Downloading: {title[:30]}...")
                            self.log(f"Downloading: {title} (URL: {download_url[:50]}...)")
                            
                            try:
<<<<<<< HEAD
                                self.log(f"  → Fetching deck file...")
=======
                                # Download and import
>>>>>>> parent of acc9c8d (wewe)
                                deck_content = api.download_deck_file(download_url)
                                self.log(f"  → Downloaded {len(deck_content)} bytes")
                                
                                self.log(f"  → Importing into Anki...")
                                anki_deck_id = import_deck(deck_content, title)
                                self.log(f"  → Imported as Anki deck ID: {anki_deck_id}")
                                
                                self.log(f"  → Saving tracking info...")
                                config.save_downloaded_deck(deck_id, version, anki_deck_id)
                                
                                success_count += 1
                                self.log(f"✓ {title} - Complete!")
                            except Exception as e:
                                import traceback
                                error_details = traceback.format_exc()
                                self.log(f"✗ {title}: {e}")
                                self.log(f"Error details:\n{error_details}")
                                failed.append(f"{title}: {str(e)}")
                        else:
                            # Failed in batch response
                            title = download.get('title', 'Unknown')
                            error = download.get('error', 'Unknown error')
                            failed.append(f"{title}: {error}")
                            self.log(f"✗ {title}: {error}")
                            self.log(f"  Failed download response: {download}")
                    
<<<<<<< HEAD
                    # Check for failed items in response
                    failed_items = result.get('failed', [])
                    if failed_items:
                        self.log(f"Processing {len(failed_items)} failed item(s)...")
                        for fail in failed_items:
                            title = fail.get('title', 'Unknown')
                            error = fail.get('error', 'Unknown error')
                            failed.append(f"{title}: {error}")
                            self.log(f"✗ {title}: {error}")
                else:
                    error_msg = result.get('error', 'Batch download failed')
                    self.log(f"✗ Batch API returned success=false: {error_msg}")
                    self.log(f"Full response: {result}")
                    for deck in batch:
                        failed.append(f"{deck.get('title', 'Unknown')}: {error_msg}")
                
            except NottorneyAPIError as e:
                error_msg = str(e)
                self.log(f"✗ Batch {batch_num} API error: {error_msg}")
                self.log(f"Error type: {type(e).__name__}")
                import traceback
                self.log(f"Traceback:\n{traceback.format_exc()}")
                
                # Try to get more details from the exception if available
                if hasattr(e, 'response'):
                    self.log(f"Response object: {e.response}")
                if hasattr(e, 'args') and e.args:
                    self.log(f"Error args: {e.args}")
                
                for deck in batch:
                    failed.append(f"{deck.get('title', 'Unknown')}: {error_msg}")
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                self.log(f"✗ Unexpected error in batch {batch_num}: {e}")
                self.log(f"Error details:\n{error_details}")
                for deck in batch:
                    failed.append(f"{deck.get('title', 'Unknown')}: {str(e)}")
=======
                    # Process failed decks from API
                    for fail in result.get('failed', []):
                        title = fail.get('title', 'Unknown')
                        error = fail.get('error', 'Unknown error')
                        failed.append(f"{title}: {error}")
                        self.log(f"✗ {title}: {error}")
                
            except Exception as e:
                # Entire batch failed
                self.log(f"✗ Batch {batch_num} failed: {e}")
                for deck in batch:
                    failed.append(f"{deck.get('title', 'Unknown')}: Batch request failed")
>>>>>>> parent of acc9c8d (wewe)
        
        self.progress.setValue(len(decks))
        self.is_syncing = False
        self.progress.hide()
        
        # Show results
        if success_count == len(decks):
            QMessageBox.information(self, "Complete", f"✓ Downloaded all {success_count} deck(s)!")
        elif success_count > 0:
            msg = f"Downloaded {success_count}/{len(decks)} deck(s)\n\n"
            if failed:
                msg += "Failed:\n" + "\n".join(failed[:3])
            QMessageBox.warning(self, "Partial Success", msg)
        else:
            QMessageBox.critical(self, "Failed", "All downloads failed")
        
        self.load_deck_status()
    
    def toggle_advanced(self):
        """Toggle advanced section"""
        self.show_advanced = not self.show_advanced
        
        if self.show_advanced:
            self.advanced_widget.show()
            self.advanced_btn.setText("Hide Decks")
            self.setMinimumSize(500, 600)
            self.populate_deck_list()
        else:
            self.advanced_widget.hide()
            self.advanced_btn.setText("Browse Decks")
            self.setMinimumSize(500, 400)
    
    def populate_deck_list(self):
        """Populate deck list"""
        self.deck_list.clear()
        
        for deck in self.decks:
            title = deck.get('title', 'Unknown')
            deck_id = self.get_deck_id(deck)
            
            if not config.is_deck_downloaded(deck_id):
                status = "○"
            else:
                current_version = self.get_deck_version(deck)
                saved_version = config.get_deck_version(deck_id)
                if current_version != saved_version:
                    status = "⟳"
                else:
                    status = "✓"
            
            item = QListWidgetItem(f"{status} {title}")
            item.setData(Qt.ItemDataRole.UserRole, deck)
            self.deck_list.addItem(item)
    
    def filter_decks(self, text):
        """Filter decks"""
        for i in range(self.deck_list.count()):
            item = self.deck_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
    
    def download_selected(self):
        """Download selected decks"""
        selected = self.deck_list.selectedItems()
        if not selected:
            self.status_label.setText("Select decks to download")
            return
        
        decks_to_download = [item.data(Qt.ItemDataRole.UserRole) for item in selected]
        self.batch_download_decks(decks_to_download)
    
    def get_deck_id(self, deck):
<<<<<<< HEAD
        """
        Extract deck ID from deck object
        Handles multiple possible field names: deck_id, id, deckId
        """
        if not deck:
            return None
        
        # Try common field names for deck ID (priority order)
        deck_id = deck.get('deck_id') or deck.get('id') or deck.get('deckId')
        
        # Debug: log if we can't find the ID
        if not deck_id:
            available_keys = list(deck.keys()) if isinstance(deck, dict) else 'Not a dict'
            self.log(f"⚠ Warning: Could not extract deck_id from deck. Available keys: {available_keys}")
            self.log(f"  Full deck object: {deck}")
        
        return deck_id
    
    def get_deck_version(self, deck):
        """Extract version from deck object"""
        if not deck:
            return None
        # Try common field names for version
        return deck.get('version') or deck.get('current_version') or deck.get('currentVersion')
=======
        """Get deck ID"""
        return deck.get('deck_id') or deck.get('id')
    
    def get_deck_version(self, deck):
        """Get deck version"""
        return deck.get('current_version') or deck.get('version') or '1.0'
>>>>>>> parent of acc9c8d (wewe)
