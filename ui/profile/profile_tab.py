"""
Profile Tab

Main profile selection tab with project save/load functionality.
Now simplified using extracted widgets.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QInputDialog, QMessageBox, QFileDialog
from PySide6.QtCore import Signal, Qt
from datetime import datetime
import json
import os
import shutil

from ..widgets.themed_widgets import ThemedSplitter, ThemedLabel, BlueButton, PurpleButton, GreenButton
from .widgets.profile_grid import ProfileGrid


class ProfileTab(QWidget):
    """Main profile selection tab with project save/load functionality"""
    profiles_selected = Signal(str, str)  # hinge_profile, lock_profile
    next_clicked = Signal()
    profiles_modified = Signal()  # Signal for when profiles are modified
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.selected_hinge = None # ?
        self.selected_lock = None # ?


        self.setup_ui()
        self.apply_styling()
        self.connect_signals()
        self.load_current_profiles()
    
    def apply_styling(self): # TODO: Move to theme manager
        """Apply dark theme styling"""
        self.setStyleSheet("""
            ProfileTab {
                background-color: #282a36;
                color: #ffffff;
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
        
        # Project buttons (blue)
        self.save_project_button = BlueButton("Save Project")
        toolbar_layout.addWidget(self.save_project_button)
        
        self.load_project_button = BlueButton("Load Project")
        toolbar_layout.addWidget(self.load_project_button)
        
        toolbar_layout.addSpacing(20)
        
        # Profile set buttons (purple)
        self.save_button = PurpleButton("Save Set")
        toolbar_layout.addWidget(self.save_button)
        
        self.load_button = PurpleButton("Load Set")
        toolbar_layout.addWidget(self.load_button)
        
        toolbar_layout.addStretch()
        
        # Profile grids with splitter
        splitter = ThemedSplitter(Qt.Horizontal)
        layout.addWidget(splitter, 1)
        
        # Create hinge and lock grids
        self.hinge_grid = ProfileGrid("hinge", self.dollar_variables_info)
        self.lock_grid = ProfileGrid("lock", self.dollar_variables_info)
        
        splitter.addWidget(self.hinge_grid)
        splitter.addWidget(self.lock_grid)
        
        # Set initial splitter sizes (50/50)
        splitter.setSizes([400, 400])
        
        # Bottom controls
        bottom_layout = QHBoxLayout()
        layout.addLayout(bottom_layout)
        
        self.selection_label = ThemedLabel("Selected: [Hinge: None] [Lock: None]")
        self.selection_label.setStyleSheet("QLabel { font-weight: bold; padding: 5px; }")
        bottom_layout.addWidget(self.selection_label)
        
        bottom_layout.addStretch()
        
        self.next_button = GreenButton("Next →")
        self.next_button.setEnabled(False)
        bottom_layout.addWidget(self.next_button)
    
    def connect_signals(self):
        """Connect widget signals"""
        self.hinge_grid.selection_changed.connect(self.on_hinge_selected)
        self.lock_grid.selection_changed.connect(self.on_lock_selected)
        self.hinge_grid.data_modified.connect(self.on_profiles_modified)
        self.lock_grid.data_modified.connect(self.on_profiles_modified)
        self.next_button.clicked.connect(self.on_next_clicked)
    
    def on_hinge_selected(self, name):
        """Handle hinge profile selection"""
        self.selected_hinge = name if name else None
        self.update_selection_display()
        self.save_current_profiles()
        # Emit profiles modified signal to trigger border updates
        self.profiles_modified.emit()
    
    def on_lock_selected(self, name):
        """Handle lock profile selection"""
        self.selected_lock = name if name else None
        self.update_selection_display()
        self.save_current_profiles()
        # Emit profiles modified signal to trigger border updates
        self.profiles_modified.emit()
    
    def on_profiles_modified(self):
        """Handle when profile data is modified"""
        self.save_current_profiles()
        # Emit signal to notify main window that profiles changed
        self.profiles_modified.emit()
    
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
            "frame_gcode": {
                "gcode_right": "",
                "gcode_left": ""
            }
        }
        
        with open(self.current_file, 'w') as f:
            json.dump(default_data, f, indent=2)
        
        self.load_profile_data(default_data)
    
    def save_current_profiles(self):
        """Save current state to current.json (without selected profiles)"""
        data = self.get_current_data()
        
        try:
            with open(self.current_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving current profiles: {str(e)}")
    
    def get_current_data(self):
        """Get current data including types and frame G-code (without selections)"""
        data = {
            "hinges": {
                "types": self.hinge_grid.types,
                "profiles": self.hinge_grid.get_profiles_data()
            },
            "locks": {
                "types": self.lock_grid.types,
                "profiles": self.lock_grid.get_profiles_data()
            },
            "frame_gcode": self._frame_gcode_data
        }
        
        return data
    
    def save_frame_gcode_data(self, frame_gcode_data):
        """Save frame G-code data"""
        self._frame_gcode_data = frame_gcode_data
        self.save_current_profiles()
    
    def get_frame_gcode_data(self):
        """Get frame G-code data"""
        return self._frame_gcode_data
    
    def set_main_window(self, main_window):
        pass