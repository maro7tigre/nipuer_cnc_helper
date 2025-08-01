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
        self.selected_hinge = None
        self.selected_lock = None
        self.profiles_dir = "profiles"
        self.current_file = os.path.join(self.profiles_dir, "current.json")
        self.saved_dir = os.path.join(self.profiles_dir, "saved")
        self.projects_dir = "projects"  # New projects directory
        self._frame_gcode_data = {'gcode_right': '', 'gcode_left': ''}  # Initialize frame G-code data
        self.dollar_variables_info = {}  # Store $ variables info
        
        # Ensure directories exist
        os.makedirs(self.saved_dir, exist_ok=True)
        os.makedirs(self.projects_dir, exist_ok=True)
        
        self.setup_ui()
        self.apply_styling()
        self.connect_signals()
        self.load_current_profiles()
    
    def set_dollar_variables_info(self, dollar_variables_info):
        """Set available $ variables information"""
        self.dollar_variables_info = dollar_variables_info
        self.hinge_grid.set_dollar_variables_info(dollar_variables_info)
        self.lock_grid.set_dollar_variables_info(dollar_variables_info)
    
    def apply_styling(self):
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
        self.save_project_button.clicked.connect(self.save_project)
        toolbar_layout.addWidget(self.save_project_button)
        
        self.load_project_button = BlueButton("Load Project")
        self.load_project_button.clicked.connect(self.load_project)
        toolbar_layout.addWidget(self.load_project_button)
        
        toolbar_layout.addSpacing(20)
        
        # Profile set buttons (purple)
        self.save_button = PurpleButton("Save Set")
        self.save_button.clicked.connect(self.save_profile_set)
        toolbar_layout.addWidget(self.save_button)
        
        self.load_button = PurpleButton("Load Set")
        self.load_button.clicked.connect(self.load_profile_set)
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
                
                # Emit profiles modified signal to trigger border updates
                self.profiles_modified.emit()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load profile set: {str(e)}")
    
    def save_project(self):
        """Save complete project with selected profiles and frame config"""
        project_name, ok = QInputDialog.getText(self, "Save Project", "Enter project name:")
        if not ok or not project_name.strip():
            return
        
        project_name = project_name.strip()
        project_dir = os.path.join(self.projects_dir, project_name)
        
        if os.path.exists(project_dir):
            reply = QMessageBox.question(self, "Project Exists", 
                                       f"Project '{project_name}' already exists. Overwrite?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
            
            # Remove existing project directory
            shutil.rmtree(project_dir)
        
        try:
            os.makedirs(project_dir, exist_ok=True)
            
            # Save config.json with selected profiles and frame data
            config_data = {
                "selected_hinge": self.selected_hinge,
                "selected_lock": self.selected_lock,
                "profiles": self.get_current_data(),
                "timestamp": datetime.now().isoformat()
            }
            
            config_file = os.path.join(project_dir, "config.json")
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            QMessageBox.information(self, "Success", f"Project '{project_name}' saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project: {str(e)}")
    
    def load_project(self):
        """Load complete project"""
        project_name = QFileDialog.getExistingDirectory(
            self, "Select Project Directory", self.projects_dir
        )
        
        if not project_name:
            return
        
        config_file = os.path.join(project_name, "config.json")
        if not os.path.exists(config_file):
            QMessageBox.critical(self, "Error", "Invalid project: config.json not found.")
            return
        
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Load profile data
            profiles_data = config_data.get("profiles", {})
            self.load_profile_data(profiles_data)
            
            # Restore selections
            selected_hinge = config_data.get("selected_hinge")
            selected_lock = config_data.get("selected_lock")
            
            if selected_hinge:
                self.hinge_grid.on_item_clicked(selected_hinge)
            if selected_lock:
                self.lock_grid.on_item_clicked(selected_lock)
            
            # Save to current.json
            self.save_current_profiles()
            
            project_name_only = os.path.basename(project_name)
            QMessageBox.information(self, "Success", f"Project '{project_name_only}' loaded successfully!")
            
            # Emit profiles modified signal
            self.profiles_modified.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load project: {str(e)}")
    
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
        
        # Load frame G-code data
        self._frame_gcode_data = data.get("frame_gcode", {'gcode_right': '', 'gcode_left': ''})
    
    def save_frame_gcode_data(self, frame_gcode_data):
        """Save frame G-code data"""
        self._frame_gcode_data = frame_gcode_data
        self.save_current_profiles()
    
    def get_frame_gcode_data(self):
        """Get frame G-code data"""
        return self._frame_gcode_data