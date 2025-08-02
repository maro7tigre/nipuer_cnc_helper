"""
Frame Tab

Simplified frame configuration tab that works with centralized main_window data management.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QButtonGroup
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QDoubleValidator

from ..widgets.themed_widgets import (ThemedSplitter, ThemedLabel, ThemedLineEdit, ThemedCheckBox, 
                                    ThemedRadioButton, ThemedSpinBox, ThemedGroupBox, PurpleButton, GreenButton)
from ..widgets.simple_widgets import ClickableLabel, ErrorLineEdit
from .widgets.frame_preview import FramePreview
from .widgets.order_widget import OrderWidget


class FrameTab(QWidget):
    """Simplified frame configuration tab that uses main_window for all data management"""
    back_clicked = Signal()
    next_clicked = Signal()
    
    # Configuration parameters - easily adjustable
    MAX_FRAME_HEIGHT = 2500
    MIN_FRAME_HEIGHT = 840
    
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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.hinge_positions = []
        self.hinge_active = []
        self.execution_order = []
        
        self.setup_ui()
        self.apply_styling()
        self.connect_signals()
        
        # Subscribe to main_window events
        if self.main_window:
            self.main_window.events.subscribe('profiles', self.on_profiles_updated)
            self.main_window.events.subscribe('variables', self.on_variables_updated)
        
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
    
    def apply_styling(self):
        """Apply dark theme styling"""
        self.setStyleSheet("""
            FrameTab {
                background-color: #282a36;
                color: #ffffff;
            }
        """)
    
    def setup_ui(self):
        """Initialize user interface with three-panel layout"""
        main_layout = QVBoxLayout(self)
        
        # Content area with splitter
        content_splitter = ThemedSplitter(Qt.Horizontal)
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
        frame_group = ThemedGroupBox("Frame Configuration")
        frame_layout = QFormLayout()
        frame_group.setLayout(frame_layout)
        
        # Frame height with min/max validation
        self.height_input = ThemedLineEdit("2100")
        self.height_input.setValidator(QDoubleValidator(self.MIN_FRAME_HEIGHT, self.MAX_FRAME_HEIGHT, 2))
        frame_layout.addRow("Frame Height (mm):", self.height_input)
        
        # Machine offsets
        self.x_offset_input = ThemedLineEdit("0")
        self.x_offset_input.setValidator(QDoubleValidator(-1000, 1000, 2))
        frame_layout.addRow("Machine X Offset:", self.x_offset_input)
        
        self.y_offset_input = ThemedLineEdit("0")
        self.y_offset_input.setValidator(QDoubleValidator(-1000, 1000, 2))
        frame_layout.addRow("Machine Y Offset:", self.y_offset_input)
        
        self.z_offset_input = ThemedLineEdit("0")
        self.z_offset_input.setValidator(QDoubleValidator(-1000, 1000, 2))
        frame_layout.addRow("Machine Z Offset:", self.z_offset_input)
        
        layout.addWidget(frame_group)
        
        # PM positions group
        pm_group = ThemedGroupBox("PM Positions")
        pm_layout = QVBoxLayout()
        pm_group.setLayout(pm_layout)
        
        # PM auto checkbox
        self.pm_auto_check = ThemedCheckBox("Auto-position")
        self.pm_auto_check.setChecked(False)  # Default to unchecked
        pm_layout.addWidget(self.pm_auto_check)
        
        # PM position inputs
        self.pm_inputs_widget = QWidget()
        pm_inputs_layout = QFormLayout(self.pm_inputs_widget)
        pm_layout.addWidget(self.pm_inputs_widget)
        
        self.pm_inputs = []
        for i in range(4):
            pm_input = ErrorLineEdit("0")
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
        orientation_group = ThemedGroupBox("Door Orientation")
        orientation_layout = QVBoxLayout()
        orientation_group.setLayout(orientation_layout)
        
        # Radio buttons layout
        radio_layout = QHBoxLayout()
        
        self.orientation_group = QButtonGroup()
        self.right_radio = ThemedRadioButton("Right (droite)")
        self.left_radio = ThemedRadioButton("Left (gauche)")
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
        lock_group = ThemedGroupBox("Lock Configuration")
        lock_layout = QVBoxLayout()
        lock_group.setLayout(lock_layout)
        
        # Auto checkbox and position
        lock_auto_layout = QHBoxLayout()
        self.lock_auto_check = ThemedCheckBox("Auto")
        self.lock_auto_check.setChecked(True)
        lock_auto_layout.addWidget(self.lock_auto_check)
        
        lock_auto_layout.addWidget(ThemedLabel("Position:"))
        self.lock_position_input = ThemedLineEdit("1050")
        self.lock_position_input.setValidator(QDoubleValidator(0, self.MAX_FRAME_HEIGHT, 2))
        self.lock_position_input.setEnabled(False)
        lock_auto_layout.addWidget(self.lock_position_input)
        
        self.lock_active_check = ThemedCheckBox("Active")
        self.lock_active_check.setChecked(True)
        lock_auto_layout.addWidget(self.lock_active_check)
        
        lock_layout.addLayout(lock_auto_layout)
        
        # Lock Y offset
        lock_offset_layout = QHBoxLayout()
        lock_offset_layout.addWidget(ThemedLabel("Y Offset:"))
        self.lock_y_offset_input = ThemedLineEdit("0")
        self.lock_y_offset_input.setValidator(QDoubleValidator(-100, 100, 2))
        lock_offset_layout.addWidget(self.lock_y_offset_input)
        lock_layout.addLayout(lock_offset_layout)
        
        layout.addWidget(lock_group)
        
        # Hinge configuration
        hinge_group = ThemedGroupBox("Hinge Configuration")
        hinge_layout = QVBoxLayout()
        hinge_group.setLayout(hinge_layout)
        
        # Hinge count selector
        count_layout = QHBoxLayout()
        count_layout.addWidget(ThemedLabel("Number of Hinges:"))
        self.hinge_count_spin = ThemedSpinBox()
        self.hinge_count_spin.setRange(0, 4)
        self.hinge_count_spin.setValue(3)  # Default to 3
        count_layout.addWidget(self.hinge_count_spin)
        count_layout.addStretch()
        hinge_layout.addLayout(count_layout)
        
        # Auto checkbox
        self.hinge_auto_check = ThemedCheckBox("Auto-position")
        self.hinge_auto_check.setChecked(True)
        hinge_layout.addWidget(self.hinge_auto_check)
        
        # Hinge positions container
        self.hinge_positions_widget = QWidget()
        self.hinge_positions_layout = QVBoxLayout(self.hinge_positions_widget)
        self.hinge_positions_layout.setContentsMargins(0, 0, 0, 0)
        hinge_layout.addWidget(self.hinge_positions_widget)
        
        # Z offset for all hinges
        z_offset_layout = QHBoxLayout()
        z_offset_layout.addWidget(ThemedLabel("Z Offset (all):"))
        self.hinge_z_offset_input = ThemedLineEdit("0")
        self.hinge_z_offset_input.setValidator(QDoubleValidator(-100, 100, 2))
        z_offset_layout.addWidget(self.hinge_z_offset_input)
        hinge_layout.addLayout(z_offset_layout)
        
        layout.addWidget(hinge_group)
        
        # Execution order widget - now resizable
        order_group = ThemedGroupBox("Component Order")
        order_layout = QVBoxLayout()
        order_group.setLayout(order_layout)
        
        self.order_widget = OrderWidget()
        self.order_widget.order_changed.connect(self.on_order_changed)
        order_layout.addWidget(self.order_widget, 1)  # Give it stretch factor
        
        layout.addWidget(order_group, 1)  # Give order group stretch
        
        return widget
    
    def create_navigation(self):
        """Create bottom navigation buttons"""
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()
        
        self.back_button = PurpleButton("← Back")
        self.next_button = GreenButton("Next →")
        
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
    
    def on_profiles_updated(self):
        """Handle profiles updated from main_window"""
        # Nothing specific to do - preview might update itself
        pass
    
    def on_variables_updated(self):
        """Handle variables updated from main_window"""
        # Update UI from main_window variables
        self.load_from_main_window()
    
    def load_from_main_window(self):
        """Load configuration from main_window variables"""
        if not self.main_window:
            return
        
        dollar_vars = self.main_window.get_dollar_variable()
        
        # Update UI elements
        self.height_input.setText(str(dollar_vars.get("frame_height", 2100)))
        self.x_offset_input.setText(str(dollar_vars.get("machine_x_offset", 0)))
        self.y_offset_input.setText(str(dollar_vars.get("machine_y_offset", 0)))
        self.z_offset_input.setText(str(dollar_vars.get("machine_z_offset", 0)))
        
        # PM positions
        for i in range(4):
            pm_key = f"pm{i+1}_position"
            self.pm_inputs[i].setText(str(dollar_vars.get(pm_key, 0)))
        
        # Lock configuration
        self.lock_position_input.setText(str(dollar_vars.get("lock_position", 1050)))
        self.lock_y_offset_input.setText(str(dollar_vars.get("lock_y_offset", 0)))
        self.lock_active_check.setChecked(bool(dollar_vars.get("lock_active", 1)))
        
        # Hinge configuration
        self.hinge_z_offset_input.setText(str(dollar_vars.get("hinge_y_offset", 0)))
        
        # Hinge positions and active states
        for i in range(4):
            pos_key = f"hinge{i+1}_position"
            active_key = f"hinge{i+1}_active"
            
            if i < len(self.hinge_inputs):
                self.hinge_inputs[i].setText(str(dollar_vars.get(pos_key, 0)))
            if i < len(self.hinge_active_checks):
                self.hinge_active_checks[i].setChecked(bool(dollar_vars.get(active_key, 0)))
        
        # Orientation
        orientation = dollar_vars.get("orientation", "right")
        if orientation == "left":
            self.left_radio.setChecked(True)
        else:
            self.right_radio.setChecked(True)
    
    def update_main_window_variables(self):
        """Update main_window with current configuration"""
        if not self.main_window:
            return
        
        # Gather all variables from UI
        variables = {}
        
        # Frame and machine settings
        variables["frame_height"] = float(self.height_input.text() or 0)
        variables["frame_width"] = 1200  # Fixed
        variables["machine_x_offset"] = float(self.x_offset_input.text() or 0)
        variables["machine_y_offset"] = float(self.y_offset_input.text() or 0)
        variables["machine_z_offset"] = float(self.z_offset_input.text() or 0)
        
        # PM positions
        for i, pm_input in enumerate(self.pm_inputs):
            variables[f"pm{i+1}_position"] = float(pm_input.text() or 0)
        
        # Lock configuration
        variables["lock_position"] = float(self.lock_position_input.text() or 0)
        variables["lock_y_offset"] = float(self.lock_y_offset_input.text() or 0)
        variables["lock_active"] = 1 if self.lock_active_check.isChecked() else 0
        
        # Hinge configuration
        variables["hinge_y_offset"] = float(self.hinge_z_offset_input.text() or 0)
        
        # Hinge positions and active states
        for i in range(4):
            if i < len(self.hinge_inputs):
                variables[f"hinge{i+1}_position"] = float(self.hinge_inputs[i].text() or 0)
            else:
                variables[f"hinge{i+1}_position"] = 0
            
            if i < len(self.hinge_active_checks):
                variables[f"hinge{i+1}_active"] = 1 if self.hinge_active_checks[i].isChecked() else 0
            else:
                variables[f"hinge{i+1}_active"] = 0
        
        # Orientation
        variables["orientation"] = "left" if self.left_radio.isChecked() else "right"
        
        # Order variables
        order_map = {}
        for idx, item_id in enumerate(self.execution_order):
            order_map[item_id] = idx + 1
        
        variables["lock_order"] = order_map.get("lock", 0)
        for i in range(4):
            variables[f"hinge{i+1}_order"] = order_map.get(f"hinge{i+1}", 0)
        
        # Update main_window
        self.main_window.update_dollar_variables(variables)
    
    # All the existing methods for PM positions, lock, hinges, etc.
    # (keeping the same auto-position calculation logic)
    
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
            
            hinge_layout.addWidget(ThemedLabel(f"Hinge {i+1}:"))
            
            # Position input
            position_input = ThemedLineEdit("0")
            position_input.setValidator(QDoubleValidator(0, self.MAX_FRAME_HEIGHT, 2))
            position_input.textChanged.connect(self.on_hinge_position_changed)
            hinge_layout.addWidget(position_input)
            self.hinge_inputs.append(position_input)
            
            # Active checkbox
            active_check = ThemedCheckBox("Active")
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
    
    # Keep all the existing auto-position calculation methods
    def on_frame_height_changed(self):
        self.update_all_auto_positions()
        self.on_config_changed()
    
    def on_lock_auto_changed(self):
        auto_enabled = self.lock_auto_check.isChecked()
        self.lock_position_input.setEnabled(not auto_enabled)
        if auto_enabled:
            self.update_all_auto_positions()
        self.on_config_changed()
    
    def on_lock_position_changed(self):
        self.update_all_auto_positions()
        self.on_config_changed()
    
    def on_lock_active_changed(self):
        self.update_order_widget()
        self.on_config_changed()
    
    def on_hinge_auto_changed(self):
        auto_enabled = self.hinge_auto_check.isChecked()
        for input_field in self.hinge_inputs:
            input_field.setEnabled(not auto_enabled)
        if auto_enabled:
            self.update_all_auto_positions()
        self.on_config_changed()
    
    def on_hinge_position_changed(self):
        self.update_all_auto_positions()
        self.on_config_changed()
    
    def on_hinge_active_changed(self):
        self.update_order_widget()
        self.on_config_changed()
    
    def on_pm_auto_changed(self):
        auto_enabled = self.pm_auto_check.isChecked()
        for i, input_field in enumerate(self.pm_inputs):
            if i == 0:  # First PM is always editable
                input_field.setEnabled(True)
            else:
                input_field.setEnabled(not auto_enabled)
        if auto_enabled:
            self.update_all_auto_positions()
        self.on_config_changed()
    
    def on_order_changed(self, order):
        self.execution_order = order
        self.on_config_changed()
    
    def update_order_widget(self):
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
        # Simplified version - just use minimum distances
        pm1_pos = float(self.pm_inputs[0].text() or -25)
        self._fallback_pm_positions(pm1_pos)
    
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
        # Reset all borders first
        for pm_input in self.pm_inputs:
            pm_input.set_error(False)
        
        # Basic validation - can be expanded
        # For now, just ensure they're in ascending order
        positions = []
        for pm_input in self.pm_inputs:
            try:
                pos = float(pm_input.text() or 0)
                positions.append(pos)
            except ValueError:
                pm_input.set_error(True)
                positions.append(0)
        
        # Check ascending order
        for i in range(1, len(positions)):
            if positions[i] <= positions[i-1]:
                self.pm_inputs[i].set_error(True)
    
    def edit_right_gcode(self):
        """Open G-code editor for right orientation"""
        from ..dialogs.gcode_dialog import ProfileGCodeDialog
        from PySide6.QtWidgets import QDialog
        
        # Get current G-code for right orientation from main_window
        current_gcode = self.main_window.get_current_gcode("right_gcode")
        
        dialog = ProfileGCodeDialog("Right Door G-Code", current_gcode, self)
        if dialog.exec_() == QDialog.Accepted:
            # Update main_window with new G-code
            new_gcode = dialog.get_gcode()
            self.main_window.update_current_gcodes("right_gcode", new_gcode)
    
    def edit_left_gcode(self):
        """Open G-code editor for left orientation"""
        from ..dialogs.gcode_dialog import ProfileGCodeDialog
        from PySide6.QtWidgets import QDialog
        
        # Get current G-code for left orientation from main_window
        current_gcode = self.main_window.get_current_gcode("left_gcode")
        
        dialog = ProfileGCodeDialog("Left Door G-Code", current_gcode, self)
        if dialog.exec_() == QDialog.Accepted:
            # Update main_window with new G-code
            new_gcode = dialog.get_gcode()
            self.main_window.update_current_gcodes("left_gcode", new_gcode)
    
    def on_config_changed(self):
        """Handle any configuration change"""
        # Update main_window with new variables
        self.update_main_window_variables()
        
        # Update preview
        config = self.get_configuration()
        self.preview.update_config(config)
    
    def get_configuration(self):
        """Get current frame configuration for preview"""
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
            'execution_order': self.execution_order,
        }
        
        return config
    
    def on_next_clicked(self):
        """Validate configuration and proceed"""
        config = self.get_configuration()
        
        if config['height'] <= 0:
            # In a real app, show error message
            return
        
        self.next_clicked.emit()
    
    def get_app_config(self):
        """Get tab configuration for saving"""
        return {
            "frame_config": self.get_configuration()
        }
    
    def set_app_config(self, config):
        """Set tab configuration from loading"""
        frame_config = config.get("frame_config", {})
        
        # Update main_window with frame config
        if self.main_window and frame_config:
            # Convert frame config to dollar variables and update main_window
            pass  # Implementation depends on specific needs