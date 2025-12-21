"""
Login Dialog for AnkiPH Addon
Modern Premium Login UI with centered card design
Version: 5.0.0 - Complete Redesign
"""

import webbrowser
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, Qt, QFrame, QGraphicsDropShadowEffect, QColor,
    QWidget
)
from aqt import mw

from ..api_client import api, set_access_token, AnkiPHAPIError
from ..config import config
from ..constants import REGISTER_URL, FORGOT_PASSWORD_URL
from .styles import COLORS
from .components import ClickableLabel


class LoginDialog(QDialog):
    """Modern Premium Login Dialog for AnkiPH"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sign in to AnkiPH")
        self.setFixedSize(420, 480)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the modern login UI"""
        # Main layout with transparent background
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Card container
        self.card = QFrame()
        self.card.setObjectName("loginCard")
        self.apply_card_style()
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(40, 35, 40, 35)
        card_layout.setSpacing(0)
        
        # Close button (top right)
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.reject)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_layout.addWidget(close_btn)
        card_layout.addLayout(close_layout)
        
        card_layout.addSpacing(5)
        
        # Branding Header
        brand_layout = QVBoxLayout()
        brand_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_layout.setSpacing(8)
        
        # App icon/logo placeholder (using emoji for now)
        logo_label = QLabel("📚")
        logo_label.setObjectName("logoLabel")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_layout.addWidget(logo_label)
        
        # App title
        title_label = QLabel("AnkiPH")
        title_label.setObjectName("brandTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Sign in to your account")
        subtitle_label.setObjectName("brandSubtitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_layout.addWidget(subtitle_label)
        
        card_layout.addLayout(brand_layout)
        card_layout.addSpacing(30)
        
        # Email/Username Input (Stacked)
        email_container = QVBoxLayout()
        email_container.setSpacing(8)
        
        email_label = QLabel("Username or Email")
        email_label.setObjectName("inputLabel")
        email_container.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setObjectName("modernInput")
        self.email_input.setPlaceholderText("Enter your username or email")
        self.email_input.setMinimumHeight(44)
        email_container.addWidget(self.email_input)
        
        card_layout.addLayout(email_container)
        card_layout.addSpacing(20)
        
        # Password Input (Stacked with eye toggle)
        password_container = QVBoxLayout()
        password_container.setSpacing(8)
        
        password_label = QLabel("Password")
        password_label.setObjectName("inputLabel")
        password_container.addWidget(password_label)
        
        # Password field with toggle button
        password_row = QHBoxLayout()
        password_row.setSpacing(0)
        
        self.password_input = QLineEdit()
        self.password_input.setObjectName("modernInput")
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(44)
        self.password_input.returnPressed.connect(self.login)
        password_row.addWidget(self.password_input)
        
        # Eye toggle button (overlaid)
        self.eye_btn = QPushButton("👁")
        self.eye_btn.setObjectName("eyeBtn")
        self.eye_btn.setFixedSize(44, 44)
        self.eye_btn.setCheckable(True)
        self.eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.eye_btn.clicked.connect(self.toggle_password_visibility)
        password_row.addWidget(self.eye_btn)
        
        password_container.addLayout(password_row)
        card_layout.addLayout(password_container)
        
        card_layout.addSpacing(28)
        
        # Sign In Button
        self.signin_btn = QPushButton("Sign In")
        self.signin_btn.setObjectName("signinBtn")
        self.signin_btn.setMinimumHeight(48)
        self.signin_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.signin_btn.clicked.connect(self.login)
        card_layout.addWidget(self.signin_btn)
        
        card_layout.addSpacing(24)
        
        # Divider line
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setObjectName("divider")
        card_layout.addWidget(divider)
        
        card_layout.addSpacing(20)
        
        # Register link
        register_layout = QHBoxLayout()
        register_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        register_text = QLabel("Don't have an account?")
        register_text.setObjectName("linkText")
        register_layout.addWidget(register_text)
        
        register_link = ClickableLabel("Register now")
        register_link.setObjectName("linkLabel")
        register_link.clicked.connect(lambda: webbrowser.open(REGISTER_URL))
        register_layout.addWidget(register_link)
        
        card_layout.addLayout(register_layout)
        
        card_layout.addSpacing(8)
        
        # Forgot password link
        forgot_layout = QHBoxLayout()
        forgot_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        forgot_link = ClickableLabel("Forgot password?")
        forgot_link.setObjectName("linkLabel")
        forgot_link.clicked.connect(lambda: webbrowser.open(FORGOT_PASSWORD_URL))
        forgot_layout.addWidget(forgot_link)
        
        card_layout.addLayout(forgot_layout)
        
        card_layout.addStretch()
        
        main_layout.addWidget(self.card)
        
        # Add drop shadow to card
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 10)
        self.card.setGraphicsEffect(shadow)
    
    def apply_card_style(self):
        """Apply modern card styling"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: transparent;
            }}
            
            QFrame#loginCard {{
                background-color: {COLORS['bg_secondary']};
                border-radius: 16px;
                border: 1px solid {COLORS['border']};
            }}
            
            QPushButton#closeBtn {{
                background-color: transparent;
                color: {COLORS['text_muted']};
                border: none;
                border-radius: 14px;
                font-size: 16px;
            }}
            
            QPushButton#closeBtn:hover {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
            }}
            
            QLabel#logoLabel {{
                font-size: 48px;
                padding: 10px;
            }}
            
            QLabel#brandTitle {{
                font-size: 26px;
                font-weight: bold;
                color: {COLORS['text_primary']};
                letter-spacing: 1px;
            }}
            
            QLabel#brandSubtitle {{
                font-size: 13px;
                color: {COLORS['text_muted']};
            }}
            
            QLabel#inputLabel {{
                font-size: 13px;
                font-weight: 600;
                color: {COLORS['text_secondary']};
            }}
            
            QLineEdit#modernInput {{
                background-color: {COLORS['bg_primary']};
                border: 2px solid {COLORS['border']};
                border-radius: 10px;
                padding: 10px 16px;
                font-size: 14px;
                color: {COLORS['text_primary']};
            }}
            
            QLineEdit#modernInput:focus {{
                border-color: {COLORS['btn_primary']};
                background-color: #252525;
            }}
            
            QLineEdit#modernInput::placeholder {{
                color: {COLORS['text_muted']};
            }}
            
            QPushButton#eyeBtn {{
                background-color: {COLORS['bg_primary']};
                border: 2px solid {COLORS['border']};
                border-left: none;
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
                border-top-left-radius: 0;
                border-bottom-left-radius: 0;
                font-size: 16px;
                color: {COLORS['text_muted']};
            }}
            
            QPushButton#eyeBtn:hover {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
            }}
            
            QPushButton#eyeBtn:checked {{
                color: {COLORS['btn_primary']};
            }}
            
            QPushButton#signinBtn {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['btn_primary']}, stop:1 #5fa8f5);
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
                color: white;
                padding: 12px;
            }}
            
            QPushButton#signinBtn:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a9fe8, stop:1 #6fb3ff);
            }}
            
            QPushButton#signinBtn:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3a80c9, stop:1 #4a90d9);
            }}
            
            QPushButton#signinBtn:disabled {{
                background: {COLORS['bg_tertiary']};
                color: {COLORS['text_muted']};
            }}
            
            QFrame#divider {{
                background-color: {COLORS['border']};
                max-height: 1px;
            }}
            
            QLabel#linkText {{
                font-size: 13px;
                color: {COLORS['text_muted']};
            }}
            
            QLabel#linkLabel {{
                font-size: 13px;
                color: {COLORS['text_link']};
                font-weight: 600;
                padding-left: 4px;
            }}
            
            QLabel#linkLabel:hover {{
                color: #8cc4ff;
                text-decoration: underline;
            }}
        """)
    
    def toggle_password_visibility(self):
        """Toggle password visibility with eye icon"""
        if self.eye_btn.isChecked():
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.eye_btn.setText("👁‍🗨")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.eye_btn.setText("👁")
    
    def login(self):
        """Perform login"""
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        
        if not email or not password:
            from aqt.qt import QMessageBox
            QMessageBox.warning(self, "Missing Information", "Please enter both email and password.")
            return
        
        try:
            # Disable inputs during login
            self.email_input.setEnabled(False)
            self.password_input.setEnabled(False)
            self.signin_btn.setEnabled(False)
            self.signin_btn.setText("Signing in...")
            
            # Force UI update
            from aqt.qt import QApplication
            QApplication.processEvents()
            
            result = api.login(email, password)
            
            if result.get('success'):
                access_token = result.get('access_token')
                refresh_token = result.get('refresh_token')
                expires_at = result.get('expires_at')
                user_data = result.get('user', {})
                
                if access_token:
                    config.save_tokens(access_token, refresh_token, expires_at)
                    config.save_user_data(user_data)
                    set_access_token(access_token)
                    
                    from aqt.qt import QMessageBox
                    QMessageBox.information(self, "Success", "Login successful!")
                    self.accept()
                else:
                    raise Exception("No access token received from server")
            else:
                from aqt.qt import QMessageBox
                QMessageBox.warning(self, "Login Failed", result.get('message', 'Login failed. Please check your credentials.'))
        
        except AnkiPHAPIError as e:
            from aqt.qt import QMessageBox
            QMessageBox.critical(self, "Error", str(e))
        except Exception as e:
            from aqt.qt import QMessageBox
            QMessageBox.critical(self, "Error", f"Login failed: {e}")
        finally:
            self.email_input.setEnabled(True)
            self.password_input.setEnabled(True)
            self.signin_btn.setEnabled(True)
            self.signin_btn.setText("Sign In")
    
    def get_login_result(self):
        """Return whether login was successful"""
        return self.result() == QDialog.DialogCode.Accepted
    
    # Allow dragging the frameless window
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()


def show_login_dialog(parent=None) -> bool:
    """
    Show the login dialog and return True if login was successful.
    
    Args:
        parent: Parent widget
    
    Returns:
        True if user logged in successfully, False otherwise
    """
    dialog = LoginDialog(parent or mw)
    result = dialog.exec()
    return result == QDialog.DialogCode.Accepted
