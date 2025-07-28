from PySide6.QtWidgets import (QFrame, QVBoxLayout, QLabel, QDialog, QHBoxLayout, 
                             QPushButton)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor


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
        from gcode_ide import GCodeEditor
        
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
    """Individual file item with dual content tracking and visual modification indication"""
    
    content_changed = Signal(str)  # Emits new content when edited
    
    def __init__(self, name, file_type, side, dollar_variables_info=None):
        super().__init__()
        self.name = name
        self.file_type = file_type  # 'frame', 'lock', 'hinge'
        self.side = side  # 'left', 'right'
        self.dollar_variables_info = dollar_variables_info or {}
        
        # Two sets of content
        self.auto_generated_content = ""  # Auto-generated from parameters
        self.displayed_content = ""       # What's shown and can be edited
        self._manually_modified = False   # Track if user has manually modified
        
        self.setFixedSize(140, 100)
        self.setCursor(Qt.PointingHandCursor)
        
        self.setup_ui()
        self.update_border_color()
    
    def setup_ui(self):
        """Setup the widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Icon area
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(60, 60)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setScaledContents(True)
        self.update_icon()
        layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        
        # Name label
        self.name_label = QLabel(self.name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setFont(QFont("Arial", 9, QFont.Bold))
        self.name_label.setStyleSheet("QLabel { color: #ffffff; background-color: transparent; }")
        layout.addWidget(self.name_label)
    
    def update_icon(self):
        """Update the icon based on file type"""
        pixmap = QPixmap(60, 60)
        pixmap.fill(QColor("#44475c"))
        
        painter = QPainter(pixmap)
        painter.setPen(QColor("#bdbdc0"))
        
        # Different icons for different file types
        if self.file_type == 'frame':
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "🔲")
        elif self.file_type == 'lock':
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "🔒")
        elif self.file_type == 'hinge':
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "🔗")
        else:
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "📄")
        
        painter.end()
        self.icon_label.setPixmap(pixmap)
    
    def set_dollar_variables_info(self, dollar_variables_info):
        """Update $ variables information"""
        self.dollar_variables_info = dollar_variables_info
    
    def update_auto_generated_content(self, content):
        """Update the auto-generated content (from parameter changes)"""
        self.auto_generated_content = content
    
    def update_displayed_content(self, content):
        """Update the displayed content (what user sees/edits)"""
        self.displayed_content = content
    
    def get_displayed_content(self):
        """Get the current displayed content"""
        return self.displayed_content
    
    def copy_auto_to_displayed(self):
        """Copy auto-generated content to displayed content"""
        self.displayed_content = self.auto_generated_content
    
    def is_manually_modified(self):
        """Check if content has been manually modified"""
        return self._manually_modified
    
    def set_manually_modified(self, modified):
        """Set manual modification flag"""
        self._manually_modified = modified
    
    def update_border_color(self):
        """Update border color based on content state"""
        if self.displayed_content != self.auto_generated_content:
            # Red border - displayed content differs from auto-generated
            border_color = "#ff4444"
            bg_color = "#2d1f1f"
        else:
            # Green border - displayed content matches auto-generated
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
            self.displayed_content, 
            self.dollar_variables_info,
            self
        )
        
        if dialog.exec_() == QDialog.Accepted:
            new_content = dialog.get_content()
            self.displayed_content = new_content
            self._manually_modified = True
            self.update_border_color()
            self.content_changed.emit(new_content)
    
    def reset_to_auto_generated(self):
        """Reset displayed content to auto-generated version"""
        self.displayed_content = self.auto_generated_content
        self._manually_modified = False
        self.update_border_color()
        self.content_changed.emit(self.displayed_content)
    
    def has_content(self):
        """Check if file has any displayed content"""
        return bool(self.displayed_content.strip())