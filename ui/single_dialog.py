"""
Minimal Dialog for Nottorney Addon
FIXED: Complete PyQt6 compatibility + proper response handling + field name fixes
Version: 1.0.4 - FIXED: Prevents dialog closure during download, adds progress dialog
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox, Qt,
    QProgressDialog
)
from aqt import mw
import sys
import os

# Get parent directory to import from root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_client import api, set_access_token, NottorneyAPIError
from config import config
from deck_importer import import_deck_with_progress


class MinimalNottorneyDialog(QDialog):
    """Minimal dialog for Nottorney operations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚖️ Nottorney")
        self.setMinimumSize(600, 500)
        self.all_decks = []  # Store all decks for filtering
        self.import_in_progress = False  # Track import state
        self.progress_dialog = None  # Progress dialog reference
        self.setup_ui()
    
    def closeEvent(self, event):
        """Override close event to prevent closing during import"""
        if self.import_in_progress:
            reply = QMessageBox.question(
                self,
                "Import in Progress",
                "A deck is being imported. Closing now may leave the import incomplete.\n\n"
                "Are you sure you want to close?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        # Clean up progress dialog if it exists
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        event.accept()
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Title
        title = QLabel("⚖️ Nottorney Deck Manager")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Check if logged in
        if not config.is_logged_in():
            self.setup_login_ui(layout)
        else:
            self.setup_deck_browser_ui(layout)
        
        self.setLayout(layout)
    
    def setup_login_ui(self, layout):
        """Setup login interface"""
        # Login message
        msg = QLabel("Please login to access your purchased decks")
        msg.setStyleSheet("color: #555; font-size: 13px; padding: 10px;")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg)
        
        # Email input
        email_label = QLabel("Email:")
        email_label.setStyleSheet("font-weight: bold;")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email address")
        
        # Password input
        password_label = QLabel("Password:")
        password_label.setStyleSheet("font-weight: bold;")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Allow Enter key to submit
        self.password_input.returnPressed.connect(self.login)
        
        layout.addWidget(email_label)
        layout.addWidget(self.email_input)
        layout.addWidget(password_label)
        layout.addWidget(self.password_input)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        login_btn = QPushButton("Login")
        login_btn.setStyleSheet("padding: 8px; font-weight: bold;")
        login_btn.clicked.connect(self.login)
        button_layout.addWidget(login_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("padding: 8px;")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Add stretch to push everything to top
        layout.addStretch()
    
    def setup_deck_browser_ui(self, layout):
        """Setup deck browser interface"""
        # User info
        user_label = QLabel("✓ Logged in")
        user_label.setStyleSheet("color: #4CAF50; font-size: 12px; padding: 5px;")
        layout.addWidget(user_label)
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search decks by name...")
        self.search_input.textChanged.connect(self.filter_decks)
        layout.addWidget(self.search_input)
        
        # Deck list
        deck_list_label = QLabel("Available Decks:")
        deck_list_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(deck_list_label)
        
        self.deck_list = QListWidget()
        self.deck_list.setStyleSheet("QListWidget::item { padding: 8px; }")
        self.deck_list.itemDoubleClicked.connect(self.download_deck)
        layout.addWidget(self.deck_list)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setToolTip("Reload deck list from server")
        refresh_btn.clicked.connect(self.load_decks)
        button_layout.addWidget(refresh_btn)
        
        download_btn = QPushButton("⬇️ Download Selected")
        download_btn.setStyleSheet("padding: 8px; font-weight: bold;")
        download_btn.setToolTip("Download the selected deck")
        download_btn.clicked.connect(self.download_deck)
        button_layout.addWidget(download_btn)
        
        logout_btn = QPushButton("Logout")
        logout_btn.setToolTip("Logout and clear credentials")
        logout_btn.clicked.connect(self.logout)
        button_layout.addWidget(logout_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.setStyleSheet("padding: 8px;")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        # Load decks on startup
        self.load_decks()
    
    def login(self):
        """Login user"""
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        
        if not email or not password:
            QMessageBox.warning(self, "Missing Information", 
                              "Please enter both email and password.")
            return
        
        try:
            # Show loading state
            self.email_input.setEnabled(False)
            self.password_input.setEnabled(False)
            
            # Make API call
            result = api.login(email, password)
            
            if result.get('success'):
                access_token = result.get('access_token')
                refresh_token = result.get('refresh_token')
                expires_at = result.get('expires_at')
                
                if access_token:
                    # Save tokens
                    config.save_tokens(access_token, refresh_token, expires_at)
                    set_access_token(access_token)
                    
                    QMessageBox.information(self, "Success", 
                                          "Login successful! Reopen Nottorney to browse decks.")
                    self.accept()  # Close dialog
                else:
                    raise Exception("No access token received")
            else:
                error_msg = result.get('message', 'Login failed')
                QMessageBox.warning(self, "Login Failed", error_msg)
        
        except NottorneyAPIError as e:
            error_msg = str(e)
            if e.status_code == 401:
                error_msg = "Invalid email or password."
            QMessageBox.critical(self, "Login Error", error_msg)
        
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Login failed:\n{str(e)}")
        
        finally:
            # Re-enable inputs
            self.email_input.setEnabled(True)
            self.password_input.setEnabled(True)
    
    def logout(self):
        """Logout user"""
        reply = QMessageBox.question(
            self, "Confirm Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            config.clear_tokens()
            set_access_token(None)
            QMessageBox.information(self, "Logged Out", 
                                  "You have been logged out successfully.")
            self.accept()  # Close dialog
    
    def load_decks(self):
        """Load decks from API"""
        # Set access token before API call
        token = config.get_access_token()
        if not token:
            self.status_label.setText("❌ Not logged in")
            return
        
        set_access_token(token)
        
        try:
            self.status_label.setText("⏳ Loading decks...")
            self.deck_list.clear()
            self.all_decks = []
            
            # Call browse_decks (now includes action parameter)
            result = api.browse_decks()
            
            # FIXED: Handle both response formats - check for decks key OR success
            has_decks = "decks" in result
            is_successful = result.get('success', False)
            
            if has_decks or is_successful:
                decks = result.get('decks', [])
                self.all_decks = decks
                
                # Get downloaded decks to mark them
                downloaded_decks = config.get_downloaded_decks()
                
                for deck in decks:
                    deck_id = deck.get('id')
                    
                    # FIXED: Use 'title' field instead of 'name' for deck display
                    deck_name = deck.get('title') or deck.get('name', 'Unknown Deck')
                    deck_version = deck.get('version', '1.0')
                    
                    # Check if already downloaded
                    is_downloaded = deck_id in downloaded_decks
                    
                    # Create display text
                    display_text = f"{'✓ ' if is_downloaded else ''}{deck_name}"
                    if deck_version:
                        display_text += f" (v{deck_version})"
                    
                    item = QListWidgetItem(display_text)
                    # FIXED: PyQt6 requires Qt.ItemDataRole.UserRole (not just Qt.UserRole)
                    item.setData(Qt.ItemDataRole.UserRole, deck)
                    
                    # Mark downloaded decks visually
                    if is_downloaded:
                        item.setForeground(Qt.GlobalColor.darkGreen)
                    
                    self.deck_list.addItem(item)
                
                self.status_label.setText(f"✓ Loaded {len(decks)} deck(s)")
            else:
                error_msg = result.get('message') or result.get('error', 'Failed to load decks')
                self.status_label.setText(f"❌ {error_msg}")
                QMessageBox.warning(self, "Error", error_msg)
        
        except NottorneyAPIError as e:
            error_msg = str(e)
            if e.status_code == 401:
                error_msg = "Session expired. Please login again."
                config.clear_tokens()
            self.status_label.setText(f"❌ {error_msg}")
            QMessageBox.warning(self, "Error", error_msg)
        
        except Exception as e: 
            error_msg = f"Failed to load decks: {str(e)}"
            self.status_label.setText("❌ Load failed")
            QMessageBox.warning(self, "Error", error_msg)
    
    def filter_decks(self):
        """Filter deck list based on search"""
        query = self.search_input.text().lower()
        
        for i in range(self.deck_list.count()):
            item = self.deck_list.item(i)
            # Hide items that don't match search
            matches = query in item.text().lower()
            item.setHidden(not matches)
    
    def download_deck(self):
        """Download selected deck"""
        current = self.deck_list.currentItem()
        if not current:
            QMessageBox.warning(self, "No Selection", 
                              "Please select a deck to download.")
            return
        
        # FIXED: PyQt6 requires Qt.ItemDataRole.UserRole
        deck = current.data(Qt.ItemDataRole.UserRole)
        deck_id = deck.get('id')
        
        # FIXED: Use 'title' field instead of 'name'
        deck_name = deck.get('title') or deck.get('name', 'Unknown')
        deck_version = deck.get('version', '1.0')
        
        # Check if already downloaded
        if config.is_deck_downloaded(deck_id):
            reply = QMessageBox.question(
                self, "Already Downloaded",
                f"'{deck_name}' is already downloaded.\n\nDownload again?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Set access token
        token = config.get_access_token()
        if not token:
            QMessageBox.warning(self, "Not Logged In", 
                              "Please login first.")
            return
        
        set_access_token(token)
        
        # FIXED: Set import in progress flag
        self.import_in_progress = True
        
        # FIXED: Disable close button AND all dialog buttons during download
        self.close_btn.setEnabled(False)
        for btn in self.findChildren(QPushButton):
            if btn.text() in ["⬇️ Download Selected", "🔄 Refresh", "Logout"]:
                btn.setEnabled(False)
        
        try:
            self.status_label.setText(f"⏳ Downloading {deck_name}...")
            
            # Get download URL from API
            result = api.download_deck(deck_id)
            
            if not result.get('success'):
                error_msg = result.get('message', 'Download failed')
                raise Exception(error_msg)
            
            download_url = result.get('download_url')
            if not download_url:
                raise Exception("No download URL received")
            
            self.status_label.setText(f"⏳ Fetching deck file...")
            
            # Download the actual file
            deck_content = api.download_deck_file(download_url)
            
            if not deck_content or len(deck_content) == 0:
                raise Exception("Downloaded file is empty")
            
            # FIXED: Show progress dialog
            self.progress_dialog = QProgressDialog(
                f"Importing '{deck_name}' into Anki...\n\nThis may take a few moments.",
                None,  # No cancel button
                0, 0,  # Indeterminate progress
                self
            )
            self.progress_dialog.setWindowTitle("Importing Deck")
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.setMinimumDuration(0)  # Show immediately
            self.progress_dialog.setCancelButton(None)  # Disable cancel
            self.progress_dialog.show()
            
            self.status_label.setText(f"⏳ Importing into Anki...")
            
            # Import into Anki with progress
            def on_import_success(anki_deck_id):
                # Clear import in progress flag
                self.import_in_progress = False
                
                # Close progress dialog
                if self.progress_dialog:
                    self.progress_dialog.close()
                    self.progress_dialog = None
                
                # Save to config
                success = config.save_downloaded_deck(deck_id, deck_version, anki_deck_id)
                
                if success:
                    self.status_label.setText(f"✓ '{deck_name}' imported successfully!")
                    QMessageBox.information(
                        self, "Success",
                        f"'{deck_name}' has been imported successfully!\n\n"
                        f"You can now study it in Anki."
                    )
                    # Reload deck list to update status
                    self.load_decks()
                else:
                    self.status_label.setText(f"⚠️ Import succeeded but tracking failed")
                    QMessageBox.warning(
                        self, "Partial Success",
                        f"'{deck_name}' was imported but couldn't be tracked.\n\n"
                        f"You may need to download it again later for updates."
                    )
                
                # FIXED: Re-enable all buttons
                self.close_btn.setEnabled(True)
                for btn in self.findChildren(QPushButton):
                    if btn.text() in ["⬇️ Download Selected", "🔄 Refresh", "Logout"]:
                        btn.setEnabled(True)
            
            def on_import_failure(error_msg):
                # Clear import in progress flag
                self.import_in_progress = False
                
                # Close progress dialog
                if self.progress_dialog:
                    self.progress_dialog.close()
                    self.progress_dialog = None
                
                self.status_label.setText(f"❌ Import failed")
                QMessageBox.critical(
                    self, "Import Failed",
                    f"Failed to import '{deck_name}':\n\n{error_msg}"
                )
                
                # FIXED: Re-enable all buttons
                self.close_btn.setEnabled(True)
                for btn in self.findChildren(QPushButton):
                    if btn.text() in ["⬇️ Download Selected", "🔄 Refresh", "Logout"]:
                        btn.setEnabled(True)
            
            # FIXED: Import with progress tracking, passing self as parent
            import_deck_with_progress(
                deck_content, 
                deck_name,
                on_success=on_import_success,
                on_failure=on_import_failure,
                parent=self  # Pass dialog as parent to bind lifecycle
            )
        
        except NottorneyAPIError as e:
            # Clear import in progress flag
            self.import_in_progress = False
            
            # Close progress dialog
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None
            
            error_msg = str(e)
            if e.status_code == 403:
                error_msg = f"You don't have access to '{deck_name}'.\n\nPlease purchase it first."
            elif e.status_code == 401:
                error_msg = "Session expired. Please login again."
                config.clear_tokens()
            
            self.status_label.setText(f"❌ Download failed")
            QMessageBox.critical(self, "Download Error", error_msg)
            
            # FIXED: Re-enable all buttons
            self.close_btn.setEnabled(True)
            for btn in self.findChildren(QPushButton):
                if btn.text() in ["⬇️ Download Selected", "🔄 Refresh", "Logout"]:
                    btn.setEnabled(True)
        
        except Exception as e:
            # Clear import in progress flag
            self.import_in_progress = False
            
            # Close progress dialog
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None
            
            self.status_label.setText(f"❌ Download failed")
            QMessageBox.critical(
                self, "Error",
                f"Failed to download '{deck_name}':\n\n{str(e)}"
            )
            
            # FIXED: Re-enable all buttons
            self.close_btn.setEnabled(True)
            for btn in self.findChildren(QPushButton):
                if btn.text() in ["⬇️ Download Selected", "🔄 Refresh", "Logout"]:
                    btn.setEnabled(True)