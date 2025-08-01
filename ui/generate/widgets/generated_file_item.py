"""
Generated File Item Widget

Individual file item with dual content tracking and visual state management.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QDialog
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from ...widgets.themed_widgets import ThemedLabel
from ...widgets.simple_widgets import ClickableImageLabel, PlaceholderPixmap


class GCodeEditDialog(QDialog):
    """Dialog for editing G-code with the full editor"""
    
    def __init__(self, title, content, dollar_variables_info=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit {title}")
        self.setModal(True)
        self.resize(800, 600)
        self.dollar_variables_info = dollar_variables_info or {}
        
        # Enable maximize/minimize buttons
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | 
                           Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | 
                           Qt.WindowCloseButtonHint)
        
        # Apply styling
        self.setStyleSheet("""
            GCodeEditDialog {
                background-color: #282a36;
                color: #ffffff;
            }
            QPushButton {
                background-color: #1d1f28;
                color: #23c87b;
                border: 2px solid #23c87b;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #000000;
                color: #1a945b;
                border: 2px solid #1a945b;
            }
            QPushButton:pressed {
                background-color: #23c87b;
                color: #1d1f28;
            }
            QPushButton#cancel_button {
                color: #BB86FC;
                border: 2px solid #BB86FC;
            }
            QPushButton#cancel_button:hover {
                color: #9965DA;
                border: 2px solid #9965DA;
            }
        """)
        
        self.setup_ui(content)
    
    def setup_ui(self, content):
        """Setup the dialog UI"""
        from ...gcode_ide import GCodeEditor
        from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton
        
        layout = QVBoxLayout(self)
        
        # G-code editor
        self.editor = GCodeEditor(self)
        self.editor.set_dollar_variables_info(self.dollar_variables_info)
        self.editor.setPlainText(content)
        layout.addWidget(self.editor)
        
        # Buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("cancel_button")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
    
    def get_content(self):
        """Get the edited content"""
        return self.editor.toPlainText()


class GeneratedFileItem(QFrame):
    """Individual file item with dual content tracking and visual state management"""
    
    content_changed = Signal(str)  # Emits new content when edited
    
    def __init__(self, name, file_type, side, dollar_variables_info=None, parent=None):
        super().__init__(parent)
        self.name = name
        self.file_type = file_type  # 'frame', 'lock', 'hinge'
        self.side = side  # 'left', 'right'
        self.dollar_variables_info = dollar_variables_info or {}
        
        # Dual content tracking
        self.auto_content = ""      # Auto-generated from parameters
        self.manual_content = ""    # Manual/displayed content (what user sees/edits)
        
        self.setFixedSize(140, 100)
        self.setCursor(Qt.PointingHandCursor)
        
        self.setup_ui()
        self.update_visual_state()
    
    def setup_ui(self):
        """Setup the widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Icon area
        self.icon_label = ClickableImageLabel((60, 60))
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setScaledContents(True)
        self.update_icon()
        layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        
        # Name label
        self.name_label = ThemedLabel(self.name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setFont(QFont("Arial", 9, QFont.Bold))
        layout.addWidget(self.name_label)
    
    def update_icon(self):
        """Update the icon based on file type"""
        # Different icons for different file types
        if self.file_type == 'frame':
            icon = "🔲"
        elif self.file_type == 'lock':
            icon = "🔒"
        elif self.file_type == 'hinge':
            icon = "🔗"
        else:
            icon = "📄"
        
        pixmap = PlaceholderPixmap.create((60, 60), icon, "#44475c", "#bdbdc0")
        self.icon_label.setPixmap(pixmap)
    
    def set_dollar_variables_info(self, dollar_variables_info):
        """Update $ variables information"""
        self.dollar_variables_info = dollar_variables_info
    
    def update_auto_content(self, content):
        """Update the auto-generated content"""
        self.auto_content = content
    
    def update_manual_content(self, content):
        """Update the manual/displayed content"""
        self.manual_content = content
    
    def set_manual_content(self, content):
        """Set manual content (from user editing)"""
        self.manual_content = content
    
    def get_manual_content(self):
        """Get the current manual content"""
        return self.manual_content
    
    def get_auto_content(self):
        """Get the auto-generated content"""
        return self.auto_content
    
    def update_visual_state(self):
        """Update visual state based on content comparison"""
        if self.manual_content != self.auto_content:
            # Red border - manual content differs from auto-generated
            border_color = "#ff4444"
            bg_color = "#2d1f1f"
        else:
            # Green border - manual content matches auto-generated
            border_color = "#23c87b"
            bg_color = "#1f2d20"
        
        self.setStyleSheet(f"""
            GeneratedFileItem {{
                background-color: {bg_color};
                border: 3px solid {border_color};
                border-radius: 6px;
            }}
            GeneratedFileItem:hover {{
                background-color: #3a3d4d;
                border: 3px solid #BB86FC;
            }}
        """)
    
    def mousePressEvent(self, event):
        """Handle click to open editor"""
        if event.button() == Qt.LeftButton:
            self.open_editor()
    
    def open_editor(self):
        """Open G-code editor dialog"""
        dialog = GCodeEditDialog(
            f"{self.side.title()} {self.name}", 
            self.manual_content, 
            self.dollar_variables_info,
            self
        )
        
        if dialog.exec_() == QDialog.Accepted:
            new_content = dialog.get_content()
            self.manual_content = new_content
            self.update_visual_state()
            self.content_changed.emit(new_content)
    
    def reset_to_auto_generated(self):
        """Reset manual content to auto-generated version"""
        self.manual_content = self.auto_content
        self.update_visual_state()
        self.content_changed.emit(self.manual_content)
    
    def has_content(self):
        """Check if file has any manual content"""
        return bool(self.manual_content.strip())