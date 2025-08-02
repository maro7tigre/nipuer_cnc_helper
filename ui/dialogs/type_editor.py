"""
Type Editor Dialog

Simplified type editor that works with centralized main_window data management.
"""

from PySide6.QtWidgets import QDialog, QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, QMessageBox, QDialogButtonBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
import os

from ..widgets.themed_widgets import ThemedLabel, ThemedLineEdit, ThemedSplitter, PurpleButton
from ..widgets.simple_widgets import ClickableImageLabel, PlaceholderPixmap
from ..gcode_ide import GCodeEditor


class TypeEditor(QDialog):
    """Simplified type editor that integrates with main_window data management"""
    
    def __init__(self, profile_type, type_data=None, parent=None):
        super().__init__(parent)
        self.profile_type = profile_type
        self.type_data = type_data or {}
        self.main_window = parent.main_window if hasattr(parent, 'main_window') else parent
        self.image_path = type_data.get("image") if type_data else None
        self.preview_path = type_data.get("preview") if type_data else None
        
        self.setWindowTitle(f"{'Edit' if type_data else 'New'} {profile_type.capitalize()} Type")
        self.setModal(True)
        self.resize(1000, 700)
        
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
            TypeEditor {
                background-color: #282a36;
                color: #ffffff;
            }
        """)
    
    def setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        
        # Main content split
        content_split = ThemedSplitter(Qt.Horizontal)
        layout.addWidget(content_split, 1)
        
        # Left side - Images and name
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Type name
        left_layout.addWidget(ThemedLabel("Type Name:"))
        self.name_edit = ThemedLineEdit()
        left_layout.addWidget(self.name_edit)
        
        left_layout.addSpacing(20)
        
        # Type image
        left_layout.addWidget(ThemedLabel("Type Image:"))
        self.image_label = ClickableImageLabel((150, 150))
        self.image_label.clicked.connect(self.select_image)
        self.set_placeholder_image()
        left_layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
        
        left_layout.addSpacing(20)
        
        # Preview image
        left_layout.addWidget(ThemedLabel("Preview Image:"))
        self.preview_label = ClickableImageLabel((200, 200))
        self.preview_label.clicked.connect(self.select_preview)
        self.set_placeholder_preview()
        left_layout.addWidget(self.preview_label, alignment=Qt.AlignCenter)
        
        left_layout.addStretch()
        content_split.addWidget(left_widget)
        
        # Middle - GCode editor
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        
        # GCode header
        gcode_header = QHBoxLayout()
        middle_layout.addLayout(gcode_header)
        
        gcode_header.addWidget(ThemedLabel("G-Code Template:"))
        gcode_header.addStretch()
        
        upload_btn = PurpleButton("Upload")
        upload_btn.clicked.connect(self.upload_gcode)
        gcode_header.addWidget(upload_btn)
        
        save_btn = PurpleButton("Save")
        save_btn.clicked.connect(self.save_gcode)
        gcode_header.addWidget(save_btn)
        
        # G-code editor with $ variables support from main_window
        self.gcode_edit = GCodeEditor(self)
        dollar_vars = self.main_window.get_dollar_variable()
        self.gcode_edit.set_dollar_variables_info(dollar_vars)
        self.gcode_edit.setPlaceholderText(
            "Enter G-code with variables:\n"
            "L variables: {L1}, {L2:default}\n"
            "Custom variables: {custom_var:default}\n"
            "$ variables: {$frame_height}, {$lock_position}, etc.\n\n"
            "Click the ? button to see all available $ variables."
        )
        
        # Connect to variable changes
        self.gcode_edit.variables_changed.connect(self.on_variables_changed)
        
        middle_layout.addWidget(self.gcode_edit)
        
        content_split.addWidget(middle_widget)
        
        content_split.setSizes([300, 700])
        
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
        # Validate type name
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", 
                              "Please enter a type name before saving.")
            self.name_edit.setFocus()
            return
        
        # All validation passed, close dialog
        super().accept()
    
    def on_variables_changed(self, variables):
        """Handle variables detected in G-code"""
        if variables:
            var_names = [f"{{{name}{':' + default if default else ''}}}" for name, default in variables]
    
    def load_data(self):
        """Load existing type data"""
        if self.type_data:
            self.name_edit.setText(self.type_data.get("name", ""))
            self.gcode_edit.setPlainText(self.type_data.get("gcode", ""))
            
            if self.image_path:
                pixmap = QPixmap(self.image_path)
                if not pixmap.isNull():
                    self.image_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio))
            
            if self.preview_path:
                pixmap = QPixmap(self.preview_path)
                if not pixmap.isNull():
                    self.preview_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
            
            # Load existing data if editing
            if self.type_data.get("gcode"):
                # Trigger variable detection
                self.on_variables_changed(self.gcode_edit.getVariables())
    
    def get_type_data(self):
        """Get type data from dialog"""
        data = {
            "name": self.name_edit.text(),
            "gcode": self.gcode_edit.toPlainText(),
            "image": self.image_path,
            "preview": self.preview_path,
            "variables": self.gcode_edit.getVariables()
        }
        
        return data
    
    def select_image(self):
        """Select type image"""
        default_dir = os.path.join("profiles", "images")
        os.makedirs(default_dir, exist_ok=True)
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Image", default_dir, "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if filename:
            self.image_path = filename
            pixmap = QPixmap(filename)
            self.image_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio))
    
    def select_preview(self):
        """Select preview image"""
        default_dir = os.path.join("profiles", "images")
        os.makedirs(default_dir, exist_ok=True)
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Preview Image", default_dir, "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if filename:
            self.preview_path = filename
            pixmap = QPixmap(filename)
            self.preview_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
    
    def upload_gcode(self):
        """Upload G-code from file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Upload G-Code", "", "G-Code Files (*.gcode *.nc *.txt)"
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    self.gcode_edit.setPlainText(f.read())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
    
    def save_gcode(self):
        """Save G-code to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save G-Code", "", "G-Code Files (*.gcode)"
        )
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.gcode_edit.toPlainText())
                QMessageBox.information(self, "Success", "G-code saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")
    
    def set_placeholder_image(self):
        """Set placeholder for type image"""
        pixmap = PlaceholderPixmap.create((150, 150), "Type Image")
        self.image_label.setPixmap(pixmap)
    
    def set_placeholder_preview(self):
        """Set placeholder for preview image"""
        pixmap = PlaceholderPixmap.create((200, 200), "Preview")
        self.preview_label.setPixmap(pixmap)