"""
Simplified Main Dialog for AnkiPH Addon
Single unified dialog with minimal UI - AnkiHub-style simplicity
ENHANCED: Added tiered access support (v3.0)
Version: 3.0.0
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox, Qt,
    QWidget, QProgressDialog
)
from aqt import mw
from aqt.utils import showInfo

from ..api_client import api, set_access_token, AnkiPHAPIError, AccessTier, can_sync_updates, show_upgrade_prompt
from ..config import config
from ..deck_importer import import_deck_with_progress
from ..update_checker import update_checker


class AnkiPHMainDialog(QDialog):
    """Simplified single dialog for AnkiPH operations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚖️ AnkiPH")
        self.setMinimumSize(500, 400)
        self.import_in_progress = False
        self.progress_dialog = None
        self.setup_ui()
    
    def closeEvent(self, event):
        """Prevent closing during import"""
        if self.import_in_progress:
            reply = QMessageBox.question(
                self, "Import in Progress",
                "A deck is being imported. Close anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        if self.progress_dialog:
            self.progress_dialog.close()
        event.accept()
    
    def setup_ui(self):
        """Setup main UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Title
        title = QLabel("AnkiPH")
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        if not config.is_logged_in():
            self.setup_login_ui(layout)
        else:
            self.setup_main_ui(layout)
        
        self.setLayout(layout)
    
    def setup_login_ui(self, layout):
        """Setup login form"""
        msg = QLabel("Please login to access your purchased decks")
        msg.setStyleSheet("color: #555; font-size: 14px; padding: 15px;")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        layout.addWidget(self.email_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.login)
        layout.addWidget(self.password_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        login_btn = QPushButton("Login")
        login_btn.setStyleSheet("padding: 10px; font-weight: bold;")
        login_btn.clicked.connect(self.login)
        btn_layout.addWidget(login_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
    
    def setup_main_ui(self, layout):
        """Setup main logged-in UI"""
        # User bar
        user_bar = QHBoxLayout()
        
        user_label = QLabel("Logged in")
        user_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        user_bar.addWidget(user_label)
        
        # Subscription status (v3.0)
        status_text = config.get_access_status_text()
        if config.has_full_access():
            status_style = "color: #4CAF50; font-size: 11px; padding: 2px 8px; background: #E8F5E9; border-radius: 3px;"
        else:
            status_style = "color: #FF9800; font-size: 11px; padding: 2px 8px; background: #FFF3E0; border-radius: 3px;"
        
        self.subscription_label = QLabel(status_text)
        self.subscription_label.setStyleSheet(status_style)
        user_bar.addWidget(self.subscription_label)
        
        user_bar.addStretch()
        
        # Settings button - use text instead of emoji
        settings_btn = QPushButton("Settings")
        settings_btn.setStyleSheet("padding: 5px 15px;")
        settings_btn.clicked.connect(self.open_settings)
        user_bar.addWidget(settings_btn)
        
        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet("padding: 5px 15px;")
        logout_btn.clicked.connect(self.logout)
        user_bar.addWidget(logout_btn)
        
        layout.addLayout(user_bar)
        
        # Deck list header
        header = QLabel("Your Decks")
        header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(header)
        
        # Deck list
        self.deck_list = QListWidget()
        self.deck_list.setStyleSheet("QListWidget::item { padding: 10px; }")
        layout.addWidget(self.deck_list)
        
        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; font-size: 11px; padding: 3px 5px;")
        layout.addWidget(self.status_label)
        
        # Bottom buttons
        btn_layout = QHBoxLayout()
        
        sync_btn = QPushButton("Sync All")
        sync_btn.setStyleSheet("padding: 10px 20px; font-weight: bold; background-color: #4CAF50; color: white;")
        sync_btn.clicked.connect(self.sync_all)
        btn_layout.addWidget(sync_btn)
        
        download_btn = QPushButton("Download New")
        download_btn.setStyleSheet("padding: 10px 15px;")
        download_btn.clicked.connect(self.download_new_deck)
        btn_layout.addWidget(download_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("padding: 10px 15px;")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        # Load decks
        self.load_decks()
    
    # === LOGIN/LOGOUT ===
    
    def login(self):
        """Login user"""
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        
        if not email or not password:
            QMessageBox.warning(self, "Missing Info", "Enter email and password.")
            return
        
        try:
            self.email_input.setEnabled(False)
            self.password_input.setEnabled(False)
            
            result = api.login(email, password)
            
            if result.get('success'):
                access_token = result.get('access_token')
                refresh_token = result.get('refresh_token')
                expires_at = result.get('expires_at')
                user_data = result.get('user', {})
                
                if access_token:
                    config.save_tokens(access_token, refresh_token, expires_at)
                    config.save_user_data(user_data)
                    set_access_token(access_token)
                    
                    QMessageBox.information(self, "Success", "Login successful!\nReopen to see your decks.")
                    self.accept()
                else:
                    raise Exception("No access token received")
            else:
                QMessageBox.warning(self, "Login Failed", result.get('message', 'Login failed'))
        
        except AnkiPHAPIError as e:
            QMessageBox.critical(self, "Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Login failed: {e}")
        finally:
            self.email_input.setEnabled(True)
            self.password_input.setEnabled(True)
    
    def logout(self):
        """Logout user"""
        reply = QMessageBox.question(
            self, "Confirm Logout", "Are you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            config.clear_tokens()
            set_access_token(None)
            QMessageBox.information(self, "Logged Out", "You have been logged out.")
            self.accept()
    
    # === DECK OPERATIONS ===
    
    def load_decks(self):
        """Load user's decks with status"""
        self.deck_list.clear()
        self.status_label.setText("Loading...")
        
        try:
            # Clean up deleted decks
            from ..sync import clean_deleted_decks
            clean_deleted_decks()
            
            downloaded_decks = config.get_downloaded_decks()
            
            if not downloaded_decks:
                self.status_label.setText("No decks yet - click 'Download New'")
                return
            
            for deck_id, deck_info in downloaded_decks.items():
                version = deck_info.get('version', '1.0')
                has_update = config.has_update_available(deck_id)
                
                # Get deck name from Anki
                anki_deck_id = deck_info.get('anki_deck_id')
                deck_name = f"Deck {deck_id[:8]}"
                
                if anki_deck_id and mw.col:
                    try:
                        deck = mw.col.decks.get(int(anki_deck_id))
                        if deck:
                            deck_name = deck['name']
                    except:
                        pass
                
                # Status indicator
                if has_update:
                    status = "[Update available]"
                    color = Qt.GlobalColor.darkYellow
                else:
                    status = "Up to date"
                    color = Qt.GlobalColor.darkGreen
                
                item = QListWidgetItem(f"{deck_name} (v{version})  -  {status}")
                item.setData(Qt.ItemDataRole.UserRole, {'deck_id': deck_id, 'info': deck_info})
                item.setForeground(color)
                self.deck_list.addItem(item)
            
            self.status_label.setText(f"{len(downloaded_decks)} deck(s)")
        
        except Exception as e:
            self.status_label.setText(f"Load failed: {e}")
    
    def sync_all(self):
        """Sync all decks - check for updates and apply"""
        self.status_label.setText("Checking for updates...")
        
        try:
            # Check for updates
            updates = update_checker.check_for_updates(silent=True)
            
            if not updates:
                # Try to sync progress (non-critical - backend may not support yet)
                try:
                    from ..sync import sync_progress
                    sync_progress()
                except Exception as e:
                    print(f"Progress sync skipped (non-critical): {e}")
                
                self.status_label.setText("All synced, no updates")
                QMessageBox.information(self, "Sync Complete", "All decks are up to date!")
                return
            
            # Check access before applying updates (v3.0)
            if not config.has_full_access():
                # Free tier - check if they can sync
                showInfo(
                    "Free tier decks don't receive updates.\n\n"
                    "Subscribe to AnkiPH or get the Collection to receive the latest content!"
                )
                show_upgrade_prompt()
                self.status_label.setText("Upgrade required for updates")
                return
            
            # Apply updates
            reply = QMessageBox.question(
                self, "Updates Available",
                f"{len(updates)} update(s) available. Apply now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                applied = 0
                for deck_id, update_info in updates.items():
                    try:
                        self.status_label.setText(f"Updating {deck_id[:8]}...")
                        self._apply_update(deck_id, update_info)
                        applied += 1
                    except Exception as e:
                        print(f"Failed to update {deck_id}: {e}")
                
                # Try to sync progress after updates (non-critical)
                try:
                    from ..sync import sync_progress
                    sync_progress()
                except Exception as e:
                    print(f"Progress sync skipped (non-critical): {e}")
                
                self.load_decks()
                QMessageBox.information(self, "Done", f"Applied {applied} update(s)")
            else:
                self.status_label.setText(f"{len(updates)} updates pending")
        
        except Exception as e:
            self.status_label.setText("Sync failed")
            QMessageBox.critical(self, "Error", f"Sync failed: {e}")
    
    def _apply_update(self, deck_id, update_info):
        """Apply a single deck update"""
        token = config.get_access_token()
        if token:
            set_access_token(token)
        
        result = api.download_deck(deck_id)
        
        if result.get('success') and result.get('download_url'):
            anki_deck_id = import_deck_with_progress(
                result['download_url'],
                deck_id,
                progress_callback=None
            )
            
            if anki_deck_id:
                config.save_downloaded_deck(
                    deck_id,
                    update_info.get('latest_version', '1.0'),
                    anki_deck_id
                )
                config.clear_update(deck_id)
    
    def download_new_deck(self):
        """Show deck browser to download new deck"""
        # DeckBrowserDialog is defined below in this same file
        dialog = DeckBrowserDialog(self)
        if dialog.exec():
            self.load_decks()
    
    def open_settings(self):
        """Open settings dialog"""
        from .settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec()


class DeckBrowserDialog(QDialog):
    """Simple deck browser for downloading new decks"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download New Deck")
        self.setMinimumSize(400, 300)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search decks...")
        self.search_input.textChanged.connect(self.filter_decks)
        layout.addWidget(self.search_input)
        
        # Deck list
        self.deck_list = QListWidget()
        self.deck_list.itemDoubleClicked.connect(self.download_selected)
        layout.addWidget(self.deck_list)
        
        # Status
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        download_btn = QPushButton("Download")
        download_btn.clicked.connect(self.download_selected)
        btn_layout.addWidget(download_btn)
        
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        self.load_decks()
    
    def load_decks(self):
        """Load available decks from server"""
        self.deck_list.clear()
        self.status_label.setText("Loading...")
        
        token = config.get_access_token()
        if token:
            set_access_token(token)
        
        try:
            result = api.browse_decks()
            
            if result.get('success') or 'decks' in result:
                decks = result.get('decks', [])
                downloaded = config.get_downloaded_decks()
                
                for deck in decks:
                    deck_id = deck.get('id')
                    name = deck.get('title') or deck.get('name', 'Unknown')
                    version = deck.get('version', '1.0')
                    
                    is_downloaded = deck_id in downloaded
                    prefix = "[Downloaded] " if is_downloaded else ""
                    
                    item = QListWidgetItem(f"{prefix}{name} (v{version})")
                    item.setData(Qt.ItemDataRole.UserRole, deck)
                    
                    if is_downloaded:
                        item.setForeground(Qt.GlobalColor.darkGreen)
                    
                    self.deck_list.addItem(item)
                
                self.status_label.setText(f"{len(decks)} deck(s) available")
            else:
                self.status_label.setText("Failed to load")
        
        except Exception as e:
            self.status_label.setText(f"Error: {e}")
    
    def filter_decks(self):
        """Filter deck list by search text"""
        query = self.search_input.text().lower()
        for i in range(self.deck_list.count()):
            item = self.deck_list.item(i)
            item.setHidden(query not in item.text().lower())
    
    def download_selected(self):
        """Download selected deck"""
        current = self.deck_list.currentItem()
        if not current:
            QMessageBox.warning(self, "No Selection", "Select a deck to download.")
            return
        
        deck = current.data(Qt.ItemDataRole.UserRole)
        deck_id = deck.get('id')
        
        # Check if already downloaded
        if deck_id in config.get_downloaded_decks():
            QMessageBox.information(self, "Already Downloaded", "This deck is already downloaded.")
            return
        
        self.status_label.setText("Downloading...")
        
        try:
            token = config.get_access_token()
            if token:
                set_access_token(token)
            
            result = api.download_deck(deck_id)
            
            if result.get('success') and result.get('download_url'):
                anki_deck_id = import_deck_with_progress(
                    result['download_url'],
                    deck_id,
                    progress_callback=None
                )
                
                if anki_deck_id:
                    config.save_downloaded_deck(
                        deck_id,
                        deck.get('version', '1.0'),
                        anki_deck_id
                    )
                    QMessageBox.information(self, "Success", "Deck downloaded!")
                    self.accept()
                else:
                    raise Exception("Import failed")
            else:
                raise Exception(result.get('message', 'Download failed'))
        
        except Exception as e:
            self.status_label.setText("Failed")
            QMessageBox.critical(self, "Error", f"Download failed: {e}")
