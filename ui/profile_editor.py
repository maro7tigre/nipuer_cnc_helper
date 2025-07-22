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


class ClickableImageLabel(QLabel):
    """Clickable image label that follows theme"""
    clicked = Signal()
    
    def __init__(self, size=(100, 100)):
        super().__init__()
        self.setFixedSize(*size)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("class", "image-selector")
        self.setScaledContents(False)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()


class TypeItem(QFrame):
    """Individual type item widget for horizontal scroll"""
    clicked = Signal(str)
    edit_requested = Signal(str)
    duplicate_requested = Signal(str)
    delete_requested = Signal(str)
    
    # MARK: - Initialization
    def __init__(self, name, image_path=None, is_add_button=False):
        super().__init__()
        self.name = name
        self.image_path = image_path
        self.is_add_button = is_add_button
        self.selected = False
        
        self.setProperty("class", "profile-item")
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
        """Update selection state"""
        self.selected = selected
        self.setProperty("selected", str(selected).lower())
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
    
    def update_style(self):
        """Update visual styling"""
        self.set_selected(self.selected)
    
    # MARK: - Event Handlers
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
    """Horizontal scrollable type selector"""
    type_selected = Signal(dict)  # Emits type data
    types_modified = Signal()  # Emits when types are added/edited/deleted
    
    # MARK: - Initialization
    def __init__(self, profile_type):
        super().__init__()
        self.profile_type = profile_type  # "hinge" or "lock"
        self.selected_type = None
        self.types = {}  # name -> type_data
        self.type_items = {}  # name -> TypeItem widget
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel(f"{self.profile_type.capitalize()} Types")
        title.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(title)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFixedHeight(150)
        scroll.setWidgetResizable(True)
        
        # Container
        container = QWidget()
        self.items_layout = QHBoxLayout(container)
        self.items_layout.setSpacing(10)
        self.items_layout.setContentsMargins(5, 5, 5, 5)
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # Add initial "+" button
        self.add_type_button()
    
    # MARK: - Type Management
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
        """Handle type selection"""
        if self.selected_type and self.selected_type in self.type_items:
            self.type_items[self.selected_type].set_selected(False)
        
        self.selected_type = name
        if name in self.type_items:
            self.type_items[name].set_selected(True)
            self.type_selected.emit(self.types[name])
    
    # MARK: - Type Operations
    def add_new_type(self):
        """Create new type"""
        dialog = TypeEditor(self.profile_type)
        if dialog.exec_() == QDialog.Accepted:
            type_data = dialog.get_type_data()
            self.add_type_item(type_data)
            self.types_modified.emit()
    
    def edit_type(self, name):
        """Edit existing type"""
        if name in self.types:
            dialog = TypeEditor(self.profile_type, self.types[name])
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
            
            dialog = TypeEditor(self.profile_type, copy_data)
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


class TypeEditor(QDialog):
    """Type editor dialog"""
    
    # MARK: - Initialization
    def __init__(self, profile_type, type_data=None, parent=None):
        super().__init__(parent)
        self.profile_type = profile_type
        self.type_data = type_data or {}
        self.image_path = type_data.get("image") if type_data else None
        self.preview_path = type_data.get("preview") if type_data else None
        
        self.setWindowTitle(f"{'Edit' if type_data else 'New'} {profile_type.capitalize()} Type")
        self.setModal(True)
        self.resize(800, 600)
        
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
        
        # Right side - GCode editor
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # GCode header
        gcode_header = QHBoxLayout()
        right_layout.addLayout(gcode_header)
        
        gcode_header.addWidget(QLabel("G-Code Template:"))
        gcode_header.addStretch()
        
        upload_btn = QPushButton("Upload")
        upload_btn.clicked.connect(self.upload_gcode)
        gcode_header.addWidget(upload_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_gcode)
        gcode_header.addWidget(save_btn)
        
        self.gcode_edit = QTextEdit()
        self.gcode_edit.setPlaceholderText("Enter G-code with variables like {L1}, {L2:10}, etc.")
        right_layout.addWidget(self.gcode_edit)
        
        content_split.addWidget(right_widget)
        content_split.setSizes([300, 500])
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    # MARK: - Data Management
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
    
    def get_type_data(self):
        """Get type data from dialog"""
        return {
            "name": self.name_edit.text(),
            "gcode": self.gcode_edit.toPlainText(),
            "image": self.image_path,
            "preview": self.preview_path
        }
    
    # MARK: - File Operations
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
    
    # MARK: - UI Helpers
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


class VariableEditor(QWidget):
    """Vertical scrollable variable editor"""
    
    # MARK: - Initialization
    def __init__(self):
        super().__init__()
        self.variables = {}  # var_name -> (default_value, line_edit)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        self.title_label = QLabel("Variables")
        self.title_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(self.title_label)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidgetResizable(True)
        
        # Container
        container = QWidget()
        self.vars_layout = QVBoxLayout(container)
        self.vars_layout.setSpacing(5)
        self.vars_layout.setContentsMargins(5, 5, 5, 5)
        
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)
    
    # MARK: - Variable Management
    def update_variables(self, gcode):
        """Extract variables from gcode and update UI"""
        # Clear existing
        while self.vars_layout.count():
            item = self.vars_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.variables.clear()
        
        # Find all variables {VAR} or {VAR:default}
        pattern = r'\{([A-Z]\d+)(?::([0-9.]+))?\}'
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
            line_edit.setValidator(QDoubleValidator())
            if default:
                line_edit.setText(default)
            line_edit.setPlaceholderText("0.0")
            var_layout.addWidget(line_edit)
            
            self.vars_layout.addWidget(var_widget)
            self.variables[var_name] = (default, line_edit)
        
        # Add stretch
        self.vars_layout.addStretch()
        
        # Update visibility
        self.setVisible(len(self.variables) > 0)
    
    def get_variable_values(self):
        """Get all variable values"""
        values = {}
        for var_name, (default, line_edit) in self.variables.items():
            text = line_edit.text()
            values[var_name] = float(text) if text else 0.0
        return values
    
    def set_variable_values(self, values):
        """Set variable values"""
        for var_name, value in values.items():
            if var_name in self.variables:
                _, line_edit = self.variables[var_name]
                line_edit.setText(str(value))


class ProfileEditor(QDialog):
    """Main profile editor dialog"""
    
    # MARK: - Initialization
    def __init__(self, profile_type, profile_data=None, parent=None):
        super().__init__(parent)
        self.profile_type = profile_type  # "hinge" or "lock"
        self.profile_data = profile_data or {}
        self.current_type = None
        self.profile_image_path = profile_data.get("image") if profile_data else None
        
        self.setWindowTitle(f"{'Edit' if profile_data else 'New'} {profile_type.capitalize()} Profile")
        self.setModal(True)
        self.resize(900, 700)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        
        # Type selector
        self.type_selector = TypeSelector(self.profile_type)
        self.type_selector.type_selected.connect(self.on_type_selected)
        layout.addWidget(self.type_selector)
        
        # Main content area
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        layout.addWidget(content_widget, 1)
        
        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        content_layout.addWidget(splitter)
        
        # Left side - Variables and profile image
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Profile image
        left_layout.addWidget(QLabel("Profile Image:"))
        self.profile_image_label = ClickableImageLabel((150, 150))
        self.profile_image_label.clicked.connect(self.select_profile_image)
        self.set_profile_placeholder()
        left_layout.addWidget(self.profile_image_label, alignment=Qt.AlignCenter)
        
        left_layout.addSpacing(20)
        
        # Variables
        self.variable_editor = VariableEditor()
        self.variable_editor.setVisible(False)
        left_layout.addWidget(self.variable_editor, 1)
        
        splitter.addWidget(left_widget)
        
        # Right side - Profile name and preview
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Profile name
        right_layout.addWidget(QLabel("Profile Name:"))
        self.profile_name_edit = QLineEdit()
        right_layout.addWidget(self.profile_name_edit)
        
        right_layout.addSpacing(20)
        
        # Type preview
        right_layout.addWidget(QLabel("Type Preview:"))
        self.preview_image_label = QLabel()
        self.preview_image_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        self.preview_image_label.setScaledContents(True)
        self.preview_image_label.setAlignment(Qt.AlignCenter)
        self.preview_image_label.setProperty("class", "image-selector")
        self.preview_image_label.setText("Select a type to see preview")
        right_layout.addWidget(self.preview_image_label)
        
        right_layout.addStretch()
        splitter.addWidget(right_widget)
        
        splitter.setStretchFactor(0, 1)   # left
        splitter.setStretchFactor(1, 3)   # right
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    # MARK: - Data Management
    def load_data(self):
        """Load existing profile data"""
        if self.profile_data:
            self.profile_name_edit.setText(self.profile_data.get("name", ""))
            
            if self.profile_image_path:
                pixmap = QPixmap(self.profile_image_path)
                if not pixmap.isNull():
                    self.profile_image_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio))
            
            # If profile has a type, select it
            if self.profile_data.get("type"):
                # This will be handled by parent after loading types
                pass
    
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
            "variables": self.variable_editor.get_variable_values(),
            "image": self.profile_image_path
        }
        return data
    
    # MARK: - Event Handlers
    def on_type_selected(self, type_data):
        """Handle type selection"""
        self.current_type = type_data
        
        # Update variables
        self.variable_editor.update_variables(type_data.get("gcode", ""))
        
        # Load saved variable values if editing
        if self.profile_data.get("variables") and self.profile_data.get("type") == type_data["name"]:
            self.variable_editor.set_variable_values(self.profile_data["variables"])
        
        # Update preview
        if type_data.get("preview"):
            pixmap = QPixmap(type_data["preview"])
            if not pixmap.isNull():
                self.preview_image_label.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio))
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
    
    # MARK: - UI Helpers
    def set_profile_placeholder(self):
        """Set placeholder for profile image"""
        pixmap = QPixmap(150, 150)
        pixmap.fill(QColor("#44475c"))
        painter = QPainter(pixmap)
        painter.setPen(QColor("#bdbdc0"))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "Profile Image")
        painter.end()
        self.profile_image_label.setPixmap(pixmap)