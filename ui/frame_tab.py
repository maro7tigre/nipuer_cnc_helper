from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                             QLabel, QLineEdit, QComboBox, QCheckBox,
                             QGroupBox, QFormLayout)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QDoubleValidator


class FrameTab(QWidget):
    """Frame configuration tab"""
    back_clicked = Signal()
    next_clicked = Signal()
    configuration_changed = Signal(dict)
    
    # MARK: - Initialization
    def __init__(self):
        super().__init__()
        self.hinge_positions = []
        self.profiles = {}
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Initialize user interface"""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Content area (left config, right visual)
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)
        
        # Left side - Configuration
        left_widget = self.create_config_panel()
        content_layout.addWidget(left_widget, 2)
        
        # Right side - Visual guide
        right_widget = self.create_visual_panel()
        content_layout.addWidget(right_widget, 1)
        
        # Bottom navigation
        nav_layout = self.create_navigation()
        main_layout.addLayout(nav_layout)
    
    def create_config_panel(self):
        """Create left configuration panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Frame dimensions
        dimensions_group = QGroupBox("Frame Dimensions")
        dimensions_layout = QFormLayout()
        dimensions_group.setLayout(dimensions_layout)
        layout.addWidget(dimensions_group)
        
        # TODO: Add width and height inputs with validators
        self.width_input = QLineEdit("1200.0")
        self.height_input = QLineEdit("2100.0")
        dimensions_layout.addRow("Width (mm):", self.width_input)
        dimensions_layout.addRow("Height (mm):", self.height_input)
        
        # Hinge configuration
        hinge_group = QGroupBox("Hinge Configuration")
        hinge_layout = QVBoxLayout()
        hinge_group.setLayout(hinge_layout)
        layout.addWidget(hinge_group)
        
        # TODO: Add hinge count selector
        self.hinge_count = QComboBox()
        self.hinge_count.addItems(["2", "3", "4", "5"])
        
        # TODO: Add auto-position checkbox
        self.auto_position = QCheckBox("Auto-position")
        
        # TODO: Add hinge position inputs container
        self.positions_container = QWidget()
        
        # TODO: Add alignment options
        self.y_alignment = QComboBox()
        self.z_alignment = QComboBox()
        
        layout.addStretch()
        return widget
    
    def create_visual_panel(self):
        """Create right visual panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Visual guide
        visual_group = QGroupBox("Visual Guide")
        visual_layout = QVBoxLayout()
        visual_group.setLayout(visual_layout)
        layout.addWidget(visual_group)
        
        # TODO: Add frame diagram/preview
        diagram_label = QLabel("Frame\nDiagram")
        diagram_label.setFixedSize(300, 400)
        diagram_label.setAlignment(Qt.AlignCenter)
        visual_layout.addWidget(diagram_label, alignment=Qt.AlignCenter)
        
        # Lock configuration
        lock_group = QGroupBox("Lock Configuration")
        lock_layout = QFormLayout()
        lock_group.setLayout(lock_layout)
        layout.addWidget(lock_group)
        
        # TODO: Add lock position input
        self.lock_position = QLineEdit("1050.0")
        lock_layout.addRow("Position (mm):", self.lock_position)
        
        layout.addStretch()
        return widget
    
    def create_navigation(self):
        """Create bottom navigation buttons"""
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()
        
        self.back_button = QPushButton("← Back")
        self.next_button = QPushButton("Next →")
        
        nav_layout.addWidget(self.back_button)
        nav_layout.addWidget(self.next_button)
        
        return nav_layout
    
    def connect_signals(self):
        """Connect widget signals"""
        self.back_button.clicked.connect(self.back_clicked)
        self.next_button.clicked.connect(self.on_next_clicked)
        
        # TODO: Connect input change signals to on_config_changed
        # TODO: Connect hinge count changes to update_hinge_positions
        # TODO: Connect auto-position changes
    
    # MARK: - Profile Management
    def set_profiles(self, hinge_profile, lock_profile):
        """Set selected profiles from previous tab"""
        self.profiles = {
            'hinge': hinge_profile,
            'lock': lock_profile
        }
    
    # MARK: - Hinge Position Management
    def update_hinge_positions(self):
        """Update hinge position inputs based on count"""
        # TODO: Clear existing position inputs
        # TODO: Create new position inputs based on hinge_count
        # TODO: Set default positions if auto-position enabled
        pass
    
    def on_auto_position_changed(self, state):
        """Handle auto-position checkbox changes"""
        # TODO: Enable/disable position inputs
        # TODO: Calculate positions if auto-position enabled
        pass
    
    def calculate_auto_positions(self):
        """Calculate automatic hinge positions"""
        # TODO: Calculate equal spacing based on frame height
        # TODO: Update position input values
        pass
    
    # MARK: - Configuration Management
    def on_config_changed(self):
        """Handle configuration changes"""
        # TODO: Validate inputs
        # TODO: Update visual diagram
        self.configuration_changed.emit(self.get_configuration())
    
    def get_configuration(self):
        """Get current frame configuration"""
        # TODO: Collect all configuration values
        config = {
            'width': 0.0,
            'height': 0.0,
            'hinge_count': 3,
            'hinge_positions': [],
            'y_alignment': 'Center',
            'z_alignment': 'Front',
            'lock_position': 0.0,
            'profiles': self.profiles
        }
        return config
    
    # MARK: - Event Handlers
    def on_next_clicked(self):
        """Validate configuration and proceed"""
        # TODO: Validate all inputs
        # TODO: Show error messages if invalid
        # TODO: Emit next_clicked if valid
        self.next_clicked.emit()