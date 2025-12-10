"""
Enhanced Deck Manager Dialog for Nottorney Addon
Features: Clean UI, Basic/Advanced modes, better styling
FIXED: List item display issues
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QMessageBox, QProgressDialog,
    Qt, QTextEdit, QCheckBox, QLineEdit, QComboBox, QGroupBox,
    QSplitter, QWidget, QScrollArea, QFrame, QTabWidget
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
        self.setWindowTitle("⚖️ Nottorney Deck Manager")
        self.setMinimumSize(1000, 750)
        self.decks = []
        self.filtered_decks = []
        self.show_updates_only = False
        self.search_text = ""
        self.sort_by = "title"
        self.advanced_mode = False
        
        # Apply modern stylesheet
        self.setStyleSheet(self.get_stylesheet())
        
        self.setup_ui()
        self.load_decks()
    
    def get_stylesheet(self):
        """Return the modern stylesheet for the dialog"""
        return """
            QDialog {
                background-color: #f8f9fa;
            }
            
            QGroupBox {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
                color: #2c3e50;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: #2c3e50;
            }
            
            QListWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 5px;
                outline: none;
                color: #2c3e50;
            }
            
            QListWidget::item {
                padding: 15px;
                border-bottom: 1px solid #f0f0f0;
                border-radius: 6px;
                margin: 2px;
                color: #2c3e50;
                background-color: white;
            }
            
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
                border: 2px solid #2196f3;
            }
            
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
            
            QPushButton {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 8px 16px;
                color: #2c3e50;
                font-weight: 500;
            }
            
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #2196f3;
            }
            
            QPushButton:pressed {
                background-color: #e3f2fd;
            }
            
            QPushButton:disabled {
                background-color: #f0f0f0;
                color: #999;
                border-color: #e0e0e0;
            }
            
            QPushButton#primaryButton {
                background-color: #4caf50;
                color: white;
                border: none;
                font-weight: bold;
            }
            
            QPushButton#primaryButton:hover {
                background-color: #45a049;
            }
            
            QPushButton#primaryButton:disabled {
                background-color: #cccccc;
            }
            
            QPushButton#dangerButton {
                background-color: #f44336;
                color: white;
                border: none;
            }
            
            QPushButton#dangerButton:hover {
                background-color: #da190b;
            }
            
            QLineEdit, QComboBox {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 8px;
                color: #2c3e50;
            }
            
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #2196f3;
            }
            
            QLabel {
                color: #2c3e50;
            }
            
            QLabel#headerLabel {
                color: #2c3e50;
                font-size: 24px;
                font-weight: bold;
            }
            
            QLabel#infoLabel {
                background-color: white;
                border-left: 4px solid #2196f3;
                border-radius: 6px;
                padding: 12px;
                color: #2c3e50;
            }
            
            QLabel#statsLabel {
                background-color: #e3f2fd;
                border-radius: 6px;
                padding: 8px 12px;
                color: #1976d2;
                font-weight: bold;
            }
            
            QLabel#detailsLabel {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                color: #2c3e50;
            }
            
            QTextEdit#debugLog {
                background-color: #2b2b2b;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                border-radius: 6px;
            }
            
            QCheckBox {
                color: #2c3e50;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #d0d0d0;
            }
            
            QCheckBox::indicator:checked {
                background-color: #2196f3;
                border-color: #2196f3;
            }
            
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
            }
            
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 2px;
                color: #666;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                color: #2196f3;
                font-weight: bold;
            }
            
            QTabBar::tab:hover {
                background-color: #e3f2fd;
            }
        """
    
    def populate_deck_list(self, decks):
        """Populate both deck lists with proper text formatting"""
        self.deck_list.clear()
        self.adv_deck_list.clear()
        
        if not decks:
            self.stats_label.setText("0 decks found")
            self.adv_stats_label.setText("0 decks found")
            self.details_label.setText("No decks match your filters")
            return
        
        stats_text = f"{len(decks)} deck(s)"
        self.stats_label.setText(stats_text)
        self.adv_stats_label.setText(stats_text)
        
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
            
            # Status icon
            if has_update:
                icon = "⟳"
                status = "Update Available"
            elif is_downloaded:
                icon = "✓"
                status = "Downloaded"
            else:
                icon = "○"
                status = "Not Downloaded"
            
            # Format display text - Use plain text, not HTML
            # QListWidget displays plain text by default
            display = f"{icon} {title}\n"
            display += f"📖 {subject} • 🃏 {cards} cards • v{version}\n"
            display += f"{status}"
            
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, deck)
            
            # Add visual styling through item properties
            if has_update:
                # Orange-ish for updates
                item.setForeground(Qt.GlobalColor.darkYellow)
            elif is_downloaded:
                # Green for downloaded
                item.setForeground(Qt.GlobalColor.darkGreen)
            
            # Add to both lists (create separate items for each list)
            item2 = QListWidgetItem(display)
            item2.setData(Qt.ItemDataRole.UserRole, deck)
            if has_update:
                item2.setForeground(Qt.GlobalColor.darkYellow)
            elif is_downloaded:
                item2.setForeground(Qt.GlobalColor.darkGreen)
            
            self.deck_list.addItem(item)
            self.adv_deck_list.addItem(item2)
    
    # ... (rest of the methods remain the same, just include the key fix above)
    # I'm showing the critical fix - the populate_deck_list method
    # The rest of your code can stay as-is, just update this method