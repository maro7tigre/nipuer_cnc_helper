from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QInputDialog, QMessageBox, QFileDialog
from PySide6.QtCore import Qt, QSettings
from .profile.profile_tab import ProfileTab
from .frame.frame_tab import FrameTab
from .generate.generate_tab import GenerateTab
import json
import os
import re
import shutil
from datetime import datetime


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CNC Frame Wizard")
        
        # MARK: - Variables Initiation
        # Profile set dictionaries
        self.hinges_types = {}      # {type_name: {name, gcode, image, preview, variables}}
        self.locks_types = {}       # {type_name: {name, gcode, image, preview, variables}}
        self.hinges_profiles = {}   # {profile_name: {name, type, l_variables, custom_variables, image}}
        self.locks_profiles = {}    # {profile_name: {name, type, l_variables, custom_variables, image}}
        
        # Gcode dictionaries
        self.current_gcodes = {"hinge_gcode": None, "lock_gcode": None, "right_gcode": None, "left_gcode": None}
        self.processed_gcodes = {"hinge_gcode": None, "lock_gcode": None, "right_gcode": None, "left_gcode": None}
        self.generated_gcodes = {"hinge_gcode": None, "lock_gcode": None, "right_gcode": None, "left_gcode": None}
        
        # $variables dictionary
        self.dollar_variables = {
            "selected_hinge": None,
            "selected_lock": None,
            "frame_height": 2100,
            "frame_width": 1200,
            "machine_x_offset": 0,
            "machine_y_offset": 0,
            "machine_z_offset": 0,
            "pm1_position": -25,
            "pm2_position": 700,
            "pm3_position": 1230,
            "pm4_position": 1540,
            "lock_position": 1050,
            "lock_y_offset": 0,
            "lock_active": 1,
            "hinge_y_offset": 0,
            "orientation": "right",
            "hinge1_position": 0,
            "hinge2_position": 0,
            "hinge3_position": 0,
            "hinge4_position": 0,
            "hinge1_active": 0,
            "hinge2_active": 0,
            "hinge3_active": 0,
            "hinge4_active": 0,
            "lock_order": 0,
            "hinge1_order": 0,
            "hinge2_order": 0,
            "hinge3_order": 0,
            "hinge4_order": 0
        }
        
        # Initialize settings
        self.settings = QSettings("CNCFrameWizard", "AppConfig")
        
        self.default_config_init()
        
        # Setup UI
        self.setup_ui()
        
        # Load configurations
        self.load_app_config()
        self.load_profile_set()
        
    def default_config_init(self):
        """ Initialize default configurations if not set """
        self.profiles_dir = "profiles"
        self.current_file = os.path.join(self.profiles_dir, "current.json")
        self.saved_dir = os.path.join(self.profiles_dir, "saved")
        self.projects_dir = "projects" 
        
        # Ensure directories exist
        os.makedirs(self.saved_dir, exist_ok=True)
        os.makedirs(self.projects_dir, exist_ok=True)
    
    def setup_ui(self):
        """Setup user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Create tabs
        self.profile_tab = ProfileTab(self)
        self.frame_tab = FrameTab(self)
        self.generate_tab = GenerateTab(self)
        
        # Add tabs
        self.tabs.addTab(self.profile_tab, "Profile Selection")
        self.tabs.addTab(self.frame_tab, "Frame Setup")
        self.tabs.addTab(self.generate_tab, "Generate Files")
        
        # Initially disable tabs 2 and 3
        self.tabs.setTabEnabled(1, False)
        self.tabs.setTabEnabled(2, False)
        
        # Connect signals
        self.connect_signals()
        
        # Show window
        if not self.settings.contains("geometry"):
            self.showMaximized()
        else:
            self.show()
    
    # MARK: - Signals connecting
    def connect_signals(self):
        """Connect tab signals"""
        
        # Profile tab signals
        self.profile_tab.profiles_selected.connect(self.on_profiles_selected)
        self.profile_tab.profiles_modified.connect(self.on_profiles_modified)
        self.profile_tab.next_clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        
        self.profile_tab.save_project_button.clicked.connect(self.save_project)
        self.profile_tab.load_project_button.clicked.connect(self.load_project)
        self.profile_tab.save_button.clicked.connect(self.save_profile_set())
        self.profile_tab.load_button.clicked.connect(self.load_profile_set)
        
        # Frame tab signals
        self.frame_tab.back_clicked.connect(lambda: self.tabs.setCurrentIndex(0))
        self.frame_tab.next_clicked.connect(lambda: self.tabs.setCurrentIndex(2))
        self.frame_tab.configuration_changed.connect(self.on_frame_configured)
        self.frame_tab.frame_gcode_changed.connect(self.on_frame_gcode_changed)
        
        # Generate tab signals
        self.generate_tab.back_clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        self.generate_tab.generate_clicked.connect(self.generate_files)
    
    def closeEvent(self, event):
        """Save app configuration before closing"""
        self.save_app_config()
        event.accept()
    
    # MARK: - App Config
    def save_app_config(self):
        """Save application configuration"""
        try:
            config = {
                "geometry": self.saveGeometry().data().hex(),
                "windowState": self.saveState().data().hex()
            }
            
            # Get config from each tab
            if hasattr(self.profile_tab, 'get_app_config'):
                config["profile_tab"] = self.profile_tab.get_app_config()
            if hasattr(self.frame_tab, 'get_app_config'):
                config["frame_tab"] = self.frame_tab.get_app_config()
            if hasattr(self.generate_tab, 'get_app_config'):
                config["generate_tab"] = self.generate_tab.get_app_config()
            
            self.settings.setValue("app_config", json.dumps(config))
            self.settings.sync()
        except Exception as e:
            print(f"Error saving app config: {str(e)}")
    
    def load_app_config(self):
        """Load application configuration"""
        try:
            config_str = self.settings.value("app_config")
            if not config_str:
                return
            
            config = json.loads(config_str)
            
            # Restore window state
            if "geometry" in config:
                self.restoreGeometry(bytes.fromhex(config["geometry"]))
            if "windowState" in config:
                self.restoreState(bytes.fromhex(config["windowState"]))
            
            # Load config for each tab
            if hasattr(self.profile_tab, 'set_app_config') and "profile_tab" in config:
                self.profile_tab.set_app_config(config["profile_tab"])
            if hasattr(self.frame_tab, 'set_app_config') and "frame_tab" in config:
                self.frame_tab.set_app_config(config["frame_tab"])
            if hasattr(self.generate_tab, 'set_app_config') and "generate_tab" in config:
                self.generate_tab.set_app_config(config["generate_tab"])
        except Exception as e:
            print(f"Error loading app config: {str(e)}")
    
    # MARK: - Profile Set
    # TODO: add a parameter for when the user save or load a profile set while if none just save and load profiles/current.json
    def save_profile_set(self, current=False):
        """Save current profile set to current.json"""
        if current:
            filename = self.current_file
        else:
            # Default filename with date
            default_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.json")

            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Profile Set", 
                os.path.join(self.saved_dir, default_name),
                "JSON Files (*.json)"
            )
        if filename:
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                
                data = {
                    "hinges": {
                        "types": self.hinges_types,
                        "profiles": self.hinges_profiles
                    },
                    "locks": {
                        "types": self.locks_types,
                        "profiles": self.locks_profiles
                    },
                    "frame_gcode": {
                        "right_gcode": self.current_gcodes["right_gcode"],
                        "left_gcode": self.current_gcodes["left_gcode"]
                    }
                }
                
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                QMessageBox.information(self, "Success", "Profile set saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save profile set: {str(e)}")
    
    def load_profile_set(self, current=False):
        """Load profile set from current.json"""
        if current:
            filename = self.current_file
        else:
            filename, _ = QFileDialog.getOpenFileName(
                self, "Load Profile Set", 
                self.saved_dir,
                "JSON Files (*.json)"
            )
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                # Load types and profiles
                if "hinges" in data:
                    self.hinges_types = data["hinges"].get("types", {})
                    self.hinges_profiles = data["hinges"].get("profiles", {})
                if "locks" in data:
                    self.locks_types = data["locks"].get("types", {})
                    self.locks_profiles = data["locks"].get("profiles", {})
                # Load frame gcodes
                if "frame_gcode" in data:
                    self.current_gcodes["right_gcode"] = data["frame_gcode"].get("right_gcode")
                    self.current_gcodes["left_gcode"] = data["frame_gcode"].get("left_gcode")
            except Exception as e:
                print(f"Error loading profile set: {str(e)}")
    
    # MARK: - Project File
    def save_project(self):
        """Save project with $variables and generated gcodes"""
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
            
            data = {
                "dollar_variables": self.dollar_variables,
                "generated_gcodes": self.generated_gcodes,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(os.path.join(project_dir, "project.json"), 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving project: {str(e)}")
            return False
    
    def load_project(self):
        """Load complete project"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Project", 
            self.projects_dir,
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
        

                # Load $variables and generated gcodes
                if "dollar_variables" in data:
                    self.dollar_variables.update(data["dollar_variables"])
                if "generated_gcodes" in data:
                    self.generated_gcodes = data["generated_gcodes"]
                    
                
                #TODO: if profiles are selected enable second and if all frame tab configuration are valid enable third tab
                QMessageBox.information(self, "Success", "Profile set loaded successfully!")
                
                return True
        
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load profile set: {str(e)}")
            return False
    
    
    # MARK: - Update Variables
    def update_hinge_type(self, name, data=None):
        """Update hinge type (delete if data is None)"""
        if data is None:
            self.hinges_types.pop(name, None)
        else:
            self.hinges_types[name] = data
        self.save_profile_set()
    
    def update_lock_type(self, name, data=None):
        """Update lock type (delete if data is None)"""
        if data is None:
            self.locks_types.pop(name, None)
        else:
            self.locks_types[name] = data
        self.save_profile_set()
    
    def update_hinge_profile(self, name, data=None):
        """Update hinge profile (delete if data is None)"""
        if data is None:
            self.hinges_profiles.pop(name, None)
        else:
            self.hinges_profiles[name] = data
        self.save_profile_set()
    
    def update_lock_profile(self, name, data=None):
        """Update lock profile (delete if data is None)"""
        if data is None:
            self.locks_profiles.pop(name, None)
        else:
            self.locks_profiles[name] = data
        self.save_profile_set()
    
    def update_current_gcode(self, name, gcode):
        """Update current gcode and trigger processing"""
        if name in self.current_gcodes:
            self.current_gcodes[name] = gcode
            self.process_gcodes()
    
    def process_gcodes(self):
        """Process current gcodes with $variables"""
        for name, gcode in self.current_gcodes.items():
            if gcode:
                processed = self.replace_dollar_variables(gcode)
                self.processed_gcodes[name] = processed
    
    def copy_to_generated(self):
        """Copy processed gcodes to generated"""
        self.generated_gcodes = self.processed_gcodes.copy()
        
    def update_generated_gcode(self, name, gcode):
        """Update generated gcode"""
        if name in self.generated_gcodes:
            self.generated_gcodes[name] = gcode
    
    def update_dollar_variable(self, name, value):
        """Update $variable"""
        self.dollar_variables[name] = value
        self.process_gcodes()
    
    # MARK: - Get Variables 
    def get_hinge_type(self, name):
        """Get hinge type data"""
        return self.hinges_types.get(name)
    
    def get_lock_type(self, name):
        """Get lock type data"""
        return self.locks_types.get(name)
    
    def get_hinge_profile(self, name):
        """Get hinge profile data"""
        return self.hinges_profiles.get(name)
    
    def get_lock_profile(self, name):
        """Get lock profile data"""
        return self.locks_profiles.get(name)
    
    def get_hinge_profile_gcode(self, name):
        """Get hinge profile gcode"""
        #TODO: get the selected type of the profile, get the gcode of the type and replace the L and custom variables
    
    def get_lock_profile_gcode(self, name):
        """Get lock profile gcode"""
        #TODO
    
    def get_current_gcode(self, name):
        """Get current gcode"""
        return self.current_gcodes.get(name)
    
    def get_processed_gcode(self, name):
        """Get processed gcode"""
        return self.processed_gcodes.get(name)
    
    def get_generated_gcode(self, name):
        """Get generated gcode"""
        return self.generated_gcodes.get(name)
    
    def get_dollar_variable(self, name=None):
        """Get $variable or all $variables if name is None"""
        if name is None:
            return self.dollar_variables.copy()
        elif name in self.dollar_variables:
            return self.dollar_variables.get(name)
        else:
            return "" # Return empty string if variable not found
    
    # MARK: - Helper
    def replace_dollar_variables(self, gcode):
        """Replace $variables in gcode with actual values"""
        if not gcode:
            return gcode
        
        result = gcode
        for var_name, value in self.dollar_variables.items():
            pattern = f"{{\\${var_name}}}"
            if value is not None:
                result = re.sub(pattern, str(value), result)
        return result
    
    # MARK: - Event Handlers
    def on_profiles_selected(self, hinge_profile, lock_profile):
        """Handle profile selection"""
        self.update_dollar_variable("selected_hinge", hinge_profile)
        self.update_dollar_variable("selected_lock", lock_profile)
        
        # Update current gcodes from selected profiles
        hinge_data = self.get_hinge_profile(hinge_profile)
        lock_data = self.get_lock_profile(lock_profile)
        
        if hinge_data and hinge_data.get("type"):
            hinge_type = self.get_hinge_type(hinge_data["type"])
            if hinge_type:
                self.update_current_gcode("hinge_gcode", hinge_type.get("gcode"))
        
        if lock_data and lock_data.get("type"):
            lock_type = self.get_lock_type(lock_data["type"])
            if lock_type:
                self.update_current_gcode("lock_gcode", lock_type.get("gcode"))
        
        self.tabs.setTabEnabled(1, True)
    
    def on_profiles_modified(self):
        """Handle profile modifications"""
        self.save_profile_set()
    
    def on_frame_configured(self, frame_data):
        """Handle frame configuration changes"""
        # Update $variables from frame data
        if "dollar_variables" in frame_data:
            for name, value in frame_data["dollar_variables"].items():
                self.update_dollar_variable(name, value)
        
        self.tabs.setTabEnabled(2, True)
    
    def on_frame_gcode_changed(self, frame_gcode_data):
        """Handle frame gcode changes"""
        if "gcode_right" in frame_gcode_data:
            self.update_current_gcode("right_gcode", frame_gcode_data["gcode_right"])
        if "gcode_left" in frame_gcode_data:
            self.update_current_gcode("left_gcode", frame_gcode_data["gcode_left"])
    
    def generate_files(self):
        """Generate final gcode files"""        
        # Copy processed to generated
        self.copy_to_generated()
        
        # Update generate tab display
        self.generate_tab.update_files_from_main_window()
        
        print("Files generated successfully!")