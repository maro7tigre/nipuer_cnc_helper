"""
Simple Widgets Module

Basic functional widgets that don't need their own files.
These are utility widgets used across the application.
"""

from PySide6.QtWidgets import QLabel, QLineEdit, QSizePolicy
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor
from .themed_widgets import ThemedLineEdit


class ClickableLabel(QLabel):
    """Label that acts like a button/link with hover effects"""
    clicked = Signal()
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QLabel {
                color: #BB86FC;
                text-decoration: underline;
                background-color: transparent;
            }
            QLabel:hover {
                color: #9965DA;
            }
        """)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ScaledImageLabel(QLabel):
    """Image label that maintains aspect ratio when scaling to fill available space"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScaledContents(False)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._pixmap = None
    
    def setPixmap(self, pixmap):
        """Set pixmap and store original for scaling"""
        self._pixmap = pixmap
        self.updatePixmap()
    
    def updatePixmap(self):
        """Update displayed pixmap based on current size"""
        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                self.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            super().setPixmap(scaled)
    
    def resizeEvent(self, event):
        """Handle resize to update pixmap scaling"""
        super().resizeEvent(event)
        self.updatePixmap()


class ClickableImageLabel(QLabel):
    """Image selector that opens file browser on click"""
    clicked = Signal()
    
    def __init__(self, size=(100, 100), parent=None):
        super().__init__(parent)
        self.setFixedSize(*size)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.PointingHandCursor)
        self.setScaledContents(False)
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


class ErrorLineEdit(ThemedLineEdit):
    """LineEdit with red border for validation errors"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._has_error = False
    
    def set_error(self, has_error):
        """Set error state and update styling"""
        self._has_error = has_error
        if has_error:
            self.setStyleSheet("""
                QLineEdit {
                    background-color: #1d1f28;
                    color: #ffffff;
                    border: 2px solid #ff4444;
                    border-radius: 4px;
                    padding: 4px;
                }
                QLineEdit:focus {
                    border: 2px solid #ff4444;
                }
            """)
        else:
            # Reset to normal themed style
            self.setStyleSheet("""
                QLineEdit {
                    background-color: #1d1f28;
                    color: #ffffff;
                    border: 1px solid #6f779a;
                    border-radius: 4px;
                    padding: 4px;
                }
                QLineEdit:focus {
                    border: 1px solid #BB86FC;
                }
            """)
    
    def has_error(self):
        """Check if widget has error state"""
        return self._has_error


class PlaceholderPixmap:
    """Utility class for creating placeholder pixmaps with text/icons"""
    
    @staticmethod
    def create(size, text="", background_color="#44475c", text_color="#bdbdc0"):
        """Create a placeholder pixmap with text"""
        pixmap = QPixmap(*size)
        pixmap.fill(QColor(background_color))
        
        if text:
            painter = QPainter(pixmap)
            painter.setPen(QColor(text_color))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
            painter.end()
        
        return pixmap
    
    @staticmethod
    def create_profile_placeholder(size=(150, 150)):
        """Create profile image placeholder"""
        return PlaceholderPixmap.create(size, "Profile Image")
    
    @staticmethod
    def create_type_placeholder(size=(80, 80)):
        """Create type image placeholder"""
        return PlaceholderPixmap.create(size, "📐")
    
    @staticmethod
    def create_add_button(size=(80, 80)):
        """Create add button placeholder"""
        return PlaceholderPixmap.create(size, "+")
    
    @staticmethod
    def create_file_icon(size=(60, 60), icon="📄"):
        """Create file icon placeholder"""
        return PlaceholderPixmap.create(size, icon)