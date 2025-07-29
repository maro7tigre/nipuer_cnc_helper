from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                             QLabel, QLineEdit, QComboBox, QCheckBox,
                             QGroupBox, QFormLayout, QSplitter, QButtonGroup,
                             QRadioButton, QSpinBox)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QDoubleValidator, QPainter, QColor, QPen, QBrush
from .profile_gcode_dialog import ProfileGCodeDialog
from .order_widget import OrderWidget


class FramePreview(QWidget):
    """Visual preview area for frame configuration"""
    
    def __init__(self):
        super().__init__()
        self.frame_height = 2100
        self.frame_width = 1200
        self.lock_position = 1050
        self.lock_y_offset = 0
        self.lock_active = True
        self.hinge_positions = []
        self.hinge_active = []
        self.hinge_y_offset = 0
        self.pm_positions = []
        self.orientation = "right"  # "right" or "left"
        
        self.setMinimumSize(400, 600)
        self.setStyleSheet("background-color: #f0f0f0;")
    
    def update_config(self, config):
        """Update preview with new configuration"""
        self.frame_height = config.get('height', 2100)
        self.frame_width = config.get('width', 1200)
        self.lock_position = config.get('lock_position', 1050)
        self.lock_y_offset = config.get('lock_y_offset', 0)
        self.lock_active = config.get('lock_active', True)
        self.hinge_positions = config.get('hinge_positions', [])
        self.hinge_active = config.get('hinge_active', [])
        self.hinge_y_offset = config.get('hinge_y_offset', 0)
        self.pm_positions = config.get('pm_positions', [])
        self.orientation = config.get('orientation', 'right')
        self.update()
    
    def paintEvent(self, event):
        """Draw the frame preview"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate scaling to fit the widget
        widget_width = self.width()
        widget_height = self.height()
        
        # Frame dimensions in preview (scaled)
        scale = min(widget_height / (self.frame_height + 100), 
                   widget_width / (self.frame_width * 2 + 100))
        
        frame_height_scaled = self.frame_height * scale
        frame_width_scaled = 100*scale  # Fixed visual width
        
        # PMs dimensions
        large_PM = [300*scale,130*scale]
        small_PM = [152*scale,82*scale]
        
        frame_gap = small_PM[0]-frame_width_scaled
        
        # Center the drawing
        start_x = widget_width / 2
        start_y = (widget_height - frame_height_scaled) / 2
        
        # Draw PMs large
        for pm_pos in self.pm_positions:
            pm_y = start_y + pm_pos * scale  # Position from top
            # Large rectangle below frames
            painter.setBrush(QBrush(QColor(128, 128, 128)))
            painter.drawRect(start_x - large_PM[0]/2, pm_y - large_PM[1]/2, large_PM[0], large_PM[1])
                
        # Draw frames
        # First frame (left)
        painter.setBrush(QBrush(QColor(160, 82, 45)))  # Light brown
        painter.setPen(QPen(QColor(101, 67, 33), 2))
        painter.drawRect(start_x - frame_gap/2 - frame_width_scaled, start_y, frame_width_scaled/2, frame_height_scaled)
        
        painter.setBrush(QBrush(QColor(139, 69, 19)))  # Dark brown
        painter.drawRect(start_x - frame_width_scaled/2 - frame_gap/2, start_y, frame_width_scaled/2, frame_height_scaled)
        
        # Second frame (right) - mirrored
        painter.setBrush(QBrush(QColor(139, 69, 19)))  # Dark brown
        painter.drawRect(start_x + frame_gap/2, start_y, frame_width_scaled/2, frame_height_scaled)
        
        painter.setBrush(QBrush(QColor(160, 82, 45)))  # Light brown
        painter.drawRect(start_x + frame_width_scaled/2 + frame_gap/2, start_y, frame_width_scaled/2, frame_height_scaled)
        
        # Draw PMs small
        painter.setBrush(QBrush(QColor(128, 128, 128)))  # Grey
        painter.setPen(QPen(QColor(64, 64, 64), 2))
        
        for pm_pos in self.pm_positions:
            pm_y = start_y + pm_pos * scale  # Position from top
            # Small rectangle above frames
            painter.setBrush(QBrush(QColor(192, 192, 192)))  # Lighter grey
            painter.drawRect(start_x - small_PM[0]/2, pm_y - small_PM[1]/2, small_PM[0], small_PM[1])
        
        # Draw lock
        if self.lock_active and self.lock_position > 0:
            painter.setBrush(QBrush(QColor(0, 255, 0)))  # Green
            painter.setPen(QPen(QColor(0, 128, 0), 2))
            
            lock_y = start_y + self.lock_position * scale  # Position from top
            lock_width = 35*scale
            lock_height = 180*scale
            
            if self.orientation == "right":
                lock_x = start_x - 35*scale/2 - lock_width - self.lock_y_offset*scale
            else:  # left
                lock_x = start_x + 35*scale/2 + self.lock_y_offset*scale
            
            painter.drawRect(lock_x, lock_y - lock_height/2, lock_width, lock_height)
        
        # Draw hinges
        painter.setBrush(QBrush(QColor(0, 0, 255)))  # Blue
        painter.setPen(QPen(QColor(0, 0, 128), 2))
        
        for i, (hinge_pos, active) in enumerate(zip(self.hinge_positions, self.hinge_active)):
            if active and hinge_pos > 0:
                hinge_y = start_y + hinge_pos * scale  # Position from top
                hinge_width = 20*scale
                hinge_height = 80*scale
                
                if self.orientation == "right":
                    hinge_x = start_x + 35*scale/2 + self.hinge_y_offset*scale
                else:  # left
                    hinge_x = start_x - 35*scale/2 - hinge_width - self.hinge_y_offset*scale
                
                painter.drawRect(hinge_x, hinge_y - hinge_height/2, hinge_width, hinge_height)


class ClickableLabel(QLabel):
    """Clickable label that looks like a link"""
    clicked = Signal()
    
    def __init__(self, text):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QLabel {
                color: #BB86FC;
                text-decoration: underline;
                background-color: transparent;
            }
            QLabel:hover {
                color: #9965DA;
            }
        """)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class FrameTab(QWidget):
    """Frame configuration tab with resizable order widget and three-panel layout"""
    back_clicked = Signal()
    next_clicked = Signal()
    configuration_changed = Signal(dict)
    frame_gcode_changed = Signal(dict)  # New signal for frame G-code changes
    
    # Configuration parameters - easily adjustable
    MAX_FRAME_HEIGHT = 2500  # Maximum frame height
    MIN_FRAME_HEIGHT = 840   # Minimum frame height
    
    PM_CONFIG = {
        'sizes': {
            1: [265, 140],  # PM1 dimensions [width, height]
            2: [140, 175],  # PM2 dimensions
            3: [175, 240],  # PM3 dimensions
            4: [240, 120]   # PM4 dimensions
        },
        'lock_safety_distance': 170,
        'hinge_safety_distance': 170,
        'min_range_size': 120
    }
    
    def __init__(self):
        super().__init__()
        self.hinge_positions = []
        self.hinge_active = []
        self.profiles = {}
        self.profile_data = {}  # Store full profile data
        self.execution_order = []
        self.dollar_variables_info = {}  # Store $ variables info
        
        self.setup_ui()
        self.connect_signals()
        self.apply_styling()
        
        # Initialize with default values
        self.update_hinge_count(3)  # Default to 3 hinges
        
        # Set default PM positions
        default_positions = [-25, 700, 1230, 1540]
        for i, pos in enumerate(default_positions):
            self.pm_inputs[i].setText(str(pos))
        
        # Set PM auto to unchecked by default
        self.pm_auto_check.setChecked(False)
        
        # Apply auto-position states after UI setup
        self.on_pm_auto_changed()
        self.on_lock_auto_changed()
        self.on_hinge_auto_changed()
        
        # Update auto positions after everything is setup
        self.update_all_auto_positions()
        self.on_config_changed()
    
    def set_dollar_variables_info(self, dollar_variables_info):
        """Set available $ variables information for G-code editors"""
        self.dollar_variables_info = dollar_variables_info
    
    def apply_styling(self):
        """Apply dark theme styling"""
        self.setStyleSheet("""
            FrameTab {
                background-color: #282a36;
                color: #ffffff;
            }
            QGroupBox {
                border: 2px solid #44475c;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #ffffff;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit {
                background-color: #1d1f28;
                color: #ffffff;
                border: 1px solid #6f779a;
                border-radius: 4px;
                padding: 4px;
            }
            QLineEdit:focus {
                border: 1px solid #BB86FC;
            }
            QLineEdit:disabled {
                background-color: #0d0f18;
                color: #6f779a;
            }
            QLineEdit.error {
                border: 2px solid #ff4444;
            }
            QCheckBox {
                color: #ffffff;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #6f779a;
                background-color: #1d1f28;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #23c87b;
                border-color: #23c87b;
            }
            QSpinBox {
                background-color: #1d1f28;
                color: #ffffff;
                border: 1px solid #6f779a;
                border-radius: 4px;
                padding: 4px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #44475c;
                border: none;
                width: 16px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #6f779a;
            }
            QPushButton {
                background-color: #1d1f28;
                color: #BB86FC;
                border: 2px solid #BB86FC;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #000000;
                color: #9965DA;
                border: 2px solid #9965DA;
            }
            QPushButton:pressed {
                background-color: #BB86FC;
                color: #1d1f28;
            }
            QPushButton#next_button {
                background-color: #1d1f28;
                color: #23c87b;
                border: 2px solid #23c87b;
            }
            QPushButton#next_button:hover {
                background-color: #000000;
                color: #1a945b;
                border: 2px solid #1a945b;
            }
            QPushButton#next_button:pressed {
                background-color: #23c87b;
                color: #1d1f28;
            }
            QRadioButton {
                color: #ffffff;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #6f779a;
                background-color: #1d1f28;
                border-radius: 8px;
            }
            QRadioButton::indicator:checked {
                background-color: #23c87b;
                border-color: #23c87b;
            }
            QSplitter::handle {
                background-color: #44475c;
                width: 4px;
            }
            QSplitter::handle:hover {
                background-color: #BB86FC;
            }
        """)
    
    def setup_ui(self):
        """Initialize user interface with three-panel layout"""
        main_layout = QVBoxLayout(self)
        
        # Content area with splitter
        content_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(content_splitter)
        
        # Left panel
        left_widget = self.create_left_panel()
        content_splitter.addWidget(left_widget)
        
        # Middle panel (preview)
        middle_widget = self.create_middle_panel()
        content_splitter.addWidget(middle_widget)
        
        # Right panel
        right_widget = self.create_right_panel()
        content_splitter.addWidget(right_widget)
        
        # Set initial splitter sizes
        content_splitter.setSizes([300, 400, 300])
        
        # Bottom navigation
        nav_layout = self.create_navigation()
        main_layout.addLayout(nav_layout)
    
    def create_left_panel(self):
        """Create left panel with frame dimensions and PM positions"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Frame dimensions group
        frame_group = QGroupBox("Frame Configuration")
        frame_layout = QFormLayout()
        frame_group.setLayout(frame_layout)
        
        # Frame height with min/max validation
        self.height_input = QLineEdit("2100")
        self.height_input.setValidator(QDoubleValidator(self.MIN_FRAME_HEIGHT, self.MAX_FRAME_HEIGHT, 2))
        frame_layout.addRow("Frame Height (mm):", self.height_input)
        
        # Machine offsets
        self.x_offset_input = QLineEdit("0")
        self.x_offset_input.setValidator(QDoubleValidator(-1000, 1000, 2))
        frame_layout.addRow("Machine X Offset:", self.x_offset_input)
        
        self.y_offset_input = QLineEdit("0")
        self.y_offset_input.setValidator(QDoubleValidator(-1000, 1000, 2))
        frame_layout.addRow("Machine Y Offset:", self.y_offset_input)
        
        self.z_offset_input = QLineEdit("0")
        self.z_offset_input.setValidator(QDoubleValidator(-1000, 1000, 2))
        frame_layout.addRow("Machine Z Offset:", self.z_offset_input)
        
        layout.addWidget(frame_group)
        
        # PM positions group
        pm_group = QGroupBox("PM Positions")
        pm_layout = QVBoxLayout()
        pm_group.setLayout(pm_layout)
        
        # PM auto checkbox
        self.pm_auto_check = QCheckBox("Auto-position")
        self.pm_auto_check.setChecked(False)  # Default to unchecked
        pm_layout.addWidget(self.pm_auto_check)
        
        # PM position inputs
        self.pm_inputs_widget = QWidget()
        pm_inputs_layout = QFormLayout(self.pm_inputs_widget)
        pm_layout.addWidget(self.pm_inputs_widget)
        
        self.pm_inputs = []
        for i in range(4):
            pm_input = QLineEdit("0")
            pm_input.setValidator(QDoubleValidator(-100, self.MAX_FRAME_HEIGHT, 2))
            pm_inputs_layout.addRow(f"PM{i+1} Position:", pm_input)
            self.pm_inputs.append(pm_input)
        
        layout.addWidget(pm_group)
        layout.addStretch()
        
        return widget
    
    def create_middle_panel(self):
        """Create middle panel with preview and orientation switch"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Orientation switch with G-code edit links
        orientation_group = QGroupBox("Door Orientation")
        orientation_layout = QVBoxLayout()
        orientation_group.setLayout(orientation_layout)
        
        # Radio buttons layout
        radio_layout = QHBoxLayout()
        
        self.orientation_group = QButtonGroup()
        self.right_radio = QRadioButton("Right (droite)")
        self.left_radio = QRadioButton("Left (gauche)")
        self.right_radio.setChecked(True)
        
        self.orientation_group.addButton(self.right_radio)
        self.orientation_group.addButton(self.left_radio)
        
        radio_layout.addWidget(self.right_radio)
        self.right_gcode_link = ClickableLabel("Edit")
        self.right_gcode_link.clicked.connect(self.edit_right_gcode)
        radio_layout.addWidget(self.right_gcode_link)
        
        radio_layout.addStretch()
        
        radio_layout.addWidget(self.left_radio)
        self.left_gcode_link = ClickableLabel("Edit")
        self.left_gcode_link.clicked.connect(self.edit_left_gcode)
        radio_layout.addWidget(self.left_gcode_link)
        
        orientation_layout.addLayout(radio_layout)
        
        layout.addWidget(orientation_group)
        
        # Preview area
        self.preview = FramePreview()
        layout.addWidget(self.preview, 1)
        
        return widget
    
    def create_right_panel(self):
        """Create right panel with lock and hinge configuration"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Lock configuration
        lock_group = QGroupBox("Lock Configuration")
        lock_layout = QVBoxLayout()
        lock_group.setLayout(lock_layout)
        
        # Auto checkbox and position
        lock_auto_layout = QHBoxLayout()
        self.lock_auto_check = QCheckBox("Auto")
        self.lock_auto_check.setChecked(True)
        lock_auto_layout.addWidget(self.lock_auto_check)
        
        lock_auto_layout.addWidget(QLabel("Position:"))
        self.lock_position_input = QLineEdit("1050")
        self.lock_position_input.setValidator(QDoubleValidator(0, self.MAX_FRAME_HEIGHT, 2))
        self.lock_position_input.setEnabled(False)
        lock_auto_layout.addWidget(self.lock_position_input)
        
        self.lock_active_check = QCheckBox("Active")
        self.lock_active_check.setChecked(True)
        lock_auto_layout.addWidget(self.lock_active_check)
        
        lock_layout.addLayout(lock_auto_layout)
        
        # Lock Y offset
        lock_offset_layout = QHBoxLayout()
        lock_offset_layout.addWidget(QLabel("Y Offset:"))
        self.lock_y_offset_input = QLineEdit("0")
        self.lock_y_offset_input.setValidator(QDoubleValidator(-100, 100, 2))
        lock_offset_layout.addWidget(self.lock_y_offset_input)
        lock_layout.addLayout(lock_offset_layout)
        
        layout.addWidget(lock_group)
        
        # Hinge configuration
        hinge_group = QGroupBox("Hinge Configuration")
        hinge_layout = QVBoxLayout()
        hinge_group.setLayout(hinge_layout)
        
        # Hinge count selector
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Number of Hinges:"))
        self.hinge_count_spin = QSpinBox()
        self.hinge_count_spin.setRange(0, 4)
        self.hinge_count_spin.setValue(3)  # Default to 3
        count_layout.addWidget(self.hinge_count_spin)
        count_layout.addStretch()
        hinge_layout.addLayout(count_layout)
        
        # Auto checkbox
        self.hinge_auto_check = QCheckBox("Auto-position")
        self.hinge_auto_check.setChecked(True)
        hinge_layout.addWidget(self.hinge_auto_check)
        
        # Hinge positions container
        self.hinge_positions_widget = QWidget()
        self.hinge_positions_layout = QVBoxLayout(self.hinge_positions_widget)
        self.hinge_positions_layout.setContentsMargins(0, 0, 0, 0)
        hinge_layout.addWidget(self.hinge_positions_widget)
        
        # Z offset for all hinges
        z_offset_layout = QHBoxLayout()
        z_offset_layout.addWidget(QLabel("Z Offset (all):"))
        self.hinge_z_offset_input = QLineEdit("0")
        self.hinge_z_offset_input.setValidator(QDoubleValidator(-100, 100, 2))
        z_offset_layout.addWidget(self.hinge_z_offset_input)
        hinge_layout.addLayout(z_offset_layout)
        
        layout.addWidget(hinge_group)
        
        # Execution order widget - now resizable
        order_group = QGroupBox("Component Order")
        order_layout = QVBoxLayout()
        order_group.setLayout(order_layout)
        
        self.order_widget = OrderWidget()
        self.order_widget.order_changed.connect(self.on_order_changed)
        # Remove fixed height to make it resizable
        order_layout.addWidget(self.order_widget, 1)  # Give it stretch factor
        
        layout.addWidget(order_group, 1)  # Give order group stretch
        
        return widget
    
    def create_navigation(self):
        """Create bottom navigation buttons"""
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()
        
        self.back_button = QPushButton("← Back")
        self.next_button = QPushButton("Next →")
        self.next_button.setObjectName("next_button")
        
        nav_layout.addWidget(self.back_button)
        nav_layout.addWidget(self.next_button)
        
        return nav_layout
    
    def connect_signals(self):
        """Connect widget signals"""
        self.back_button.clicked.connect(self.back_clicked)
        self.next_button.clicked.connect(self.on_next_clicked)
        
        # Frame dimension changes
        self.height_input.textChanged.connect(self.on_frame_height_changed)
        self.height_input.editingFinished.connect(self.enforce_min_height)
        self.x_offset_input.textChanged.connect(self.on_config_changed)
        self.y_offset_input.textChanged.connect(self.on_config_changed)
        self.z_offset_input.textChanged.connect(self.on_config_changed)
        
        # PM configuration
        self.pm_auto_check.stateChanged.connect(self.on_pm_auto_changed)
        for pm_input in self.pm_inputs:
            pm_input.textChanged.connect(self.on_pm_position_changed)
        
        # Lock configuration
        self.lock_auto_check.stateChanged.connect(self.on_lock_auto_changed)
        self.lock_position_input.textChanged.connect(self.on_lock_position_changed)
        self.lock_active_check.stateChanged.connect(self.on_lock_active_changed)
        self.lock_y_offset_input.textChanged.connect(self.on_config_changed)
        
        # Hinge configuration
        self.hinge_count_spin.valueChanged.connect(self.update_hinge_count)
        self.hinge_auto_check.stateChanged.connect(self.on_hinge_auto_changed)
        self.hinge_z_offset_input.textChanged.connect(self.on_config_changed)
        
        # Orientation
        self.orientation_group.buttonClicked.connect(self.on_config_changed)
    
    def on_pm_position_changed(self):
        """Handle manual PM position changes"""
        self.validate_pm_positions()
        self.on_config_changed()
    
    def enforce_min_height(self):
        """Enforce minimum frame height"""
        try:
            height = float(self.height_input.text() or 0)
            if height < self.MIN_FRAME_HEIGHT:
                self.height_input.setText(str(self.MIN_FRAME_HEIGHT))
            elif height > self.MAX_FRAME_HEIGHT:
                self.height_input.setText(str(self.MAX_FRAME_HEIGHT))
        except ValueError:
            self.height_input.setText(str(self.MIN_FRAME_HEIGHT))
    
    def update_hinge_count(self, count):
        """Update hinge position inputs based on count"""
        # Clear existing inputs
        while self.hinge_positions_layout.count():
            item = self.hinge_positions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.hinge_positions = []
        self.hinge_active = []
        self.hinge_inputs = []
        self.hinge_active_checks = []
        
        # Create new inputs
        for i in range(count):
            hinge_layout = QHBoxLayout()
            
            hinge_layout.addWidget(QLabel(f"Hinge {i+1}:"))
            
            # Position input
            position_input = QLineEdit("0")
            position_input.setValidator(QDoubleValidator(0, self.MAX_FRAME_HEIGHT, 2))
            position_input.textChanged.connect(self.on_hinge_position_changed)
            hinge_layout.addWidget(position_input)
            self.hinge_inputs.append(position_input)
            
            # Active checkbox
            active_check = QCheckBox("Active")
            active_check.setChecked(True)
            active_check.stateChanged.connect(self.on_hinge_active_changed)
            hinge_layout.addWidget(active_check)
            self.hinge_active_checks.append(active_check)
            
            self.hinge_positions_layout.addLayout(hinge_layout)
            self.hinge_positions.append(0)
            self.hinge_active.append(True)
        
        # Set enabled state for position inputs
        auto_enabled = self.hinge_auto_check.isChecked()
        for input_field in self.hinge_inputs:
            input_field.setEnabled(not auto_enabled)
        
        # Update auto positions after creating new inputs
        self.update_all_auto_positions()
        self.update_order_widget()
        self.on_config_changed()
    
    def on_frame_height_changed(self):
        """Handle frame height changes"""
        self.update_all_auto_positions()
        self.on_config_changed()
    
    def on_lock_auto_changed(self):
        """Handle lock auto checkbox changes"""
        auto_enabled = self.lock_auto_check.isChecked()
        self.lock_position_input.setEnabled(not auto_enabled)
        
        if auto_enabled:
            self.update_all_auto_positions()
        
        self.on_config_changed()
    
    def on_lock_position_changed(self):
        """Handle lock position changes"""
        self.update_all_auto_positions()
        self.on_config_changed()
    
    def on_lock_active_changed(self):
        """Handle lock active state changes"""
        self.update_order_widget()
        self.on_config_changed()
    
    def on_hinge_auto_changed(self):
        """Handle hinge auto checkbox changes"""
        auto_enabled = self.hinge_auto_check.isChecked()
        
        # Enable/disable position inputs
        for input_field in self.hinge_inputs:
            input_field.setEnabled(not auto_enabled)
        
        if auto_enabled:
            self.update_all_auto_positions()
        
        self.on_config_changed()
    
    def on_hinge_position_changed(self):
        """Handle hinge position changes"""
        self.update_all_auto_positions()
        self.on_config_changed()
    
    def on_hinge_active_changed(self):
        """Handle hinge active state changes"""
        self.update_order_widget()
        self.on_config_changed()
    
    def on_pm_auto_changed(self):
        """Handle PM auto checkbox changes"""
        auto_enabled = self.pm_auto_check.isChecked()
        
        # Enable/disable PM position inputs (except the first one)
        for i, input_field in enumerate(self.pm_inputs):
            if i == 0:  # First PM is always editable
                input_field.setEnabled(True)
            else:
                input_field.setEnabled(not auto_enabled)
        
        if auto_enabled:
            self.update_all_auto_positions()
        
        self.on_config_changed()
    
    def on_order_changed(self, order):
        """Handle execution order changes"""
        self.execution_order = order
        self.on_config_changed()
    
    def update_order_widget(self):
        """Update the order widget based on active components"""
        lock_active = self.lock_active_check.isChecked()
        hinge_count = self.hinge_count_spin.value()
        hinge_active = [check.isChecked() for check in self.hinge_active_checks]
        
        self.order_widget.update_items(lock_active, hinge_count, hinge_active)
    
    def update_all_auto_positions(self):
        """Update all auto positions in order: lock -> hinges -> PMs"""
        # Update lock position if auto
        if self.lock_auto_check.isChecked():
            self.calculate_lock_position()
        
        # Update hinge positions if auto  
        if self.hinge_auto_check.isChecked():
            self.calculate_auto_hinge_positions()
        
        # Update PM positions if auto
        if self.pm_auto_check.isChecked():
            self.calculate_auto_pm_positions()
        
        # Validate PM positions (works for both auto and manual)
        self.validate_pm_positions()
    
    def calculate_lock_position(self):
        """Calculate automatic lock position (1050mm from bottom)"""
        try:
            height = float(self.height_input.text() or 0)
            # Lock is 1050mm from bottom, positions are from top
            lock_pos = height - 1050
            self.lock_position_input.setText(f"{lock_pos:.1f}")
        except ValueError:
            pass
    
    def calculate_auto_hinge_positions(self):
        """Calculate automatic hinge positions with specific rules"""
        try:
            height = float(self.height_input.text() or 0)
            count = len(self.hinge_inputs)
            
            if count > 0 and height > 0:
                if count == 1:
                    # Single hinge at middle
                    self.hinge_inputs[0].setText(f"{height/2:.1f}")
                elif count == 2:
                    # First at 150, last at appropriate position
                    self.hinge_inputs[0].setText("150.0")
                    if height >= 2000:
                        self.hinge_inputs[1].setText("1800.0")
                    else:
                        self.hinge_inputs[1].setText(f"{height - 200:.1f}")
                elif count == 3:
                    # First at 150, last at appropriate position
                    self.hinge_inputs[0].setText("150.0")
                    if height >= 2000:
                        last_pos = 1800
                    else:
                        last_pos = height - 200
                    self.hinge_inputs[2].setText(f"{last_pos:.1f}")
                    
                    # Middle positioned so lower-to-middle is 1.5x upper-to-middle
                    middle_pos = 150 + (last_pos - 150) / 2.5
                    self.hinge_inputs[1].setText(f"{middle_pos:.1f}")
                elif count == 4:
                    # First at 150, last at appropriate position
                    self.hinge_inputs[0].setText("150.0")
                    if height >= 2000:
                        last_pos = 1800
                    else:
                        last_pos = height - 200
                    self.hinge_inputs[3].setText(f"{last_pos:.1f}")
                    
                    # Calculate with cascading 1.5x ratios
                    total_distance = last_pos - 150
                    d1 = total_distance / 4.75
                    
                    self.hinge_inputs[1].setText(f"{150 + d1:.1f}")
                    self.hinge_inputs[2].setText(f"{150 + d1 + 1.5*d1:.1f}")
        except ValueError:
            pass
    
    def calculate_auto_pm_positions(self):
        """Calculate automatic PM positions following the improved algorithm"""
        config = self.PM_CONFIG
        
        try:
            height = float(self.height_input.text() or 0)
            if height <= 0:
                return
            
            # Step 1: Get PM1 position (user-controlled)
            pm1_pos = float(self.pm_inputs[0].text() or -25)
            
            # Step 2: Calculate minimum distance from PM1 to PM2
            pm1_size = config['sizes'][1]
            pm2_size = config['sizes'][2]
            min_pm1_to_pm2 = pm1_size[0]/2 + pm2_size[0]/2  # 265/2 + 140/2 = 202.5
            
            # Define available range for PM2-4
            range_start = pm1_pos + min_pm1_to_pm2
            pm4_size = config['sizes'][4]
            range_end = height - pm4_size[1]/2  # height - 120
            
            if range_end <= range_start:
                # Not enough space - fallback to minimum distances
                self._fallback_pm_positions(pm1_pos)
                return
            
            # Step 3: Get obstacles (active lock and hinges)
            obstacles = []
            
            # Add lock obstacle
            if self.lock_active_check.isChecked():
                lock_pos = float(self.lock_position_input.text() or 0)
                if lock_pos > 0:
                    safety = config['lock_safety_distance']
                    obstacles.append((lock_pos - safety, lock_pos + safety))
            
            # Add hinge obstacles
            for input_field, check in zip(self.hinge_inputs, self.hinge_active_checks):
                if check.isChecked():
                    hinge_pos = float(input_field.text() or 0)
                    if hinge_pos > 0:
                        safety = config['hinge_safety_distance']
                        obstacles.append((hinge_pos - safety, hinge_pos + safety))
            
            # Step 4: Calculate valid ranges by removing obstacle zones
            valid_ranges = self._calculate_valid_ranges(range_start, range_end, obstacles)
            
            # Step 5: Filter ranges that are too small
            min_size = config['min_range_size']
            valid_ranges = [(start, end) for start, end in valid_ranges if end - start >= min_size]
            
            if not valid_ranges:
                # No valid ranges - fallback
                self._fallback_pm_positions(pm1_pos)
                return
            
            # Step 6: Place PM4 at end of last valid range
            pm4_pos = valid_ranges[-1][1]
            
            # Step 7: Find optimal positions for PM2 and PM3
            pm2_pos, pm3_pos = self._optimize_pm2_pm3_positions(pm1_pos, pm4_pos, valid_ranges)
            
            # Update inputs
            self.pm_inputs[1].setText(f"{pm2_pos:.1f}")
            self.pm_inputs[2].setText(f"{pm3_pos:.1f}")
            self.pm_inputs[3].setText(f"{pm4_pos:.1f}")
            
        except ValueError:
            # Error in calculations - use fallback
            pm1_pos = float(self.pm_inputs[0].text() or -25)
            self._fallback_pm_positions(pm1_pos)
    
    def _calculate_valid_ranges(self, range_start, range_end, obstacles):
        """Calculate valid ranges by removing obstacle zones"""
        # Sort obstacles by start position
        obstacles = sorted(obstacles, key=lambda x: x[0])
        
        valid_ranges = []
        current_start = range_start
        
        for obstacle_start, obstacle_end in obstacles:
            # Only consider obstacles that overlap with our range
            obstacle_start = max(obstacle_start, range_start)
            obstacle_end = min(obstacle_end, range_end)
            
            if obstacle_start < range_end and obstacle_end > range_start:
                # This obstacle overlaps with our range
                if obstacle_start > current_start:
                    # Add range before this obstacle
                    valid_ranges.append((current_start, obstacle_start))
                
                # Move current start past this obstacle
                current_start = max(current_start, obstacle_end)
        
        # Add final range if there's space after last obstacle
        if current_start < range_end:
            valid_ranges.append((current_start, range_end))
        
        return valid_ranges
    
    def _optimize_pm2_pm3_positions(self, pm1_pos, pm4_pos, valid_ranges):
        """Find optimal positions for PM2 and PM3 that maximize distances"""
        config = self.PM_CONFIG
        
        # Calculate minimum distances
        pm2_size = config['sizes'][2]
        pm3_size = config['sizes'][3]
        min_pm1_to_pm2 = config['sizes'][1][0]/2 + pm2_size[0]/2  # 202.5
        min_pm2_to_pm3 = pm2_size[0]/2 + pm3_size[0]/2  # 157.5
        min_pm3_to_pm4 = pm3_size[0]/2 + config['sizes'][4][0]/2  # 207.5
        
        # Start with minimum distances
        pm2_pos = pm1_pos + min_pm1_to_pm2
        pm3_pos = pm4_pos - min_pm3_to_pm4
        
        # Check if we have enough space between PM2 and PM3
        if pm3_pos - pm2_pos < min_pm2_to_pm3:
            # Not enough space - use minimum distances from PM1
            pm2_pos = pm1_pos + min_pm1_to_pm2
            pm3_pos = pm2_pos + min_pm2_to_pm3
            return pm2_pos, pm3_pos
        
        # Try to place PM2 and PM3 in valid ranges
        best_pm2 = pm2_pos
        best_pm3 = pm3_pos
        
        # Check if PM2 position is in a valid range
        pm2_valid = self._position_in_valid_ranges(pm2_pos, valid_ranges)
        if not pm2_valid:
            # Find the closest valid range for PM2
            for start, end in valid_ranges:
                if start >= pm1_pos + min_pm1_to_pm2:
                    best_pm2 = start
                    break
        
        # Check if PM3 position is in a valid range  
        pm3_valid = self._position_in_valid_ranges(pm3_pos, valid_ranges)
        if not pm3_valid:
            # Find the closest valid range for PM3
            for start, end in reversed(valid_ranges):
                if end <= pm4_pos - min_pm3_to_pm4:
                    best_pm3 = end
                    break
        
        # Ensure minimum distance between PM2 and PM3
        if best_pm3 - best_pm2 < min_pm2_to_pm3:
            # Adjust positions to maintain minimum distance
            mid_point = (best_pm2 + best_pm3) / 2
            best_pm2 = mid_point - min_pm2_to_pm3 / 2
            best_pm3 = mid_point + min_pm2_to_pm3 / 2
            
            # Ensure they're still in valid ranges
            if not self._position_in_valid_ranges(best_pm2, valid_ranges):
                best_pm2 = pm1_pos + min_pm1_to_pm2
            if not self._position_in_valid_ranges(best_pm3, valid_ranges):
                best_pm3 = best_pm2 + min_pm2_to_pm3
        
        return best_pm2, best_pm3
    
    def _position_in_valid_ranges(self, position, valid_ranges):
        """Check if a position is within any valid range"""
        for start, end in valid_ranges:
            if start <= position <= end:
                return True
        return False
    
    def _fallback_pm_positions(self, pm1_pos):
        """Fallback to minimum distances when optimization fails"""
        config = self.PM_CONFIG
        
        # Calculate minimum distances
        min_distances = [
            config['sizes'][1][0]/2 + config['sizes'][2][0]/2,  # PM1-PM2: 202.5
            config['sizes'][2][0]/2 + config['sizes'][3][0]/2,  # PM2-PM3: 157.5
            config['sizes'][3][0]/2 + config['sizes'][4][0]/2   # PM3-PM4: 207.5
        ]
        
        pm2_pos = pm1_pos + min_distances[0]
        pm3_pos = pm2_pos + min_distances[1]
        pm4_pos = pm3_pos + min_distances[2]
        
        self.pm_inputs[1].setText(f"{pm2_pos:.1f}")
        self.pm_inputs[2].setText(f"{pm3_pos:.1f}")
        self.pm_inputs[3].setText(f"{pm4_pos:.1f}")

    def validate_pm_positions(self):
        """Validate PM positions and mark errors with red borders"""
        config = self.PM_CONFIG
        
        # Calculate minimum distances
        min_distances = {
            '1-2': config['sizes'][1][0]/2 + config['sizes'][2][0]/2,  # 202.5
            '2-3': config['sizes'][2][0]/2 + config['sizes'][3][0]/2,  # 157.5
            '3-4': config['sizes'][3][0]/2 + config['sizes'][4][0]/2   # 207.5
        }
        
        # Reset all borders first
        for pm_input in self.pm_inputs:
            pm_input.setProperty("class", "")
            pm_input.style().polish(pm_input)
        
        # Get PM positions
        pm_positions = []
        for pm_input in self.pm_inputs:
            try:
                pos = float(pm_input.text() or 0)
                pm_positions.append(pos)
            except ValueError:
                pm_positions.append(0)
        
        # Track errors for each PM
        errors = [False] * 4
        
        # Check minimum distances between consecutive PMs
        distance_checks = [
            (0, 1, min_distances['1-2']),
            (1, 2, min_distances['2-3']),
            (2, 3, min_distances['3-4'])
        ]
        
        for i, j, min_dist in distance_checks:
            if pm_positions[j] - pm_positions[i] < min_dist:
                errors[i] = True
                errors[j] = True
        
        # Check distance from obstacles (lock and hinges)
        obstacles = []
        
        # Add lock position if active
        if self.lock_active_check.isChecked():
            try:
                lock_pos = float(self.lock_position_input.text() or 0)
                if lock_pos > 0:
                    obstacles.append(lock_pos)
            except ValueError:
                pass
        
        # Add active hinge positions
        for input_field, check in zip(self.hinge_inputs, self.hinge_active_checks):
            if check.isChecked():
                try:
                    hinge_pos = float(input_field.text() or 0)
                    if hinge_pos > 0:
                        obstacles.append(hinge_pos)
                except ValueError:
                    pass
        
        # Check each PM against obstacles
        lock_safety = config['lock_safety_distance'] 
        hinge_safety = config['hinge_safety_distance']
        safety_distance = max(lock_safety, hinge_safety)
        
        for i, pm_pos in enumerate(pm_positions):
            for obstacle_pos in obstacles:
                if abs(pm_pos - obstacle_pos) < safety_distance:
                    errors[i] = True
        
        # Check if PM4 exceeds frame height constraint
        try:
            height = float(self.height_input.text() or 0)
            if pm_positions[3] > height - config['sizes'][4][1]/2:  # PM4 too high
                errors[3] = True
        except ValueError:
            pass
        
        # Apply error styling
        for pm_input, has_error in zip(self.pm_inputs, errors):
            if has_error:
                pm_input.setProperty("class", "error")
                pm_input.style().polish(pm_input)
    
    def edit_right_gcode(self):
        """Open G-code editor for right orientation"""
        # Get current G-code for right orientation
        current_gcode = ""
        if 'hinge' in self.profile_data:
            current_gcode = self.profile_data['hinge'].get('gcode_right', '')
        
        from PySide6.QtWidgets import QDialog
        dialog = ProfileGCodeDialog("Right Door G-Code", current_gcode, self, self.dollar_variables_info)
        if dialog.exec_() == QDialog.Accepted:
            # Ensure hinge profile data exists
            if 'hinge' not in self.profile_data:
                self.profile_data['hinge'] = {}
            # Update with new G-code
            self.profile_data['hinge']['gcode_right'] = dialog.get_gcode()
            self.on_config_changed()
            # Emit frame G-code change signal
            self.frame_gcode_changed.emit(self.get_frame_gcode_data())
    
    def edit_left_gcode(self):
        """Open G-code editor for left orientation"""
        # Get current G-code for left orientation  
        current_gcode = ""
        if 'hinge' in self.profile_data:
            current_gcode = self.profile_data['hinge'].get('gcode_left', '')
        
        from PySide6.QtWidgets import QDialog
        dialog = ProfileGCodeDialog("Left Door G-Code", current_gcode, self, self.dollar_variables_info)
        if dialog.exec_() == QDialog.Accepted:
            # Ensure hinge profile data exists
            if 'hinge' not in self.profile_data:
                self.profile_data['hinge'] = {}
            # Update with new G-code
            self.profile_data['hinge']['gcode_left'] = dialog.get_gcode()
            self.on_config_changed()
            # Emit frame G-code change signal
            self.frame_gcode_changed.emit(self.get_frame_gcode_data())
    
    def on_config_changed(self):
        """Handle any configuration change"""
        config = self.get_configuration()
        self.preview.update_config(config)
        self.configuration_changed.emit(config)
    
    def get_configuration(self):
        """Get current frame configuration including $ variables"""
        # Get hinge positions and active states
        hinge_positions = []
        hinge_active = []
        for i, (input_field, check) in enumerate(zip(self.hinge_inputs, self.hinge_active_checks)):
            try:
                pos = float(input_field.text() or 0)
                hinge_positions.append(pos)
                hinge_active.append(check.isChecked())
            except ValueError:
                hinge_positions.append(0)
                hinge_active.append(False)
        
        # Get PM positions
        pm_positions = []
        for pm_input in self.pm_inputs:
            try:
                pos = float(pm_input.text() or 0)
                pm_positions.append(pos)
            except ValueError:
                pm_positions.append(0)
        
        # Generate $ variables for G-code replacement
        dollar_vars = {
            'frame_height': float(self.height_input.text() or 0),
            'frame_width': 1200,  # Fixed width
            'machine_x_offset': float(self.x_offset_input.text() or 0),
            'machine_y_offset': float(self.y_offset_input.text() or 0),
            'machine_z_offset': float(self.z_offset_input.text() or 0),
            'pm1_position': pm_positions[0] if len(pm_positions) > 0 else 0,
            'pm2_position': pm_positions[1] if len(pm_positions) > 1 else 0,
            'pm3_position': pm_positions[2] if len(pm_positions) > 2 else 0,
            'pm4_position': pm_positions[3] if len(pm_positions) > 3 else 0,
            'lock_position': float(self.lock_position_input.text() or 0),
            'lock_y_offset': float(self.lock_y_offset_input.text() or 0),
            'lock_active': 1 if self.lock_active_check.isChecked() else 0,
            'hinge_y_offset': float(self.hinge_z_offset_input.text() or 0),
            'orientation': 'left' if self.left_radio.isChecked() else 'right',
        }
        
        # Add hinge $ variables
        for i in range(4):  # Always generate for 4 hinges
            if i < len(hinge_positions):
                dollar_vars[f'hinge{i+1}_position'] = hinge_positions[i]
                dollar_vars[f'hinge{i+1}_active'] = 1 if hinge_active[i] else 0
            else:
                dollar_vars[f'hinge{i+1}_position'] = 0
                dollar_vars[f'hinge{i+1}_active'] = 0
        
        # Add order $ variables
        order_map = {}
        for idx, item_id in enumerate(self.execution_order):
            order_map[item_id] = idx + 1
        
        # Lock order
        dollar_vars['lock_order'] = order_map.get('lock', 0)
        
        # Hinge orders
        for i in range(4):
            hinge_key = f'hinge{i+1}'
            dollar_vars[f'hinge{i+1}_order'] = order_map.get(hinge_key, 0)
        
        config = {
            'width': 1200,  # Fixed for now
            'height': dollar_vars['frame_height'],
            'x_offset': dollar_vars['machine_x_offset'],
            'y_offset': dollar_vars['machine_y_offset'],
            'z_offset': dollar_vars['machine_z_offset'],
            'pm_positions': pm_positions,
            'pm_auto': self.pm_auto_check.isChecked(),
            'lock_position': dollar_vars['lock_position'],
            'lock_y_offset': dollar_vars['lock_y_offset'],
            'lock_active': self.lock_active_check.isChecked(),
            'lock_auto': self.lock_auto_check.isChecked(),
            'hinge_count': self.hinge_count_spin.value(),
            'hinge_positions': hinge_positions,
            'hinge_active': hinge_active,
            'hinge_y_offset': float(self.hinge_z_offset_input.text() or 0),
            'hinge_auto': self.hinge_auto_check.isChecked(),
            'orientation': 'left' if self.left_radio.isChecked() else 'right',
            'execution_order': self.execution_order,
            'profiles': self.profiles,
            'profile_data': self.profile_data,  # Include full profile data
            'dollar_variables': dollar_vars  # $ variables for G-code replacement
        }
        
        return config
    
    def set_profiles(self, hinge_profile_name, lock_profile_name):
        """Set selected profiles from previous tab"""
        self.profiles = {
            'hinge': hinge_profile_name,
            'lock': lock_profile_name
        }
        
        # Initialize profile data structure for G-code storage
        if 'hinge' not in self.profile_data:
            self.profile_data['hinge'] = {
                'gcode_right': '',
                'gcode_left': ''
            }
        if 'lock' not in self.profile_data:
            self.profile_data['lock'] = {
                'gcode': ''
            }
        
        # Update order widget after profiles are set
        self.update_order_widget()
    
    def set_profile_data(self, hinge_profile_data, lock_profile_data):
        """Set full profile data from previous tab"""
        self.profile_data = {
            'hinge': hinge_profile_data or {'gcode_right': '', 'gcode_left': ''},
            'lock': lock_profile_data or {'gcode': ''}
        }
    
    def on_next_clicked(self):
        """Validate configuration and proceed"""
        config = self.get_configuration()
        
        if config['height'] <= 0:
            # In a real app, show error message
            return
        
        self.next_clicked.emit()
    
    def get_frame_gcode_data(self):
        """Get frame G-code data for saving"""
        return {
            'gcode_right': self.profile_data.get('hinge', {}).get('gcode_right', ''),
            'gcode_left': self.profile_data.get('hinge', {}).get('gcode_left', '')
        }
    
    def set_frame_gcode_data(self, frame_gcode_data):
        """Set frame G-code data from loading"""
        if 'hinge' not in self.profile_data:
            self.profile_data['hinge'] = {}
        
        self.profile_data['hinge']['gcode_right'] = frame_gcode_data.get('gcode_right', '')
        self.profile_data['hinge']['gcode_left'] = frame_gcode_data.get('gcode_left', '')
        
        # Update configuration to trigger generator update
        self.on_config_changed()