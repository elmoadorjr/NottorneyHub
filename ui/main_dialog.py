"""
Deck Management Dialog for AnkiPH Addon
AnkiHub-style two-panel layout with deck list and details
Version: 3.2.0
"""

import webbrowser
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox, Qt,
    QWidget, QSplitter, QFrame, QCheckBox, QSizePolicy, QApplication
)
from aqt import mw
from aqt.utils import showInfo, tooltip

from ..api_client import api, set_access_token, AnkiPHAPIError, show_upgrade_prompt
from ..config import config
from ..deck_importer import import_deck
from ..update_checker import update_checker
from ..constants import HOMEPAGE_URL, TERMS_URL, PRIVACY_URL, PLANS_URL, COMMUNITY_URL


class DeckManagementDialog(QDialog):
    """AnkiHub-style two-panel deck management dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AnkiPH | Deck Management")
        self.setMinimumSize(700, 500)
        self.resize(800, 550)
        self.selected_deck = None
        self.all_decks = []  # Store deck data for filtering
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        """Setup the two-panel UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Check login state
        if not config.is_logged_in():
            layout.addWidget(self._create_login_prompt())
        else:
            # Top action bar (only when logged in)
            layout.addWidget(self._create_action_bar())
            
            # Main content - two panel splitter
            layout.addWidget(self._create_main_content())
            
            # Bottom status bar
            layout.addWidget(self._create_status_bar())
        
        self.setLayout(layout)
    
    def _rebuild_ui(self):
        """Rebuild the UI (used after login to refresh in-place)"""
        # Clear existing layout
        if self.layout():
            old_layout = self.layout()
            while old_layout.count():
                child = old_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            QWidget().setLayout(old_layout)
        
        # Rebuild
        self.setup_ui()
        self.apply_styles()
    
    def _create_action_bar(self):
        """Create top action bar with Browse and Create buttons"""
        bar = QWidget()
        bar.setObjectName("actionBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(15, 12, 15, 12)
        
        # Browse Decks button (primary)
        browse_btn = QPushButton("🔗 Browse Decks")
        browse_btn.setObjectName("primaryBtn")
        browse_btn.clicked.connect(self.browse_decks)
        layout.addWidget(browse_btn)
        
        layout.addStretch()
        
        # Create Deck button (secondary/outline)
        create_btn = QPushButton("+ Create AnkiPH Deck")
        create_btn.setObjectName("secondaryBtn")
        create_btn.clicked.connect(self.create_deck)
        layout.addWidget(create_btn)
        
        return bar
    
    def _create_login_prompt(self):
        """Create login prompt for unauthenticated users"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        msg = QLabel("Please sign in to manage your decks")
        msg.setStyleSheet("color: #888; font-size: 14px; padding: 40px;")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg)
        
        login_btn = QPushButton("Sign In")
        login_btn.setObjectName("primaryBtn")
        login_btn.setFixedWidth(200)
        login_btn.clicked.connect(self.show_login)
        layout.addWidget(login_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return container
    
    def _create_main_content(self):
        """Create two-panel splitter layout"""
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("mainSplitter")
        
        # Left panel - deck list
        left_panel = self._create_deck_list_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - deck details
        self.details_panel = self._create_details_panel()
        splitter.addWidget(self.details_panel)
        
        # Set initial sizes (40% left, 60% right)
        splitter.setSizes([280, 420])
        
        return splitter
    
    def _create_deck_list_panel(self):
        """Create left panel with subscribed decks list"""
        panel = QFrame()
        panel.setObjectName("leftPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QLabel("Subscribed AnkiPH Decks")
        header.setObjectName("panelHeader")
        layout.addWidget(header)
        
        # Deck list
        self.deck_list = QListWidget()
        self.deck_list.setObjectName("deckList")
        self.deck_list.itemClicked.connect(self.on_deck_selected)
        layout.addWidget(self.deck_list)
        
        # Load decks
        self.load_decks()
        
        return panel
    
    def _create_details_panel(self):
        """Create right panel with deck details"""
        panel = QFrame()
        panel.setObjectName("rightPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)
        
        # Deck title
        self.detail_title = QLabel("Select a deck")
        self.detail_title.setObjectName("detailTitle")
        layout.addWidget(self.detail_title)
        
        # Action buttons row
        btn_row = QHBoxLayout()
        
        self.open_web_btn = QPushButton("Open on Web")
        self.open_web_btn.setObjectName("outlineBtn")
        self.open_web_btn.clicked.connect(self.open_on_web)
        self.open_web_btn.setEnabled(False)
        btn_row.addWidget(self.open_web_btn)
        
        self.unsubscribe_btn = QPushButton("Unsubscribe")
        self.unsubscribe_btn.setObjectName("dangerOutlineBtn")
        self.unsubscribe_btn.clicked.connect(self.unsubscribe_deck)
        self.unsubscribe_btn.setEnabled(False)
        btn_row.addWidget(self.unsubscribe_btn)
        
        btn_row.addStretch()
        layout.addLayout(btn_row)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("separator")
        layout.addWidget(sep)
        
        # Deck Options section
        options_header = QLabel("Deck Options")
        options_header.setObjectName("sectionHeader")
        layout.addWidget(options_header)
        
        # Install status
        self.install_status = QLabel("")
        self.install_status.setObjectName("installStatus")
        layout.addWidget(self.install_status)
        
        # Sync/Install button
        self.sync_btn = QPushButton("🔄 Sync to Install")
        self.sync_btn.setObjectName("syncBtn")
        self.sync_btn.clicked.connect(self.sync_install_deck)
        self.sync_btn.setVisible(False)
        layout.addWidget(self.sync_btn)
        
        # Deck info
        self.info_container = QWidget()
        info_layout = QVBoxLayout(self.info_container)
        info_layout.setContentsMargins(0, 10, 0, 0)
        info_layout.setSpacing(6)
        
        self.version_label = QLabel("")
        self.cards_label = QLabel("")
        self.updated_label = QLabel("")
        
        for lbl in [self.version_label, self.cards_label, self.updated_label]:
            lbl.setObjectName("infoLabel")
            info_layout.addWidget(lbl)
        
        layout.addWidget(self.info_container)
        self.info_container.setVisible(False)
        
        layout.addStretch()
        
        return panel
    
    def _create_status_bar(self):
        """Create bottom status bar"""
        bar = QWidget()
        bar.setObjectName("statusBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # User info
        user = config.get_user()
        email = user.get('email', 'Unknown') if user else 'Unknown'
        user_label = QLabel(f"Logged in as: {email}")
        user_label.setObjectName("statusText")
        layout.addWidget(user_label)
        
        # Subscription status
        status = config.get_access_status_text()
        status_label = QLabel(status)
        status_label.setObjectName("subscriptionBadge" if config.has_full_access() else "freeBadge")
        layout.addWidget(status_label)
        
        layout.addStretch()
        
        # Settings button
        settings_btn = QPushButton("Settings")
        settings_btn.setObjectName("linkBtn")
        settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(settings_btn)
        
        # Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("linkBtn")
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)
        
        return bar
    
    def apply_styles(self):
        """Apply dark theme styles matching AnkiHub"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            
            #actionBar {
                background-color: #252525;
                border-bottom: 1px solid #333;
            }
            
            #primaryBtn {
                background-color: #4a90d9;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            #primaryBtn:hover {
                background-color: #5a9fe9;
            }
            
            #secondaryBtn {
                background-color: transparent;
                color: #aaa;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 10px 24px;
                font-size: 13px;
            }
            #secondaryBtn:hover {
                border-color: #888;
                color: #fff;
            }
            
            #leftPanel {
                background-color: #1e1e1e;
                border-right: 1px solid #333;
            }
            
            #panelHeader {
                background-color: #252525;
                color: #fff;
                font-weight: bold;
                font-size: 12px;
                padding: 12px 15px;
                border-bottom: 1px solid #333;
            }
            
            #deckList {
                background-color: #1e1e1e;
                border: none;
                color: #e0e0e0;
                font-size: 13px;
            }
            #deckList::item {
                padding: 10px 15px;
                border-bottom: 1px solid #2a2a2a;
            }
            #deckList::item:selected {
                background-color: #3a5070;
                color: white;
            }
            #deckList::item:hover:!selected {
                background-color: #2a2a2a;
            }
            
            #rightPanel {
                background-color: #1e1e1e;
            }
            
            #detailTitle {
                color: #4a90d9;
                font-size: 18px;
                font-weight: bold;
            }
            
            #outlineBtn {
                background-color: transparent;
                color: #aaa;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
            }
            #outlineBtn:hover {
                border-color: #888;
                color: #fff;
            }
            #outlineBtn:disabled {
                color: #555;
                border-color: #333;
            }
            
            #dangerOutlineBtn {
                background-color: transparent;
                color: #e57373;
                border: 1px solid #e57373;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
            }
            #dangerOutlineBtn:hover {
                background-color: #e57373;
                color: white;
            }
            #dangerOutlineBtn:disabled {
                color: #555;
                border-color: #333;
            }
            
            #separator {
                color: #333;
            }
            
            #sectionHeader {
                color: #fff;
                font-weight: bold;
                font-size: 13px;
                margin-top: 5px;
            }
            
            #installStatus {
                color: #ffa726;
                font-size: 12px;
            }
            
            #syncBtn {
                background-color: #4a90d9;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 13px;
            }
            #syncBtn:hover {
                background-color: #5a9fe9;
            }
            
            #infoLabel {
                color: #888;
                font-size: 12px;
            }
            
            #statusBar {
                background-color: #252525;
                border-top: 1px solid #333;
            }
            
            #statusText {
                color: #888;
                font-size: 11px;
            }
            
            #subscriptionBadge {
                background-color: #4CAF50;
                color: white;
                padding: 3px 10px;
                border-radius: 10px;
                font-size: 10px;
            }
            
            #freeBadge {
                background-color: #FF9800;
                color: white;
                padding: 3px 10px;
                border-radius: 10px;
                font-size: 10px;
            }
            
            #linkBtn {
                background: transparent;
                border: none;
                color: #4a90d9;
                font-size: 12px;
                padding: 5px 10px;
            }
            #linkBtn:hover {
                color: #6ab0f9;
                text-decoration: underline;
            }
        """)
    
    # === DATA LOADING ===
    
    def load_decks(self):
        """Load subscribed decks from local config"""
        self.deck_list.clear()
        
        try:
            downloaded_decks = config.get_downloaded_decks()
            
            if not downloaded_decks:
                item = QListWidgetItem("No decks yet - click Browse Decks")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                self.deck_list.addItem(item)
                return
            
            for deck_id, deck_info in downloaded_decks.items():
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
                
                item = QListWidgetItem(deck_name)
                item.setData(Qt.ItemDataRole.UserRole, {
                    'deck_id': deck_id,
                    'info': deck_info,
                    'name': deck_name
                })
                self.deck_list.addItem(item)
        
        except Exception as e:
            print(f"Error loading decks: {e}")
    
    def on_deck_selected(self, item):
        """Handle deck selection - show details in right panel"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        self.selected_deck = data
        deck_info = data.get('info', {})
        
        # Update title
        self.detail_title.setText(data.get('name', 'Unknown Deck'))
        
        # Enable buttons
        self.open_web_btn.setEnabled(True)
        self.unsubscribe_btn.setEnabled(True)
        
        # Check install status
        anki_deck_id = deck_info.get('anki_deck_id')
        is_installed = False
        
        if anki_deck_id and mw.col:
            try:
                deck = mw.col.decks.get(int(anki_deck_id))
                is_installed = deck is not None
            except:
                pass
        
        # Update install status
        has_update = config.has_update_available(data.get('deck_id', ''))
        
        if not is_installed:
            self.install_status.setText("⚠ This deck is not installed yet!")
            self.install_status.setStyleSheet("color: #ffa726;")
            self.sync_btn.setText("🔄 Sync to Install")
            self.sync_btn.setVisible(True)
        elif has_update:
            self.install_status.setText("⬆ Update available!")
            self.install_status.setStyleSheet("color: #4a90d9;")
            self.sync_btn.setText("🔄 Sync Update")
            self.sync_btn.setVisible(True)
        else:
            self.install_status.setText("✓ Installed and up to date")
            self.install_status.setStyleSheet("color: #4CAF50;")
            self.sync_btn.setVisible(False)
        
        # Show info
        version = deck_info.get('version', '1.0')
        self.version_label.setText(f"Version: {version}")
        self.cards_label.setText(f"Cards: {deck_info.get('card_count', 'Unknown')}")
        self.updated_label.setText(f"Downloaded: {deck_info.get('downloaded_at', 'Unknown')[:10] if deck_info.get('downloaded_at') else 'Unknown'}")
        self.info_container.setVisible(True)
    
    # === ACTIONS ===
    
    def browse_decks(self):
        """Open deck browser dialog"""
        dialog = DeckBrowserDialog(self)
        if dialog.exec():
            self.load_decks()
    
    def create_deck(self):
        """Create a new collaborative deck"""
        # Check if user can create decks
        if not config.can_create_decks():
            show_membership_required_dialog(self)
            return
        
        # Show confirmation dialog
        dialog = CreateDeckConfirmDialog(self)
        if dialog.exec():
            # Open deck creation form
            from .tabbed_dialog import TabbedDialog
            # For now, just show info - full creation UI would be added later
            showInfo("Deck creation feature coming soon!\n\nYou can create decks at:\n" + HOMEPAGE_URL)
    
    def sync_install_deck(self):
        """Sync/install the selected deck"""
        if not self.selected_deck:
            return
        
        deck_id = self.selected_deck.get('deck_id')
        deck_name = self.selected_deck.get('name', 'Unknown')
        
        # Show sync confirmation dialog
        dialog = SyncInstallDialog(self, [deck_name])
        if dialog.exec():
            self._do_install(deck_id, deck_name, dialog.use_recommended_settings)
    
    def _do_install(self, deck_id, deck_name, use_recommended=True):
        """Perform the actual deck installation"""
        # Show loading state
        self.setCursor(Qt.CursorShape.WaitCursor)
        self.sync_btn.setEnabled(False)
        self.sync_btn.setText("Downloading...")
        QApplication.processEvents()
        
        try:
            token = config.get_access_token()
            if token:
                set_access_token(token)
            
            result = api.download_deck(deck_id)
            print(f"\u2713 download_deck response: {result}")
            
            if result.get('success') and result.get('download_url'):
                download_url = result['download_url']
                print(f"\u2713 Got download URL: {download_url[:80]}...")
                
                # Update status
                self.sync_btn.setText("Importing...")
                QApplication.processEvents()
                
                # Download the file
                deck_content = api.download_deck_file(download_url)
                
                # Import
                anki_deck_id = import_deck(deck_content, deck_name)
                
                if anki_deck_id:
                    config.save_downloaded_deck(
                        deck_id,
                        self.selected_deck.get('info', {}).get('version', '1.0'),
                        anki_deck_id
                    )
                    tooltip(f"\u2713 {deck_name} installed!")
                    self.load_decks()
                    # Reselect to update details panel
                    if self.selected_deck:
                        self.on_deck_selected(self.deck_list.currentItem())
                else:
                    raise Exception("Import failed")
            else:
                raise Exception(result.get('message', 'No download URL'))
        
        except Exception as e:
            print(f"\u2717 Install error: {e}")
            QMessageBox.critical(self, "Error", f"Install failed: {e}")
        finally:
            # Restore cursor and button
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.sync_btn.setEnabled(True)
            self.sync_btn.setText("Sync")
    
    def open_on_web(self):
        """Open deck on web"""
        webbrowser.open(HOMEPAGE_URL)
    
    def unsubscribe_deck(self):
        """Unsubscribe from deck"""
        if not self.selected_deck:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Unsubscribe",
            f"Remove '{self.selected_deck.get('name')}' from your subscribed decks?\n\n"
            "The cards will remain in Anki but you won't receive updates.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            deck_id = self.selected_deck.get('deck_id')
            config.remove_downloaded_deck(deck_id)
            self.selected_deck = None
            self.detail_title.setText("Select a deck")
            self.open_web_btn.setEnabled(False)
            self.unsubscribe_btn.setEnabled(False)
            self.install_status.setText("")
            self.sync_btn.setVisible(False)
            self.info_container.setVisible(False)
            self.load_decks()
            tooltip("Deck unsubscribed")
    
    def show_login(self):
        """Show login dialog"""
        from .login_dialog import LoginDialog
        dialog = LoginDialog(self)
        if dialog.exec():
            # Refresh UI in-place instead of requiring reopen
            tooltip("Login successful!")
            self._rebuild_ui()
    
    def open_settings(self):
        """Open settings dialog"""
        from .settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec()
    
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


# === HELPER DIALOGS ===

class DeckBrowserDialog(QDialog):
    """Browse available decks to subscribe"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Browse Decks")
        self.setMinimumSize(450, 350)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Search
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search decks...")
        self.search.textChanged.connect(self.filter_decks)
        layout.addWidget(self.search)
        
        # List
        self.deck_list = QListWidget()
        self.deck_list.itemDoubleClicked.connect(self.subscribe_selected)
        layout.addWidget(self.deck_list)
        
        # Status
        self.status = QLabel("")
        layout.addWidget(self.status)
        
        # Buttons
        btn_row = QHBoxLayout()
        
        sub_btn = QPushButton("Subscribe")
        sub_btn.clicked.connect(self.subscribe_selected)
        btn_row.addWidget(sub_btn)
        
        btn_row.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)
        
        layout.addLayout(btn_row)
        self.setLayout(layout)
        
        self.load_decks()
    
    def load_decks(self):
        """Load available decks from server"""
        self.deck_list.clear()
        self.status.setText("Loading...")
        
        try:
            token = config.get_access_token()
            if token:
                set_access_token(token)
            
            result = api.browse_decks()
            
            if result.get('success') or 'decks' in result:
                decks = result.get('decks', [])
                downloaded = config.get_downloaded_decks()
                
                for deck in decks:
                    deck_id = deck.get('id')
                    name = deck.get('title') or deck.get('name', 'Unknown')
                    
                    is_subscribed = deck_id in downloaded
                    prefix = "✓ " if is_subscribed else ""
                    
                    item = QListWidgetItem(f"{prefix}{name}")
                    item.setData(Qt.ItemDataRole.UserRole, deck)
                    self.deck_list.addItem(item)
                
                self.status.setText(f"{len(decks)} deck(s) available")
            else:
                self.status.setText("Failed to load")
        
        except Exception as e:
            self.status.setText(f"Error: {e}")
    
    def filter_decks(self):
        """Filter deck list"""
        query = self.search.text().lower()
        for i in range(self.deck_list.count()):
            item = self.deck_list.item(i)
            item.setHidden(query not in item.text().lower())
    
    def subscribe_selected(self):
        """Subscribe to selected deck"""
        current = self.deck_list.currentItem()
        if not current:
            QMessageBox.warning(self, "No Selection", "Select a deck first.")
            return
        
        deck = current.data(Qt.ItemDataRole.UserRole)
        deck_id = deck.get('id')
        deck_name = deck.get('title') or deck.get('name')
        
        # Check if already subscribed
        if deck_id in config.get_downloaded_decks():
            QMessageBox.information(self, "Already Subscribed", "You're already subscribed to this deck.")
            return
        
        # Show sync install dialog
        dialog = SyncInstallDialog(self, [deck_name])
        if dialog.exec():
            self._subscribe_and_install(deck, dialog.use_recommended_settings)
    
    def _subscribe_and_install(self, deck, use_recommended):
        """Subscribe and install deck"""
        deck_id = deck.get('id')
        deck_name = deck.get('title') or deck.get('name')
        
        self.status.setText("Installing...")
        
        try:
            token = config.get_access_token()
            if token:
                set_access_token(token)
            
            result = api.download_deck(deck_id)
            print(f"✓ download_deck response: {result}")
            
            if result.get('success') and result.get('download_url'):
                download_url = result['download_url']
                
                # Download file
                deck_content = api.download_deck_file(download_url)
                
                # Import
                anki_deck_id = import_deck(deck_content, deck_name)
                
                if anki_deck_id:
                    config.save_downloaded_deck(
                        deck_id,
                        deck.get('version', '1.0'),
                        anki_deck_id
                    )
                    QMessageBox.information(self, "Success", f"Subscribed to {deck_name}!")
                    self.accept()
                else:
                    raise Exception("Import failed")
            else:
                raise Exception(result.get('message', 'No download URL'))
        
        except Exception as e:
            print(f"✗ Subscribe error: {e}")
            self.status.setText("Failed")
            QMessageBox.critical(self, "Error", f"Subscribe failed: {e}")


class SyncInstallDialog(QDialog):
    """Sync/Install confirmation with warnings"""
    
    def __init__(self, parent=None, deck_names=None):
        super().__init__(parent)
        self.setWindowTitle("AnkiPH | Sync")
        self.setMinimumWidth(400)
        self.deck_names = deck_names or []
        self.use_recommended_settings = True
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Header
        header = QLabel("You have new AnkiPH decks to install:")
        header.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(header)
        
        # Deck list
        for name in self.deck_names:
            item = QLabel(f"• {name}")
            item.setStyleSheet("color: #4a90d9; padding-left: 10px;")
            layout.addWidget(item)
        
        # Warning
        warning = QLabel(
            "⚠ Please go to your other devices with Anki and sync before installing new deck(s).\n"
            "Any unsynchronized reviews or changes on other devices may be lost during installation."
        )
        warning.setStyleSheet("color: #ffa726; font-size: 11px; padding: 10px; background-color: #2d2d2d; border-radius: 4px;")
        warning.setWordWrap(True)
        layout.addWidget(warning)
        
        # Checkbox
        self.checkbox = QCheckBox("Use recommended deck settings")
        self.checkbox.setChecked(True)
        self.checkbox.setStyleSheet("color: #888;")
        layout.addWidget(self.checkbox)
        
        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        install_btn = QPushButton("Install")
        install_btn.setStyleSheet("background-color: #4a90d9; color: white; padding: 8px 20px; border: none; border-radius: 4px;")
        install_btn.clicked.connect(self.on_install)
        btn_row.addWidget(install_btn)
        
        skip_btn = QPushButton("Skip")
        skip_btn.setStyleSheet("padding: 8px 20px;")
        skip_btn.clicked.connect(self.reject)
        btn_row.addWidget(skip_btn)
        
        layout.addLayout(btn_row)
        self.setLayout(layout)
    
    def on_install(self):
        self.use_recommended_settings = self.checkbox.isChecked()
        self.accept()


class CreateDeckConfirmDialog(QDialog):
    """Confirm deck creation with terms"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm AnkiPH Deck Creation")
        self.setMinimumWidth(400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Question
        question = QLabel("Are you sure you want to create a new AnkiPH deck?")
        question.setStyleSheet("font-size: 13px;")
        layout.addWidget(question)
        
        # Links
        terms_link = QLabel(f'Terms of use: <a href="{TERMS_URL}" style="color: #4a90d9;">{TERMS_URL}</a>')
        terms_link.setOpenExternalLinks(True)
        layout.addWidget(terms_link)
        
        privacy_link = QLabel(f'Privacy Policy: <a href="{PRIVACY_URL}" style="color: #4a90d9;">{PRIVACY_URL}</a>')
        privacy_link.setOpenExternalLinks(True)
        layout.addWidget(privacy_link)
        
        # Checkbox
        self.agree_checkbox = QCheckBox("by checking this checkbox you agree to the terms of use")
        self.agree_checkbox.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.agree_checkbox)
        
        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        yes_btn = QPushButton("Yes")
        yes_btn.setStyleSheet("background-color: #4a90d9; color: white; padding: 8px 20px; border: none; border-radius: 4px;")
        yes_btn.clicked.connect(self.on_yes)
        btn_row.addWidget(yes_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("padding: 8px 20px;")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        
        layout.addLayout(btn_row)
        self.setLayout(layout)
    
    def on_yes(self):
        if not self.agree_checkbox.isChecked():
            QMessageBox.warning(self, "Terms Required", "Please agree to the terms of use to continue.")
            return
        self.accept()


def show_membership_required_dialog(parent=None):
    """Show friendly paywall dialog"""
    msg = QMessageBox(parent)
    msg.setWindowTitle("Oh no!")
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setText("The action you are trying to perform requires an active membership.")
    msg.setInformativeText(
        f'Unlock a membership here: <a href="{PLANS_URL}">AnkiPH Plans</a>\n\n'
        f'Or if you prefer, reach out for support at our <a href="{COMMUNITY_URL}">AnkiPH Community</a>.'
    )
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()


# For backwards compatibility - alias to new dialog
AnkiPHMainDialog = DeckManagementDialog
