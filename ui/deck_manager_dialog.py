"""
Enhanced Deck Manager Dialog for Nottorney Addon
Features: Better UI, search, sorting, bulk operations, detailed stats
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QMessageBox, QProgressDialog,
    Qt, QTextEdit, QCheckBox, QLineEdit, QComboBox, QGroupBox,
    QSplitter, QWidget, QScrollArea, QFrame
)
from aqt import mw
from ..api_client import api, NottorneyAPIError
from ..config import config
from ..deck_importer import import_deck
import traceback


class DeckManagerDialog(QDialog):
    """Enhanced dialog for managing purchased decks"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nottorney Deck Manager")
        self.setMinimumSize(900, 700)
        self.decks = []
        self.filtered_decks = []
        self.show_updates_only = False
        self.search_text = ""
        self.sort_by = "title"
        self.setup_ui()
        self.load_decks()
    
    def setup_ui(self):
        """Set up the enhanced UI"""
        layout = QVBoxLayout()
        
        # Header Section
        header_layout = QVBoxLayout()
        
        # Title and user info
        title_layout = QHBoxLayout()
        title = QLabel("<h2>📚 Your Nottorney Decks</h2>")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        user = config.get_user()
        if user:
            user_label = QLabel(f"👤 <b>{user.get('email', 'Unknown')}</b>")
            title_layout.addWidget(user_label)
        
        header_layout.addLayout(title_layout)
        
        # Status/Info bar
        self.info_label = QLabel("Loading decks...")
        self.info_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #e3f2fd;
                border-radius: 4px;
                border-left: 4px solid #2196f3;
            }
        """)
        header_layout.addWidget(self.info_label)
        
        layout.addLayout(header_layout)
        
        # Control Panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # Main Content - Split view
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Deck List
        left_panel = self.create_deck_list_panel()
        splitter.addWidget(left_panel)
        
        # Right: Details Panel
        right_panel = self.create_details_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter, 1)
        
        # Bottom Buttons
        button_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("🔄 Refresh List")
        self.refresh_button.clicked.connect(self.load_decks)
        
        self.sync_button = QPushButton("☁️ Sync Progress")
        self.sync_button.clicked.connect(self.sync_progress)
        
        self.download_button = QPushButton("⬇️ Download/Update Deck")
        self.download_button.clicked.connect(self.download_selected_deck)
        self.download_button.setEnabled(False)
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.sync_button)
        button_layout.addStretch()
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_control_panel(self):
        """Create the control panel with search and filters"""
        panel = QGroupBox("Filters & Search")
        layout = QHBoxLayout()
        
        # Search box
        search_label = QLabel("🔍")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search decks by title or subject...")
        self.search_input.textChanged.connect(self.on_search_changed)
        self.search_input.setMinimumWidth(250)
        
        # Sort by dropdown
        sort_label = QLabel("Sort by:")
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Title (A-Z)",
            "Title (Z-A)", 
            "Subject",
            "Card Count",
            "Recently Downloaded",
            "Updates Available"
        ])
        self.sort_combo.currentIndexChanged.connect(self.on_sort_changed)
        
        # Filter checkboxes
        self.updates_checkbox = QCheckBox("Updates Only")
        self.updates_checkbox.stateChanged.connect(self.filter_decks)
        
        self.downloaded_checkbox = QCheckBox("Downloaded Only")
        self.downloaded_checkbox.stateChanged.connect(self.filter_decks)
        
        # Check updates button
        self.check_updates_button = QPushButton("🔄 Check for Updates")
        self.check_updates_button.clicked.connect(self.check_for_updates)
        
        layout.addWidget(search_label)
        layout.addWidget(self.search_input)
        layout.addWidget(sort_label)
        layout.addWidget(self.sort_combo)
        layout.addWidget(self.updates_checkbox)
        layout.addWidget(self.downloaded_checkbox)
        layout.addStretch()
        layout.addWidget(self.check_updates_button)
        
        panel.setLayout(layout)
        return panel
    
    def create_deck_list_panel(self):
        """Create the deck list panel"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Stats summary
        self.stats_label = QLabel("0 decks")
        self.stats_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(self.stats_label)
        
        # Deck list
        self.deck_list = QListWidget()
        self.deck_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.deck_list.itemDoubleClicked.connect(self.download_selected_deck)
        self.deck_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        layout.addWidget(self.deck_list)
        
        widget.setLayout(layout)
        return widget
    
    def create_details_panel(self):
        """Create the details panel"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Details header
        details_header = QLabel("<h3>Deck Details</h3>")
        layout.addWidget(details_header)
        
        # Scrollable details area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout()
        
        # Placeholder
        self.details_label = QLabel("Select a deck to view details")
        self.details_label.setWordWrap(True)
        self.details_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.details_label.setStyleSheet("""
            QLabel {
                padding: 15px;
                background-color: #fafafa;
                border-radius: 4px;
            }
        """)
        
        self.details_layout.addWidget(self.details_label)
        self.details_layout.addStretch()
        
        self.details_widget.setLayout(self.details_layout)
        scroll.setWidget(self.details_widget)
        
        layout.addWidget(scroll)
        
        # Debug log (collapsible)
        debug_group = QGroupBox("Debug Log")
        debug_group.setCheckable(True)
        debug_group.setChecked(False)
        debug_layout = QVBoxLayout()
        
        self.debug_log = QTextEdit()
        self.debug_log.setReadOnly(True)
        self.debug_log.setMaximumHeight(150)
        self.debug_log.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        debug_layout.addWidget(self.debug_log)
        debug_group.setLayout(debug_layout)
        
        layout.addWidget(debug_group)
        
        widget.setLayout(layout)
        return widget
    
    def log(self, message):
        """Add message to debug log"""
        self.debug_log.append(message)
        print(message)
    
    def on_search_changed(self, text):
        """Handle search text change"""
        self.search_text = text.lower()
        self.filter_decks()
    
    def on_sort_changed(self, index):
        """Handle sort change"""
        sort_map = {
            0: "title_asc",
            1: "title_desc",
            2: "subject",
            3: "card_count",
            4: "downloaded_date",
            5: "has_update"
        }
        self.sort_by = sort_map.get(index, "title_asc")
        self.filter_decks()
    
    def filter_decks(self):
        """Filter and sort decks based on current criteria"""
        if not self.decks:
            self.populate_deck_list([])
            return
        
        filtered = self.decks.copy()
        
        # Apply search filter
        if self.search_text:
            filtered = [d for d in filtered if 
                       self.search_text in d.get('title', '').lower() or
                       self.search_text in d.get('subject', '').lower() or
                       self.search_text in d.get('description', '').lower()]
        
        # Apply checkbox filters
        if self.updates_checkbox.isChecked():
            filtered = [d for d in filtered if self.has_update(d)]
        
        if self.downloaded_checkbox.isChecked():
            filtered = [d for d in filtered if self.is_downloaded(d)]
        
        # Sort
        filtered = self.sort_decks(filtered)
        
        self.filtered_decks = filtered
        self.populate_deck_list(filtered)
    
    def sort_decks(self, decks):
        """Sort decks based on current sort criteria"""
        if self.sort_by == "title_asc":
            return sorted(decks, key=lambda d: d.get('title', '').lower())
        elif self.sort_by == "title_desc":
            return sorted(decks, key=lambda d: d.get('title', '').lower(), reverse=True)
        elif self.sort_by == "subject":
            return sorted(decks, key=lambda d: d.get('subject', '').lower())
        elif self.sort_by == "card_count":
            return sorted(decks, key=lambda d: d.get('card_count', 0), reverse=True)
        elif self.sort_by == "downloaded_date":
            def get_date(d):
                deck_id = self.get_deck_id(d)
                if not deck_id or not config.is_deck_downloaded(deck_id):
                    return ""
                info = config.get_downloaded_decks().get(deck_id, {})
                return info.get('downloaded_at', '')
            return sorted(decks, key=get_date, reverse=True)
        elif self.sort_by == "has_update":
            return sorted(decks, key=lambda d: self.has_update(d), reverse=True)
        
        return decks
    
    def has_update(self, deck):
        """Check if deck has an update available"""
        deck_id = self.get_deck_id(deck)
        if not deck_id or not config.is_deck_downloaded(deck_id):
            return False
        
        current_version = self.get_deck_version(deck)
        downloaded_version = config.get_deck_version(deck_id)
        
        return downloaded_version != current_version
    
    def is_downloaded(self, deck):
        """Check if deck is downloaded"""
        deck_id = self.get_deck_id(deck)
        return deck_id and config.is_deck_downloaded(deck_id)
    
    def get_deck_id(self, deck):
        """Safely extract deck_id"""
        return deck.get('deck_id') or deck.get('id')
    
    def get_deck_version(self, deck):
        """Safely extract version"""
        return (deck.get('current_version') or 
                deck.get('version') or 
                deck.get('latest_version') or '1.0')
    
    def check_for_updates(self):
        """Check for updates on all decks"""
        self.check_updates_button.setEnabled(False)
        self.info_label.setText("⏳ Checking for updates...")
        
        try:
            self.log("\n=== Checking for updates ===")
            result = api.check_updates()
            
            updates_count = result.get('updates_available', 0)
            total = result.get('total_decks', 0)
            
            if updates_count > 0:
                self.info_label.setText(f"✨ {updates_count} update(s) available!")
                self.info_label.setStyleSheet("""
                    QLabel {
                        padding: 8px;
                        background-color: #fff3cd;
                        border-radius: 4px;
                        border-left: 4px solid #ffc107;
                    }
                """)
                QMessageBox.information(
                    self, "Updates Available",
                    f"🎉 {updates_count} deck update(s) available!\n\n"
                    f"Total decks: {total}\n\n"
                    "Enable 'Updates Only' filter to see them."
                )
            else:
                self.info_label.setText(f"✅ All {total} decks are up to date!")
                self.info_label.setStyleSheet("""
                    QLabel {
                        padding: 8px;
                        background-color: #d4edda;
                        border-radius: 4px;
                        border-left: 4px solid #28a745;
                    }
                """)
            
            self.load_decks()
            
        except NottorneyAPIError as e:
            self.log(f"Update check error: {str(e)}")
            self.info_label.setText("❌ Failed to check updates")
            QMessageBox.warning(self, "Error", f"Failed to check updates:\n\n{str(e)}")
        finally:
            self.check_updates_button.setEnabled(True)
    
    def sync_progress(self):
        """Sync progress to server"""
        try:
            from .. import sync
            
            self.sync_button.setEnabled(False)
            self.sync_button.setText("⏳ Syncing...")
            
            result = sync.sync_progress()
            
            if result:
                synced = result.get('synced_count', 0)
                QMessageBox.information(
                    self, "Sync Complete",
                    f"✅ Successfully synced progress for {synced} deck(s)!"
                )
            else:
                QMessageBox.information(
                    self, "Nothing to Sync",
                    "No downloaded decks to sync. Download some decks first!"
                )
        except Exception as e:
            self.log(f"Sync error: {str(e)}")
            QMessageBox.warning(self, "Sync Error", f"Failed to sync:\n\n{str(e)}")
        finally:
            self.sync_button.setEnabled(True)
            self.sync_button.setText("☁️ Sync Progress")
    
    def load_decks(self):
        """Load decks from API"""
        self.info_label.setText("⏳ Loading decks...")
        self.deck_list.clear()
        self.details_label.setText("Loading...")
        
        # Disable controls
        self.refresh_button.setEnabled(False)
        self.check_updates_button.setEnabled(False)
        self.download_button.setEnabled(False)
        
        try:
            self.log("\n=== Fetching decks ===")
            self.decks = api.get_purchased_decks()
            
            if not self.decks:
                self.info_label.setText("📭 No purchased decks found")
                self.stats_label.setText("0 decks")
                return
            
            total = len(self.decks)
            downloaded = sum(1 for d in self.decks if self.is_downloaded(d))
            updates = sum(1 for d in self.decks if self.has_update(d))
            
            self.info_label.setText(
                f"📚 {total} deck(s) | ✓ {downloaded} downloaded | ⟳ {updates} updates"
            )
            
            self.log(f"Loaded {total} decks")
            self.filter_decks()
            
        except NottorneyAPIError as e:
            self.log(f"API Error: {str(e)}")
            self.info_label.setText(f"❌ Error: {str(e)}")
            if "auth" in str(e).lower():
                QMessageBox.warning(
                    self, "Authentication Error",
                    f"{str(e)}\n\nPlease login again."
                )
        except Exception as e:
            self.log(f"Exception: {str(e)}\n{traceback.format_exc()}")
            self.info_label.setText(f"❌ Unexpected error")
            QMessageBox.critical(self, "Error", f"Unexpected error:\n\n{str(e)}")
        finally:
            self.refresh_button.setEnabled(True)
            self.check_updates_button.setEnabled(True)
    
    def populate_deck_list(self, decks):
        """Populate the deck list"""
        self.deck_list.clear()
        
        if not decks:
            self.stats_label.setText("0 decks found")
            self.details_label.setText("No decks match your filters")
            return
        
        self.stats_label.setText(f"{len(decks)} deck(s)")
        
        for deck in decks:
            deck_id = self.get_deck_id(deck)
            if not deck_id:
                continue
            
            title = deck.get('title', 'Unknown')
            subject = deck.get('subject', 'N/A')
            cards = deck.get('card_count', 0)
            version = self.get_deck_version(deck)
            
            is_downloaded = self.is_downloaded(deck)
            has_update = self.has_update(deck)
            
            # Status icon and text
            if has_update:
                icon = "⟳"
                status = "Update Available"
                color = "#ff9800"
            elif is_downloaded:
                icon = "✓"
                status = "Downloaded"
                color = "#4caf50"
            else:
                icon = "○"
                status = "Not Downloaded"
                color = "#757575"
            
            # Format display text
            display = f"{icon} <b>{title}</b>\n"
            display += f"   {subject} • {cards} cards • v{version}\n"
            display += f"   <span style='color: {color};'>{status}</span>"
            
            item = QListWidgetItem()
            item.setText(display)
            item.setData(Qt.ItemDataRole.UserRole, deck)
            
            self.deck_list.addItem(item)
    
    def on_selection_changed(self):
        """Handle deck selection"""
        items = self.deck_list.selectedItems()
        
        if not items:
            self.download_button.setEnabled(False)
            self.details_label.setText("Select a deck to view details")
            return
        
        self.download_button.setEnabled(True)
        deck = items[0].data(Qt.ItemDataRole.UserRole)
        self.show_deck_details(deck)
    
    def show_deck_details(self, deck):
        """Show detailed deck information"""
        title = deck.get('title', 'Unknown')
        desc = deck.get('description', 'No description available')
        subject = deck.get('subject', 'N/A')
        cards = deck.get('card_count', 0)
        version = self.get_deck_version(deck)
        deck_id = self.get_deck_id(deck)
        
        is_downloaded = self.is_downloaded(deck)
        has_update = self.has_update(deck)
        
        # Build detailed HTML
        html = f"<h3 style='color: #2196f3;'>{title}</h3>"
        html += f"<p style='color: #666;'><i>{desc}</i></p>"
        
        html += "<hr>"
        
        html += "<table cellpadding='5' style='width: 100%;'>"
        html += f"<tr><td><b>Subject:</b></td><td>{subject}</td></tr>"
        html += f"<tr><td><b>Cards:</b></td><td>{cards}</td></tr>"
        html += f"<tr><td><b>Version:</b></td><td>v{version}</td></tr>"
        
        if is_downloaded:
            downloaded_ver = config.get_deck_version(deck_id)
            html += f"<tr><td><b>Downloaded:</b></td><td>v{downloaded_ver}</td></tr>"
            
            dl_info = config.get_downloaded_decks().get(deck_id, {})
            dl_date = dl_info.get('downloaded_at', 'Unknown')
            if dl_date != 'Unknown':
                dl_date = dl_date.split('T')[0]  # Just the date
            html += f"<tr><td><b>Downloaded On:</b></td><td>{dl_date}</td></tr>"
        
        html += "</table>"
        
        html += "<hr>"
        
        if has_update:
            downloaded_ver = config.get_deck_version(deck_id)
            html += f"<div style='background: #fff3cd; padding: 10px; border-radius: 4px; border-left: 4px solid #ffc107;'>"
            html += f"<b>🎉 Update Available!</b><br>"
            html += f"v{downloaded_ver} → v{version}"
            html += "</div>"
        elif is_downloaded:
            html += f"<div style='background: #d4edda; padding: 10px; border-radius: 4px; border-left: 4px solid #28a745;'>"
            html += "<b>✅ Up to Date</b>"
            html += "</div>"
        else:
            html += f"<div style='background: #e3f2fd; padding: 10px; border-radius: 4px; border-left: 4px solid #2196f3;'>"
            html += "<b>⬇️ Click 'Download' to import this deck</b>"
            html += "</div>"
        
        self.details_label.setText(html)
    
    def download_selected_deck(self):
        """Download/update the selected deck"""
        items = self.deck_list.selectedItems()
        if not items:
            return
        
        deck = items[0].data(Qt.ItemDataRole.UserRole)
        deck_id = self.get_deck_id(deck)
        deck_version = self.get_deck_version(deck)
        deck_title = deck.get('title', 'Unknown')
        
        self.log(f"\n=== Download: {deck_title} ===")
        
        # Confirm if already downloaded
        if config.is_deck_downloaded(deck_id):
            downloaded_ver = config.get_deck_version(deck_id)
            
            if downloaded_ver == deck_version:
                reply = QMessageBox.question(
                    self, "Re-download Deck",
                    f"You already have {deck_title} v{deck_version}.\n\n"
                    "Download again?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
            else:
                reply = QMessageBox.question(
                    self, "Update Deck",
                    f"Update {deck_title}?\n\n"
                    f"v{downloaded_ver} → v{deck_version}",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
        
        # Progress dialog
        progress = QProgressDialog("Preparing download...", "Cancel", 0, 100, self)
        progress.setWindowTitle("Downloading Deck")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(10)
        
        try:
            # Step 1: Get download URL
            progress.setLabelText("Getting download link...")
            progress.setValue(20)
            
            download_info = api.download_deck(deck_id)
            download_url = download_info.get('download_url')
            
            if not download_url:
                raise NottorneyAPIError("No download URL received")
            
            # Step 2: Download file
            progress.setLabelText("Downloading deck file...")
            progress.setValue(40)
            
            deck_content = api.download_deck_file(download_url)
            self.log(f"Downloaded {len(deck_content)} bytes")
            
            # Step 3: Import
            progress.setLabelText("Importing into Anki...")
            progress.setValue(70)
            
            anki_deck_id = import_deck(deck_content, deck_title)
            self.log(f"Imported as deck ID: {anki_deck_id}")
            
            # Step 4: Save config
            progress.setValue(90)
            actual_version = download_info.get('version', deck_version)
            config.save_downloaded_deck(deck_id, actual_version, anki_deck_id)
            
            progress.setValue(100)
            progress.close()
            
            self.log("=== Download Complete ===")
            
            QMessageBox.information(
                self, "Success!",
                f"✅ Successfully imported:\n\n{deck_title} (v{actual_version})\n\n"
                "The deck is now available in your Anki collection."
            )
            
            self.load_decks()
            
        except NottorneyAPIError as e:
            progress.close()
            self.log(f"API Error: {str(e)}")
            QMessageBox.warning(
                self, "Download Failed",
                f"Failed to download deck:\n\n{str(e)}"
            )
        except Exception as e:
            progress.close()
            self.log(f"Exception: {str(e)}\n{traceback.format_exc()}")
            QMessageBox.critical(
                self, "Error",
                f"Unexpected error:\n\n{str(e)}"
            )