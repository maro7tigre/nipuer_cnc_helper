from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                             QLabel, QLineEdit, QComboBox, QCheckBox,
                             QGroupBox, QFormLayout, QSplitter, QButtonGroup,
                             QRadioButton, QSpinBox)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QDoubleValidator, QPainter, QColor, QPen, QBrush


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
        
        # Draw PMs large (removed the > 0 check)
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
        
        # Draw PMs small (removed the > 0 check)
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


class FrameTab(QWidget):
    """Frame configuration tab with three-panel layout"""
    back_clicked = Signal()
    next_clicked = Signal()
    configuration_changed = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.hinge_positions = []
        self.hinge_active = []
        self.profiles = {}
        
        self.setup_ui()
        self.connect_signals()
        self.apply_styling()
        
        # Initialize with default values
        self.update_hinge_count(2)
        # Set first PM to -25 as default
        self.pm_inputs[0].setText("-25")
        # Update auto positions after everything is setup
        self.update_all_auto_positions()
        self.on_config_changed()
    
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
        
        # Upper part - Frame dimensions and offsets
        upper_group = QGroupBox("Frame Configuration")
        upper_layout = QFormLayout()
        upper_group.setLayout(upper_layout)
        
        # Frame height with minimum value enforcement
        self.height_input = QLineEdit("2100")
        self.height_input.setValidator(QDoubleValidator(840, 10000, 2))
        upper_layout.addRow("Frame Height (mm):", self.height_input)
        
        # Machine offsets
        self.x_offset_input = QLineEdit("0")
        self.x_offset_input.setValidator(QDoubleValidator(-1000, 1000, 2))
        upper_layout.addRow("Machine X Offset:", self.x_offset_input)
        
        self.y_offset_input = QLineEdit("0")
        self.y_offset_input.setValidator(QDoubleValidator(-1000, 1000, 2))
        upper_layout.addRow("Machine Y Offset:", self.y_offset_input)
        
        self.z_offset_input = QLineEdit("0")
        self.z_offset_input.setValidator(QDoubleValidator(-1000, 1000, 2))
        upper_layout.addRow("Machine Z Offset:", self.z_offset_input)
        
        layout.addWidget(upper_group)
        
        # Lower part - PM positions
        pm_group = QGroupBox("PM Positions")
        pm_layout = QVBoxLayout()
        pm_group.setLayout(pm_layout)
        
        # PM auto checkbox
        self.pm_auto_check = QCheckBox("Auto-position")
        self.pm_auto_check.setChecked(True)
        pm_layout.addWidget(self.pm_auto_check)
        
        # PM position inputs container
        self.pm_inputs_widget = QWidget()
        pm_inputs_layout = QFormLayout(self.pm_inputs_widget)
        pm_layout.addWidget(self.pm_inputs_widget)
        
        # PM position inputs
        self.pm_inputs = []
        for i in range(4):
            pm_input = QLineEdit("0")
            pm_input.setValidator(QDoubleValidator(-100, 10000, 2))
            pm_inputs_layout.addRow(f"PM{i+1} Position:", pm_input)
            self.pm_inputs.append(pm_input)
        
        layout.addWidget(pm_group)
        layout.addStretch()
        
        return widget
    
    def create_middle_panel(self):
        """Create middle panel with preview and orientation switch"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Orientation switch
        orientation_group = QGroupBox("Door Orientation")
        orientation_layout = QHBoxLayout()
        orientation_group.setLayout(orientation_layout)
        
        self.orientation_group = QButtonGroup()
        self.right_radio = QRadioButton("Right")
        self.left_radio = QRadioButton("Left")
        self.right_radio.setChecked(True)
        
        self.orientation_group.addButton(self.right_radio)
        self.orientation_group.addButton(self.left_radio)
        
        orientation_layout.addWidget(self.right_radio)
        orientation_layout.addWidget(self.left_radio)
        orientation_layout.addStretch()
        
        layout.addWidget(orientation_group)
        
        # Preview area
        self.preview = FramePreview()
        layout.addWidget(self.preview, 1)
        
        return widget
    
    def create_right_panel(self):
        """Create right panel with lock and hinge configuration"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Upper part - Lock configuration
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
        self.lock_position_input.setValidator(QDoubleValidator(0, 10000, 2))
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
        
        # Lower part - Hinge configuration
        hinge_group = QGroupBox("Hinge Configuration")
        hinge_layout = QVBoxLayout()
        hinge_group.setLayout(hinge_layout)
        
        # Hinge count selector
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Number of Hinges:"))
        self.hinge_count_spin = QSpinBox()
        self.hinge_count_spin.setRange(0, 4)
        self.hinge_count_spin.setValue(2)
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
        layout.addStretch()
        
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
            pm_input.textChanged.connect(self.on_config_changed)
        
        # Lock configuration
        self.lock_auto_check.stateChanged.connect(self.on_lock_auto_changed)
        self.lock_position_input.textChanged.connect(self.on_lock_position_changed)
        self.lock_active_check.stateChanged.connect(self.on_config_changed)
        self.lock_y_offset_input.textChanged.connect(self.on_config_changed)
        
        # Hinge configuration
        self.hinge_count_spin.valueChanged.connect(self.update_hinge_count)
        self.hinge_auto_check.stateChanged.connect(self.on_hinge_auto_changed)
        self.hinge_z_offset_input.textChanged.connect(self.on_config_changed)
        
        # Orientation
        self.orientation_group.buttonClicked.connect(self.on_config_changed)
    
    def enforce_min_height(self):
        """Enforce minimum frame height of 840mm"""
        try:
            height = float(self.height_input.text() or 0)
            if height < 840:
                self.height_input.setText("840")
        except ValueError:
            self.height_input.setText("840")
    
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
            # Create horizontal layout for each hinge
            hinge_layout = QHBoxLayout()
            
            hinge_layout.addWidget(QLabel(f"Hinge {i+1}:"))
            
            # Position input
            position_input = QLineEdit("0")
            position_input.setValidator(QDoubleValidator(0, 10000, 2))
            position_input.textChanged.connect(self.on_hinge_position_changed)
            hinge_layout.addWidget(position_input)
            self.hinge_inputs.append(position_input)
            
            # Active checkbox
            active_check = QCheckBox("Active")
            active_check.setChecked(True)
            active_check.stateChanged.connect(self.on_config_changed)
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
        """Handle lock position changes - triggers PM auto update"""
        self.update_all_auto_positions()
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
        """Handle hinge position changes - triggers PM auto update"""
        self.update_all_auto_positions()
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
        
        # Validate PM positions
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
                    # If first is at 150 and last at last_pos:
                    # middle = first + (last - first) / 2.5
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
                    # Total distance = last_pos - 150
                    # If d1 is first distance, then d2 = 1.5*d1, d3 = 1.5*d2 = 2.25*d1
                    # Total = d1 + d2 + d3 = d1 + 1.5*d1 + 2.25*d1 = 4.75*d1
                    total_distance = last_pos - 150
                    d1 = total_distance / 4.75
                    
                    self.hinge_inputs[1].setText(f"{150 + d1:.1f}")
                    self.hinge_inputs[2].setText(f"{150 + d1 + 1.5*d1:.1f}")
                    # Fourth position is already set as last_pos
        except ValueError:
            pass
    
    def calculate_auto_pm_positions(self):
        """Calculate automatic PM positions based on rules and constraints"""
        try:
            height = float(self.height_input.text() or 0)
            
            if height <= 0:
                return
            
            # Get lock position
            lock_pos = float(self.lock_position_input.text() or 0)
            
            # Get active hinge positions
            hinge_positions = []
            for i, (input_field, check) in enumerate(zip(self.hinge_inputs, self.hinge_active_checks)):
                if check.isChecked():
                    try:
                        pos = float(input_field.text() or 0)
                        if pos > 0:
                            hinge_positions.append(pos)
                    except ValueError:
                        pass
            
            # First PM is always at -25 (set by user or default)
            pm1_pos = float(self.pm_inputs[0].text() or -25)
            
            # Calculate positions for PM 2, 3, and 4
            # Rules:
            # 1. PM1-PM2 >= 265
            # 2. PM2-PM3 >= 140
            # 3. PM3-PM4 >= 175
            # 4. PM1-PM4 < height - 240
            # 5. Stay away from lock and hinges (>= 170)
            
            # Maximum span available
            max_span = height - 240 - pm1_pos
            
            # Minimum required distances
            min_distances = [265, 140, 175]  # PM1-2, PM2-3, PM3-4
            min_total = sum(min_distances)
            
            if max_span < min_total:
                # Can't satisfy all constraints, use minimum distances
                pm2_pos = pm1_pos + 265
                pm3_pos = pm2_pos + 140
                pm4_pos = pm3_pos + 175
            else:
                # Create list of all obstacles (lock and hinges)
                obstacles = [lock_pos] + hinge_positions
                obstacles.sort()
                
                # Try to distribute PMs optimally
                # Start with minimum distances
                positions = [pm1_pos]
                positions.append(pm1_pos + 265)
                positions.append(positions[1] + 140)
                positions.append(positions[2] + 175)
                
                # If we have extra space, distribute it
                extra_space = max_span - min_total
                if extra_space > 0:
                    # Add extra space proportionally to each gap
                    # Favor larger gaps between lower PMs
                    weights = [3, 2, 1]  # More space between PM1-2, less between PM3-4
                    total_weight = sum(weights)
                    
                    for i in range(3):
                        extra = extra_space * weights[i] / total_weight
                        positions[i+1] += extra * (i+1)  # Cumulative effect
                
                # Adjust positions to avoid obstacles
                for i in range(1, 4):
                    # Check distance from obstacles
                    for obstacle in obstacles:
                        if abs(positions[i] - obstacle) < 170:
                            # Too close to obstacle, adjust
                            if positions[i] < obstacle:
                                # Move PM before obstacle
                                new_pos = obstacle - 170
                                if i > 1 and new_pos - positions[i-1] < min_distances[i-1]:
                                    # Would violate minimum distance, move after obstacle
                                    new_pos = obstacle + 170
                            else:
                                # Move PM after obstacle
                                new_pos = obstacle + 170
                            
                            # Check if new position is valid
                            if i < 3:
                                # Make sure we don't push next PMs too far
                                remaining_space = height - 240 - new_pos
                                remaining_distances = sum(min_distances[i:])
                                if remaining_space >= remaining_distances:
                                    positions[i] = new_pos
                
                pm2_pos = positions[1]
                pm3_pos = positions[2]
                pm4_pos = positions[3]
            
            # Update PM inputs (skip PM1 as it's user-controlled)
            self.pm_inputs[1].setText(f"{pm2_pos:.1f}")
            self.pm_inputs[2].setText(f"{pm3_pos:.1f}")
            self.pm_inputs[3].setText(f"{pm4_pos:.1f}")
            
        except ValueError:
            pass
    
    def validate_pm_positions(self):
        """Validate PM positions and mark errors with red borders"""
        try:
            # Reset all borders first
            for pm_input in self.pm_inputs:
                pm_input.setProperty("class", "")
                pm_input.style().polish(pm_input)
            
            # Get all positions
            pm_positions = []
            for pm_input in self.pm_inputs:
                try:
                    pos = float(pm_input.text() or 0)
                    pm_positions.append(pos)
                except ValueError:
                    pm_positions.append(0)
            
            # Get lock and hinge positions
            lock_pos = float(self.lock_position_input.text() or 0)
            height = float(self.height_input.text() or 0)
            
            hinge_positions = []
            for i, (input_field, check) in enumerate(zip(self.hinge_inputs, self.hinge_active_checks)):
                if check.isChecked():
                    try:
                        pos = float(input_field.text() or 0)
                        if pos > 0:
                            hinge_positions.append(pos)
                    except ValueError:
                        pass
            
            # Check rules in order of priority
            errors = [False] * 4
            
            # Rule 1: Order must be maintained (PM1 < PM2 < PM3 < PM4)
            for i in range(3):
                if pm_positions[i] >= pm_positions[i+1]:
                    errors[i] = True
                    errors[i+1] = True
            
            # Rule 2: Minimum distances
            min_distances = [265, 140, 175]  # PM1-2, PM2-3, PM3-4
            for i in range(3):
                if pm_positions[i+1] - pm_positions[i] < min_distances[i]:
                    errors[i] = True
                    errors[i+1] = True
            
            # Rule 3: Total span < height - 240
            if pm_positions[3] - pm_positions[0] >= height - 240:
                # Mark all as errors since total span is too large
                for i in range(4):
                    errors[i] = True
            
            # Rule 4: Distance from lock and hinges >= 170
            obstacles = [lock_pos] + hinge_positions
            for i, pm_pos in enumerate(pm_positions):
                for obstacle in obstacles:
                    if abs(pm_pos - obstacle) < 170:
                        errors[i] = True
            
            # Apply error styling
            for i, (pm_input, has_error) in enumerate(zip(self.pm_inputs, errors)):
                if has_error:
                    pm_input.setProperty("class", "error")
                    pm_input.style().polish(pm_input)
                    
        except ValueError:
            pass
    
    def on_config_changed(self):
        """Handle any configuration change"""
        config = self.get_configuration()
        self.preview.update_config(config)
        self.configuration_changed.emit(config)
    
    def get_configuration(self):
        """Get current frame configuration"""
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
        
        config = {
            'width': 1200,  # Fixed for now
            'height': float(self.height_input.text() or 0),
            'x_offset': float(self.x_offset_input.text() or 0),
            'y_offset': float(self.y_offset_input.text() or 0),
            'z_offset': float(self.z_offset_input.text() or 0),
            'pm_positions': pm_positions,
            'pm_auto': self.pm_auto_check.isChecked(),
            'lock_position': float(self.lock_position_input.text() or 0),
            'lock_y_offset': float(self.lock_y_offset_input.text() or 0),
            'lock_active': self.lock_active_check.isChecked(),
            'lock_auto': self.lock_auto_check.isChecked(),
            'hinge_count': self.hinge_count_spin.value(),
            'hinge_positions': hinge_positions,
            'hinge_active': hinge_active,
            'hinge_y_offset': float(self.hinge_z_offset_input.text() or 0),
            'hinge_auto': self.hinge_auto_check.isChecked(),
            'orientation': 'left' if self.left_radio.isChecked() else 'right',
            'profiles': self.profiles
        }
        
        return config
    
    def set_profiles(self, hinge_profile, lock_profile):
        """Set selected profiles from previous tab"""
        self.profiles = {
            'hinge': hinge_profile,
            'lock': lock_profile
        }
    
    def on_next_clicked(self):
        """Validate configuration and proceed"""
        # Basic validation
        config = self.get_configuration()
        
        if config['height'] <= 0:
            # In a real app, show error message
            return
        
        self.next_clicked.emit()