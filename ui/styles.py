"""
Shared UI Styles for AnkiPH Addon
Centralized dark theme and color constants
Version: 4.0.0
"""

# Color palette
COLORS = {
    # Backgrounds
    "bg_primary": "#1e1e1e",
    "bg_secondary": "#2d2d2d",
    "bg_tertiary": "#3d3d3d",
    "bg_hover": "#404040",
    "bg_selected": "#4a90d9",
    
    # Text
    "text_primary": "#ffffff",
    "text_secondary": "#cccccc",
    "text_muted": "#888888",
    "text_link": "#6bb3f8",
    
    # Borders
    "border": "#555555",
    "border_focus": "#4a90d9",
    
    # Status colors
    "success": "#4CAF50",
    "warning": "#ff9800",
    "error": "#f44336",
    "info": "#2196F3",
    
    # Buttons
    "btn_primary": "#4a90d9",
    "btn_primary_hover": "#5a9fe8",
    "btn_secondary": "#555555",
    "btn_secondary_hover": "#666666",
}

# Base dark theme stylesheet
DARK_THEME = f"""
    QDialog, QWidget {{
        background-color: {COLORS["bg_secondary"]};
        color: {COLORS["text_primary"]};
    }}
    
    QLabel {{
        color: {COLORS["text_primary"]};
        font-size: 13px;
    }}
    
    QLabel[class="title"] {{
        font-size: 16px;
        font-weight: bold;
        padding: 10px;
    }}
    
    QLabel[class="subtitle"] {{
        font-size: 14px;
        font-weight: bold;
    }}
    
    QLabel[class="muted"] {{
        color: {COLORS["text_muted"]};
        font-size: 12px;
    }}
    
    QLineEdit, QTextEdit {{
        background-color: {COLORS["bg_primary"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        padding: 8px 12px;
        color: {COLORS["text_primary"]};
        font-size: 13px;
    }}
    
    QLineEdit:focus, QTextEdit:focus {{
        border-color: {COLORS["border_focus"]};
    }}
    
    QLineEdit::placeholder {{
        color: {COLORS["text_muted"]};
    }}
    
    QPushButton {{
        background-color: {COLORS["btn_secondary"]};
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        color: {COLORS["text_primary"]};
        font-size: 13px;
    }}
    
    QPushButton:hover {{
        background-color: {COLORS["btn_secondary_hover"]};
    }}
    
    QPushButton:pressed {{
        background-color: {COLORS["bg_tertiary"]};
    }}
    
    QPushButton:disabled {{
        background-color: {COLORS["bg_tertiary"]};
        color: {COLORS["text_muted"]};
    }}
    
    QPushButton[class="primary"] {{
        background-color: {COLORS["btn_primary"]};
        font-weight: bold;
    }}
    
    QPushButton[class="primary"]:hover {{
        background-color: {COLORS["btn_primary_hover"]};
    }}
    
    QPushButton[class="success"] {{
        background-color: {COLORS["success"]};
        font-weight: bold;
    }}
    
    QPushButton[class="warning"] {{
        background-color: {COLORS["warning"]};
        font-weight: bold;
    }}
    
    QPushButton[class="danger"] {{
        background-color: {COLORS["error"]};
        font-weight: bold;
    }}
    
    QListWidget {{
        background-color: {COLORS["bg_primary"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        padding: 4px;
    }}
    
    QListWidget::item {{
        padding: 8px;
        border-radius: 4px;
        margin: 2px;
    }}
    
    QListWidget::item:hover {{
        background-color: {COLORS["bg_hover"]};
    }}
    
    QListWidget::item:selected {{
        background-color: {COLORS["bg_selected"]};
    }}
    
    QTabWidget::pane {{
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        background-color: {COLORS["bg_secondary"]};
    }}
    
    QTabBar::tab {{
        background-color: {COLORS["bg_tertiary"]};
        color: {COLORS["text_secondary"]};
        padding: 10px 20px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    
    QTabBar::tab:selected {{
        background-color: {COLORS["bg_selected"]};
        color: {COLORS["text_primary"]};
    }}
    
    QTabBar::tab:hover:!selected {{
        background-color: {COLORS["bg_hover"]};
    }}
    
    QGroupBox {{
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        margin-top: 12px;
        padding-top: 8px;
        font-weight: bold;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }}
    
    QCheckBox {{
        color: {COLORS["text_primary"]};
        spacing: 8px;
    }}
    
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {COLORS["border"]};
        border-radius: 3px;
        background-color: {COLORS["bg_primary"]};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {COLORS["btn_primary"]};
        border-color: {COLORS["btn_primary"]};
    }}
    
    QProgressBar {{
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        text-align: center;
        background-color: {COLORS["bg_primary"]};
    }}
    
    QProgressBar::chunk {{
        background-color: {COLORS["btn_primary"]};
        border-radius: 3px;
    }}
    
    QComboBox {{
        background-color: {COLORS["bg_primary"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        padding: 6px 12px;
        color: {COLORS["text_primary"]};
    }}
    
    QComboBox:hover {{
        border-color: {COLORS["border_focus"]};
    }}
    
    QComboBox::drop-down {{
        border: none;
        padding-right: 10px;
    }}
    
    QScrollBar:vertical {{
        background-color: {COLORS["bg_primary"]};
        width: 12px;
        border-radius: 6px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {COLORS["border"]};
        border-radius: 6px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS["text_muted"]};
    }}
    
    QSplitter::handle {{
        background-color: {COLORS["border"]};
    }}
"""


def apply_dark_theme(widget):
    """Apply the dark theme to a widget"""
    widget.setStyleSheet(DARK_THEME)


def get_button_style(style_type: str = "secondary") -> str:
    """Get inline style for a button type"""
    if style_type == "primary":
        return f"background-color: {COLORS['btn_primary']}; font-weight: bold; padding: 10px 20px;"
    elif style_type == "success":
        return f"background-color: {COLORS['success']}; font-weight: bold; padding: 10px 20px; color: white;"
    elif style_type == "warning":
        return f"background-color: {COLORS['warning']}; font-weight: bold; padding: 10px 20px; color: white;"
    elif style_type == "danger":
        return f"background-color: {COLORS['error']}; font-weight: bold; padding: 10px 20px; color: white;"
    else:
        return f"background-color: {COLORS['btn_secondary']}; padding: 8px 16px;"
