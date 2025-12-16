"""
Settings Dialog for Nottorney Addon
Features: General settings, Protected Fields, Sync, Admin (for admins)
Version: 1.1.0
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox, Qt,
    QTabWidget, QWidget, QCheckBox, QSpinBox, QGroupBox,
    QFormLayout, QComboBox, QTextEdit, QProgressBar
)
from aqt import mw

from ..api_client import api, set_access_token, NottorneyAPIError
from ..config import config


class SettingsDialog(QDialog):
    """Settings dialog with multiple configuration tabs"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Nottorney Settings")
        self.setMinimumSize(600, 500)
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup main UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Title
        title = QLabel("⚙️ Settings")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabBar::tab { padding: 8px 20px; }")
        
        # Create tabs
        self.general_tab = self.create_general_tab()
        self.protected_fields_tab = self.create_protected_fields_tab()
        self.sync_tab = self.create_sync_tab()
        
        self.tabs.addTab(self.general_tab, "🔧 General")
        self.tabs.addTab(self.protected_fields_tab, "🛡️ Protected Fields")
        self.tabs.addTab(self.sync_tab, "🔄 Sync")
        
        # Add Admin tab only if user is admin
        if config.is_admin():
            self.admin_tab = self.create_admin_tab()
            self.tabs.addTab(self.admin_tab, "👑 Admin")
        
        layout.addWidget(self.tabs)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save Settings")
        save_btn.setStyleSheet("padding: 10px; font-weight: bold; background-color: #4CAF50; color: white;")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("padding: 10px;")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_general_tab(self):
        """Create General settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # UI Mode
        ui_group = QGroupBox("User Interface")
        ui_layout = QFormLayout()
        
        self.ui_mode_combo = QComboBox()
        self.ui_mode_combo.addItem("Tabbed (Modern)", "tabbed")
        self.ui_mode_combo.addItem("Minimal (Legacy)", "minimal")
        ui_layout.addRow("UI Mode:", self.ui_mode_combo)
        
        ui_group.setLayout(ui_layout)
        layout.addWidget(ui_group)
        
        # Update Checking
        update_group = QGroupBox("Update Checking")
        update_layout = QFormLayout()
        
        self.auto_check_updates = QCheckBox("Automatically check for deck updates")
        update_layout.addRow(self.auto_check_updates)
        
        self.update_interval = QSpinBox()
        self.update_interval.setMinimum(1)
        self.update_interval.setMaximum(168)  # 1 week max
        self.update_interval.setSuffix(" hours")
        update_layout.addRow("Check interval:", self.update_interval)
        
        update_group.setLayout(update_layout)
        layout.addWidget(update_group)
        
        # Auto Sync
        sync_group = QGroupBox("Progress Sync")
        sync_layout = QFormLayout()
        
        self.auto_sync_enabled = QCheckBox("Automatically sync study progress")
        sync_layout.addRow(self.auto_sync_enabled)
        
        sync_group.setLayout(sync_layout)
        layout.addWidget(sync_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_protected_fields_tab(self):
        """Create Protected Fields settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "Protected fields are preserved during sync updates.\n"
            "Add field names that you want to keep from being overwritten."
        )
        instructions.setStyleSheet("color: #666; padding: 10px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Deck selector
        deck_layout = QHBoxLayout()
        deck_label = QLabel("Select Deck:")
        deck_label.setStyleSheet("font-weight: bold;")
        deck_layout.addWidget(deck_label)
        
        self.deck_selector = QComboBox()
        self.deck_selector.setMinimumWidth(300)
        self.deck_selector.currentIndexChanged.connect(self.on_deck_selected)
        deck_layout.addWidget(self.deck_selector)
        
        deck_layout.addStretch()
        layout.addLayout(deck_layout)
        
        # Protected fields list
        fields_group = QGroupBox("Protected Fields for Selected Deck")
        fields_layout = QVBoxLayout()
        
        self.protected_fields_list = QListWidget()
        self.protected_fields_list.setStyleSheet("QListWidget::item { padding: 8px; }")
        fields_layout.addWidget(self.protected_fields_list)
        
        # Add/Remove buttons
        field_btn_layout = QHBoxLayout()
        
        self.new_field_input = QLineEdit()
        self.new_field_input.setPlaceholderText("Enter field name to protect...")
        field_btn_layout.addWidget(self.new_field_input)
        
        add_field_btn = QPushButton("➕ Add")
        add_field_btn.clicked.connect(self.add_protected_field)
        field_btn_layout.addWidget(add_field_btn)
        
        remove_field_btn = QPushButton("➖ Remove Selected")
        remove_field_btn.clicked.connect(self.remove_protected_field)
        field_btn_layout.addWidget(remove_field_btn)
        
        fields_layout.addLayout(field_btn_layout)
        fields_group.setLayout(fields_layout)
        layout.addWidget(fields_group)
        
        # Fetch from server button
        fetch_btn = QPushButton("🔄 Fetch Protected Fields from Server")
        fetch_btn.clicked.connect(self.fetch_protected_fields)
        layout.addWidget(fetch_btn)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_sync_tab(self):
        """Create Sync settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Sync options
        sync_group = QGroupBox("Sync Preferences")
        sync_layout = QFormLayout()
        
        self.sync_tags = QCheckBox("Sync tags with server")
        sync_layout.addRow(self.sync_tags)
        
        self.sync_suspend = QCheckBox("Sync suspend/buried state")
        sync_layout.addRow(self.sync_suspend)
        
        self.sync_note_types = QCheckBox("Sync note type templates")
        sync_layout.addRow(self.sync_note_types)
        
        sync_group.setLayout(sync_layout)
        layout.addWidget(sync_group)
        
        # Sync info
        info_group = QGroupBox("Sync Status")
        info_layout = QVBoxLayout()
        
        last_sync = config.get_last_update_check() or "Never"
        self.last_sync_label = QLabel(f"Last sync check: {last_sync}")
        self.last_sync_label.setStyleSheet("color: #666;")
        info_layout.addWidget(self.last_sync_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def load_settings(self):
        """Load current settings into UI"""
        # General tab
        ui_mode = config.get_ui_mode()
        index = self.ui_mode_combo.findData(ui_mode)
        if index >= 0:
            self.ui_mode_combo.setCurrentIndex(index)
        
        self.auto_check_updates.setChecked(config.get_auto_check_updates())
        self.update_interval.setValue(config.get_update_check_interval_hours())
        self.auto_sync_enabled.setChecked(config.get_auto_sync_enabled())
        
        # Protected fields tab - load decks
        self.load_deck_list()
        
        # Sync tab - these are placeholders for future config
        self.sync_tags.setChecked(True)
        self.sync_suspend.setChecked(True)
        self.sync_note_types.setChecked(True)
    
    def load_deck_list(self):
        """Load downloaded decks into deck selector"""
        self.deck_selector.clear()
        self.deck_selector.addItem("-- Select a deck --", None)
        
        downloaded_decks = config.get_downloaded_decks()
        
        for deck_id, deck_info in downloaded_decks.items():
            # Get deck name from Anki if possible
            anki_deck_id = deck_info.get('anki_deck_id')
            deck_name = f"Deck {deck_id[:8]}"
            
            if anki_deck_id and mw.col:
                try:
                    deck = mw.col.decks.get(int(anki_deck_id))
                    if deck:
                        deck_name = deck['name']
                except:
                    pass
            
            version = deck_info.get('version', '?')
            display_text = f"{deck_name} (v{version})"
            self.deck_selector.addItem(display_text, deck_id)
    
    def on_deck_selected(self, index):
        """Handle deck selection change"""
        self.protected_fields_list.clear()
        
        deck_id = self.deck_selector.currentData()
        if not deck_id:
            return
        
        # Load protected fields for this deck
        protected = config.get_protected_fields(deck_id)
        
        for field_name in protected:
            item = QListWidgetItem(f"🛡️ {field_name}")
            item.setData(Qt.ItemDataRole.UserRole, field_name)
            self.protected_fields_list.addItem(item)
    
    def add_protected_field(self):
        """Add a new protected field"""
        deck_id = self.deck_selector.currentData()
        if not deck_id:
            QMessageBox.warning(self, "No Deck Selected", "Please select a deck first.")
            return
        
        field_name = self.new_field_input.text().strip()
        if not field_name:
            QMessageBox.warning(self, "Empty Field", "Please enter a field name.")
            return
        
        # Get current protected fields
        protected = list(config.get_protected_fields(deck_id))
        
        if field_name in protected:
            QMessageBox.warning(self, "Already Protected", f"'{field_name}' is already protected.")
            return
        
        # Add to list
        protected.append(field_name)
        config.save_protected_fields(deck_id, protected)
        
        # Update UI
        item = QListWidgetItem(f"🛡️ {field_name}")
        item.setData(Qt.ItemDataRole.UserRole, field_name)
        self.protected_fields_list.addItem(item)
        
        self.new_field_input.clear()
        QMessageBox.information(self, "Added", f"'{field_name}' is now protected.")
    
    def remove_protected_field(self):
        """Remove selected protected field"""
        current = self.protected_fields_list.currentItem()
        if not current:
            QMessageBox.warning(self, "No Selection", "Please select a field to remove.")
            return
        
        deck_id = self.deck_selector.currentData()
        if not deck_id:
            return
        
        field_name = current.data(Qt.ItemDataRole.UserRole)
        
        # Remove from config
        protected = list(config.get_protected_fields(deck_id))
        if field_name in protected:
            protected.remove(field_name)
            config.save_protected_fields(deck_id, protected)
        
        # Update UI
        row = self.protected_fields_list.row(current)
        self.protected_fields_list.takeItem(row)
        
        QMessageBox.information(self, "Removed", f"'{field_name}' is no longer protected.")
    
    def fetch_protected_fields(self):
        """Fetch protected fields from server"""
        deck_id = self.deck_selector.currentData()
        if not deck_id:
            QMessageBox.warning(self, "No Deck Selected", "Please select a deck first.")
            return
        
        token = config.get_access_token()
        if not token:
            QMessageBox.warning(self, "Not Logged In", "Please login first.")
            return
        
        set_access_token(token)
        
        try:
            result = api.get_protected_fields(deck_id)
            
            if result.get('success'):
                server_fields = result.get('protected_fields', [])
                
                if server_fields:
                    # Update local config
                    config.save_protected_fields(deck_id, server_fields)
                    
                    # Reload UI
                    self.on_deck_selected(self.deck_selector.currentIndex())
                    
                    QMessageBox.information(
                        self, "Success",
                        f"Loaded {len(server_fields)} protected field(s) from server."
                    )
                else:
                    QMessageBox.information(
                        self, "No Fields",
                        "No protected fields configured on server for this deck."
                    )
            else:
                QMessageBox.warning(self, "Error", "Failed to fetch from server.")
        
        except NottorneyAPIError as e:
            QMessageBox.critical(self, "API Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch: {e}")
    
    def create_admin_tab(self):
        """Create Admin tab (only visible to admins)"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Warning banner
        warning = QLabel(
            "⚠️ Admin Mode - Changes here affect ALL users of your decks!\n"
            "Only use these features if you are a deck publisher."
        )
        warning.setStyleSheet(
            "background-color: #fff3cd; color: #856404; "
            "padding: 10px; border-radius: 5px; font-weight: bold;"
        )
        warning.setWordWrap(True)
        layout.addWidget(warning)
        
        # Deck selector
        deck_group = QGroupBox("Select Deck to Manage")
        deck_layout = QFormLayout()
        
        self.admin_deck_selector = QComboBox()
        self.admin_deck_selector.setMinimumWidth(300)
        deck_layout.addRow("Anki Deck:", self.admin_deck_selector)
        
        # Create new deck option
        self.admin_create_new = QCheckBox("Create NEW deck (first-time import)")
        self.admin_create_new.setStyleSheet("color: #28a745; font-weight: bold;")
        self.admin_create_new.stateChanged.connect(self.on_create_new_changed)
        deck_layout.addRow("", self.admin_create_new)
        
        # Deck title for new deck
        self.admin_deck_title = QLineEdit()
        self.admin_deck_title.setPlaceholderText("Enter deck title for new deck")
        self.admin_deck_title.setEnabled(False)
        deck_layout.addRow("Deck Title:", self.admin_deck_title)
        
        # Deck ID input for existing deck
        self.admin_deck_id_input = QLineEdit()
        self.admin_deck_id_input.setPlaceholderText("Enter existing deck UUID (leave empty for new deck)")
        deck_layout.addRow("Existing Deck ID:", self.admin_deck_id_input)
        
        # Load decks
        self.load_admin_decks()
        
        deck_group.setLayout(deck_layout)
        layout.addWidget(deck_group)
        
        # Push Changes Section
        push_group = QGroupBox("Push Changes to Server")
        push_layout = QVBoxLayout()
        
        push_info = QLabel(
            "Push modified cards from your Anki to the server database.\n"
            "This will create a new version for all users to sync."
        )
        push_info.setStyleSheet("color: #666;")
        push_info.setWordWrap(True)
        push_layout.addWidget(push_info)
        
        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel("New Version:"))
        self.admin_version_input = QLineEdit()
        self.admin_version_input.setPlaceholderText("e.g., 2.2.0")
        version_layout.addWidget(self.admin_version_input)
        push_layout.addLayout(version_layout)
        
        notes_layout = QHBoxLayout()
        notes_layout.addWidget(QLabel("Version Notes:"))
        self.admin_notes_input = QLineEdit()
        self.admin_notes_input.setPlaceholderText("e.g., Updated 50 cards with new citations")
        notes_layout.addWidget(self.admin_notes_input)
        push_layout.addLayout(notes_layout)
        
        push_btn = QPushButton("🚀 Push Changes to Server")
        push_btn.setStyleSheet(
            "padding: 10px; font-weight: bold; "
            "background-color: #007bff; color: white;"
        )
        push_btn.clicked.connect(self.admin_push_changes)
        push_layout.addWidget(push_btn)
        
        push_group.setLayout(push_layout)
        layout.addWidget(push_group)
        
        # Import Deck Section
        import_group = QGroupBox("Import Full Deck to Database")
        import_layout = QVBoxLayout()
        
        import_info = QLabel(
            "One-time import of all cards from your Anki deck to the server.\n"
            "Use this for initial setup or to completely refresh the database."
        )
        import_info.setStyleSheet("color: #666;")
        import_info.setWordWrap(True)
        import_layout.addWidget(import_info)
        
        self.admin_clear_existing = QCheckBox("Clear existing cards before import")
        self.admin_clear_existing.setStyleSheet("color: #dc3545;")
        import_layout.addWidget(self.admin_clear_existing)
        
        import_btn = QPushButton("📥 Import Full Deck to Database")
        import_btn.setStyleSheet(
            "padding: 10px; font-weight: bold; "
            "background-color: #28a745; color: white;"
        )
        import_btn.clicked.connect(self.admin_import_deck)
        import_layout.addWidget(import_btn)
        
        import_group.setLayout(import_layout)
        layout.addWidget(import_group)
        
        # Status output
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        self.admin_status = QTextEdit()
        self.admin_status.setReadOnly(True)
        self.admin_status.setMaximumHeight(100)
        self.admin_status.setStyleSheet("font-family: monospace; font-size: 11px;")
        status_layout.addWidget(self.admin_status)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def load_admin_decks(self):
        """Load ALL Anki decks into admin deck selector"""
        self.admin_deck_selector.clear()
        self.admin_deck_selector.addItem("-- Select a deck --", None)
        
        if not mw.col:
            return
        
        # Get all Anki decks
        all_decks = mw.col.decks.all_names_and_ids()
        
        for deck in all_decks:
            deck_name = deck.name
            anki_id = deck.id
            
            # Skip default deck
            if deck_name == "Default":
                continue
            
            # Check if this deck is already tracked (has a Nottorney deck_id)
            downloaded = config.get_downloaded_decks()
            nottorney_id = None
            for nid, info in downloaded.items():
                if info.get('anki_deck_id') == anki_id:
                    nottorney_id = nid
                    break
            
            # Store anki_id as data since we need to look up cards by it
            display_text = f"{deck_name}"
            if nottorney_id:
                display_text += f" (ID: {nottorney_id[:8]}...)"
            
            # Store tuple of (anki_id, nottorney_id)
            self.admin_deck_selector.addItem(display_text, (anki_id, nottorney_id))
    
    def admin_log(self, message):
        """Add message to admin status log"""
        self.admin_status.append(message)
    
    def on_create_new_changed(self, state):
        """Toggle create new deck options"""
        is_new = self.admin_create_new.isChecked()
        self.admin_deck_title.setEnabled(is_new)
        self.admin_deck_id_input.setEnabled(not is_new)
        if is_new:
            self.admin_deck_id_input.clear()
    
    def admin_push_changes(self):
        """Push changes from Anki to server"""
        deck_data = self.admin_deck_selector.currentData()
        if not deck_data:
            QMessageBox.warning(self, "No Deck Selected", "Please select a deck first.")
            return
        
        anki_deck_id, existing_nottorney_id = deck_data
        
        # Get deck_id from input or existing mapping
        deck_id = self.admin_deck_id_input.text().strip()
        if not deck_id and existing_nottorney_id:
            deck_id = existing_nottorney_id
        
        if not deck_id:
            QMessageBox.warning(
                self, "Deck ID Required", 
                "Please enter the Server Deck ID (UUID from Nottorney database)."
            )
            return
        
        version = self.admin_version_input.text().strip()
        if not version:
            QMessageBox.warning(self, "Version Required", "Please enter a version number.")
            return
        
        version_notes = self.admin_notes_input.text().strip() or None
        
        if not mw.col:
            QMessageBox.warning(self, "No Collection", "Anki collection not available.")
            return
        
        # Confirm action
        reply = QMessageBox.question(
            self, "Confirm Push",
            f"This will push all cards from this deck to the server as version {version}.\n\n"
            f"Server Deck ID: {deck_id}\n\n"
            "All users will receive these changes on their next sync.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.admin_log(f"🔄 Collecting cards from deck...")
        
        try:
            # Get all notes from this deck
            deck_name = mw.col.decks.get(anki_deck_id)['name']
            note_ids = mw.col.find_notes(f'"deck:{deck_name}"')
            
            changes = []
            for nid in note_ids:
                note = mw.col.get_note(nid)
                fields = {}
                for field_name in note.keys():
                    fields[field_name] = note[field_name]
                
                changes.append({
                    "card_guid": note.guid,
                    "note_type": note.note_type()['name'],
                    "fields": fields,
                    "tags": note.tags,
                    "change_type": "modify"
                })
            
            self.admin_log(f"📦 Found {len(changes)} cards to push")
            self.admin_log(f"🚀 Pushing to server...")
            
            # Set token
            token = config.get_access_token()
            if token:
                set_access_token(token)
            
            # Make API call
            result = api.admin_push_changes(deck_id, changes, version, version_notes)
            
            if result.get('success'):
                added = result.get('cards_added', 0)
                modified = result.get('cards_modified', 0)
                self.admin_log(f"✅ Push successful! Added: {added}, Modified: {modified}")
                self.admin_log(f"📌 New version: {result.get('new_version', version)}")
                
                # Update local version
                config.update_deck_version(deck_id, version)
                
                QMessageBox.information(
                    self, "Push Successful",
                    f"Pushed {len(changes)} cards to server.\n\n"
                    f"New version: {result.get('new_version', version)}"
                )
            else:
                self.admin_log(f"❌ Push failed: {result.get('error', 'Unknown error')}")
                
        except NottorneyAPIError as e:
            self.admin_log(f"❌ API Error: {e}")
            QMessageBox.critical(self, "API Error", str(e))
        except Exception as e:
            self.admin_log(f"❌ Error: {e}")
            QMessageBox.critical(self, "Error", f"Push failed: {e}")
    
    def admin_import_deck(self):
        """Import full deck to database"""
        deck_data = self.admin_deck_selector.currentData()
        if not deck_data:
            QMessageBox.warning(self, "No Deck Selected", "Please select a deck first.")
            return
        
        anki_deck_id, existing_nottorney_id = deck_data
        is_new_deck = self.admin_create_new.isChecked()
        
        # For new deck, require title. For existing deck, require ID.
        deck_id = None
        deck_title = None
        
        if is_new_deck:
            deck_title = self.admin_deck_title.text().strip()
            if not deck_title:
                QMessageBox.warning(
                    self, "Deck Title Required", 
                    "Please enter a title for the new deck."
                )
                return
        else:
            # Get deck_id from input or existing mapping
            deck_id = self.admin_deck_id_input.text().strip()
            if not deck_id and existing_nottorney_id:
                deck_id = existing_nottorney_id
            
            if not deck_id:
                QMessageBox.warning(
                    self, "Deck ID Required", 
                    "Please enter the existing Deck ID, or check 'Create NEW deck'."
                )
                return
        
        version = self.admin_version_input.text().strip()
        if not version:
            QMessageBox.warning(self, "Version Required", "Please enter a version number.")
            return
        
        version_notes = self.admin_notes_input.text().strip() or None
        clear_existing = self.admin_clear_existing.isChecked()
        
        if not mw.col:
            QMessageBox.warning(self, "No Collection", "Anki collection not available.")
            return
        
        # Confirm action
        if is_new_deck:
            warning_text = (
                f"This will CREATE a new deck '{deck_title}' and import ALL cards "
                f"as version {version}.\n\nContinue?"
            )
        else:
            warning_text = (
                f"This will import ALL cards from this deck to the server database "
                f"as version {version}.\n\n"
                f"Server Deck ID: {deck_id}\n\n"
            )
            if clear_existing:
                warning_text += "⚠️ WARNING: Existing cards will be DELETED first!\n\n"
            warning_text += "This is typically used for initial setup. Continue?"
        
        reply = QMessageBox.question(
            self, "Confirm Import",
            warning_text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.admin_log(f"🔄 Collecting all cards from deck...")
        
        try:
            # Get all notes from this deck
            deck_name = mw.col.decks.get(anki_deck_id)['name']
            note_ids = mw.col.find_notes(f'"deck:{deck_name}"')
            
            cards = []
            for nid in note_ids:
                note = mw.col.get_note(nid)
                fields = {}
                for field_name in note.keys():
                    fields[field_name] = note[field_name]
                
                cards.append({
                    "card_guid": note.guid,
                    "note_type": note.note_type()['name'],
                    "fields": fields,
                    "tags": note.tags
                })
            
            self.admin_log(f"📦 Found {len(cards)} cards to import")
            self.admin_log(f"📥 Importing to server database...")
            
            # Set token
            token = config.get_access_token()
            if token:
                set_access_token(token)
            
            # Make API call - pass deck_title for new deck, deck_id for existing
            if is_new_deck:
                result = api.admin_import_deck(
                    deck_id=None, 
                    cards=cards, 
                    version=version, 
                    version_notes=version_notes, 
                    clear_existing=False,
                    deck_title=deck_title
                )
            else:
                result = api.admin_import_deck(
                    deck_id=deck_id, 
                    cards=cards, 
                    version=version, 
                    version_notes=version_notes, 
                    clear_existing=clear_existing
                )
            
            if result.get('success'):
                imported = result.get('cards_imported', 0)
                new_deck_id = result.get('deck_id', deck_id)
                self.admin_log(f"✅ Import successful! {imported} cards imported")
                self.admin_log(f"📌 Version: {result.get('version', version)}")
                if is_new_deck:
                    self.admin_log(f"🆕 Created deck ID: {new_deck_id}")
                
                # Track the deck locally
                if new_deck_id:
                    config.save_downloaded_deck(new_deck_id, version, anki_deck_id)
                
                QMessageBox.information(
                    self, "Import Successful",
                    f"Imported {imported} cards to database.\n\n"
                    f"Deck ID: {new_deck_id}\n"
                    f"Version: {result.get('version', version)}"
                )
            else:
                self.admin_log(f"❌ Import failed: {result.get('error', 'Unknown error')}")
                
        except NottorneyAPIError as e:
            self.admin_log(f"❌ API Error: {e}")
            QMessageBox.critical(self, "API Error", str(e))
        except Exception as e:
            self.admin_log(f"❌ Error: {e}")
            QMessageBox.critical(self, "Error", f"Import failed: {e}")
    
    def save_settings(self):
        """Save all settings"""
        try:
            # General settings
            ui_mode = self.ui_mode_combo.currentData()
            config.set_ui_mode(ui_mode)
            
            config.set_auto_check_updates(self.auto_check_updates.isChecked())
            config.set_update_check_interval_hours(self.update_interval.value())
            config.set_auto_sync_enabled(self.auto_sync_enabled.isChecked())
            
            # Protected fields are saved immediately when added/removed
            
            # Show success
            QMessageBox.information(
                self, "Settings Saved",
                "Settings saved successfully!\n\n"
                "Some changes may require restarting Anki."
            )
            
            self.accept()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings:\n{e}")


def show_settings_dialog(parent=None):
    """Show the settings dialog"""
    dialog = SettingsDialog(parent or mw)
    dialog.exec()
