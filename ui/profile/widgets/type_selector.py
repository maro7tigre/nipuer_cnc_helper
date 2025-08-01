"""
Type Selector Widget

Horizontal scrollable type selector with add button functionality.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDialog, QMessageBox
from PySide6.QtCore import Signal, Qt
from ...widgets.themed_widgets import ThemedLabel, ThemedScrollArea
from .type_item import TypeItem


class TypeSelector(QWidget):
    """Horizontal scrollable type selector with Python styling"""
    type_selected = Signal(dict)
    types_modified = Signal()
    
    def __init__(self, profile_type, dollar_variables_info=None, parent=None):
        super().__init__(parent)
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
        title = ThemedLabel(f"{self.profile_type.capitalize()} Types")
        title.setStyleSheet("QLabel { font-weight: bold; padding: 5px; }")
        layout.addWidget(title)
        
        # Scroll area
        scroll = ThemedScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFixedHeight(150)
        scroll.setWidgetResizable(True)
        
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
        from ...dialogs.type_editor import TypeEditor
        
        dialog = TypeEditor(self.profile_type, dollar_variables_info=self.dollar_variables_info)
        if dialog.exec_() == QDialog.Accepted:
            type_data = dialog.get_type_data()
            self.add_type_item(type_data)
            self.types_modified.emit()
    
    def edit_type(self, name):
        """Edit existing type"""
        if name in self.types:
            from ...dialogs.type_editor import TypeEditor
            
            dialog = TypeEditor(self.profile_type, self.types[name], 
                              dollar_variables_info=self.dollar_variables_info)
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
            from ...dialogs.type_editor import TypeEditor
            
            # Create copy with new name
            copy_data = self.types[name].copy()
            copy_data["name"] = f"{name} Copy"
            
            dialog = TypeEditor(self.profile_type, copy_data, 
                              dollar_variables_info=self.dollar_variables_info)
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