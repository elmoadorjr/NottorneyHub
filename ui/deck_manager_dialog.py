"""
Enhanced Deck Manager Dialog for Nottorney Addon
Features: Dark Mode Default, Checkboxes, Beginner-Friendly UI
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QMessageBox, QProgressDialog,
    Qt, QTextEdit, QCheckBox, QLineEdit, QComboBox, QGroupBox,
    QWidget, QTabWidget, QSizePolicy
)
from aqt import mw
from ..api_client import api, NottorneyAPIError
from ..config import config
from ..deck_importer import import_deck


class DeckManagerDialog(QDialog):
    """Enhanced dialog for managing purchased decks with dark mode default"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚖️ Nottorney Deck Manager")
        self.setMinimumSize(1100, 800)
        self.decks = []
        self.filtered_decks = []
        self.search_text = ""
        self.sort_by = "title_asc"
        self.dark_mode = True  # Dark mode by default
        self.filter_mode = "all"  # Track current filter
        
        self.setup_ui()
        self.apply_theme()
        self.load_decks()
    
    def get_light_stylesheet(self):
        """Light theme stylesheet"""
        return """
            QDialog { background-color: #f8f9fa; }
            QGroupBox {
                background-color: white; border: 1px solid #e0e0e0;
                border-radius: 8px; margin-top: 10px; padding-top: 15px;
                font-weight: bold; color: #2c3e50;
            }
            QListWidget {
                background-color: white; border: 1px solid #e0e0e0;
                border-radius: 8px; padding: 8px; outline: none; color: #2c3e50;
            }
            QListWidget::item {
                padding: 12px; border: 1px solid #f0f0f0;
                border-radius: 6px; margin: 4px 2px;
                background-color: white;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5; border-color: #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd; color: #1976d2;
                border: 2px solid #2196f3;
            }
            QPushButton {
                background-color: white; border: 1px solid #d0d0d0;
                border-radius: 6px; padding: 10px 18px; color: #2c3e50;
                font-weight: 500; font-size: 13px;
            }
            QPushButton:hover { background-color: #f5f5f5; border-color: #2196f3; }
            QPushButton:pressed { background-color: #e3f2fd; }
            QPushButton#primaryButton {
                background-color: #4caf50; color: white; border: none;
                font-weight: bold; font-size: 14px; padding: 12px 24px;
            }
            QPushButton#primaryButton:hover { background-color: #45a049; }
            QPushButton#dangerButton {
                background-color: #f44336; color: white; border: none;
            }
            QPushButton#dangerButton:hover { background-color: #da190b; }
            QLineEdit, QComboBox {
                background-color: white; border: 1px solid #d0d0d0;
                border-radius: 6px; padding: 10px; color: #2c3e50; font-size: 13px;
            }
            QLabel { color: #2c3e50; }
            QLabel#headerLabel { color: #2c3e50; font-size: 26px; font-weight: bold; }
            QLabel#infoLabel {
                background-color: #e3f2fd; border-left: 4px solid #2196f3;
                border-radius: 6px; padding: 14px; color: #1976d2; font-size: 13px;
            }
            QLabel#statsLabel {
                background-color: #e3f2fd; border-radius: 6px;
                padding: 10px 14px; color: #1976d2; font-weight: bold; font-size: 14px;
            }
            QLabel#helpLabel {
                background-color: #fff3e0; border-left: 4px solid #ff9800;
                border-radius: 6px; padding: 12px; color: #e65100; font-size: 12px;
            }
            QCheckBox { color: #2c3e50; font-size: 13px; }
            QCheckBox::indicator { width: 18px; height: 18px; }
        """
    
    def get_dark_stylesheet(self):
        """Dark theme stylesheet"""
        return """
            QDialog { background-color: #1e1e1e; }
            QGroupBox {
                background-color: #2d2d2d; border: 1px solid #404040;
                border-radius: 8px; margin-top: 10px; padding-top: 15px;
                font-weight: bold; color: #e0e0e0;
            }
            QListWidget {
                background-color: #2d2d2d; border: 1px solid #404040;
                border-radius: 8px; padding: 8px; outline: none; color: #e0e0e0;
            }
            QListWidget::item {
                padding: 12px; border: 1px solid #3a3a3a;
                border-radius: 6px; margin: 4px 2px;
                background-color: #2d2d2d;
            }
            QListWidget::item:hover {
                background-color: #353535; border-color: #4a4a4a;
            }
            QListWidget::item:selected {
                background-color: #1565c0; color: #ffffff;
                border: 2px solid #2196f3;
            }
            QPushButton {
                background-color: #2d2d2d; border: 1px solid #505050;
                border-radius: 6px; padding: 10px 18px; color: #e0e0e0;
                font-weight: 500; font-size: 13px;
            }
            QPushButton:hover { background-color: #353535; border-color: #2196f3; }
            QPushButton:pressed { background-color: #1565c0; }
            QPushButton#primaryButton {
                background-color: #4caf50; color: white; border: none;
                font-weight: bold; font-size: 14px; padding: 12px 24px;
            }
            QPushButton#primaryButton:hover { background-color: #45a049; }
            QPushButton#dangerButton {
                background-color: #f44336; color: white; border: none;
            }
            QPushButton#dangerButton:hover { background-color: #da190b; }
            QLineEdit, QComboBox {
                background-color: #2d2d2d; border: 1px solid #505050;
                border-radius: 6px; padding: 10px; color: #e0e0e0; font-size: 13px;
            }
            QLabel { color: #e0e0e0; }
            QLabel#headerLabel { color: #e0e0e0; font-size: 26px; font-weight: bold; }
            QLabel#infoLabel {
                background-color: #1565c0; border-left: 4px solid #2196f3;
                border-radius: 6px; padding: 14px; color: #ffffff; font-size: 13px;
            }
            QLabel#statsLabel {
                background-color: #1565c0; border-radius: 6px;
                padding: 10px 14px; color: #ffffff; font-weight: bold; font-size: 14px;
            }
            QLabel#helpLabel {
                background-color: #3d2e00; border-left: 4px solid #ff9800;
                border-radius: 6px; padding: 12px; color: #ffb74d; font-size: 12px;
            }
            QCheckBox { color: #e0e0e0; font-size: 13px; }
            QCheckBox::indicator { width: 18px; height: 18px; }
        """
    
    def apply_theme(self):
        """Apply current theme"""
        self.setStyleSheet(self.get_dark_stylesheet() if self.dark_mode else self.get_light_stylesheet())
    
    def toggle_theme(self):
        """Toggle between light and dark mode"""
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        self.theme_button.setText("☀️ Light Mode" if self.dark_mode else "🌙 Dark Mode")
    
    def setup_ui(self):
        """Set up UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = self.create_header()
        layout.addLayout(header_layout)
        
        # Help section for beginners
        help_label = QLabel("💡 <b>Quick Start:</b> Use checkboxes to select decks, then click Download Selected. "
                           "You can also use Search to find specific decks or filters to view downloaded/updated decks.")
        help_label.setObjectName("helpLabel")
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
        # Tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_decks_tab(), "📚 My Decks")
        self.tab_widget.addTab(self.create_settings_tab(), "⚙️ Settings")
        layout.addWidget(self.tab_widget, 1)
        
        # Bottom buttons
        layout.addLayout(self.create_bottom_buttons())
        self.setLayout(layout)
    
    def create_header(self):
        """Create header"""
        layout = QVBoxLayout()
        
        title_layout = QHBoxLayout()
        title = QLabel("📚 Your Nottorney Decks")
        title.setObjectName("headerLabel")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # Theme toggle
        self.theme_button = QPushButton("☀️ Light Mode")  # Shows opposite of current
        self.theme_button.clicked.connect(self.toggle_theme)
        self.theme_button.setMaximumWidth(150)
        title_layout.addWidget(self.theme_button)
        
        user = config.get_user()
        if user:
            user_label = QLabel(f"👤 {user.get('email', 'User')}")
            title_layout.addWidget(user_label)
        
        layout.addLayout(title_layout)
        
        self.info_label = QLabel("Loading decks...")
        self.info_label.setObjectName("infoLabel")
        layout.addWidget(self.info_label)
        
        return layout
    
    def create_decks_tab(self):
        """Create main decks tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Search and sort in one row
        top_controls = QHBoxLayout()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search by title or subject...")
        self.search_input.textChanged.connect(self.on_search_changed)
        top_controls.addWidget(self.search_input, 2)
        
        # Sort
        top_controls.addWidget(QLabel("Sort:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Title (A-Z)", "Title (Z-A)", "Subject",
            "Most Cards", "Recently Downloaded", "Updates First"
        ])
        self.sort_combo.currentIndexChanged.connect(self.on_sort_changed)
        self.sort_combo.setMaximumWidth(180)
        top_controls.addWidget(self.sort_combo)
        
        layout.addLayout(top_controls)
        
        # Filter buttons
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Show:"))
        
        self.show_all_btn = QPushButton("📚 All Decks")
        self.show_all_btn.setCheckable(True)
        self.show_all_btn.setChecked(True)
        self.show_all_btn.clicked.connect(lambda: self.quick_filter("all"))
        
        self.show_downloaded_btn = QPushButton("✓ Downloaded")
        self.show_downloaded_btn.setCheckable(True)
        self.show_downloaded_btn.clicked.connect(lambda: self.quick_filter("downloaded"))
        
        self.show_not_downloaded_btn = QPushButton("○ Not Downloaded")
        self.show_not_downloaded_btn.setCheckable(True)
        self.show_not_downloaded_btn.clicked.connect(lambda: self.quick_filter("not_downloaded"))
        
        self.show_updates_btn = QPushButton("⟳ Updates Available")
        self.show_updates_btn.setCheckable(True)
        self.show_updates_btn.clicked.connect(lambda: self.quick_filter("updates"))
        
        filter_layout.addWidget(self.show_all_btn)
        filter_layout.addWidget(self.show_downloaded_btn)
        filter_layout.addWidget(self.show_not_downloaded_btn)
        filter_layout.addWidget(self.show_updates_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Stats
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("0 decks")
        self.stats_label.setObjectName("statsLabel")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        
        self.check_updates_button = QPushButton("🔄 Check for Updates")
        self.check_updates_button.clicked.connect(self.check_for_updates)
        stats_layout.addWidget(self.check_updates_button)
        
        layout.addLayout(stats_layout)
        
        # Deck list with checkboxes
        self.deck_list = QListWidget()
        self.deck_list.itemChanged.connect(self.on_item_checked)
        layout.addWidget(self.deck_list)
        
        # Selection controls
        select_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("☑️ Select All")
        self.select_all_btn.clicked.connect(self.select_all_visible)
        
        self.deselect_btn = QPushButton("☐ Deselect All")
        self.deselect_btn.clicked.connect(self.deselect_all)
        
        self.selection_label = QLabel("0 selected")
        
        select_layout.addWidget(self.select_all_btn)
        select_layout.addWidget(self.deselect_btn)
        select_layout.addWidget(self.selection_label)
        select_layout.addStretch()
        
        layout.addLayout(select_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_settings_tab(self):
        """Create settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Details
        details_group = QGroupBox("📋 Deck Details")
        details_layout = QVBoxLayout()
        self.details_label = QLabel("Select a deck to view details")
        self.details_label.setWordWrap(True)
        details_layout.addWidget(self.details_label)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group, 1)
        
        # Quick tips
        tips_group = QGroupBox("💡 Tips for Beginners")
        tips_layout = QVBoxLayout()
        tips_text = QLabel(
            "<b>How to use this addon:</b><br><br>"
            "1. <b>Browse Decks:</b> All your purchased decks are shown on the 'My Decks' tab<br>"
            "2. <b>Search:</b> Use the search box to find specific decks by name or subject<br>"
            "3. <b>Select Decks:</b> Check the boxes next to decks you want to download<br>"
            "4. <b>Download:</b> Click 'Download Selected' to import decks into Anki<br>"
            "5. <b>Updates:</b> Click 'Check for Updates' to see if new versions are available<br>"
            "6. <b>Filters:</b> Use the filter buttons to show only downloaded or updated decks<br><br>"
            "<b>Icons:</b><br>"
            "✓ = Already downloaded | ○ = Not downloaded yet | ⟳ = Update available"
        )
        tips_text.setWordWrap(True)
        tips_layout.addWidget(tips_text)
        tips_group.setLayout(tips_layout)
        layout.addWidget(tips_group)
        
        # Debug log
        debug_group = QGroupBox("🐛 Debug Log")
        debug_group.setCheckable(True)
        debug_group.setChecked(False)
        debug_layout = QVBoxLayout()
        self.debug_log = QTextEdit()
        self.debug_log.setReadOnly(True)
        self.debug_log.setMaximumHeight(150)
        self.debug_log.setStyleSheet("background-color: #1a1a1a; color: #00ff00; font-family: monospace;")
        debug_layout.addWidget(self.debug_log)
        debug_group.setLayout(debug_layout)
        layout.addWidget(debug_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_bottom_buttons(self):
        """Create bottom buttons"""
        layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("🔄 Refresh List")
        self.refresh_button.clicked.connect(self.load_decks)
        
        self.download_all_button = QPushButton("⬇️ Download All Visible")
        self.download_all_button.setObjectName("primaryButton")
        self.download_all_button.clicked.connect(self.download_all_visible)
        
        self.download_button = QPushButton("⬇️ Download Selected")
        self.download_button.setObjectName("primaryButton")
        self.download_button.clicked.connect(self.download_selected)
        self.download_button.setEnabled(False)
        
        close_button = QPushButton("✕ Close")
        close_button.clicked.connect(self.accept)
        
        layout.addWidget(self.refresh_button)
        layout.addStretch()
        layout.addWidget(self.download_all_button)
        layout.addWidget(self.download_button)
        layout.addWidget(close_button)
        
        return layout
    
    def log(self, message):
        """Log message"""
        self.debug_log.append(message)
        print(message)
    
    def on_search_changed(self, text):
        """Handle search"""
        self.search_text = text.lower()
        self.filter_decks()
    
    def on_sort_changed(self, index):
        """Handle sort change"""
        sort_map = {
            0: "title_asc", 1: "title_desc", 2: "subject",
            3: "card_count", 4: "downloaded_date", 5: "has_update"
        }
        self.sort_by = sort_map.get(index, "title_asc")
        self.filter_decks()
    
    def quick_filter(self, filter_type):
        """Quick filter"""
        self.filter_mode = filter_type
        self.show_all_btn.setChecked(filter_type == "all")
        self.show_downloaded_btn.setChecked(filter_type == "downloaded")
        self.show_not_downloaded_btn.setChecked(filter_type == "not_downloaded")
        self.show_updates_btn.setChecked(filter_type == "updates")
        self.filter_decks()
    
    def filter_decks(self):
        """Filter decks"""
        if not self.decks:
            self.populate_deck_list([])
            return
        
        filtered = self.decks.copy()
        
        # Search filter
        if self.search_text:
            filtered = [d for d in filtered if 
                       self.search_text in d.get('title', '').lower() or
                       self.search_text in d.get('subject', '').lower()]
        
        # Status filter
        if self.filter_mode == "downloaded":
            filtered = [d for d in filtered if self.is_downloaded(d)]
        elif self.filter_mode == "not_downloaded":
            filtered = [d for d in filtered if not self.is_downloaded(d)]
        elif self.filter_mode == "updates":
            filtered = [d for d in filtered if self.has_update(d)]
        
        self.filtered_decks = self.sort_decks(filtered)
        self.populate_deck_list(self.filtered_decks)
    
    def sort_decks(self, decks):
        """Sort decks"""
        if self.sort_by == "title_asc":
            return sorted(decks, key=lambda d: d.get('title', '').lower())
        elif self.sort_by == "title_desc":
            return sorted(decks, key=lambda d: d.get('title', '').lower(), reverse=True)
        elif self.sort_by == "subject":
            return sorted(decks, key=lambda d: d.get('subject', '').lower())
        elif self.sort_by == "card_count":
            return sorted(decks, key=lambda d: d.get('card_count', 0), reverse=True)
        elif self.sort_by == "has_update":
            return sorted(decks, key=lambda d: self.has_update(d), reverse=True)
        return decks
    
    def has_update(self, deck):
        """Check if has update"""
        deck_id = self.get_deck_id(deck)
        if not deck_id or not config.is_deck_downloaded(deck_id):
            return False
        return config.get_deck_version(deck_id) != self.get_deck_version(deck)
    
    def is_downloaded(self, deck):
        """Check if downloaded"""
        deck_id = self.get_deck_id(deck)
        return deck_id and config.is_deck_downloaded(deck_id)
    
    def get_deck_id(self, deck):
        return deck.get('deck_id') or deck.get('id')
    
    def get_deck_version(self, deck):
        return deck.get('current_version') or deck.get('version') or '1.0'
    
    def load_decks(self):
        """Load decks"""
        self.info_label.setText("⏳ Loading your decks...")
        self.deck_list.clear()
        
        try:
            self.log("\n=== Loading decks ===")
            self.decks = api.get_purchased_decks()
            
            total = len(self.decks)
            downloaded = sum(1 for d in self.decks if self.is_downloaded(d))
            updates = sum(1 for d in self.decks if self.has_update(d))
            
            self.info_label.setText(
                f"📚 {total} total deck(s) • ✓ {downloaded} downloaded • ⟳ {updates} update(s) available"
            )
            self.filter_decks()
            
        except Exception as e:
            self.log(f"Error: {str(e)}")
            self.info_label.setText("❌ Failed to load decks")
            QMessageBox.warning(self, "Error", f"Failed to load decks:\n\n{str(e)}")
    
    def populate_deck_list(self, decks):
        """Populate list with checkboxes"""
        self.deck_list.clear()
        self.stats_label.setText(f"{len(decks)} deck(s) shown")
        
        for deck in decks:
            title = deck.get('title', 'Unknown')
            subject = deck.get('subject', 'N/A')
            cards = deck.get('card_count', 0)
            version = self.get_deck_version(deck)
            
            is_dl = self.is_downloaded(deck)
            has_upd = self.has_update(deck)
            
            # Status icon
            if has_upd:
                icon = "⟳"
                status = "Update Available"
            elif is_dl:
                icon = "✓"
                status = "Downloaded"
            else:
                icon = "○"
                status = "Not Downloaded"
            
            display = f"{icon} {title}\n   📖 {subject} • 🃏 {cards} cards • v{version} • {status}"
            
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, deck)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.deck_list.addItem(item)
        
        self.update_selection_count()
    
    def on_item_checked(self, item):
        """Handle checkbox state change"""
        self.update_selection_count()
        
        # Show details if only one is checked
        checked_items = self.get_checked_items()
        if len(checked_items) == 1:
            deck = checked_items[0].data(Qt.ItemDataRole.UserRole)
            self.show_deck_details(deck)
    
    def get_checked_items(self):
        """Get all checked items"""
        checked = []
        for i in range(self.deck_list.count()):
            item = self.deck_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked.append(item)
        return checked
    
    def update_selection_count(self):
        """Update selection count label"""
        count = len(self.get_checked_items())
        self.selection_label.setText(f"{count} selected")
        self.download_button.setEnabled(count > 0)
        
        if count == 0:
            self.details_label.setText("Select a deck to view details")
    
    def select_all_visible(self):
        """Select all visible items"""
        for i in range(self.deck_list.count()):
            item = self.deck_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)
        self.update_selection_count()
    
    def deselect_all(self):
        """Deselect all items"""
        for i in range(self.deck_list.count()):
            item = self.deck_list.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)
        self.update_selection_count()
    
    def show_deck_details(self, deck):
        """Show details"""
        title = deck.get('title', 'Unknown')
        desc = deck.get('description', 'No description available')
        subject = deck.get('subject', 'N/A')
        cards = deck.get('card_count', 0)
        version = self.get_deck_version(deck)
        
        is_dl = self.is_downloaded(deck)
        has_upd = self.has_update(deck)
        
        status = ""
        if has_upd:
            status = "<p style='color: #ff9800;'><b>⟳ Update Available!</b></p>"
        elif is_dl:
            status = "<p style='color: #4caf50;'><b>✓ Downloaded</b></p>"
        else:
            status = "<p><b>○ Not Downloaded Yet</b></p>"
        
        html = f"""
        <h2>{title}</h2>
        {status}
        <p><b>Subject:</b> {subject}</p>
        <p><b>Cards:</b> {cards}</p>
        <p><b>Version:</b> v{version}</p>
        <p><b>Description:</b><br>{desc}</p>
        """
        
        self.details_label.setText(html)
    
    def check_for_updates(self):
        """Check updates"""
        try:
            self.check_updates_button.setEnabled(False)
            self.check_updates_button.setText("⏳ Checking...")
            
            result = api.check_updates()
            updates = result.get('updates_available', 0)
            
            if updates > 0:
                QMessageBox.information(
                    self, "Updates Available",
                    f"🎉 {updates} deck update(s) available!\n\n"
                    f"Use the 'Updates Available' filter to see which decks have updates."
                )
            else:
                QMessageBox.information(
                    self, "All Up to Date",
                    "✅ All your decks are up to date!"
                )
            
            self.load_decks()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to check for updates:\n\n{str(e)}")
        finally:
            self.check_updates_button.setEnabled(True)
            self.check_updates_button.setText("🔄 Check for Updates")
    
    def download_selected(self):
        """Download checked decks"""
        checked_items = self.get_checked_items()
        if not checked_items:
            return
        
        decks_to_download = [item.data(Qt.ItemDataRole.UserRole) for item in checked_items]
        self.download_decks(decks_to_download)
    
    def download_all_visible(self):
        """Download all filtered decks"""
        if not self.filtered_decks:
            QMessageBox.information(self, "No Decks", "No decks to download with current filters.")
            return
        
        reply = QMessageBox.question(
            self, "Download All Visible",
            f"Download all {len(self.filtered_decks)} visible deck(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.download_decks(self.filtered_decks)
    
    def download_decks(self, decks):
        """Download multiple decks"""
        total = len(decks)
        
        progress = QProgressDialog(f"Downloading {total} deck(s)...", "Cancel", 0, total, self)
        progress.setWindowTitle("Downloading Decks")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumWidth(400)
        
        success_count = 0
        failed = []
        
        for i, deck in enumerate(decks):
            if progress.wasCanceled():
                break
            
            deck_title = deck.get('title', 'Unknown')
            progress.setLabelText(f"Downloading {i+1}/{total}:\n{deck_title}")
            progress.setValue(i)
            
            try:
                deck_id = self.get_deck_id(deck)
                version = self.get_deck_version(deck)
                
                # Download
                self.log(f"Downloading: {deck_title}")
                download_info = api.download_deck(deck_id)
                deck_content = api.download_deck_file(download_info['download_url'])
                
                # Import
                self.log(f"Importing: {deck_title}")
                anki_deck_id = import_deck(deck_content, deck_title)
                config.save_downloaded_deck(deck_id, version, anki_deck_id)
                
                success_count += 1
                self.log(f"✓ Success: {deck_title}")
                
            except Exception as e:
                error_msg = str(e)
                failed.append(f"{deck_title}: {error_msg}")
                self.log(f"✗ Failed: {deck_title} - {error_msg}")
        
        progress.setValue(total)
        progress.close()
        
        # Summary
        if success_count == total:
            msg = f"✅ Successfully downloaded all {total} deck(s)!\n\nYou can now study them in Anki."
            QMessageBox.information(self, "Download Complete", msg)
        elif success_count > 0:
            msg = f"✅ Downloaded {success_count}/{total} deck(s)"
            if failed:
                msg += f"\n\n❌ Failed ({len(failed)}):\n\n" + "\n".join(failed[:3])
                if len(failed) > 3:
                    msg += f"\n... and {len(failed)-3} more"
            QMessageBox.warning(self, "Partial Success", msg)
        else:
            msg = f"❌ All downloads failed.\n\n" + "\n".join(failed[:5])
            if len(failed) > 5:
                msg += f"\n... and {len(failed)-5} more"
            QMessageBox.critical(self, "Download Failed", msg)
        
        self.load_decks()