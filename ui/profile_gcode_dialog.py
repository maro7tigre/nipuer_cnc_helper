from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QDialogButtonBox, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from gcode_ide import GCodeEditor


class ProfileGCodeDialog(QDialog):
    """Enhanced G-code editor dialog for profiles with $ variables support"""
    
    def __init__(self, profile_name, gcode_content="", parent=None, dollar_variables_info=None):
        super().__init__(parent)
        self.profile_name = profile_name
        self.original_gcode = gcode_content
        self.dollar_variables_info = dollar_variables_info or {}
        
        self.setWindowTitle(f"Edit G-Code: {profile_name}")
        self.setModal(True)
        self.resize(1000, 700)
        
        # Enable maximize/minimize buttons
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | 
                           Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | 
                           Qt.WindowCloseButtonHint)
        
        self.setup_ui()
        self.apply_styling()
        self.load_gcode()
    
    def setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        
        # Header with title and instructions
        title = QLabel(f"G-Code Editor - {self.profile_name}")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Instructions for $ variables
        instructions = QLabel(
            "Use $ variables for frame data: {$frame_height}, {$lock_position}, {$hinge1_position}, etc.\n"
            "Click the ? button in the editor to see all available $ variables."
        )
        instructions.setStyleSheet("QLabel { color: #bdbdc0; font-size: 11px; }")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Toolbar
        toolbar = QHBoxLayout()
        layout.addLayout(toolbar)
        
        toolbar.addWidget(QLabel("G-Code:"))
        toolbar.addStretch()
        
        upload_btn = QPushButton("Upload File")
        upload_btn.clicked.connect(self.upload_gcode)
        toolbar.addWidget(upload_btn)
        
        save_btn = QPushButton("Save to File")
        save_btn.clicked.connect(self.save_gcode_to_file)
        toolbar.addWidget(save_btn)
        
        # G-code editor with $ variable support
        self.gcode_editor = GCodeEditor(self)
        self.gcode_editor.set_dollar_variables_info(self.dollar_variables_info)
        
        if not self.original_gcode:
            self.gcode_editor.setPlaceholderText(
                "Enter G-code with $ variables:\n"
                "{$frame_height}, {$lock_position}, {$hinge1_position}, etc.\n\n"
                "Click the ? button to see all available $ variables."
            )
        layout.addWidget(self.gcode_editor, 1)
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def apply_styling(self):
        """Apply dark theme styling"""
        self.setStyleSheet("""
            ProfileGCodeDialog {
                background-color: #282a36;
                color: #ffffff;
            }
            ProfileGCodeDialog QLabel {
                color: #ffffff;
                background-color: transparent;
            }
            ProfileGCodeDialog QPushButton {
                background-color: #1d1f28;
                color: #BB86FC;
                border: 2px solid #BB86FC;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
            }
            ProfileGCodeDialog QPushButton:hover {
                background-color: #000000;
                color: #9965DA;
                border: 2px solid #9965DA;
            }
            ProfileGCodeDialog QPushButton:pressed {
                background-color: #BB86FC;
                color: #1d1f28;
            }
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
    
    def set_dollar_variables_info(self, dollar_variables_info):
        """Update available $ variables information"""
        self.dollar_variables_info = dollar_variables_info
        if hasattr(self, 'gcode_editor'):
            self.gcode_editor.set_dollar_variables_info(dollar_variables_info)
    
    def load_gcode(self):
        """Load G-code content into editor"""
        if self.original_gcode:
            self.gcode_editor.setPlainText(self.original_gcode)
    
    def get_gcode(self):
        """Get edited G-code content"""
        return self.gcode_editor.toPlainText()
    
    def upload_gcode(self):
        """Upload G-code from file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Upload G-Code", "", "G-Code Files (*.gcode *.nc *.txt);;All Files (*)"
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.gcode_editor.setPlainText(content)
                QMessageBox.information(self, "Success", "G-code loaded successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
    
    def save_gcode_to_file(self):
        """Save G-code to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save G-Code", f"{self.profile_name}.gcode", 
            "G-Code Files (*.gcode);;Text Files (*.txt);;All Files (*)"
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.gcode_editor.toPlainText())
                QMessageBox.information(self, "Success", "G-code saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")