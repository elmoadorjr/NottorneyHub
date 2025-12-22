"""
Reusable UI Components for AnkiPH Addon
Version: 4.0.0
"""

from aqt.qt import (
    pyqtSignal,
    QLabel, QFrame, QHBoxLayout, QVBoxLayout, 
    QProgressBar, QListWidget, QListWidgetItem, 
    QPushButton, QWidget, Qt
)

from .styles import COLORS, get_button_style


class ClickableLabel(QLabel):
    """Label that emits clicked signal"""
    clicked = pyqtSignal()
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class StatusBar(QFrame):
    """Consistent status bar widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        self.progress = QProgressBar()
        self.progress.setFixedWidth(150)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        self.setStyleSheet(f"""
            StatusBar {{
                background-color: {COLORS['bg_primary']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)
    
    def set_status(self, text: str, status_type: str = "info"):
        """Set status text with optional type (info, success, warning, error)"""
        color = COLORS.get(status_type, COLORS['text_muted'])
        self.status_label.setStyleSheet(f"color: {color}; font-size: 12px;")
        self.status_label.setText(text)
    
    def show_progress(self, value: int = -1, maximum: int = 100):
        """Show progress bar. Use value=-1 for indeterminate."""
        self.progress.setVisible(True)
        if value < 0:
            self.progress.setRange(0, 0)  # Indeterminate
        else:
            self.progress.setRange(0, maximum)
            self.progress.setValue(value)
    
    def hide_progress(self):
        """Hide progress bar"""
        self.progress.setVisible(False)


class DeckListItem(QListWidgetItem):
    """List item representing a deck with metadata"""
    
    def __init__(self, deck_id: str, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.deck_id = deck_id
        self.deck_title = title
        self.deck_subtitle = subtitle
        
        display_text = title
        if subtitle:
            display_text = f"{title}\n{subtitle}"
        self.setText(display_text)
    
    def get_deck_id(self) -> str:
        return self.deck_id


class DeckListWidget(QListWidget):
    """Enhanced deck list with styling"""
    
    deck_selected = pyqtSignal(str, str)  # deck_id, deck_title
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.itemClicked.connect(self._on_item_clicked)
    
    def _on_item_clicked(self, item):
        if isinstance(item, DeckListItem):
            self.deck_selected.emit(item.deck_id, item.deck_title)
    
    def add_deck(self, deck_id: str, title: str, subtitle: str = ""):
        """Add a deck to the list"""
        item = DeckListItem(deck_id, title, subtitle)
        self.addItem(item)
        return item
    
    def get_selected_deck(self):
        """Get the currently selected deck's ID and title"""
        item = self.currentItem()
        if isinstance(item, DeckListItem):
            return item.deck_id, item.deck_title
        return None, None
    
    def clear_decks(self):
        """Clear all decks from the list"""
        self.clear()


class ActionButton(QPushButton):
    """Styled action button"""
    
    def __init__(self, text: str, style_type: str = "secondary", parent=None):
        super().__init__(text, parent)
        self.style_type = style_type
        self.apply_style()
    
    def apply_style(self):
        self.setStyleSheet(get_button_style(self.style_type))
    
    def set_loading(self, loading: bool, loading_text: str = "Loading..."):
        """Toggle loading state"""
        self.setEnabled(not loading)
        if loading:
            self._original_text = self.text()
            self.setText(loading_text)
        else:
            if hasattr(self, '_original_text'):
                self.setText(self._original_text)


class EmptyStateWidget(QWidget):
    """Widget shown when a list is empty"""
    
    def __init__(self, message: str, action_text: str = "", parent=None):
        super().__init__(parent)
        self.action_button = None
        self.setup_ui(message, action_text)
    
    def setup_ui(self, message: str, action_text: str):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px; padding: 20px;")
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        if action_text:
            self.action_button = ActionButton(action_text, "primary")
            layout.addWidget(self.action_button, alignment=Qt.AlignmentFlag.AlignCenter)


class CardWidget(QFrame):
    """Card-style container widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            CardWidget {{
                background-color: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)
    
    def add_title(self, text: str):
        """Add a title to the card"""
        title = QLabel(text)
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 16px; font-weight: bold;")
        self.main_layout.insertWidget(0, title)
    
    def add_content(self, widget: QWidget):
        """Add content widget to the card"""
        self.main_layout.addWidget(widget)