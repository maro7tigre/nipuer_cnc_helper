from PySide6.QtWidgets import (QDialog, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                             QLabel, QScrollArea, QGridLayout, QFrame, QLineEdit,
                             QTextEdit, QDialogButtonBox, QFileDialog, QMessageBox,
                             QSplitter, QSizePolicy)
from PySide6.QtCore import Signal, Qt, QSize, QRegularExpression
from PySide6.QtGui import QPixmap, QPainter, QColor, QRegularExpressionValidator, QDoubleValidator
import re
import json
import os
from datetime import datetime

# Import the new G-code editor
from gcode_ide import GCodeEditor


class ClickableImageLabel(QLabel):
    """Clickable image label with Python-based styling"""
    clicked = Signal()
    
    def __init__(self, size=(100, 100)):
        super().__init__()
        self.setFixedSize(*size)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.PointingHandCursor)
        self.setScaledContents(False)
        self.apply_default_style()
        
    def apply_default_style(self):
        """Apply default styling"""
        self.setStyleSheet("""
            ClickableImageLabel {
                background-color: #44475c;
                border: 2px solid #6f779a;
                border-radius: 4px;
            }
            ClickableImageLabel:hover {
                background-color: #3a3d4d;
                border: 2px solid #BB86FC;
            }
        """)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()





class TypeEditor(QDialog):
    """Type editor dialog with improved styling and maximize/minimize buttons"""
    
    def __init__(self, profile_type, type_data=None, parent=None):
        super().__init__(parent)
        self.profile_type = profile_type
        self.type_data = type_data or {}
        self.image_path = type_data.get("image") if type_data else None
        self.preview_path = type_data.get("preview") if type_data else None
        
        # Machine variables validation dictionary (from backend)
        self.machine_vars = {
            "machine_x_offset": True,
            "machine_y_offset": True,
            "machine_z_offset": True,
            "spindle_speed": True,
            "feed_rate": True
        }
        
        self.setWindowTitle(f"{'Edit' if type_data else 'New'} {profile_type.capitalize()} Type")
        self.setModal(True)
        self.resize(1000, 700)
        
        # Enable maximize/minimize buttons
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | 
                           Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | 
                           Qt.WindowCloseButtonHint)
        
        # Apply dialog styling
        self.setStyleSheet("""
            TypeEditor {
                background-color: #282a36;
                color: #ffffff;
            }
            TypeEditor QLabel {
                color: #ffffff;
                background-color: transparent;
            }
            TypeEditor QLineEdit {
                background-color: #1d1f28;
                color: #ffffff;
                border: 1px solid #6f779a;
                border-radius: 4px;
                padding: 4px;
            }
            TypeEditor QLineEdit:focus {
                border: 1px solid #BB86FC;
            }
            TypeEditor QPushButton {
                background-color: #1d1f28;
                color: #BB86FC;
                border: 2px solid #BB86FC;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
            }
            TypeEditor QPushButton:hover {
                background-color: #000000;
                color: #9965DA;
                border: 2px solid #9965DA;
            }
            TypeEditor QPushButton:pressed {
                background-color: #BB86FC;
                color: #1d1f28;
            }
        """)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        
        # Main content split
        content_split = QSplitter(Qt.Horizontal)
        layout.addWidget(content_split, 1)
        
        # Left side - Images and name
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Type name
        left_layout.addWidget(QLabel("Type Name:"))
        self.name_edit = QLineEdit()
        left_layout.addWidget(self.name_edit)
        
        left_layout.addSpacing(20)
        
        # Type image
        left_layout.addWidget(QLabel("Type Image:"))
        self.image_label = ClickableImageLabel((150, 150))
        self.image_label.clicked.connect(self.select_image)
        self.set_placeholder_image()
        left_layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
        
        left_layout.addSpacing(20)
        
        # Preview image
        left_layout.addWidget(QLabel("Preview Image:"))
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
        
        gcode_header.addWidget(QLabel("G-Code Template:"))
        gcode_header.addStretch()
        
        upload_btn = QPushButton("Upload")
        upload_btn.clicked.connect(self.upload_gcode)
        gcode_header.addWidget(upload_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_gcode)
        gcode_header.addWidget(save_btn)
        
        # Use the new G-code editor
        self.gcode_edit = GCodeEditor(self)
        self.gcode_edit.setPlaceholderText("Enter G-code with variables like {L1}, {custom_var:default}, {$machine_var}, etc.")
        
        # Connect to variable changes
        self.gcode_edit.variables_changed.connect(self.on_variables_changed)
        
        middle_layout.addWidget(self.gcode_edit)
        
        content_split.addWidget(middle_widget)
        
        content_split.setSizes([300, 700])
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
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
        pixmap = QPixmap(150, 150)
        pixmap.fill(QColor("#44475c"))
        painter = QPainter(pixmap)
        painter.setPen(QColor("#bdbdc0"))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "Type Image")
        painter.end()
        self.image_label.setPixmap(pixmap)
    
    def set_placeholder_preview(self):
        """Set placeholder for preview image"""
        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("#44475c"))
        painter = QPainter(pixmap)
        painter.setPen(QColor("#bdbdc0"))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "Preview")
        painter.end()
        self.preview_label.setPixmap(pixmap)