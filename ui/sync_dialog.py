"""
Auto-Sync Dialog for Nottorney Addon
One-click syncing of all purchased decks
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, Qt, QMessageBox, QFrame, QGroupBox
)
from aqt import mw
from ..api_client import api, NottorneyAPIError
from ..config import config
from ..deck_importer import import_deck


class SyncDialog(QDialog):
    """Dialog for automatic deck syncing - maximum ease of use"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚖️ Sync My Decks")
        self.setMinimumSize(700, 600)
        self.dark_mode = True
        self.decks = []
        self.sync_in_progress = False
        
        self.setup_ui()
        self.apply_theme()
        self.load_deck_status()
    
    def get_stylesheet(self):
        """Get stylesheet for current theme"""
        if self.dark_mode:
            return """
                QDialog { background-color: #1e1e1e; }
                QGroupBox {
                    background-color: #2d2d2d; border: 1px solid #404040;
                    border-radius: 8px; margin-top: 10px; padding-top: 15px;
                    font-weight: bold; color: #e0e0e0;
                }
                QLabel { color: #e0e0e0; }
                QLabel#headerLabel { color: #e0e0e0; font-size: 26px; font-weight: bold; }
                QLabel#statusLabel {
                    background-color: #2d2d2d; border: 1px solid #404040;
                    border-radius: 8px; padding: 15px; color: #e0e0e0; font-size: 14px;
                }
                QLabel#infoLabel {
                    background-color: #1565c0; border-left: 4px solid #2196f3;
                    border-radius: 6px; padding: 14px; color: #ffffff; font-size: 13px;
                }
                QLabel#successLabel {
                    background-color: #2e7d32; border-left: 4px solid #4caf50;
                    border-radius: 6px; padding: 14px; color: #ffffff; font-size: 13px;
                }
                QProgressBar {
                    border: 1px solid #404040; border-radius: 6px;
                    background-color: #2d2d2d; text-align: center;
                    color: #e0e0e0; height: 25px;
                }
                QProgressBar::chunk {
                    background-color: #2196f3; border-radius: 5px;
                }
                QPushButton {
                    background-color: #2d2d2d; border: 1px solid #505050;
                    border-radius: 6px; padding: 12px 24px; color: #e0e0e0;
                    font-weight: 500; font-size: 14px;
                }
                QPushButton:hover { background-color: #353535; border-color: #2196f3; }
                QPushButton:pressed { background-color: #1565c0; }
                QPushButton:disabled { background-color: #1a1a1a; color: #666; }
                QPushButton#primaryButton {
                    background-color: #4caf50; color: white; border: none;
                    font-weight: bold; font-size: 16px; padding: 14px 32px;
                }
                QPushButton#primaryButton:hover { background-color: #45a049; }
                QPushButton#primaryButton:disabled { background-color: #2a4a2b; }
                QTextEdit {
                    background-color: #1a1a1a; color: #00ff00;
                    border: 1px solid #404040; border-radius: 6px;
                    font-family: monospace; font-size: 12px; padding: 8px;
                }
            """
        else:
            return """
                QDialog { background-color: #f8f9fa; }
                QGroupBox {
                    background-color: white; border: 1px solid #e0e0e0;
                    border-radius: 8px; margin-top: 10px; padding-top: 15px;
                    font-weight: bold; color: #2c3e50;
                }
                QLabel { color: #2c3e50; }
                QLabel#headerLabel { color: #2c3e50; font-size: 26px; font-weight: bold; }
                QLabel#statusLabel {
                    background-color: white; border: 1px solid #e0e0e0;
                    border-radius: 8px; padding: 15px; color: #2c3e50; font-size: 14px;
                }
                QLabel#infoLabel {
                    background-color: #e3f2fd; border-left: 4px solid #2196f3;
                    border-radius: 6px; padding: 14px; color: #1976d2; font-size: 13px;
                }
                QLabel#successLabel {
                    background-color: #e8f5e9; border-left: 4px solid #4caf50;
                    border-radius: 6px; padding: 14px; color: #2e7d32; font-size: 13px;
                }
                QProgressBar {
                    border: 1px solid #d0d0d0; border-radius: 6px;
                    background-color: white; text-align: center;
                    color: #2c3e50; height: 25px;
                }
                QProgressBar::chunk {
                    background-color: #2196f3; border-radius: 5px;
                }
                QPushButton {
                    background-color: white; border: 1px solid #d0d0d0;
                    border-radius: 6px; padding: 12px 24px; color: #2c3e50;
                    font-weight: 500; font-size: 14px;
                }
                QPushButton:hover { background-color: #f5f5f5; border-color: #2196f3; }
                QPushButton:pressed { background-color: #e3f2fd; }
                QPushButton:disabled { background-color: #f0f0f0; color: #999; }
                QPushButton#primaryButton {
                    background-color: #4caf50; color: white; border: none;
                    font-weight: bold; font-size: 16px; padding: 14px 32px;
                }
                QPushButton#primaryButton:hover { background-color: #45a049; }
                QPushButton#primaryButton:disabled { background-color: #ccc; }
                QTextEdit {
                    background-color: #1a1a1a; color: #00ff00;
                    border: 1px solid #d0d0d0; border-radius: 6px;
                    font-family: monospace; font-size: 12px; padding: 8px;
                }
            """
    
    def apply_theme(self):
        """Apply current theme"""
        self.setStyleSheet(self.get_stylesheet())
    
    def setup_ui(self):
        """Set up the UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("🔄 Sync My Decks")
        title.setObjectName("headerLabel")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        user = config.get_user()
        if user:
            user_label = QLabel(f"👤 {user.get('email', 'User')}")
            header_layout.addWidget(user_label)
        
        layout.addLayout(header_layout)
        
        # Info message
        self.info_label = QLabel(
            "💡 <b>One-Click Sync:</b> This will automatically download all your "
            "purchased decks and keep them up to date. No manual downloads needed!"
        )
        self.info_label.setObjectName("infoLabel")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        # Status display
        status_group = QGroupBox("📊 Deck Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Loading deck information...")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Log area
        log_group = QGroupBox("📝 Sync Log")
        log_group.setCheckable(True)
        log_group.setChecked(False)
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.check_button = QPushButton("🔍 Check for Updates")
        self.check_button.clicked.connect(self.check_updates)
        
        self.sync_button = QPushButton("🔄 Sync All Decks")
        self.sync_button.setObjectName("primaryButton")
        self.sync_button.clicked.connect(self.start_sync)
        
        self.close_button = QPushButton("✕ Close")
        self.close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.check_button)
        button_layout.addStretch()
        button_layout.addWidget(self.sync_button)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def log(self, message, is_error=False):
        """Add message to log"""
        prefix = "❌ " if is_error else "✓ "
        self.log_text.append(f"{prefix}{message}")
        print(message)
    
    def load_deck_status(self):
        """Load current deck status"""
        try:
            self.log("Loading deck information...")
            self.decks = api.get_purchased_decks()
            
            downloaded_decks = config.get_downloaded_decks()
            
            total = len(self.decks)
            downloaded = sum(1 for d in self.decks if self.get_deck_id(d) in downloaded_decks)
            not_downloaded = total - downloaded
            
            # Check for updates
            updates_available = 0
            for deck in self.decks:
                deck_id = self.get_deck_id(deck)
                if deck_id in downloaded_decks:
                    current_version = self.get_deck_version(deck)
                    saved_version = downloaded_decks[deck_id].get('version')
                    if current_version != saved_version:
                        updates_available += 1
            
            status_html = f"""
                <div style='font-size: 14px;'>
                    <p><b>Total Decks:</b> {total}</p>
                    <p><b>✓ Downloaded:</b> {downloaded}</p>
                    <p><b>○ Not Downloaded:</b> {not_downloaded}</p>
                    <p><b>⟳ Updates Available:</b> {updates_available}</p>
                </div>
            """
            
            self.status_label.setText(status_html)
            
            # Update info message
            if not_downloaded == 0 and updates_available == 0:
                self.info_label.setText(
                    "✅ <b>All synced!</b> All your decks are downloaded and up to date."
                )
                self.info_label.setObjectName("successLabel")
                self.apply_theme()
                self.sync_button.setText("✓ Everything Up to Date")
                self.sync_button.setEnabled(False)
            elif not_downloaded > 0 or updates_available > 0:
                action = []
                if not_downloaded > 0:
                    action.append(f"download {not_downloaded} new deck(s)")
                if updates_available > 0:
                    action.append(f"update {updates_available} deck(s)")
                
                self.info_label.setText(
                    f"🔄 <b>Ready to sync!</b> Click 'Sync All Decks' to {' and '.join(action)}."
                )
                self.sync_button.setText(f"🔄 Sync All ({not_downloaded + updates_available} changes)")
            
            self.log(f"Found {total} purchased decks")
            
        except Exception as e:
            self.log(f"Error loading decks: {str(e)}", is_error=True)
            self.status_label.setText("❌ Failed to load deck information")
            QMessageBox.warning(self, "Error", f"Failed to load decks:\n\n{str(e)}")
    
    def check_updates(self):
        """Check for updates"""
        self.check_button.setEnabled(False)
        self.check_button.setText("⏳ Checking...")
        
        try:
            self.log("Checking for updates...")
            result = api.check_updates()
            
            updates = result.get('updates_available', 0)
            
            if updates > 0:
                QMessageBox.information(
                    self, "Updates Available",
                    f"🎉 {updates} deck update(s) available!\n\n"
                    f"Click 'Sync All Decks' to download updates."
                )
                self.log(f"Found {updates} update(s)")
            else:
                QMessageBox.information(
                    self, "All Up to Date",
                    "✅ All your decks are up to date!"
                )
                self.log("All decks are up to date")
            
            self.load_deck_status()
            
        except Exception as e:
            self.log(f"Error checking updates: {str(e)}", is_error=True)
            QMessageBox.warning(self, "Error", f"Failed to check for updates:\n\n{str(e)}")
        finally:
            self.check_button.setEnabled(True)
            self.check_button.setText("🔍 Check for Updates")
    
    def start_sync(self):
        """Start the sync process"""
        if self.sync_in_progress:
            return
        
        # Confirm with user
        downloaded_decks = config.get_downloaded_decks()
        
        new_count = sum(1 for d in self.decks if self.get_deck_id(d) not in downloaded_decks)
        update_count = sum(1 for d in self.decks 
                          if self.get_deck_id(d) in downloaded_decks 
                          and self.get_deck_version(d) != downloaded_decks[self.get_deck_id(d)].get('version'))
        
        if new_count == 0 and update_count == 0:
            QMessageBox.information(self, "All Synced", "All your decks are already downloaded and up to date!")
            return
        
        message_parts = []
        if new_count > 0:
            message_parts.append(f"• Download {new_count} new deck(s)")
        if update_count > 0:
            message_parts.append(f"• Update {update_count} existing deck(s)")
        
        reply = QMessageBox.question(
            self, "Confirm Sync",
            f"This will:\n\n" + "\n".join(message_parts) + "\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.sync_in_progress = True
        self.sync_button.setEnabled(False)
        self.check_button.setEnabled(False)
        self.close_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        self.log("\n=== Starting Sync Process ===")
        self.perform_sync()
    
    def perform_sync(self):
        """Perform the actual sync"""
        downloaded_decks = config.get_downloaded_decks()
        
        # Determine which decks need action
        decks_to_sync = []
        for deck in self.decks:
            deck_id = self.get_deck_id(deck)
            current_version = self.get_deck_version(deck)
            
            if deck_id not in downloaded_decks:
                # New deck
                decks_to_sync.append((deck, 'new'))
            elif downloaded_decks[deck_id].get('version') != current_version:
                # Update available
                decks_to_sync.append((deck, 'update'))
        
        if not decks_to_sync:
            self.log("Nothing to sync!")
            self.finish_sync(0, 0, [])
            return
        
        total = len(decks_to_sync)
        success_count = 0
        failed = []
        
        self.progress_bar.setMaximum(total)
        
        for i, (deck, action_type) in enumerate(decks_to_sync):
            deck_title = deck.get('title', 'Unknown')
            deck_id = self.get_deck_id(deck)
            version = self.get_deck_version(deck)
            
            action_str = "Downloading" if action_type == 'new' else "Updating"
            self.log(f"{action_str} ({i+1}/{total}): {deck_title}")
            self.progress_bar.setValue(i)
            
            try:
                # Download deck
                download_info = api.download_deck(deck_id)
                deck_content = api.download_deck_file(download_info['download_url'])
                
                # Import into Anki
                anki_deck_id = import_deck(deck_content, deck_title)
                config.save_downloaded_deck(deck_id, version, anki_deck_id)
                
                success_count += 1
                self.log(f"✓ Success: {deck_title}")
                
            except Exception as e:
                error_msg = str(e)
                failed.append(f"{deck_title}: {error_msg}")
                self.log(f"✗ Failed: {deck_title} - {error_msg}", is_error=True)
        
        self.progress_bar.setValue(total)
        self.finish_sync(success_count, total, failed)
    
    def finish_sync(self, success_count, total, failed):
        """Finish the sync process"""
        self.sync_in_progress = False
        self.sync_button.setEnabled(True)
        self.check_button.setEnabled(True)
        self.close_button.setEnabled(True)
        
        self.log("\n=== Sync Complete ===")
        
        if success_count == total:
            msg = f"✅ Successfully synced all {total} deck(s)!\n\nYou can now study them in Anki."
            QMessageBox.information(self, "Sync Complete", msg)
            self.log(f"All {total} decks synced successfully!")
        elif success_count > 0:
            msg = f"⚠️ Synced {success_count}/{total} deck(s)"
            if failed:
                msg += f"\n\n❌ Failed ({len(failed)}):\n\n" + "\n".join(failed[:3])
                if len(failed) > 3:
                    msg += f"\n... and {len(failed)-3} more"
            QMessageBox.warning(self, "Partial Success", msg)
        else:
            msg = f"❌ Sync failed.\n\n" + "\n".join(failed[:5])
            if len(failed) > 5:
                msg += f"\n... and {len(failed)-5} more"
            QMessageBox.critical(self, "Sync Failed", msg)
        
        # Reload status
        self.load_deck_status()
    
    def get_deck_id(self, deck):
        """Get deck ID"""
        return deck.get('deck_id') or deck.get('id')
    
    def get_deck_version(self, deck):
        """Get deck version"""
        return deck.get('current_version') or deck.get('version') or '1.0'