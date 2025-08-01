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

# Import the type editor components
from .type_editor import TypeEditor, ClickableImageLabel


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


class TypeItem(QFrame):
    """Individual type item widget with Python-controlled styling"""
    clicked = Signal(str)
    edit_requested = Signal(str)
    duplicate_requested = Signal(str)
    delete_requested = Signal(str)
    
    def __init__(self, name, image_path=None, is_add_button=False):
        super().__init__()
        self.name = name
        self.image_path = image_path
        self.is_add_button = is_add_button
        self.selected = False
        self._is_hovered = False
        
        self.setFixedSize(100, 120)
        self.setCursor(Qt.PointingHandCursor)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Image
        self.image_label = QLabel()
        self.image_label.setFixedSize(80, 80)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(True)
        
        # Load image or create placeholder
        self.update_image()
        
        layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
        
        # Name
        self.name_label = QLabel(name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)
        
        self.update_style()
    
    def update_image(self):
        """Update displayed image"""
        pixmap = QPixmap(80, 80)
        if self.image_path and not self.is_add_button:
            loaded_pixmap = QPixmap(self.image_path)
            if not loaded_pixmap.isNull():
                self.image_label.setPixmap(loaded_pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                return
        
        # Default placeholder
        pixmap.fill(QColor("#44475c"))
        painter = QPainter(pixmap)
        painter.setPen(QColor("#bdbdc0"))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "+" if self.is_add_button else "📐")
        painter.end()
        self.image_label.setPixmap(pixmap)
    
    def set_selected(self, selected):
        """Update selection state with immediate styling"""
        self.selected = selected
        self.update_style()
    
    def update_style(self):
        """Apply styling based on current state"""
        if self.selected:
            # Selected state - green theme
            self.setStyleSheet("""
                TypeItem {
                    background-color: #1A2E20;
                    border: 3px solid #23c87b;
                    border-radius: 4px;
                }
            """)
        elif self._is_hovered:
            # Hover state
            self.setStyleSheet("""
                TypeItem {
                    background-color: #3a3d4d;
                    border: 2px solid #8b95c0;
                    border-radius: 4px;
                }
            """)
        else:
            # Default state
            self.setStyleSheet("""
                TypeItem {
                    background-color: #44475c;
                    border: 2px solid #6f779a;
                    border-radius: 4px;
                }
            """)
        
        # Force immediate update
        self.update()
    
    def enterEvent(self, event):
        """Handle mouse enter"""
        if not self.selected:  # Don't override selected state
            self._is_hovered = True
            self.update_style()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave"""
        self._is_hovered = False
        self.update_style()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.name)
        elif event.button() == Qt.RightButton and not self.is_add_button:
            self.show_context_menu(event.globalPos())
    
    def show_context_menu(self, pos):
        """Show context menu"""
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        
        edit_action = menu.addAction("Edit")
        duplicate_action = menu.addAction("Duplicate")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")
        
        action = menu.exec_(pos)
        
        if action == edit_action:
            self.edit_requested.emit(self.name)
        elif action == duplicate_action:
            self.duplicate_requested.emit(self.name)
        elif action == delete_action:
            self.delete_requested.emit(self.name)


class TypeSelector(QWidget):
    """Horizontal scrollable type selector with Python styling"""
    type_selected = Signal(dict)
    types_modified = Signal()
    
    def __init__(self, profile_type, dollar_variables_info=None):
        super().__init__()
        self.profile_type = profile_type  # "hinge" or "lock"
        self.selected_type = None
        self.types = {}  # name -> type_data
        self.type_items = {}  # name -> TypeItem widget
        self.dollar_variables_info = dollar_variables_info or {}
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel(f"{self.profile_type.capitalize()} Types")
        title.setStyleSheet("QLabel { font-weight: bold; padding: 5px; color: #ffffff; background-color: transparent; }")
        layout.addWidget(title)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFixedHeight(150)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #1d1f28;
                border: 1px solid #6f779a;
                border-radius: 4px;
            }
        """)
        
        # Container
        container = QWidget()
        container.setStyleSheet("QWidget { background-color: #1d1f28; }")
        self.items_layout = QHBoxLayout(container)
        self.items_layout.setSpacing(10)
        self.items_layout.setContentsMargins(5, 5, 5, 5)
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # Add initial "+" button
        self.add_type_button()
    
    def set_dollar_variables_info(self, dollar_variables_info):
        """Set available $ variables information"""
        self.dollar_variables_info = dollar_variables_info
    
    def add_type_button(self):
        """Add the '+' button"""
        add_item = TypeItem("Add", is_add_button=True)
        add_item.clicked.connect(self.add_new_type)
        self.items_layout.insertWidget(0, add_item)
    
    def load_types(self, types_data):
        """Load types from data"""
        # Clear existing (except add button)
        for item in list(self.type_items.values()):
            item.deleteLater()
        self.type_items.clear()
        self.types.clear()
        
        # Add types
        for type_name, type_data in types_data.items():
            self.add_type_item(type_data)
    
    def add_type_item(self, type_data):
        """Add a type item to the selector"""
        name = type_data["name"]
        
        # Create item
        item = TypeItem(name, type_data.get("image"))
        item.clicked.connect(lambda n: self.on_type_clicked(n))
        item.edit_requested.connect(self.edit_type)
        item.duplicate_requested.connect(self.duplicate_type)
        item.delete_requested.connect(self.delete_type)
        
        # Store data and widget
        self.types[name] = type_data
        self.type_items[name] = item
        
        # Add to layout (after the "+" button)
        self.items_layout.addWidget(item)
    
    def on_type_clicked(self, name):
        """Handle type selection with explicit state management"""
        # Clear previous selection
        if self.selected_type and self.selected_type in self.type_items:
            self.type_items[self.selected_type].set_selected(False)
        
        # Set new selection
        self.selected_type = name
        if name in self.type_items:
            self.type_items[name].set_selected(True)
            self.type_selected.emit(self.types[name])
    
    def add_new_type(self):
        """Create new type"""
        dialog = TypeEditor(self.profile_type, dollar_variables_info=self.dollar_variables_info)
        if dialog.exec_() == QDialog.Accepted:
            type_data = dialog.get_type_data()
            self.add_type_item(type_data)
            self.types_modified.emit()
    
    def edit_type(self, name):
        """Edit existing type"""
        if name in self.types:
            dialog = TypeEditor(self.profile_type, self.types[name], dollar_variables_info=self.dollar_variables_info)
            if dialog.exec_() == QDialog.Accepted:
                # Update type data
                new_data = dialog.get_type_data()
                self.types[name] = new_data
                
                # Update widget
                self.type_items[name].deleteLater()
                del self.type_items[name]
                self.add_type_item(new_data)
                self.types_modified.emit()
    
    def duplicate_type(self, name):
        """Duplicate type"""
        if name in self.types:
            # Create copy with new name
            copy_data = self.types[name].copy()
            copy_data["name"] = f"{name} Copy"
            
            dialog = TypeEditor(self.profile_type, copy_data, dollar_variables_info=self.dollar_variables_info)
            if dialog.exec_() == QDialog.Accepted:
                type_data = dialog.get_type_data()
                self.add_type_item(type_data)
                self.types_modified.emit()
    
    def delete_type(self, name):
        """Delete type"""
        reply = QMessageBox.question(self, "Delete Type", 
                                   f"Delete type '{name}'?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes and name in self.types:
            self.type_items[name].deleteLater()
            del self.type_items[name]
            del self.types[name]
            self.types_modified.emit()
    
    def get_types_data(self):
        """Get all types data"""
        return self.types.copy()


class VariableEditor(QWidget):
    """Resizable L variable editor"""
    
    def __init__(self):
        super().__init__()
        self.variables = {}  # var_name -> line_edit
        
        self.setup_ui()
        self.apply_styling()
    
    def apply_styling(self):
        """Apply Python-based styling"""
        self.setStyleSheet("""
            VariableEditor {
                background-color: #282a36;
                color: #ffffff;
            }
            VariableEditor QLabel {
                color: #ffffff;
                background-color: transparent;
            }
            VariableEditor QLineEdit {
                background-color: #1d1f28;
                color: #ffffff;
                border: 1px solid #6f779a;
                border-radius: 4px;
                padding: 4px;
            }
            VariableEditor QLineEdit:focus {
                border: 1px solid #BB86FC;
            }
            VariableEditor QScrollArea {
                background-color: #1d1f28;
                border: 1px solid #6f779a;
                border-radius: 4px;
            }
        """)
    
    def setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        self.title_label = QLabel("Variables (L)")
        self.title_label.setStyleSheet("QLabel { font-weight: bold; padding: 5px; color: #ffffff; background-color: transparent; }")
        layout.addWidget(self.title_label)
        
        # Scroll area - now resizable
        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(100)  # Minimum height
        
        # Container
        container = QWidget()
        self.vars_layout = QVBoxLayout(container)
        self.vars_layout.setSpacing(5)
        self.vars_layout.setContentsMargins(5, 5, 5, 5)
        
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)
    
    def update_variables(self, gcode):
        """Extract L variables from gcode and update UI"""
        # Clear existing
        while self.vars_layout.count():
            item = self.vars_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.variables.clear()
        
        # Find L variables {L1} or {L1:default}
        pattern = r'\{(L\d+)(?::([^}]+))?\}'
        matches = re.findall(pattern, gcode)
        
        # Create unique variables
        unique_vars = {}
        for var_name, default in matches:
            if var_name not in unique_vars:
                unique_vars[var_name] = default
        
        # Create editors
        for var_name in sorted(unique_vars.keys()):
            default = unique_vars[var_name]
            
            # Variable widget
            var_widget = QWidget()
            var_layout = QHBoxLayout(var_widget)
            var_layout.setContentsMargins(0, 0, 0, 0)
            
            # Label
            label = QLabel(f"{var_name}:")
            label.setFixedWidth(60)
            var_layout.addWidget(label)
            
            # Line edit
            line_edit = QLineEdit()
            if default:
                line_edit.setText(default)
            line_edit.setPlaceholderText("Enter value...")
            var_layout.addWidget(line_edit)
            
            self.vars_layout.addWidget(var_widget)
            self.variables[var_name] = line_edit
        
        # Add stretch
        self.vars_layout.addStretch()
        
        # Update visibility
        self.setVisible(len(self.variables) > 0)
    
    def get_variable_values(self):
        """Get all variable values as dictionary"""
        values = {}
        for var_name, line_edit in self.variables.items():
            values[var_name] = line_edit.text()
        return values
    
    def set_variable_values(self, values):
        """Set variable values"""
        for var_name, value in values.items():
            if var_name in self.variables:
                self.variables[var_name].setText(str(value))


class CustomEditor(QWidget):
    """Resizable custom variable editor"""
    
    def __init__(self):
        super().__init__()
        self.customs = {}  # var_name -> line_edit
        
        self.setup_ui()
        self.apply_styling()
    
    def apply_styling(self):
        """Apply Python-based styling"""
        self.setStyleSheet("""
            CustomEditor {
                background-color: #282a36;
                color: #ffffff;
            }
            CustomEditor QLabel {
                color: #ffffff;
                background-color: transparent;
            }
            CustomEditor QLineEdit {
                background-color: #1d1f28;
                color: #ffffff;
                border: 1px solid #6f779a;
                border-radius: 4px;
                padding: 4px;
            }
            CustomEditor QLineEdit:focus {
                border: 1px solid #BB86FC;
            }
            CustomEditor QScrollArea {
                background-color: #1d1f28;
                border: 1px solid #6f779a;
                border-radius: 4px;
            }
        """)
    
    def setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        self.title_label = QLabel("Custom Variables")
        self.title_label.setStyleSheet("QLabel { font-weight: bold; padding: 5px; color: #ffffff; background-color: transparent; }")
        layout.addWidget(self.title_label)
        
        # Scroll area - now resizable
        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(100)  # Minimum height
        
        # Container
        container = QWidget()
        self.customs_layout = QVBoxLayout(container)
        self.customs_layout.setSpacing(5)
        self.customs_layout.setContentsMargins(5, 5, 5, 5)
        
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)
    
    def update_customs(self, gcode):
        """Extract custom variables from gcode and update UI"""
        # Clear existing
        while self.customs_layout.count():
            item = self.customs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.customs.clear()
        
        # Find custom variables (not L or $ variables) - parse name:default correctly
        pattern = r'\{([^L$][^:}]*?)(?::([^}]+))?\}'
        matches = re.findall(pattern, gcode)
        
        # Create unique customs
        unique_customs = {}
        for var_name, default in matches:
            if var_name not in unique_customs:
                unique_customs[var_name] = default
        
        # Create editors
        for var_name in sorted(unique_customs.keys()):
            default = unique_customs[var_name]
            
            # Custom widget
            custom_widget = QWidget()
            custom_layout = QVBoxLayout(custom_widget)
            custom_layout.setContentsMargins(0, 0, 0, 0)
            
            # Label
            label = QLabel(f"{var_name}:")
            custom_layout.addWidget(label)
            
            # Line edit - supports any content including entire lines
            line_edit = QLineEdit()
            if default:
                line_edit.setText(default)
            line_edit.setPlaceholderText("Enter value or entire line...")
            custom_layout.addWidget(line_edit)
            
            self.customs_layout.addWidget(custom_widget)
            self.customs[var_name] = line_edit
        
        # Add stretch
        self.customs_layout.addStretch()
        
        # Update visibility
        self.setVisible(len(self.customs) > 0)
    
    def get_custom_values(self):
        """Get all custom values as dictionary"""
        values = {}
        for var_name, line_edit in self.customs.items():
            values[var_name] = line_edit.text()
        return values
    
    def set_custom_values(self, values):
        """Set custom values"""
        for var_name, value in values.items():
            if var_name in self.customs:
                self.customs[var_name].setText(str(value))


class ProfileEditor(QDialog):
    """Main profile editor dialog with validation and $ variables support"""
    
    def __init__(self, profile_type, profile_data=None, parent=None, dollar_variables_info=None):
        super().__init__(parent)
        self.profile_type = profile_type  # "hinge" or "lock"
        self.profile_data = profile_data or {}
        self.current_type = None
        self.profile_image_path = profile_data.get("image") if profile_data else None
        self.dollar_variables_info = dollar_variables_info or {}
        
        self.setWindowTitle(f"{'Edit' if profile_data else 'New'} {profile_type.capitalize()} Profile")
        self.setModal(True)
        self.resize(1100, 700)
        
        # Enable maximize/minimize buttons
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | 
                           Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | 
                           Qt.WindowCloseButtonHint)
        
        # Apply dialog styling
        self.setStyleSheet("""
            ProfileEditor {
                background-color: #282a36;
                color: #ffffff;
            }
            ProfileEditor QLabel {
                color: #ffffff;
                background-color: transparent;
            }
            ProfileEditor QLineEdit {
                background-color: #1d1f28;
                color: #ffffff;
                border: 1px solid #6f779a;
                border-radius: 4px;
                padding: 4px;
            }
            ProfileEditor QLineEdit:focus {
                border: 1px solid #BB86FC;
            }
        """)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        
        # Type selector
        self.type_selector = TypeSelector(self.profile_type, self.dollar_variables_info)
        self.type_selector.type_selected.connect(self.on_type_selected)
        layout.addWidget(self.type_selector)
        
        # Main content area with resizable splitter
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        layout.addWidget(content_widget, 1)
        
        # Splitter - now resizable by user
        splitter = QSplitter(Qt.Horizontal)
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
        
        # Middle side - Type preview
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        
        # Type preview
        middle_layout.addWidget(QLabel("Type Preview:"))
        # Use ScaledImageLabel for preview to expand and maintain aspect ratio
        self.preview_image_label = ScaledImageLabel()
        self.preview_image_label.setAlignment(Qt.AlignCenter)
        self.preview_image_label.setText("Select a type to see preview")
        self.preview_image_label.setMinimumHeight(200)
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
        
        # Right side - Profile info
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Profile name
        right_layout.addWidget(QLabel("Profile Name:"))
        self.profile_name_edit = QLineEdit()
        right_layout.addWidget(self.profile_name_edit)
        
        right_layout.addSpacing(20)
        
        # Profile image
        right_layout.addWidget(QLabel("Profile Image:"))
        self.profile_image_label = ClickableImageLabel((150, 150))
        self.profile_image_label.clicked.connect(self.select_profile_image)
        self.set_profile_placeholder()
        right_layout.addWidget(self.profile_image_label, alignment=Qt.AlignCenter)
        
        right_layout.addStretch()
        splitter.addWidget(right_widget)

        # Set initial splitter sizes - user can adjust these
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
        """Load existing profile data"""
        if self.profile_data:
            self.profile_name_edit.setText(self.profile_data.get("name", ""))
            
            if self.profile_image_path:
                pixmap = QPixmap(self.profile_image_path)
                if not pixmap.isNull():
                    self.profile_image_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio))
    
    def load_types(self, types_data):
        """Load types into selector"""
        self.type_selector.load_types(types_data)
        
        # Select type if profile has one
        if self.profile_data.get("type"):
            for type_name, type_data in types_data.items():
                if type_name == self.profile_data["type"]:
                    self.type_selector.on_type_clicked(type_name)
                    break
    
    def get_profile_data(self):
        """Get profile data from dialog"""
        data = {
            "name": self.profile_name_edit.text(),
            "type": self.current_type["name"] if self.current_type else None,
            "l_variables": self.variable_editor.get_variable_values(),
            "custom_variables": self.custom_editor.get_custom_values(),
            "image": self.profile_image_path
        }
        
        print(f"Profile data created: {data}")
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
        
        # Update preview with scaling that expands to fill space
        if type_data.get("preview"):
            pixmap = QPixmap(type_data["preview"])
            if not pixmap.isNull():
                self.preview_image_label.setPixmap(pixmap)
            else:
                self.preview_image_label.setText("No preview available")
        else:
            self.preview_image_label.setText("No preview available")
    
    def select_profile_image(self):
        """Select profile image"""
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
        pixmap = QPixmap(150, 150)
        pixmap.fill(QColor("#44475c"))
        painter = QPainter(pixmap)
        painter.setPen(QColor("#bdbdc0"))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "Profile Image")
        painter.end()
        self.profile_image_label.setPixmap(pixmap)