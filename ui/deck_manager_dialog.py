"""
Deck manager dialog UI for the Nottorney addon
Shows purchased decks and allows downloading them
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox,
    QProgressDialog
)
from aqt import mw
from ..api_client import api, NottorneyAPIError
from ..config import config
from ..deck_importer import import_deck


class DeckManagerDialog(QDialog):
    """Dialog for managing purchased decks"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nottorney Deck Manager")
        self.setMinimumSize(600, 400)
        self.decks = []
        self.setup_ui()
        self.load_decks()
    
    def setup_ui(self):
        """Set up the UI elements"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<h2>Your Purchased Decks</h2>")
        layout.addWidget(title)
        
        # Info label
        self.info_label = QLabel("Loading decks...")
        layout.addWidget(self.info_label)
        
        # Deck list
        self.deck_list = QListWidget()
        self.deck_list.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.deck_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.download_button = QPushButton("Download Deck")
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
    
    def load_decks(self):
        """Load purchased decks from the API"""
        self.info_label.setText("Loading decks...")
        self.deck_list.clear()
        self.refresh_button.setEnabled(False)
        
        try:
            self.decks = api.get_purchased_decks()
            
            if not self.decks:
                self.info_label.setText("No purchased decks found.")
                return
            
            self.info_label.setText(f"Found {len(self.decks)} deck(s)")
            
            # Add decks to list
            for deck in self.decks:
                item = QListWidgetItem()
                
                # Format deck info
                deck_title = deck.get('title', 'Unknown Deck')
                deck_version = deck.get('version', 'N/A')
                deck_id = deck.get('id', '')
                
                # Check if already downloaded
                is_downloaded = config.is_deck_downloaded(deck_id)
                downloaded_version = config.get_deck_version(deck_id) if is_downloaded else None
                
                if is_downloaded:
                    status = f"✓ Downloaded (v{downloaded_version})"
                    if downloaded_version != deck_version:
                        status += f" - New version available (v{deck_version})"
                else:
                    status = f"Available (v{deck_version})"
                
                item.setText(f"{deck_title}\n{status}")
                item.setData(1, deck)  # Store deck data
                
                self.deck_list.addItem(item)
        
        except NottorneyAPIError as e:
            self.info_label.setText(f"Error: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to load decks: {str(e)}")
        
        except Exception as e:
            self.info_label.setText(f"Unexpected error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
        
        finally:
            self.refresh_button.setEnabled(True)
    
    def on_selection_changed(self):
        """Handle deck selection change"""
        has_selection = len(self.deck_list.selectedItems()) > 0
        self.download_button.setEnabled(has_selection)
    
    def download_selected_deck(self):
        """Download the selected deck"""
        selected_items = self.deck_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        deck = item.data(1)
        
        deck_id = deck.get('id')
        deck_title = deck.get('title', 'Unknown Deck')
        deck_version = deck.get('version')
        
        # Check if already downloaded
        if config.is_deck_downloaded(deck_id):
            downloaded_version = config.get_deck_version(deck_id)
            if downloaded_version == deck_version:
                reply = QMessageBox.question(
                    self,
                    "Already Downloaded",
                    f"You've already downloaded this deck (v{downloaded_version}).\n\nDownload again?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
        
        # Show progress dialog
        progress = QProgressDialog("Downloading deck...", "Cancel", 0, 0, self)
        progress.setWindowTitle("Downloading")
        progress.setWindowModality(1)  # Qt.WindowModal
        progress.show()
        
        try:
            # Get download URL
            progress.setLabelText("Getting download link...")
            download_info = api.download_deck(deck_id, deck_version)
            
            download_url = download_info.get('download_url')
            if not download_url:
                raise NottorneyAPIError("No download URL provided")
            
            # Download the deck file
            progress.setLabelText("Downloading deck file...")
            deck_content = api.download_deck_file(download_url)
            
            # Import into Anki
            progress.setLabelText("Importing into Anki...")
            anki_deck_id = import_deck(deck_content, deck_title)
            
            # Save to config
            config.save_downloaded_deck(deck_id, deck_version, anki_deck_id)
            
            progress.close()
            
            QMessageBox.information(
                self,
                "Success",
                f"Successfully downloaded and imported '{deck_title}'!"
            )
            
            # Refresh the list
            self.load_decks()
        
        except NottorneyAPIError as e:
            progress.close()
            QMessageBox.warning(self, "Error", f"Download failed: {str(e)}")
        
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")