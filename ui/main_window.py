from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from .profile_tab import ProfileTab
from .frame_tab import FrameTab
from .generate_tab import GenerateTab


class MainWindow(QMainWindow):
    # MARK: - Initialization
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CNC Frame Wizard")
        
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
        
        # Add tabs
        self.tabs.addTab(self.profile_tab, "Profile Selection")
        self.tabs.addTab(self.frame_tab, "Frame Setup")
        self.tabs.addTab(self.generate_tab, "Generate Files")
        
        # Initially disable tabs 2 and 3
        self.tabs.setTabEnabled(1, True)
        self.tabs.setTabEnabled(2, True)
        
        # Connect signals
        self.profile_tab.profiles_selected.connect(self.on_profiles_selected)
        self.profile_tab.next_clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        
        self.frame_tab.back_clicked.connect(lambda: self.tabs.setCurrentIndex(0))
        self.frame_tab.next_clicked.connect(lambda: self.tabs.setCurrentIndex(2))
        self.frame_tab.configuration_changed.connect(self.on_frame_configured)
        
        self.generate_tab.back_clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        self.generate_tab.generate_clicked.connect(self.generate_files)
        
        # Show window maximized
        self.showMaximized()
        
    # MARK: - Event Handlers
    def on_profiles_selected(self, hinge_profile, lock_profile):
        """Enable frame tab when profiles are selected"""
        if hinge_profile and lock_profile:
            self.tabs.setTabEnabled(1, True)
            # Pass selected profiles to frame tab
            self.frame_tab.set_profiles(hinge_profile, lock_profile)
            # Update generate tab
            self.generate_tab.set_profiles(hinge_profile, lock_profile)
    
    # MARK: - Configuration
    def on_frame_configured(self, frame_data):
        """Enable generate tab when frame is configured"""
        self.tabs.setTabEnabled(2, True)
        # Pass frame data to generate tab
        self.generate_tab.set_frame_data(frame_data)
    
    # MARK: - File Operations
    def generate_files(self):
        """Generate G-code files"""
        # TODO: Implement actual file generation
        print("Generating files...")