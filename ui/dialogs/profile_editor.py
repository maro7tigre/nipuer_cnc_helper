"""
Profile Editor Dialog

Simplified profile editor that works with centralized main_window data management.
"""

from PySide6.QtWidgets import QDialog, QWidget, QHBoxLayout, QVBoxLayout, QDialogButtonBox, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
import os

from ..widgets.themed_widgets import ThemedLabel, ThemedLineEdit, ThemedSplitter
from ..widgets.simple_widgets import ClickableImageLabel, PlaceholderPixmap
from ..profile.widgets.type_selector import TypeSelector
from ..widgets.variable_editor import VariableEditor
from ..widgets.custom_editor import CustomEditor


class ProfileEditor(QDialog):
    """Simplified profile editor that integrates with main_window data management"""
    
    def __init__(self, profile_type, profile_data=None, parent=None):
        super().__init__(parent)
        self.profile_type = profile_type  # "hinge" or "lock"
        self.profile_data = profile_data or {}
        self.main_window = parent.main_window if hasattr(parent, 'main_window') else parent
        self.current_type = None
        self.profile_image_path = profile_data.get("image") if profile_data else None
        
        self.setWindowTitle(f"{'Edit' if profile_data else 'New'} {profile_type.capitalize()} Profile")
        self.setModal(True)
        self.resize(1100, 700)
        
        # Enable maximize/minimize buttons
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | 
                           Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | 
                           Qt.WindowCloseButtonHint)
        
        self.apply_styling()
        self.setup_ui()
        self.load_data()
    
    def apply_styling(self):
        """Apply dialog styling"""
        self.setStyleSheet("""
            ProfileEditor {
                background-color: #282a36;
                color: #ffffff;
            }
        """)
    
    def setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        
        # Type selector - gets data from main_window
        dollar_vars = self.main_window.get_dollar_variable()
        self.type_selector = TypeSelector(self.profile_type, dollar_vars)
        self.type_selector.type_selected.connect(self.on_type_selected)
        self.type_selector.types_modified.connect(self.on_types_modified)
        layout.addWidget(self.type_selector)
        
        # Main content area with resizable splitter
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        layout.addWidget(content_widget, 1)
        
        # Splitter - resizable by user
        splitter = ThemedSplitter(Qt.Horizontal)
        content_layout.addWidget(splitter)
        
        # Left - Variables (resizable)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Variables editor
        self.variable_editor = VariableEditor()
        self.variable_editor.setVisible(False)
        left_layout.addWidget(self.variable_editor)
        
        # Custom editor
        self.custom_editor = CustomEditor()
        self.custom_editor.setVisible(False)
        left_layout.addWidget(self.custom_editor)
        
        left_layout.addStretch()
        splitter.addWidget(left_widget)
        
        # Middle - Type preview
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        
        middle_layout.addWidget(ThemedLabel("Type Preview:"))
        self.preview_image_label = ClickableImageLabel((200, 200))
        self.preview_image_label.setText("Select a type to see preview")
        self.preview_image_label.setStyleSheet("""
            QLabel {
                background-color: #44475c;
                border: 2px solid #6f779a;
                border-radius: 4px;
                color: #bdbdc0;
            }
        """)
        middle_layout.addWidget(self.preview_image_label, 1)
        
        splitter.addWidget(middle_widget)
        
        # Right - Profile info
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Profile name
        right_layout.addWidget(ThemedLabel("Profile Name:"))
        self.profile_name_edit = ThemedLineEdit()
        right_layout.addWidget(self.profile_name_edit)
        
        right_layout.addSpacing(20)
        
        # Profile image
        right_layout.addWidget(ThemedLabel("Profile Image:"))
        self.profile_image_label = ClickableImageLabel((150, 150))
        self.profile_image_label.clicked.connect(self.select_profile_image)
        self.set_profile_placeholder()
        right_layout.addWidget(self.profile_image_label, alignment=Qt.AlignCenter)
        
        right_layout.addStretch()
        splitter.addWidget(right_widget)

        # Set initial splitter sizes
        splitter.setSizes([300, 400, 300])
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.setStyleSheet("""
            QDialogButtonBox QPushButton {
                background-color: #1d1f28;
                color: #23c87b;
                border: 2px solid #23c87b;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
            }
            QDialogButtonBox QPushButton:hover {
                background-color: #000000;
                color: #1a945b;
                border: 2px solid #1a945b;
            }
            QDialogButtonBox QPushButton:pressed {
                background-color: #23c87b;
                color: #1d1f28;
            }
        """)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def accept(self):
        """Override accept to validate before closing"""
        # Validate profile name
        name = self.profile_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", 
                              "Please enter a profile name before saving.")
            self.profile_name_edit.setFocus()
            return
        
        # Validate type selection
        if not self.current_type:
            QMessageBox.warning(self, "No Type Selected", 
                              "Please select a type before saving.")
            return
        
        # All validation passed, close dialog
        super().accept()
    
    def load_data(self):
        """Load existing profile data and types from main_window"""
        # Load types from main_window
        if self.profile_type == "hinge":
            types_data = self.main_window.hinges_types
        else:
            types_data = self.main_window.locks_types
        
        self.type_selector.load_types(types_data)
        
        # Load profile data
        if self.profile_data:
            self.profile_name_edit.setText(self.profile_data.get("name", ""))
            
            if self.profile_image_path:
                pixmap = QPixmap(self.profile_image_path)
                if not pixmap.isNull():
                    self.profile_image_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio))
            
            # Select type if profile has one
            if self.profile_data.get("type"):
                self.type_selector.on_type_clicked(self.profile_data["type"])
    
    def on_types_modified(self):
        """Handle when types are modified in the selector"""
        # Update main_window with new types
        types_data = self.type_selector.get_types_data()
        for type_name, type_data in types_data.items():
            if self.profile_type == "hinge":
                self.main_window.update_hinge_type(type_name, type_data)
            else:
                self.main_window.update_lock_type(type_name, type_data)
    
    def get_profile_data(self):
        """Get profile data from dialog"""
        data = {
            "name": self.profile_name_edit.text(),
            "type": self.current_type["name"] if self.current_type else None,
            "l_variables": self.variable_editor.get_variable_values(),
            "custom_variables": self.custom_editor.get_custom_values(),
            "image": self.profile_image_path
        }
        
        return data
    
    def on_type_selected(self, type_data):
        """Handle type selection"""
        self.current_type = type_data
        
        # Update variable editors using gcode from type
        gcode = type_data.get("gcode", "")
        self.variable_editor.update_variables(gcode)
        self.custom_editor.update_customs(gcode)
        
        # Load saved variable values if editing
        if self.profile_data.get("type") == type_data["name"]:
            if self.profile_data.get("l_variables"):
                self.variable_editor.set_variable_values(self.profile_data["l_variables"])
            if self.profile_data.get("custom_variables"):
                self.custom_editor.set_custom_values(self.profile_data["custom_variables"])
        
        # Update preview
        if type_data.get("preview"):
            pixmap = QPixmap(type_data["preview"])
            if not pixmap.isNull():
                self.preview_image_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
            else:
                self.preview_image_label.setText("No preview available")
        else:
            self.preview_image_label.setText("No preview available")
    
    def select_profile_image(self):
        """Select profile image"""
        from PySide6.QtWidgets import QFileDialog
        
        default_dir = os.path.join("profiles", "images")
        os.makedirs(default_dir, exist_ok=True)
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Profile Image", default_dir, "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if filename:
            self.profile_image_path = filename
            pixmap = QPixmap(filename)
            self.profile_image_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio))
    
    def set_profile_placeholder(self):
        """Set placeholder for profile image"""
        pixmap = PlaceholderPixmap.create_profile_placeholder((150, 150))
        self.profile_image_label.setPixmap(pixmap)