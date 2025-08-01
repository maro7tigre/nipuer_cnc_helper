from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QSettings
from .profile.profile_tab import ProfileTab
from .frame.frame_tab import FrameTab
from .generate.generate_tab import GenerateTab
import json
import os
import re
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
        
        # Setup UI
        self.setup_ui()
        
        # Load configurations
        self.load_app_config()
        self.load_profile_set()
    
    def setup_ui(self):
        """Setup user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Create tabs
        self.profile_tab = ProfileTab()
        self.frame_tab = FrameTab()
        self.generate_tab = GenerateTab()
        
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
    
    def connect_signals(self):
        """Connect tab signals"""
        # Set main window references for all tabs
        self.profile_tab.set_main_window(self)
        self.frame_tab.set_main_window(self)
        self.generate_tab.set_main_window(self)
        
        # Profile tab signals
        self.profile_tab.profiles_selected.connect(self.on_profiles_selected)
        self.profile_tab.profiles_modified.connect(self.on_profiles_modified)
        self.profile_tab.next_clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        
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
    
    # MARK: - App Config Methods
    def save_app_config(self):
        """Save application configuration"""
        try:
            config = {
                "geometry": self.saveGeometry().data().hex(),
                "windowState": self.saveState().data().hex(),
                "current_tab": self.tabs.currentIndex()
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
            
            # Restore tab index
            if "current_tab" in config:
                tab_index = config["current_tab"]
                if 0 <= tab_index < self.tabs.count() and self.tabs.isTabEnabled(tab_index):
                    self.tabs.setCurrentIndex(tab_index)
        except Exception as e:
            print(f"Error loading app config: {str(e)}")
    
    # MARK: - Profile Set Methods
    def save_profile_set(self):
        """Save current profile set to current.json"""
        try:
            os.makedirs("profiles", exist_ok=True)
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
            
            with open("profiles/current.json", 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving profile set: {str(e)}")
    
    def load_profile_set(self):
        """Load profile set from current.json"""
        try:
            if os.path.exists("profiles/current.json"):
                with open("profiles/current.json", 'r') as f:
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
    
    # MARK: - Project File Methods
    def save_project(self, project_name):
        """Save project with $variables and generated gcodes"""
        try:
            os.makedirs("projects", exist_ok=True)
            project_dir = os.path.join("projects", project_name)
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
    
    def load_project(self, project_path):
        """Load project from project.json"""
        try:
            project_file = os.path.join(project_path, "project.json")
            if os.path.exists(project_file):
                with open(project_file, 'r') as f:
                    data = json.load(f)
                
                # Load $variables and generated gcodes
                if "dollar_variables" in data:
                    self.dollar_variables.update(data["dollar_variables"])
                if "generated_gcodes" in data:
                    self.generated_gcodes = data["generated_gcodes"]
                return True
        except Exception as e:
            print(f"Error loading project: {str(e)}")
        return False
    
    # MARK: - Update Variables Methods
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
    
    def update_dollar_variable(self, name, value):
        """Update $variable"""
        self.dollar_variables[name] = value
        self.process_gcodes()
    
    # MARK: - Get Variables Methods  
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
        return self.dollar_variables.get(name)
    
    # MARK: - Helper Methods
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
        # Check if we have required data
        selected_hinge = self.get_dollar_variable("selected_hinge")
        selected_lock = self.get_dollar_variable("selected_lock")
        
        if not selected_hinge or not selected_lock:
            print("Missing profile selections")
            return
        
        # Get profile data
        hinge_profile = self.get_hinge_profile(selected_hinge)
        lock_profile = self.get_lock_profile(selected_lock)
        
        if not hinge_profile or not lock_profile:
            print("Profile data not found")
            return
        
        # Get type data
        hinge_type_name = hinge_profile.get('type')
        lock_type_name = lock_profile.get('type')
        
        if not hinge_type_name or not lock_type_name:
            print("Profile types not found")
            return
        
        hinge_type = self.get_hinge_type(hinge_type_name)
        lock_type = self.get_lock_type(lock_type_name)
        
        if not hinge_type or not lock_type:
            print("Type data not found")
            return
        
        # Update current gcodes with profile and variable substitution
        self.update_current_gcode("hinge_gcode", self.substitute_profile_variables(hinge_type.get('gcode', ''), hinge_profile))
        self.update_current_gcode("lock_gcode", self.substitute_profile_variables(lock_type.get('gcode', ''), lock_profile))
        
        # Copy processed to generated
        self.copy_to_generated()
        
        # Update generate tab display
        self.generate_tab.update_files_from_main_window()
        
        print("Files generated successfully!")
    
    def substitute_profile_variables(self, gcode, profile):
        """Substitute L and custom variables in gcode with profile values"""
        if not gcode or not profile:
            return gcode
        
        result = gcode
        
        # Substitute L variables
        l_variables = profile.get('l_variables', {})
        for var_name, value in l_variables.items():
            pattern = r'\{' + re.escape(var_name) + r'(?::[^}]*)?\}'
            result = re.sub(pattern, str(value), result)
        
        # Substitute custom variables
        custom_variables = profile.get('custom_variables', {})
        for var_name, value in custom_variables.items():
            pattern = r'\{' + re.escape(var_name) + r'(?::[^}]*)?\}'
            result = re.sub(pattern, str(value), result)
        
        return result