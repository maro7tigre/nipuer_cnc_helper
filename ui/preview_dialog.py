from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTextEdit, QLabel, QSplitter)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextOption


class PreviewDialog(QDialog):
    """Dialog for previewing G-code files"""
    
    def __init__(self, filename, gcode_content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Preview: {filename}")
        self.setModal(True)
        self.resize(900, 600)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create splitter for side-by-side view
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left side - G-code
        gcode_widget = QTextEdit()
        gcode_widget.setReadOnly(True)
        gcode_widget.setFont(QFont("Consolas", 10))
        gcode_widget.setPlainText(gcode_content)
        gcode_widget.setLineWrapMode(QTextEdit.NoWrap)
        splitter.addWidget(gcode_widget)
        
        # Right side - Toolpath preview
        preview_widget = QLabel()
        preview_widget.setMinimumWidth(400)
        preview_widget.setStyleSheet("QLabel { background-color: #333; border: 1px solid #666; }")
        preview_widget.setAlignment(Qt.AlignCenter)
        preview_widget.setText("3D Toolpath\nVisualization\n\n(Placeholder)")
        splitter.addWidget(preview_widget)
        
        # Set initial splitter sizes
        splitter.setSizes([450, 450])
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        button_layout.addStretch()
        
        # View controls (placeholder)
        reset_button = QPushButton("Reset View")
        reset_button.setEnabled(False)  # Disabled for now
        button_layout.addWidget(reset_button)
        
        zoom_button = QPushButton("Zoom")
        zoom_button.setEnabled(False)  # Disabled for now
        button_layout.addWidget(zoom_button)
        
        button_layout.addStretch()
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)