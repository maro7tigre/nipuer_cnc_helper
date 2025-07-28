from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from .profile_tab import ProfileTab
from .frame_tab import FrameTab
from .generate_tab import GenerateTab
from gcode_generator import GCodeGenerator


class MainWindow(QMainWindow):
    # MARK: - Initialization
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CNC Frame Wizard")
        
        # Create G-code generator
        self.generator = GCodeGenerator()
        
        # Create central widget and layout
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
        
        # Set generator for generate tab
        self.generate_tab.set_generator(self.generator)
        
        # Add tabs
        self.tabs.addTab(self.profile_tab, "Profile Selection")
        self.tabs.addTab(self.frame_tab, "Frame Setup")
        self.tabs.addTab(self.generate_tab, "Generate Files")
        
        # Initially disable tabs 2 and 3
        self.tabs.setTabEnabled(1, False)
        self.tabs.setTabEnabled(2, False)
        
        # Connect signals
        self.profile_tab.profiles_selected.connect(self.on_profiles_selected)
        self.profile_tab.profiles_modified.connect(self.on_profiles_modified)
        self.profile_tab.next_clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        
        self.frame_tab.back_clicked.connect(lambda: self.tabs.setCurrentIndex(0))
        self.frame_tab.next_clicked.connect(lambda: self.tabs.setCurrentIndex(2))
        self.frame_tab.configuration_changed.connect(self.on_frame_configured)
        self.frame_tab.frame_gcode_changed.connect(self.on_frame_gcode_changed)
        
        self.generate_tab.back_clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        self.generate_tab.generate_clicked.connect(self.generate_files)
        
        # Show window maximized
        self.showMaximized()
        
    # MARK: - Event Handlers
    def on_profiles_selected(self, hinge_profile, lock_profile):
        """Enable frame tab when profiles are selected and update generator"""
        if hinge_profile and lock_profile:
            self.tabs.setTabEnabled(1, True)
            
            # Get profile data from profile tab
            hinge_data = self.profile_tab.hinge_grid.profiles.get(hinge_profile, {})
            lock_data = self.profile_tab.lock_grid.profiles.get(lock_profile, {})
            
            # Pass selected profiles to frame tab
            self.frame_tab.set_profiles(hinge_profile, lock_profile)
            self.frame_tab.set_profile_data(hinge_data, lock_data)
            
            # Update generator with profile data
            self.generator.update_profiles(hinge_data, lock_data)
            
            # Update generate tab
            self.generate_tab.set_profiles(hinge_data, lock_data)
            
            # Load frame G-code data from profile tab
            frame_gcode_data = self.profile_tab.get_frame_gcode_data()
            self.frame_tab.set_frame_gcode_data(frame_gcode_data)
            
            # Update $ variables info immediately after profiles are selected
            self.update_dollar_variables_in_editors()
    
    def on_frame_gcode_changed(self, frame_gcode_data):
        """Handle frame G-code changes and save to current.json"""
        # Save frame G-code to profile tab (which handles current.json)
        self.profile_tab.save_frame_gcode_data(frame_gcode_data)
        
        # Update generator with new frame data
        frame_data = self.frame_tab.get_configuration()
        self.generator.update_frame_config(frame_data)
    
    def on_profiles_modified(self):
        """Handle when profiles are modified (selection or data changes)"""
        # Update generator with current profile data if both profiles are selected
        if self.profile_tab.selected_hinge and self.profile_tab.selected_lock:
            hinge_data = self.profile_tab.hinge_grid.profiles.get(self.profile_tab.selected_hinge, {})
            lock_data = self.profile_tab.lock_grid.profiles.get(self.profile_tab.selected_lock, {})
            
            # Update generator with new profile data
            self.generator.update_profiles(hinge_data, lock_data)
    
    # MARK: - Configuration
    def on_frame_configured(self, frame_data):
        """Enable generate tab when frame is configured and update generator"""
        self.tabs.setTabEnabled(2, True)
        
        # Update generator with frame configuration
        self.generator.update_frame_config(frame_data)
        
        # Pass frame data to generate tab
        self.generate_tab.set_frame_data(frame_data)
        
        # Update all G-code editors with $ variable information
        self.update_dollar_variables_in_editors()
    
    def update_dollar_variables_in_editors(self):
        """Update all G-code editors with available $ variables"""
        dollar_vars_info = self.generator.get_dollar_variables_info()
        
        # Update frame tab with $ variables info
        self.frame_tab.set_dollar_variables_info(dollar_vars_info)
        
        # Update generate tab's file items (if it has this method)
        if hasattr(self.generate_tab, 'update_dollar_variables_in_items'):
            self.generate_tab.update_dollar_variables_in_items(dollar_vars_info)
    
    # MARK: - File Operations
    def generate_files(self):
        """Generate G-code files using the generator"""
        # Force regeneration
        self.generator.regenerate_all()
        print("Files generated successfully!")