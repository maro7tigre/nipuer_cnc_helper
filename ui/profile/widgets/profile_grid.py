"""
Profile Grid Widget

Scrollable grid container for profile items with responsive layout.
"""

from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QGridLayout, QDialog, QMessageBox
from PySide6.QtCore import Signal, Qt
from ...widgets.themed_widgets import ThemedLabel
from .profile_item import ProfileItem


class ProfileGrid(QScrollArea):
    """Scrollable grid container for profile items with Python styling"""
    selection_changed = Signal(str)
    data_modified = Signal()
    
    def __init__(self, profile_type, dollar_variables_info=None, parent=None):
        super().__init__(parent)
        self.profile_type = profile_type  # "hinge" or "lock"
        self.selected_profile = None
        self.profiles = {}  # name -> profile_data
        self.profile_items = {}  # name -> ProfileItem widget
        self.types = {}  # Store types data
        self.dollar_variables_info = dollar_variables_info or {}
        
        # Setup scroll area styling
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setStyleSheet("""
            ProfileGrid {
                background-color: #282a36;
                border: 1px solid #44475c;
                border-radius: 4px;
            }
            ProfileGrid QScrollBar:vertical {
                background-color: #1d1f28;
                width: 12px;
                margin: 0px;
            }
            ProfileGrid QScrollBar::handle:vertical {
                background-color: #6f779a;
                min-height: 20px;
                border-radius: 6px;
            }
            ProfileGrid QScrollBar::add-line:vertical, ProfileGrid QScrollBar::sub-line:vertical {
                height: 0px;
            }
            ProfileGrid QScrollBar:horizontal {
                background-color: #1d1f28;
                height: 12px;
                margin: 0px;
            }
            ProfileGrid QScrollBar::handle:horizontal {
                background-color: #6f779a;
                min-width: 20px;
                border-radius: 6px;
            }
            ProfileGrid QScrollBar::add-line:horizontal, ProfileGrid QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        
        # Container widget
        container = QWidget()
        container.setStyleSheet("QWidget { background-color: #282a36; }")
        self.setWidget(container)
        
        # Main layout
        main_layout = QVBoxLayout(container)
        
        # Title
        title = ThemedLabel(f"{profile_type.capitalize()} Profiles")
        title.setStyleSheet("""
            QLabel {
                font-size: 16px; 
                font-weight: bold; 
                padding: 10px; 
            }
        """)
        main_layout.addWidget(title)
        
        # Grid layout for items
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        main_layout.addLayout(self.grid_layout)
        main_layout.addStretch()
    
    def set_dollar_variables_info(self, dollar_variables_info):
        """Set available $ variables information"""
        self.dollar_variables_info = dollar_variables_info
    
    def populate_profiles(self):
        """Load and display profiles"""
        # Clear existing items
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.profile_items.clear()
        
        # Add "+" button
        add_item = ProfileItem("Add", is_add_button=True)
        add_item.clicked.connect(self.add_new_profile)
        self.grid_layout.addWidget(add_item, 0, 0)
        
        # Add profiles
        row, col = 0, 1
        for profile_name, profile_data in self.profiles.items():
            self.add_profile_item(profile_name, profile_data, row, col)
            col += 1
            if col > self.get_columns_count():
                col = 0
                row += 1
    
    def add_profile_item(self, name, profile_data, row=None, col=None):
        """Add a profile item to the grid"""
        item = ProfileItem(name, profile_data)
        item.clicked.connect(self.on_item_clicked)
        item.edit_requested.connect(self.edit_profile)
        item.duplicate_requested.connect(self.duplicate_profile)
        item.delete_requested.connect(self.delete_profile)
        
        self.profiles[name] = profile_data
        self.profile_items[name] = item
        
        if row is not None and col is not None:
            self.grid_layout.addWidget(item, row, col)
        else:
            # Add to end of grid
            self.rearrange_grid()
    
    def get_columns_count(self):
        """Calculate number of columns based on current width"""
        item_width = 130  # ProfileItem width + spacing
        available_width = self.viewport().width()
        return max(1, available_width // item_width)
    
    def resizeEvent(self, event):
        """Handle resize to rearrange grid"""
        super().resizeEvent(event)
        self.rearrange_grid()
    
    def rearrange_grid(self):
        """Rearrange grid items based on current width"""
        columns = self.get_columns_count()
        
        # Get all widgets
        widgets = []
        for i in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                widgets.append(item.widget())
        
        # Clear grid
        while self.grid_layout.count():
            self.grid_layout.takeAt(0)
        
        # Re-add widgets
        row, col = 0, 0
        for widget in widgets:
            self.grid_layout.addWidget(widget, row, col)
            col += 1
            if col >= columns:
                col = 0
                row += 1
    
    def add_new_profile(self):
        """Create new profile"""
        from ...dialogs.profile_editor import ProfileEditor
        
        dialog = ProfileEditor(self.profile_type, dollar_variables_info=self.dollar_variables_info)
        dialog.load_types(self.types)  # Load available types
        
        # Connect type modification signal
        dialog.type_selector.types_modified.connect(lambda: self.on_types_modified(dialog.type_selector))
        
        if dialog.exec_() == QDialog.Accepted:
            profile_data = dialog.get_profile_data()
            if profile_data and profile_data.get("name"):
                # Check if name already exists
                if profile_data["name"] in self.profiles:
                    QMessageBox.warning(self, "Name Exists", 
                                      f"A profile named '{profile_data['name']}' already exists.")
                    return
                
                # Add new profile
                self.profiles[profile_data["name"]] = profile_data
                self.populate_profiles()
                self.data_modified.emit()
    
    def edit_profile(self, name):
        """Edit existing profile"""
        if name not in self.profiles:
            return
        
        from ...dialogs.profile_editor import ProfileEditor
        
        # Get current profile data
        current_data = self.profiles[name].copy()
        
        dialog = ProfileEditor(self.profile_type, current_data, 
                             dollar_variables_info=self.dollar_variables_info)
        dialog.load_types(self.types)  # Load available types
        
        # Connect type modification signal
        dialog.type_selector.types_modified.connect(lambda: self.on_types_modified(dialog.type_selector))
        
        if dialog.exec_() == QDialog.Accepted:
            profile_data = dialog.get_profile_data()
            if profile_data and profile_data.get("name"):
                # Handle name change
                if profile_data["name"] != name and profile_data["name"] in self.profiles:
                    QMessageBox.warning(self, "Name Exists", 
                                      f"A profile named '{profile_data['name']}' already exists.")
                    return
                
                # Update profile
                if profile_data["name"] != name:
                    del self.profiles[name]
                
                self.profiles[profile_data["name"]] = profile_data
                self.populate_profiles()
                self.data_modified.emit()
    
    def duplicate_profile(self, name):
        """Duplicate existing profile"""
        if name not in self.profiles:
            return
        
        from ...dialogs.profile_editor import ProfileEditor
        
        # Create copy with new name
        copy_data = self.profiles[name].copy()
        copy_data["name"] = f"{name} Copy"
        
        # Find unique name
        base_name = copy_data["name"]
        counter = 1
        while copy_data["name"] in self.profiles:
            copy_data["name"] = f"{base_name} {counter}"
            counter += 1
        
        dialog = ProfileEditor(self.profile_type, copy_data, 
                             dollar_variables_info=self.dollar_variables_info)
        dialog.load_types(self.types)  # Load available types
        
        # Connect type modification signal
        dialog.type_selector.types_modified.connect(lambda: self.on_types_modified(dialog.type_selector))
        
        if dialog.exec_() == QDialog.Accepted:
            profile_data = dialog.get_profile_data()
            if profile_data and profile_data.get("name"):
                # Check if name already exists
                if profile_data["name"] in self.profiles:
                    QMessageBox.warning(self, "Name Exists", 
                                      f"A profile named '{profile_data['name']}' already exists.")
                    return
                
                # Add duplicated profile
                self.profiles[profile_data["name"]] = profile_data
                self.populate_profiles()
                self.data_modified.emit()
    
    def on_types_modified(self, type_selector):
        """Handle when types are modified in dialog"""
        # Update types from the selector
        self.types = type_selector.get_types_data()
        # Save immediately
        self.data_modified.emit()
    
    def delete_profile(self, name):
        """Delete profile after confirmation"""
        reply = QMessageBox.question(self, "Delete Profile", 
                                   f"Are you sure you want to delete '{name}'?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Remove from data
            if name in self.profiles:
                del self.profiles[name]
                self.populate_profiles()
                self.data_modified.emit()
            
            # Clear selection if deleted item was selected
            if self.selected_profile == name:
                self.selected_profile = None
                self.selection_changed.emit("")
    
    def on_item_clicked(self, name):
        """Handle profile selection with explicit state management"""
        # Clear previous selection
        if self.selected_profile and self.selected_profile in self.profile_items:
            self.profile_items[self.selected_profile].set_selected(False)
        
        # Skip add button
        if name == "Add":
            return
        
        # Set new selection
        self.selected_profile = name
        if name in self.profile_items:
            self.profile_items[name].set_selected(True)
        
        self.selection_changed.emit(name)
    
    def get_profiles_data(self):
        """Get all profiles data for saving"""
        return self.profiles.copy()
    
    def load_profiles_data(self, profiles_dict):
        """Load profiles from data"""
        self.profiles = profiles_dict.copy()
        self.populate_profiles()
    
    def set_types_data(self, types_dict):
        """Set available types"""
        self.types = types_dict.copy()