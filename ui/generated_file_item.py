from PySide6.QtWidgets import (QFrame, QVBoxLayout, QLabel, QDialog, QHBoxLayout, 
                             QPushButton)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor


class GCodeEditDialog(QDialog):
    """Dialog for editing G-code with the full editor"""
    
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit {title}")
        self.setModal(True)
        self.resize(800, 600)
        
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
    """Individual file item with visual modification tracking"""
    
    content_changed = Signal(str)  # Emits new content when edited
    
    def __init__(self, name, file_type, side):
        super().__init__()
        self.name = name
        self.file_type = file_type  # 'frame', 'lock', 'hinge'
        self.side = side  # 'left', 'right'
        self.content = ""
        self.original_content = ""
        self.is_modified = False
        
        self.setFixedSize(140, 100)
        self.setCursor(Qt.PointingHandCursor)
        
        self.setup_ui()
        self.update_style()
    
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
    
    def update_content(self, content, original_content):
        """Update file content and check modification status"""
        self.content = content
        self.original_content = original_content
        self.is_modified = (content != original_content)
        self.update_style()
    
    def update_style(self):
        """Update visual style based on modification status"""
        if self.is_modified:
            # Red border for modified files
            border_color = "#ff4444"
            bg_color = "#2d1f1f"
        else:
            # Green border for unmodified files
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
        dialog = GCodeEditDialog(f"{self.side.title()} {self.name}", self.content, self)
        
        if dialog.exec_() == QDialog.Accepted:
            new_content = dialog.get_content()
            self.content = new_content
            self.is_modified = (new_content != self.original_content)
            self.update_style()
            self.content_changed.emit(new_content)
    
    def reset_to_original(self):
        """Reset content to original (auto-generated) version"""
        self.content = self.original_content
        self.is_modified = False
        self.update_style()
        self.content_changed.emit(self.content)
    
    def has_content(self):
        """Check if file has any content"""
        return bool(self.content.strip())