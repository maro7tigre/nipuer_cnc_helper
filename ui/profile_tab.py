from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                             QLabel, QScrollArea, QGridLayout, QFrame, QSplitter,
                             QMenu, QFileDialog, QMessageBox, QDialog)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QAction
import json
import os
from datetime import datetime
from .profile_editor import ProfileEditor, TypeSelector


class ProfileItem(QFrame):
    """Individual profile item widget with Python-controlled styling"""
    clicked = Signal(str)
    edit_requested = Signal(str)
    duplicate_requested = Signal(str)
    delete_requested = Signal(str)
    
    def __init__(self, name, profile_data=None, is_add_button=False):
        super().__init__()
        self.name = name
        self.profile_data = profile_data or {}
        self.is_add_button = is_add_button
        self.selected = False
        self._is_hovered = False
        
        self.setFixedSize(120, 140)
        self.setCursor(Qt.PointingHandCursor)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Image placeholder
        self.image_label = QLabel()
        self.image_label.setFixedSize(100, 100)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(True)
        
        # Create or load image
        self.update_image()
        
        layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
        
        # Name label
        self.name_label = QLabel(name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("QLabel { color: #ffffff; background-color: transparent; }")
        layout.addWidget(self.name_label)
        
        # Set initial style
        self.update_style()
    
    def update_image(self):
        """Update the displayed image"""
        pixmap = QPixmap(100, 100)
        
        if self.is_add_button:
            # Draw plus sign for add button
            pixmap.fill(QColor("#44475c"))
            painter = QPainter(pixmap)
            painter.setPen(QColor("#bdbdc0"))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "+")
            painter.end()
        elif self.profile_data.get("image"):
            # Load profile image
            loaded_pixmap = QPixmap(self.profile_data["image"])
            if not loaded_pixmap.isNull():
                pixmap = loaded_pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                pixmap.fill(QColor("#44475c"))
                painter = QPainter(pixmap)
                painter.setPen(QColor("#bdbdc0"))
                painter.drawText(pixmap.rect(), Qt.AlignCenter, "📄")
                painter.end()
        else:
            # Default profile icon
            pixmap.fill(QColor("#44475c"))
            painter = QPainter(pixmap)
            painter.setPen(QColor("#bdbdc0"))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "📄")
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
                ProfileItem {
                    background-color: #1A2E20;
                    border: 3px solid #23c87b;
                    border-radius: 4px;
                }
            """)
        elif self._is_hovered:
            # Hover state
            self.setStyleSheet("""
                ProfileItem {
                    background-color: #3a3d4d;
                    border: 2px solid #8b95c0;
                    border-radius: 4px;
                }
            """)
        else:
            # Default state
            self.setStyleSheet("""
                ProfileItem {
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
        """Handle mouse clicks"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.name)
        elif event.button() == Qt.RightButton and not self.is_add_button:
            # Show context menu for non-add buttons
            self.show_context_menu(event.globalPos())
    
    def show_context_menu(self, pos):
        """Show right-click context menu"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1d1f28;
                color: #ffffff;
                border: 1px solid #6f779a;
                border-radius: 4px;
            }
            QMenu::item {
                background-color: transparent;
                padding: 6px 16px;
            }
            QMenu::item:selected {
                background-color: #6f779a;
            }
        """)
        
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


class ProfileGrid(QScrollArea):
    """Scrollable grid container for profile items with Python styling"""
    selection_changed = Signal(str)
    data_modified = Signal()
    
    def __init__(self, profile_type):
        super().__init__()
        self.profile_type = profile_type  # "hinge" or "lock"
        self.selected_profile = None
        self.profiles = {}  # name -> profile_data
        self.profile_items = {}  # name -> ProfileItem widget
        self.types = {}  # Store types data
        
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
        title = QLabel(f"{profile_type.capitalize()} Profiles")
        title.setStyleSheet("""
            QLabel {
                font-size: 16px; 
                font-weight: bold; 
                padding: 10px; 
                color: #ffffff;
                background-color: transparent;
            }
        """)
        main_layout.addWidget(title)
        
        # Grid layout for items
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        main_layout.addLayout(self.grid_layout)
        main_layout.addStretch()
    
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
        dialog = ProfileEditor(self.profile_type)
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
        
        # Get current profile data
        current_data = self.profiles[name].copy()
        
        dialog = ProfileEditor(self.profile_type, current_data)
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
        
        # Create copy with new name
        copy_data = self.profiles[name].copy()
        copy_data["name"] = f"{name} Copy"
        
        # Find unique name
        base_name = copy_data["name"]
        counter = 1
        while copy_data["name"] in self.profiles:
            copy_data["name"] = f"{base_name} {counter}"
            counter += 1
        
        dialog = ProfileEditor(self.profile_type, copy_data)
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


class ProfileTab(QWidget):
    """Main profile selection tab with split view and Python styling"""
    profiles_selected = Signal(str, str)  # hinge_profile, lock_profile
    next_clicked = Signal()
    
    def __init__(self):
        super().__init__()
        self.selected_hinge = None
        self.selected_lock = None
        self.profiles_dir = "profiles"
        self.current_file = os.path.join(self.profiles_dir, "current.json")
        self.saved_dir = os.path.join(self.profiles_dir, "saved")
        
        # Ensure directories exist
        os.makedirs(self.saved_dir, exist_ok=True)
        
        self.setup_ui()
        self.apply_styling()
        self.connect_signals()
        self.load_current_profiles()
    
    def apply_styling(self):
        """Apply Python-based styling to the tab"""
        self.setStyleSheet("""
            ProfileTab {
                background-color: #282a36;
                color: #ffffff;
            }
            ProfileTab QPushButton {
                background-color: #1d1f28;
                color: #BB86FC;
                border: 2px solid #BB86FC;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
            }
            ProfileTab QPushButton:hover {
                background-color: #000000;
                color: #9965DA;
                border: 2px solid #9965DA;
            }
            ProfileTab QPushButton:pressed {
                background-color: #BB86FC;
                color: #1d1f28;
            }
            ProfileTab QPushButton:disabled {
                background-color: #1d1f28;
                color: #6f779a;
                border: 2px solid #6f779a;
            }
            ProfileTab QLabel {
                color: #ffffff;
                background-color: transparent;
            }
            ProfileTab QSplitter::handle {
                background-color: #44475c;
            }
            ProfileTab QSplitter::handle:horizontal {
                width: 4px;
            }
            ProfileTab QSplitter::handle:hover {
                background-color: #BB86FC;
            }
        """)
    
    def setup_ui(self):
        """Initialize user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Top toolbar
        toolbar_layout = QHBoxLayout()
        layout.addLayout(toolbar_layout)
        
        # Save/Load buttons
        self.save_button = QPushButton("Save Set")
        self.save_button.clicked.connect(self.save_profile_set)
        toolbar_layout.addWidget(self.save_button)
        
        self.load_button = QPushButton("Load Set")
        self.load_button.clicked.connect(self.load_profile_set)
        toolbar_layout.addWidget(self.load_button)
        
        toolbar_layout.addStretch()
        
        # Profile grids with splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter, 1)
        
        # Create hinge and lock grids
        self.hinge_grid = ProfileGrid("hinge")
        self.lock_grid = ProfileGrid("lock")
        
        splitter.addWidget(self.hinge_grid)
        splitter.addWidget(self.lock_grid)
        
        # Set initial splitter sizes (50/50)
        splitter.setSizes([400, 400])
        
        # Bottom controls
        bottom_layout = QHBoxLayout()
        layout.addLayout(bottom_layout)
        
        self.selection_label = QLabel("Selected: [Hinge: None] [Lock: None]")
        self.selection_label.setStyleSheet("QLabel { font-weight: bold; padding: 5px; color: #ffffff; background-color: transparent; }")
        bottom_layout.addWidget(self.selection_label)
        
        bottom_layout.addStretch()
        
        self.next_button = QPushButton("Next →")
        self.next_button.setEnabled(False)
        # Style the next button as green when enabled
        self.next_button.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #1d1f28;
                color: #6f779a;
                border: 2px solid #6f779a;
            }
        """)
        bottom_layout.addWidget(self.next_button)
    
    def connect_signals(self):
        """Connect widget signals"""
        self.hinge_grid.selection_changed.connect(self.on_hinge_selected)
        self.lock_grid.selection_changed.connect(self.on_lock_selected)
        self.hinge_grid.data_modified.connect(self.save_current_profiles)
        self.lock_grid.data_modified.connect(self.save_current_profiles)
        self.next_button.clicked.connect(self.on_next_clicked)
    
    def on_hinge_selected(self, name):
        """Handle hinge profile selection"""
        self.selected_hinge = name if name else None
        self.update_selection_display()
        self.save_current_profiles()
    
    def on_lock_selected(self, name):
        """Handle lock profile selection"""
        self.selected_lock = name if name else None
        self.update_selection_display()
        self.save_current_profiles()
    
    def update_selection_display(self):
        """Update selection display and controls"""
        hinge_text = self.selected_hinge or "None"
        lock_text = self.selected_lock or "None"
        self.selection_label.setText(f"Selected: [Hinge: {hinge_text}] [Lock: {lock_text}]")
        
        # Enable next button when both profiles selected
        both_selected = bool(self.selected_hinge and self.selected_lock)
        self.next_button.setEnabled(both_selected)
    
    def on_next_clicked(self):
        """Handle next button click"""
        if self.selected_hinge and self.selected_lock:
            self.profiles_selected.emit(self.selected_hinge, self.selected_lock)
            self.next_clicked.emit()
    
    def load_current_profiles(self):
        """Load current.json on startup"""
        if os.path.exists(self.current_file):
            try:
                # Check if file is empty or invalid
                if os.path.getsize(self.current_file) == 0:
                    print("Current profiles file is empty, creating default")
                    self.create_default_current()
                    return
                
                with open(self.current_file, 'r') as f:
                    content = f.read()
                    if not content.strip():
                        print("Current profiles file is empty, creating default")
                        self.create_default_current()
                        return
                    
                    data = json.loads(content)
                
                self.load_profile_data(data)
            except json.JSONDecodeError as e:
                print(f"Error parsing current profiles JSON: {str(e)}")
                self.create_default_current()
            except Exception as e:
                print(f"Error loading current profiles: {str(e)}")
                self.create_default_current()
        else:
            # Create default current.json
            self.create_default_current()
    
    def create_default_current(self):
        """Create default current.json file"""
        default_data = {
            "hinges": {
                "types": {},
                "profiles": {}
            },
            "locks": {
                "types": {},
                "profiles": {}
            },
            "selected_hinge": None,
            "selected_lock": None
        }
        
        with open(self.current_file, 'w') as f:
            json.dump(default_data, f, indent=2)
        
        self.load_profile_data(default_data)
    
    def save_current_profiles(self):
        """Save current state to current.json"""
        data = self.get_current_data()
        
        try:
            with open(self.current_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving current profiles: {str(e)}")
    
    def get_current_data(self):
        """Get current data including types"""
        data = {
            "hinges": {
                "types": self.hinge_grid.types,
                "profiles": self.hinge_grid.get_profiles_data()
            },
            "locks": {
                "types": self.lock_grid.types,
                "profiles": self.lock_grid.get_profiles_data()
            },
            "selected_hinge": self.selected_hinge,
            "selected_lock": self.selected_lock
        }
        
        return data
    
    def save_profile_set(self):
        """Save current profile set to file"""
        # Default filename with date
        default_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.json")
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Profile Set", 
            os.path.join(self.saved_dir, default_name),
            "JSON Files (*.json)"
        )
        
        if filename:
            data = self.get_current_data()
            
            try:
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                QMessageBox.information(self, "Success", "Profile set saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save profile set: {str(e)}")
    
    def load_profile_set(self):
        """Load profile set from file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Profile Set", 
            self.saved_dir,
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                self.load_profile_data(data)
                self.save_current_profiles()  # Update current.json
                
                QMessageBox.information(self, "Success", "Profile set loaded successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load profile set: {str(e)}")
    
    def load_profile_data(self, data):
        """Load profile data into UI"""
        # Load types
        if "hinges" in data:
            hinge_types = data["hinges"].get("types", {})
            self.hinge_grid.set_types_data(hinge_types)
            self.hinge_grid.load_profiles_data(data["hinges"].get("profiles", {}))
        
        if "locks" in data:
            lock_types = data["locks"].get("types", {})
            self.lock_grid.set_types_data(lock_types)
            self.lock_grid.load_profiles_data(data["locks"].get("profiles", {}))
        
        # Restore selection
        if data.get("selected_hinge"):
            self.hinge_grid.on_item_clicked(data["selected_hinge"])
        if data.get("selected_lock"):
            self.lock_grid.on_item_clicked(data["selected_lock"])