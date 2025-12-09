"""
Login dialog UI for the Nottorney addon
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox
)
from ..api_client import api, NottorneyAPIError


class LoginDialog(QDialog):
    """Dialog for user login"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nottorney Login")
        self.setMinimumWidth(400)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI elements"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<h2>Login to Nottorney</h2>")
        layout.addWidget(title)
        
        # Email field
        email_label = QLabel("Email:")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        layout.addWidget(email_label)
        layout.addWidget(self.email_input)
        
        # Password field
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(password_label)
        layout.addWidget(self.password_input)
        
        # Error message label (hidden by default)
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red;")
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)
        self.login_button.setDefault(True)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.login_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect Enter key to login
        self.email_input.returnPressed.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)
    
    def handle_login(self):
        """Handle the login button click"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        # Validate inputs
        if not email:
            self.show_error("Please enter your email")
            return
        
        if not password:
            self.show_error("Please enter your password")
            return
        
        # Disable button during login
        self.login_button.setEnabled(False)
        self.login_button.setText("Logging in...")
        self.hide_error()
        
        try:
            # Call the API
            result = api.login(email, password)
            
            if result.get('success'):
                # Login successful
                QMessageBox.information(
                    self,
                    "Success",
                    f"Welcome back, {result.get('user', {}).get('email', 'User')}!"
                )
                self.accept()
            else:
                self.show_error("Login failed. Please check your credentials.")
        
        except NottorneyAPIError as e:
            self.show_error(str(e))
        
        except Exception as e:
            self.show_error(f"Unexpected error: {str(e)}")
        
        finally:
            # Re-enable button
            self.login_button.setEnabled(True)
            self.login_button.setText("Login")
    
    def show_error(self, message):
        """Show an error message"""
        self.error_label.setText(message)
        self.error_label.show()
    
    def hide_error(self):
        """Hide the error message"""
        self.error_label.hide()