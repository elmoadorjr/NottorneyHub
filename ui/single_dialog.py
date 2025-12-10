"""
Minimalist Nottorney Dialog - FULLY INTEGRATED - FIXED DECK TRACKING
LESS IS BEST - Single dialog for all operations with actual API integration
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, Qt, QWidget, QTextEdit
)
from aqt import mw
from ..api_client import api, NottorneyAPIError
from ..config import config
from ..deck_importer import import_deck

# Minimalist stylesheet - dark, clean, simple
MINIMAL_STYLE = """
QDialog {
    background-color: #1a1a1a;
    color: #e0e0e0;
}

QLabel {
    color: #e0e0e0;
    font-size: 14px;
}

QLabel#title {
    font-size: 24px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#status {
    color: #888;
    font-size: 13px;
}

QPushButton {
    background-color: #2a2a2a;
    border: 1px solid #404040;
    border-radius: 6px;
    padding: 12px 24px;
    color: #e0e0e0;
    font-size: 14px;
}

QPushButton:hover {
    background-color: #333;
    border-color: #555;
}

QPushButton:disabled {
    background-color: #1a1a1a;
    color: #555;
}

QPushButton#primary {
    background-color: #4caf50;
    border: none;
    color: white;
    font-weight: bold;
}

QPushButton#primary:hover {
    background-color: #45a049;
}

QPushButton#primary:disabled {
    background-color: #2a4a2b;
    color: #666;
}

QPushButton#secondary {
    background-color: transparent;
    border: none;
    color: #888;
    padding: 8px 16px;
    font-size: 13px;
}

QPushButton#secondary:hover {
    color: #aaa;
}

QLineEdit {
    background-color: #2a2a2a;
    border: 1px solid #404040;
    border-radius: 6px;
    padding: 10px;
    color: #e0e0e0;
    font-size: 14px;
}

QLineEdit:focus {
    border-color: #4caf50;
}

QProgressBar {
    border: 1px solid #404040;
    border-radius: 6px;
    background-color: #2a2a2a;
    text-align: center;
    color: #e0e0e0;
    height: 24px;
}

QProgressBar::chunk {
    background-color: #4caf50;
    border-radius: 5px;
}

QListWidget {
    background-color: #2a2a2a;
    border: 1px solid #404040;
    border-radius: 6px;
    outline: none;
    color: #e0e0e0;
}

QListWidget::item {
    padding: 12px;
    border-bottom: 1px solid #333;
}

QListWidget::item:hover {
    background-color: #333;
}

QListWidget::item:selected {
    background-color: #4caf50;
    color: white;
}

QTextEdit {
    background-color: #1a1a1a;
    color: #00ff00;
    border: 1px solid #404040;
    border-radius: 6px;
    font-family: monospace;
    font-size: 11px;
}
"""


class MinimalNottorneyDialog(QDialog):
    """
    Single dialog for all Nottorney operations
    Minimal UI - maximum clarity - FULLY INTEGRATED
    """
    
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
        self.check_login()
    
    def setup_ui(self):
        """Minimal UI setup"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title with user email if logged in
        self.title_label = QLabel("Nottorney")
        self.title_label.setObjectName("title")
        layout.addWidget(self.title_label)
        
        # Status line (dynamic)
        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Login section (shown when logged out)
        self.login_widget = self.create_login_section()
        layout.addWidget(self.login_widget)
        
        # Sync section (shown when logged in)
        self.sync_widget = self.create_sync_section()
        layout.addWidget(self.sync_widget)
        
        # Advanced section (hidden by default)
        self.advanced_widget = self.create_advanced_section()
        layout.addWidget(self.advanced_widget)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.hide()
        layout.addWidget(self.progress)
        
        # Debug log (hidden by default)
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setMaximumHeight(150)
        self.log_widget.hide()
        layout.addWidget(self.log_widget)
        
        # Bottom actions
        bottom = QHBoxLayout()
        
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
        
        bottom.addWidget(self.log_btn)
        bottom.addWidget(self.advanced_btn)
        bottom.addStretch()
        bottom.addWidget(self.close_btn)
        layout.addLayout(bottom)
        
        self.setLayout(layout)
    
    def create_login_section(self):
        """Minimal login - inline, not separate dialog"""
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
        """Main sync interface - minimal, clear"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        self.sync_status = QLabel("")
        
        self.sync_btn = QPushButton("Download All")
        self.sync_btn.setObjectName("primary")
        self.sync_btn.clicked.connect(self.sync_all)
        
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setObjectName("secondary")
        self.logout_btn.clicked.connect(self.handle_logout)
        
        layout.addWidget(self.sync_status)
        layout.addWidget(self.sync_btn)
        layout.addWidget(self.logout_btn)
        
        widget.setLayout(layout)
        widget.hide()
        return widget
    
    def create_advanced_section(self):
        """Browse decks - only shown when requested"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Simple search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search decks...")
        self.search_input.textChanged.connect(self.filter_decks)
        
        # Deck list (simple)
        self.deck_list = QListWidget()
        self.deck_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        # Single action
        download_btn = QPushButton("Download Selected")
        download_btn.setObjectName("primary")
        download_btn.clicked.connect(self.download_selected)
        
        layout.addWidget(self.search_input)
        layout.addWidget(self.deck_list)
        layout.addWidget(download_btn)
        
        widget.setLayout(layout)
        widget.hide()
        return widget
    
    def log(self, message):
        """Add to debug log"""
        self.log_widget.append(message)
        print(message)
    
    def toggle_log(self):
        """Toggle debug log visibility"""
        self.show_log = not self.show_log
        self.log_widget.setVisible(self.show_log)
        self.log_btn.setText("Hide Log" if self.show_log else "Show Log")
        
        if self.show_log:
            self.setMinimumHeight(600)
        else:
            self.setMinimumHeight(400)
    
    def check_login(self):
        """Check if user is logged in and show appropriate UI"""
        is_logged_in = config.is_logged_in()
        
        self.log(f"Login check: {'Logged in' if is_logged_in else 'Not logged in'}")
        
        if is_logged_in:
            self.show_sync_interface()
        else:
            self.show_login_interface()
    
    def show_login_interface(self):
        """Show minimal login"""
        self.title_label.setText("Nottorney")
        self.status_label.setText("Sign in to sync your decks")
        self.login_widget.show()
        self.sync_widget.hide()
        self.advanced_widget.hide()
        self.advanced_btn.hide()
        self.email_input.setFocus()
    
    def show_sync_interface(self):
        """Show main sync interface"""
        # Update title with user email
        user = config.get_user()
        if user:
            email = user.get('email', 'User')
            self.title_label.setText(f"Nottorney\n{email}")
        else:
            self.title_label.setText("Nottorney")
        
        self.login_widget.hide()
        self.sync_widget.show()
        self.advanced_btn.show()
        
        # Load deck status
        self.load_deck_status()
    
    def handle_login(self):
        """Handle login - minimal feedback"""
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
            else:
                error = result.get('error', 'Login failed')
                self.log(f"Login failed: {error}")
                self.status_label.setText(f"❌ {error}")
        
        except NottorneyAPIError as e:
            error_msg = str(e)
            self.log(f"Login error: {error_msg}")
            
            # User-friendly error messages
            if "connection" in error_msg.lower():
                self.status_label.setText("❌ Connection error. Check your internet.")
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
            self, "Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            config.clear_tokens()
            self.log("Logged out")
            self.check_login()
    
    def clean_deleted_decks(self):
        """
        Remove tracking for decks that no longer exist in Anki
        Returns the number of decks cleaned up
        """
        downloaded_decks = config.get_downloaded_decks()
        decks_to_remove = []
        
        self.log(f"Checking {len(downloaded_decks)} tracked deck(s)...")
        
        for deck_id, deck_info in downloaded_decks.items():
            anki_deck_id = deck_info.get('anki_deck_id')
            
            if not anki_deck_id:
                self.log(f"Deck {deck_id} has no Anki ID - marking for removal")
                decks_to_remove.append(deck_id)
                continue
            
            if not self.deck_exists_in_anki(anki_deck_id):
                self.log(f"Deck {deck_id} (Anki ID: {anki_deck_id}) no longer exists - marking for removal")
                decks_to_remove.append(deck_id)
        
        # Remove the deleted decks from tracking
        for deck_id in decks_to_remove:
            success = config.remove_downloaded_deck(deck_id)
            if success:
                self.log(f"✓ Removed {deck_id} from tracking")
            else:
                self.log(f"✗ Failed to remove {deck_id}")
        
        return len(decks_to_remove)
    
    def load_deck_status(self):
        """Load and display deck status - minimal"""
        try:
            self.status_label.setText("⏳ Loading decks...")
            self.log("Fetching purchased decks...")
            
            # CRITICAL: Clean up deleted decks FIRST before loading anything
            self.log("Checking for deleted decks in Anki...")
            deleted_count = self.clean_deleted_decks()
            
            if deleted_count > 0:
                self.log(f"✓ Cleaned up {deleted_count} deleted deck(s)")
            else:
                self.log("No deleted decks found")
            
            self.decks = api.get_purchased_decks()
            downloaded_decks = config.get_downloaded_decks()
            
            total = len(self.decks)
            
            # Count new and updated decks
            new = 0
            updates = 0
            
            for deck in self.decks:
                deck_id = self.get_deck_id(deck)
                if deck_id not in downloaded_decks:
                    new += 1
                else:
                    current_version = self.get_deck_version(deck)
                    saved_version = downloaded_decks[deck_id].get('version')
                    if current_version != saved_version:
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
    
    def sync_all(self):
        """Download all new/updated decks"""
        if self.is_syncing:
            return
        
        # Get decks to sync
        downloaded_decks = config.get_downloaded_decks()
        decks_to_sync = []
        
        for deck in self.decks:
            deck_id = self.get_deck_id(deck)
            if deck_id not in downloaded_decks:
                decks_to_sync.append(deck)
            else:
                current_version = self.get_deck_version(deck)
                saved_version = downloaded_decks[deck_id].get('version')
                if current_version != saved_version:
                    decks_to_sync.append(deck)
        
        if not decks_to_sync:
            return
        
        # Confirm
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
        self.progress.setMaximum(len(decks_to_sync))
        
        success_count = 0
        failed = []
        
        for i, deck in enumerate(decks_to_sync):
            deck_title = deck.get('title', 'Unknown')
            deck_id = self.get_deck_id(deck)
            version = self.get_deck_version(deck)
            
            self.progress.setValue(i)
            self.progress.setFormat(f"Downloading {i+1}/{len(decks_to_sync)}: {deck_title[:30]}...")
            self.log(f"Downloading ({i+1}/{len(decks_to_sync)}): {deck_title}")
            
            try:
                # Download
                download_info = api.download_deck(deck_id)
                deck_content = api.download_deck_file(download_info['download_url'])
                
                # Import
                anki_deck_id = import_deck(deck_content, deck_title)
                config.save_downloaded_deck(deck_id, version, anki_deck_id)
                
                success_count += 1
                self.log(f"✓ Success: {deck_title}")
            
            except Exception as e:
                error_msg = str(e)
                failed.append(f"{deck_title}: {error_msg}")
                self.log(f"✗ Failed: {deck_title} - {error_msg}")
        
        self.progress.setValue(len(decks_to_sync))
        self.is_syncing = False
        self.progress.hide()
        
        # Show result
        if success_count == len(decks_to_sync):
            QMessageBox.information(self, "Complete", f"✓ Downloaded all {success_count} deck(s)!")
        elif success_count > 0:
            msg = f"Downloaded {success_count}/{len(decks_to_sync)} deck(s)\n\n"
            if failed:
                msg += "Failed:\n" + "\n".join(failed[:3])
            QMessageBox.warning(self, "Partial Success", msg)
        else:
            QMessageBox.critical(self, "Failed", "All downloads failed")
        
        self.load_deck_status()
    
    def toggle_advanced(self):
        """Show/hide advanced deck browser"""
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
        """Populate deck list - minimal display"""
        self.deck_list.clear()
        downloaded_decks = config.get_downloaded_decks()
        
        for deck in self.decks:
            title = deck.get('title', 'Unknown')
            deck_id = self.get_deck_id(deck)
            
            # Status indicator
            if deck_id not in downloaded_decks:
                status = "○"
            else:
                current_version = self.get_deck_version(deck)
                saved_version = downloaded_decks[deck_id].get('version')
                if current_version != saved_version:
                    status = "⟳"
                else:
                    status = "✓"
            
            item = QListWidgetItem(f"{status} {title}")
            item.setData(Qt.ItemDataRole.UserRole, deck)
            self.deck_list.addItem(item)
    
    def filter_decks(self, text):
        """Simple search filter"""
        for i in range(self.deck_list.count()):
            item = self.deck_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
    
    def download_selected(self):
        """Download selected decks from list"""
        selected = self.deck_list.selectedItems()
        
        if not selected:
            self.status_label.setText("Select decks to download")
            return
        
        decks_to_download = [item.data(Qt.ItemDataRole.UserRole) for item in selected]
        
        # Reuse sync logic
        count = len(decks_to_download)
        reply = QMessageBox.question(
            self, "Confirm",
            f"Download {count} deck(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Similar download logic as sync_all
            self.download_decks(decks_to_download)
    
    def download_decks(self, decks):
        """Download specific decks"""
        self.progress.show()
        self.progress.setMaximum(len(decks))
        
        success = 0
        for i, deck in enumerate(decks):
            deck_title = deck.get('title', 'Unknown')
            deck_id = self.get_deck_id(deck)
            version = self.get_deck_version(deck)
            
            self.progress.setValue(i)
            self.log(f"Downloading: {deck_title}")
            
            try:
                download_info = api.download_deck(deck_id)
                deck_content = api.download_deck_file(download_info['download_url'])
                anki_deck_id = import_deck(deck_content, deck_title)
                config.save_downloaded_deck(deck_id, version, anki_deck_id)
                success += 1
                self.log(f"✓ {deck_title}")
            except Exception as e:
                self.log(f"✗ {deck_title}: {e}")
        
        self.progress.hide()
        QMessageBox.information(self, "Complete", f"Downloaded {success}/{len(decks)} deck(s)")
        self.populate_deck_list()
        self.load_deck_status()
    
    def get_deck_id(self, deck):
        """Get deck ID"""
        return deck.get('deck_id') or deck.get('id')
    
    def get_deck_version(self, deck):
        """Get deck version"""
        return deck.get('current_version') or deck.get('version') or '1.0'
    
    def deck_exists_in_anki(self, anki_deck_id):
        """Check if a deck still exists in Anki"""
        try:
            if not mw or not mw.col:
                self.log(f"Warning: Anki collection not available for deck check")
                return False
            
            deck = mw.col.decks.get(anki_deck_id)
            exists = deck is not None
            
            if not exists:
                self.log(f"Deck {anki_deck_id} does not exist in Anki")
            
            return exists
        except Exception as e:
            self.log(f"Error checking deck {anki_deck_id}: {e}")
            return False