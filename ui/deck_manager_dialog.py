"""
Deck manager dialog UI for the Nottorney addon - DEBUG VERSION
Shows purchased decks and allows downloading them
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox,
    QProgressDialog, Qt, QTextEdit
)
from aqt import mw
from ..api_client import api, NottorneyAPIError
from ..config import config
from ..deck_importer import import_deck
import traceback
import json


class DeckManagerDialog(QDialog):
    """Dialog for managing purchased decks"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nottorney Deck Manager")
        self.setMinimumSize(700, 600)  # Increased height for debug log
        self.decks = []
        self.setup_ui()
        self.load_decks()
    
    def setup_ui(self):
        """Set up the UI elements"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<h2>Your Purchased Decks</h2>")
        layout.addWidget(title)
        
        # User info
        user = config.get_user()
        if user:
            user_label = QLabel(f"Logged in as: <b>{user.get('email', 'Unknown')}</b>")
            layout.addWidget(user_label)
        
        # Info label
        self.info_label = QLabel("Loading decks...")
        layout.addWidget(self.info_label)
        
        # Deck list with better formatting
        self.deck_list = QListWidget()
        self.deck_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.deck_list.setStyleSheet("""
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
        """)
        layout.addWidget(self.deck_list)
        
        # Deck details label
        self.details_label = QLabel("")
        self.details_label.setWordWrap(True)
        self.details_label.setStyleSheet("padding: 10px; background-color: #f5f5f5; border-radius: 5px;")
        layout.addWidget(self.details_label)
        
        # DEBUG LOG
        debug_label = QLabel("<b>Debug Log:</b>")
        layout.addWidget(debug_label)
        
        self.debug_log = QTextEdit()
        self.debug_log.setReadOnly(True)
        self.debug_log.setMaximumHeight(150)
        self.debug_log.setStyleSheet("background-color: #f0f0f0; font-family: monospace; font-size: 10px;")
        layout.addWidget(self.debug_log)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.download_button = QPushButton("Download/Update Deck")
        self.download_button.clicked.connect(self.download_selected_deck)
        self.download_button.setEnabled(False)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_decks)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def log(self, message):
        """Add a message to the debug log"""
        self.debug_log.append(message)
        print(message)  # Also print to console
    
    def get_deck_id(self, deck):
        """Safely extract deck_id from deck object"""
        return deck.get('deck_id') or deck.get('id') or deck.get('_id') or None
    
    def get_deck_version(self, deck):
        """Safely extract version from deck object"""
        return (deck.get('current_version') or 
                deck.get('version') or 
                deck.get('deck_version') or 
                deck.get('latest_version') or
                '1.0')
    
    def load_decks(self):
        """Load purchased decks from the API"""
        self.info_label.setText("Loading decks...")
        self.deck_list.clear()
        self.details_label.setText("")
        self.debug_log.clear()
        self.refresh_button.setEnabled(False)
        self.download_button.setEnabled(False)
        
        try:
            self.log("Fetching decks from API...")
            self.decks = api.get_purchased_decks()
            
            if not self.decks:
                self.info_label.setText("No purchased decks found.")
                self.log("No decks returned from API")
                return
            
            self.info_label.setText(f"Found {len(self.decks)} purchased deck(s)")
            self.log(f"Received {len(self.decks)} decks")
            
            # Log first deck structure
            if self.decks:
                self.log(f"\nFirst deck fields: {list(self.decks[0].keys())}")
                self.log(f"First deck sample: {json.dumps(self.decks[0], indent=2)[:300]}...")
            
            # Add decks to list
            for i, deck in enumerate(self.decks):
                item = QListWidgetItem()
                
                deck_title = deck.get('title', 'Unknown Deck')
                deck_subject = deck.get('subject', 'N/A')
                deck_version = self.get_deck_version(deck)
                card_count = deck.get('card_count', 0)
                deck_id = self.get_deck_id(deck)
                
                if not deck_id:
                    self.log(f"WARNING: Deck {i+1} has no ID!")
                    continue
                
                is_downloaded = config.is_deck_downloaded(deck_id)
                downloaded_version = config.get_deck_version(deck_id) if is_downloaded else None
                
                status_icon = "✓" if is_downloaded else "○"
                version_text = f"v{deck_version}"
                
                if is_downloaded:
                    if downloaded_version != deck_version:
                        version_text = f"v{downloaded_version} → v{deck_version} (Update)"
                        status_icon = "⟳"
                    else:
                        version_text = f"v{deck_version} (Downloaded)"
                
                display_text = f"{status_icon} {deck_title}\n   {deck_subject} • {card_count} cards • {version_text}"
                
                item.setText(display_text)
                item.setData(Qt.ItemDataRole.UserRole, deck)
                
                self.deck_list.addItem(item)
            
            self.log(f"\nSuccessfully loaded {self.deck_list.count()} decks into list")
        
        except NottorneyAPIError as e:
            error_msg = str(e)
            self.info_label.setText(f"Error: {error_msg}")
            self.log(f"API ERROR: {error_msg}")
            
            if "login" in error_msg.lower() or "auth" in error_msg.lower():
                QMessageBox.warning(self, "Authentication Error", 
                    f"{error_msg}\n\nPlease login again.")
            else:
                QMessageBox.warning(self, "Error", f"Failed to load decks: {error_msg}")
        
        except Exception as e:
            self.info_label.setText(f"Unexpected error: {str(e)}")
            self.log(f"EXCEPTION: {str(e)}")
            self.log(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
        
        finally:
            self.refresh_button.setEnabled(True)
    
    def on_selection_changed(self):
        """Handle deck selection change"""
        selected_items = self.deck_list.selectedItems()
        has_selection = len(selected_items) > 0
        
        self.download_button.setEnabled(has_selection)
        
        if has_selection:
            deck = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.show_deck_details(deck)
    
    def show_deck_details(self, deck):
        """Show details of the selected deck"""
        deck_title = deck.get('title', 'Unknown')
        deck_description = deck.get('description', 'No description available')
        deck_subject = deck.get('subject', 'N/A')
        card_count = deck.get('card_count', 0)
        deck_version = self.get_deck_version(deck)
        
        deck_id = self.get_deck_id(deck)
        is_downloaded = config.is_deck_downloaded(deck_id) if deck_id else False
        
        details = f"<b>{deck_title}</b><br>"
        details += f"<i>{deck_description}</i><br><br>"
        details += f"Subject: {deck_subject} | Cards: {card_count} | Version: {deck_version}<br>"
        
        if is_downloaded:
            downloaded_version = config.get_deck_version(deck_id)
            details += f"<span style='color: green;'>Downloaded: v{downloaded_version}</span>"
        
        self.details_label.setText(details)
    
    def download_selected_deck(self):
        """Download the selected deck"""
        selected_items = self.deck_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        deck = item.data(Qt.ItemDataRole.UserRole)
        
        deck_id = self.get_deck_id(deck)
        deck_version = self.get_deck_version(deck)
        deck_title = deck.get('title', 'Unknown Deck')
        
        self.log(f"\n=== DOWNLOAD ATTEMPT ===")
        self.log(f"Deck Title: {deck_title}")
        self.log(f"Deck ID: {deck_id}")
        self.log(f"Deck Version: {deck_version}")
        self.log(f"All deck fields: {list(deck.keys())}")
        
        if not deck_id:
            error_msg = f"Missing deck ID! Fields available: {list(deck.keys())}"
            self.log(f"ERROR: {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)
            return
        
        # Check if already downloaded
        if config.is_deck_downloaded(deck_id):
            downloaded_version = config.get_deck_version(deck_id)
            if downloaded_version == deck_version:
                reply = QMessageBox.question(
                    self, "Already Downloaded",
                    f"Already have v{downloaded_version}. Re-download?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
        
        # Show progress dialog
        progress = QProgressDialog("Preparing...", "Cancel", 0, 100, self)
        progress.setWindowTitle("Downloading")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(10)
        progress.show()
        
        try:
            # Step 1: Get download URL
            self.log("Step 1: Requesting download URL from API...")
            progress.setLabelText("Getting download link...")
            progress.setValue(20)
            
            # Try without version first
            try:
                self.log(f"  Attempt 1: download_deck('{deck_id}', version=None)")
                download_info = api.download_deck(deck_id, version=None)
                self.log(f"  SUCCESS: {download_info}")
            except NottorneyAPIError as e:
                self.log(f"  FAILED: {str(e)}")
                if "version" in str(e).lower():
                    self.log(f"  Attempt 2: download_deck('{deck_id}', version='{deck_version}')")
                    download_info = api.download_deck(deck_id, version=deck_version)
                    self.log(f"  SUCCESS: {download_info}")
                else:
                    raise
            
            download_url = download_info.get('download_url')
            if not download_url:
                raise NottorneyAPIError("No download_url in response")
            
            self.log(f"Download URL: {download_url[:80]}...")
            
            # Step 2: Download file
            self.log("Step 2: Downloading deck file...")
            progress.setLabelText("Downloading deck file...")
            progress.setValue(40)
            
            deck_content = api.download_deck_file(download_url)
            self.log(f"Downloaded {len(deck_content)} bytes")
            
            if not deck_content:
                raise NottorneyAPIError("Downloaded file is empty")
            
            # Step 3: Import into Anki
            self.log("Step 3: Importing into Anki...")
            progress.setLabelText("Importing...")
            progress.setValue(70)
            
            anki_deck_id = import_deck(deck_content, deck_title)
            self.log(f"Imported! Anki deck ID: {anki_deck_id}")
            
            # Step 4: Save to config
            self.log("Step 4: Saving to config...")
            progress.setValue(90)
            
            actual_version = download_info.get('version', deck_version)
            config.save_downloaded_deck(deck_id, actual_version, anki_deck_id)
            
            progress.setValue(100)
            progress.close()
            
            self.log("=== DOWNLOAD COMPLETE ===\n")
            
            QMessageBox.information(
                self, "Success",
                f"Successfully imported:\n\n'{deck_title}' (v{actual_version})"
            )
            
            self.load_decks()
        
        except NottorneyAPIError as e:
            progress.close()
            error_msg = str(e)
            self.log(f"API ERROR: {error_msg}")
            
            QMessageBox.warning(self, "Download Error", 
                f"Download failed:\n\n{error_msg}\n\nCheck the debug log for details.")
        
        except Exception as e:
            progress.close()
            error_msg = str(e)
            self.log(f"EXCEPTION: {error_msg}")
            self.log(traceback.format_exc())
            
            QMessageBox.critical(self, "Error", 
                f"Unexpected error:\n\n{error_msg}\n\nCheck the debug log for details.")