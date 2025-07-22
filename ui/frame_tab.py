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
        scale = min(widget_height / (self.frame_height + 200), 
                   widget_width / (self.frame_width * 2 + 500))
        
        frame_height_scaled = self.frame_height * scale
        frame_width_scaled = 100  # Fixed visual width
        frame_gap = 35  # Gap between frames
        
        # Center the drawing
        total_width = frame_width_scaled * 2 + frame_gap
        start_x = (widget_width - total_width) / 2
        start_y = (widget_height - frame_height_scaled) / 2
        
        # Draw frames
        # First frame (left)
        painter.setBrush(QBrush(QColor(139, 69, 19)))  # Dark brown
        painter.setPen(QPen(QColor(101, 67, 33), 2))
        painter.drawRect(start_x, start_y, frame_width_scaled/2, frame_height_scaled)
        
        painter.setBrush(QBrush(QColor(160, 82, 45)))  # Light brown
        painter.drawRect(start_x + frame_width_scaled/2, start_y, frame_width_scaled/2, frame_height_scaled)
        
        # Second frame (right) - mirrored
        painter.setBrush(QBrush(QColor(160, 82, 45)))  # Light brown
        painter.drawRect(start_x + frame_width_scaled + frame_gap, start_y, frame_width_scaled/2, frame_height_scaled)
        
        painter.setBrush(QBrush(QColor(139, 69, 19)))  # Dark brown
        painter.drawRect(start_x + frame_width_scaled * 1.5 + frame_gap, start_y, frame_width_scaled/2, frame_height_scaled)
        
        # Draw PMs
        painter.setBrush(QBrush(QColor(128, 128, 128)))  # Grey
        painter.setPen(QPen(QColor(64, 64, 64), 2))
        
        for pm_pos in self.pm_positions:
            if pm_pos > 0:  # Only draw if position is set
                pm_y = start_y + frame_height_scaled - (pm_pos * scale)
                # Large rectangle below frames
                painter.setBrush(QBrush(QColor(128, 128, 128)))
                painter.drawRect(start_x - 100, pm_y - 65, 300, 130)
                # Small rectangle above frames
                painter.setBrush(QBrush(QColor(192, 192, 192)))  # Lighter grey
                painter.drawRect(start_x + 9, pm_y - 76 - 152, 82, 152)
        
        # Draw lock
        if self.lock_active and self.lock_position > 0:
            painter.setBrush(QBrush(QColor(0, 255, 0)))  # Green
            painter.setPen(QPen(QColor(0, 128, 0), 2))
            
            lock_y = start_y + frame_height_scaled - (self.lock_position * scale)
            lock_width = 35
            lock_height = 180
            
            if self.orientation == "right":
                lock_x = start_x - 20 - lock_width - self.lock_y_offset
            else:  # left
                lock_x = start_x + total_width + 20 + self.lock_y_offset
            
            painter.drawRect(lock_x, lock_y - lock_height/2, lock_width, lock_height)
        
        # Draw hinges
        painter.setBrush(QBrush(QColor(0, 0, 255)))  # Blue
        painter.setPen(QPen(QColor(0, 0, 128), 2))
        
        for i, (hinge_pos, active) in enumerate(zip(self.hinge_positions, self.hinge_active)):
            if active and hinge_pos > 0:
                hinge_y = start_y + frame_height_scaled - (hinge_pos * scale)
                hinge_width = 20
                hinge_height = 80
                
                if self.orientation == "right":
                    hinge_x = start_x + total_width + 20 + self.hinge_y_offset
                else:  # left
                    hinge_x = start_x - 20 - hinge_width - self.hinge_y_offset
                
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
        
        # Frame height
        self.height_input = QLineEdit("2100")
        self.height_input.setValidator(QDoubleValidator(0, 10000, 2))
        upper_layout.addRow("Frame Height (mm):", self.height_input)
        
        # Machine offsets
        self.x_offset_input = QLineEdit("0")
        self.x_offset_input.setValidator(QDoubleValidator(-1000, 1000, 2))
        upper_layout.addRow("Machine X Offset:", self.x_offset_input)
        
        self.z_offset_input = QLineEdit("0")
        self.z_offset_input.setValidator(QDoubleValidator(-1000, 1000, 2))
        upper_layout.addRow("Machine Z Offset:", self.z_offset_input)
        
        layout.addWidget(upper_group)
        
        # Lower part - PM positions
        pm_group = QGroupBox("PM Positions")
        pm_layout = QFormLayout()
        pm_group.setLayout(pm_layout)
        
        # PM position inputs
        self.pm_inputs = []
        for i in range(4):
            pm_input = QLineEdit("0")
            pm_input.setValidator(QDoubleValidator(0, 10000, 2))
            pm_layout.addRow(f"PM{i+1} Position:", pm_input)
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
        
        lock_auto_layout.addWidget(QLabel("X Position:"))
        self.lock_position_input = QLineEdit()
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
        self.x_offset_input.textChanged.connect(self.on_config_changed)
        self.z_offset_input.textChanged.connect(self.on_config_changed)
        
        # PM position changes
        for pm_input in self.pm_inputs:
            pm_input.textChanged.connect(self.on_config_changed)
        
        # Lock configuration
        self.lock_auto_check.stateChanged.connect(self.on_lock_auto_changed)
        self.lock_position_input.textChanged.connect(self.on_config_changed)
        self.lock_active_check.stateChanged.connect(self.on_config_changed)
        self.lock_y_offset_input.textChanged.connect(self.on_config_changed)
        
        # Hinge configuration
        self.hinge_count_spin.valueChanged.connect(self.update_hinge_count)
        self.hinge_auto_check.stateChanged.connect(self.on_hinge_auto_changed)
        self.hinge_z_offset_input.textChanged.connect(self.on_config_changed)
        
        # Orientation
        self.orientation_group.buttonClicked.connect(self.on_config_changed)
    
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
            position_input = QLineEdit()
            position_input.setValidator(QDoubleValidator(0, 10000, 2))
            position_input.textChanged.connect(self.on_config_changed)
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
        
        # Calculate auto positions if enabled
        if self.hinge_auto_check.isChecked():
            self.calculate_auto_positions()
        
        self.on_config_changed()
    
    def on_frame_height_changed(self):
        """Handle frame height changes"""
        # Update lock position if auto
        if self.lock_auto_check.isChecked():
            self.calculate_lock_position()
        
        # Update hinge positions if auto
        if self.hinge_auto_check.isChecked():
            self.calculate_auto_positions()
        
        self.on_config_changed()
    
    def on_lock_auto_changed(self):
        """Handle lock auto checkbox changes"""
        auto_enabled = self.lock_auto_check.isChecked()
        self.lock_position_input.setEnabled(not auto_enabled)
        
        if auto_enabled:
            self.calculate_lock_position()
        
        self.on_config_changed()
    
    def calculate_lock_position(self):
        """Calculate automatic lock position (middle of frame)"""
        try:
            height = float(self.height_input.text() or 0)
            lock_pos = height / 2
            self.lock_position_input.setText(f"{lock_pos:.1f}")
        except ValueError:
            pass
    
    def on_hinge_auto_changed(self):
        """Handle hinge auto checkbox changes"""
        auto_enabled = self.hinge_auto_check.isChecked()
        
        # Enable/disable position inputs
        for input_field in self.hinge_inputs:
            input_field.setEnabled(not auto_enabled)
        
        if auto_enabled:
            self.calculate_auto_positions()
        
        self.on_config_changed()
    
    def calculate_auto_positions(self):
        """Calculate automatic hinge positions with equal spacing"""
        try:
            height = float(self.height_input.text() or 0)
            count = len(self.hinge_inputs)
            
            if count > 0 and height > 0:
                # Calculate equal spacing
                spacing = height / (count + 1)
                
                for i, input_field in enumerate(self.hinge_inputs):
                    position = spacing * (i + 1)
                    input_field.setText(f"{position:.1f}")
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
            'z_offset': float(self.z_offset_input.text() or 0),
            'pm_positions': pm_positions,
            'lock_position': float(self.lock_position_input.text() or 0),
            'lock_y_offset': float(self.lock_y_offset_input.text() or 0),
            'lock_active': self.lock_active_check.isChecked(),
            'hinge_count': self.hinge_count_spin.value(),
            'hinge_positions': hinge_positions,
            'hinge_active': hinge_active,
            'hinge_y_offset': float(self.hinge_z_offset_input.text() or 0),
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