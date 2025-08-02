"""
Profile Grid Widget

Simplified scrollable grid that works with main_window data management.
"""

from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QGridLayout, QDialog, QMessageBox
from PySide6.QtCore import Signal, Qt
from ...widgets.themed_widgets import ThemedLabel
from .profile_item import ProfileItem


class ProfileGrid(QScrollArea):
    """Simplified profile grid that gets/sets data through main_window"""
    selection_changed = Signal(str)
    
    def __init__(self, profile_type, main_window=None, parent=None):
        super().__init__(parent)
        self.profile_type = profile_type  # "hinge" or "lock"
        self.main_window = main_window
        self.selected_profile = None
        self.profile_items = {}  # name -> ProfileItem widget
        
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
        
        # Initial population
        self.refresh_from_main_window()
    
    def set_dollar_variables_info(self, dollar_variables_info):
        """Set available $ variables information - called when main_window variables update"""
        # Nothing to do here since dialogs get data directly from main_window
        pass
    
    def refresh_from_main_window(self):
        """Refresh profiles from main_window data"""
        if not self.main_window:
            return
        
        # Get data from main_window
        if self.profile_type == "hinge":
            profiles = self.main_window.hinges_profiles
        else:
            profiles = self.main_window.locks_profiles
        
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
        for profile_name, profile_data in profiles.items():
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
        
        dialog = ProfileEditor(self.profile_type, parent=self)
        
        if dialog.exec_() == QDialog.Accepted:
            profile_data = dialog.get_profile_data()
            if profile_data and profile_data.get("name"):
                # Check if name already exists in main_window
                existing_profiles = (self.main_window.hinges_profiles if self.profile_type == "hinge" 
                                   else self.main_window.locks_profiles)
                
                if profile_data["name"] in existing_profiles:
                    QMessageBox.warning(self, "Name Exists", 
                                      f"A profile named '{profile_data['name']}' already exists.")
                    return
                
                # Add to main_window
                if self.profile_type == "hinge":
                    self.main_window.update_hinge_profile(profile_data["name"], profile_data)
                else:
                    self.main_window.update_lock_profile(profile_data["name"], profile_data)
    
    def edit_profile(self, name):
        """Edit existing profile"""
        # Get current profile data from main_window
        if self.profile_type == "hinge":
            current_data = self.main_window.get_hinge_profile(name)
        else:
            current_data = self.main_window.get_lock_profile(name)
        
        if not current_data:
            return
        
        from ...dialogs.profile_editor import ProfileEditor
        
        dialog = ProfileEditor(self.profile_type, current_data.copy(), parent=self)
        
        if dialog.exec_() == QDialog.Accepted:
            profile_data = dialog.get_profile_data()
            if profile_data and profile_data.get("name"):
                # Handle name change
                if profile_data["name"] != name:
                    existing_profiles = (self.main_window.hinges_profiles if self.profile_type == "hinge" 
                                       else self.main_window.locks_profiles)
                    
                    if profile_data["name"] in existing_profiles:
                        QMessageBox.warning(self, "Name Exists", 
                                          f"A profile named '{profile_data['name']}' already exists.")
                        return
                    
                    # Remove old profile and add new one
                    if self.profile_type == "hinge":
                        self.main_window.update_hinge_profile(name, None)  # Delete old
                        self.main_window.update_hinge_profile(profile_data["name"], profile_data)  # Add new
                    else:
                        self.main_window.update_lock_profile(name, None)  # Delete old
                        self.main_window.update_lock_profile(profile_data["name"], profile_data)  # Add new
                else:
                    # Update existing profile
                    if self.profile_type == "hinge":
                        self.main_window.update_hinge_profile(name, profile_data)
                    else:
                        self.main_window.update_lock_profile(name, profile_data)
    
    def duplicate_profile(self, name):
        """Duplicate existing profile"""
        # Get current profile data from main_window
        if self.profile_type == "hinge":
            current_data = self.main_window.get_hinge_profile(name)
        else:
            current_data = self.main_window.get_lock_profile(name)
        
        if not current_data:
            return
        
        from ...dialogs.profile_editor import ProfileEditor
        
        # Create copy with new name
        copy_data = current_data.copy()
        copy_data["name"] = f"{name} Copy"
        
        # Find unique name
        existing_profiles = (self.main_window.hinges_profiles if self.profile_type == "hinge" 
                           else self.main_window.locks_profiles)
        
        base_name = copy_data["name"]
        counter = 1
        while copy_data["name"] in existing_profiles:
            copy_data["name"] = f"{base_name} {counter}"
            counter += 1
        
        dialog = ProfileEditor(self.profile_type, copy_data, parent=self)
        
        if dialog.exec_() == QDialog.Accepted:
            profile_data = dialog.get_profile_data()
            if profile_data and profile_data.get("name"):
                # Check if name already exists
                if profile_data["name"] in existing_profiles:
                    QMessageBox.warning(self, "Name Exists", 
                                      f"A profile named '{profile_data['name']}' already exists.")
                    return
                
                # Add duplicated profile to main_window
                if self.profile_type == "hinge":
                    self.main_window.update_hinge_profile(profile_data["name"], profile_data)
                else:
                    self.main_window.update_lock_profile(profile_data["name"], profile_data)
    
    def delete_profile(self, name):
        """Delete profile after confirmation"""
        reply = QMessageBox.question(self, "Delete Profile", 
                                   f"Are you sure you want to delete '{name}'?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Remove from main_window
            if self.profile_type == "hinge":
                self.main_window.update_hinge_profile(name, None)
            else:
                self.main_window.update_lock_profile(name, None)
            
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
    
    def set_selection(self, profile_name):
        """Set the selected profile (called from parent)"""
        # Clear previous selection
        if self.selected_profile and self.selected_profile in self.profile_items:
            self.profile_items[self.selected_profile].set_selected(False)
        
        # Set new selection
        self.selected_profile = profile_name
        if profile_name and profile_name in self.profile_items:
            self.profile_items[profile_name].set_selected(True)