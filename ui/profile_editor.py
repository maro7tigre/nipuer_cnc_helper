from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QComboBox, QFormLayout,
                             QDialogButtonBox, QGroupBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator


class ProfileEditor(QDialog):
    """Dialog for creating/editing profiles"""
    
    def __init__(self, profile_type, profile_name=None, parent=None):
        super().__init__(parent)
        self.profile_type = profile_type
        self.profile_name = profile_name
        self.is_new = profile_name is None
        
        self.setWindowTitle(f"{'New' if self.is_new else 'Edit'} {profile_type.capitalize()} Profile")
        self.setModal(True)
        self.setFixedSize(700, 500)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Profile type selection
        type_layout = QHBoxLayout()
        layout.addLayout(type_layout)
        type_layout.addWidget(QLabel("Profile Type:"))
        
        self.type_combo = QComboBox()
        if profile_type == "hinge":
            self.type_combo.addItems(["Hinge Type A", "Hinge Type B", "Hinge Type C"])
        else:
            self.type_combo.addItems(["Lock Type A", "Lock Type B", "Lock Type C"])
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        
        # Content area
        content_layout = QHBoxLayout()
        layout.addLayout(content_layout)
        
        # Left side - Variables
        variables_group = QGroupBox("Variables")
        self.variables_layout = QFormLayout()
        variables_group.setLayout(self.variables_layout)
        content_layout.addWidget(variables_group)
        
        # Create variable inputs
        self.variable_inputs = {}
        variable_names = ["Width", "Height", "Depth", "Offset", "Radius", "Angle", "Spacing", "Margin"]
        
        for var_name in variable_names:
            input_field = QLineEdit()
            input_field.setValidator(QDoubleValidator(0, 10000, 2))
            input_field.setPlaceholderText("0.0")
            self.variable_inputs[var_name] = input_field
            self.variables_layout.addRow(f"{var_name} (mm):", input_field)
        
        # Right side - Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        preview_group.setLayout(preview_layout)
        content_layout.addWidget(preview_group)
        
        # Diagram placeholder
        diagram_label = QLabel()
        diagram_label.setFixedSize(300, 300)
        diagram_label.setStyleSheet("QLabel { background-color: #444; border: 1px solid #666; }")
        diagram_label.setAlignment(Qt.AlignCenter)
        diagram_label.setText("Dimension\nDiagram\n\n(Shows what each\nvariable controls)")
        preview_layout.addWidget(diagram_label, alignment=Qt.AlignCenter)
        
        # Load existing values if editing
        if not self.is_new:
            self.load_profile_data()
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Cancel | QDialogButtonBox.Ok,
            Qt.Horizontal,
            self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_profile_data(self):
        """Load existing profile data"""
        # TODO: Load actual profile data
        # For now, just set some sample values
        sample_values = {
            "Width": "45.5",
            "Height": "120.0",
            "Depth": "15.0",
            "Offset": "2.5",
            "Radius": "5.0"
        }
        
        for var_name, value in sample_values.items():
            if var_name in self.variable_inputs:
                self.variable_inputs[var_name].setText(value)
    
    def get_profile_data(self):
        """Get profile data from inputs"""
        data = {
            'type': self.type_combo.currentText(),
            'variables': {}
        }
        
        for var_name, input_field in self.variable_inputs.items():
            value = input_field.text()
            if value:
                data['variables'][var_name] = float(value)
        
        return data