from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                             QLabel, QGroupBox, QListWidget, QListWidgetItem,
                             QLineEdit, QFileDialog)
from PySide6.QtCore import Signal, Qt
import os


class GenerateTab(QWidget):
    """File generation tab"""
    back_clicked = Signal()
    generate_clicked = Signal()
    
    # MARK: - Initialization
    def __init__(self):
        super().__init__()
        self.profiles = {}
        self.frame_data = {}
        self.output_dir = os.path.expanduser("~/CNC/Output")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Generated G-Code Files:")
        main_layout.addWidget(title)
        
        # File lists
        files_layout = QHBoxLayout()
        main_layout.addLayout(files_layout)
        
        # Left side files
        left_group = QGroupBox("Left Side")
        left_layout = QVBoxLayout()
        left_group.setLayout(left_layout)
        files_layout.addWidget(left_group)
        
        self.left_files = QListWidget()
        left_layout.addWidget(self.left_files)
        
        # Right side files  
        right_group = QGroupBox("Right Side")
        right_layout = QVBoxLayout()
        right_group.setLayout(right_layout)
        files_layout.addWidget(right_group)
        
        self.right_files = QListWidget()
        right_layout.addWidget(self.right_files)
        
        # Output directory
        output_layout = QHBoxLayout()
        main_layout.addLayout(output_layout)
        
        output_layout.addWidget(QLabel("Output Directory:"))
        self.output_path = QLineEdit(self.output_dir)
        self.output_path.setReadOnly(True)
        output_layout.addWidget(self.output_path)
        
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(browse_button)
        
        # Navigation
        nav_layout = QHBoxLayout()
        main_layout.addLayout(nav_layout)
        nav_layout.addStretch()
        
        back_button = QPushButton("← Back")
        back_button.clicked.connect(self.back_clicked)
        nav_layout.addWidget(back_button)
        
        generate_button = QPushButton("Generate Files")
        generate_button.clicked.connect(self.generate_clicked)
        nav_layout.addWidget(generate_button)
        
        # TODO: Populate file lists
        # TODO: Connect preview on double-click
        # TODO: Set up template directory selection
    
    # MARK: - Data Management
    def set_profiles(self, hinge_profile, lock_profile):
        """Set selected profiles"""
        self.profiles = {
            'hinge': hinge_profile,
            'lock': lock_profile
        }
    
    def set_frame_data(self, frame_data):
        """Set frame configuration data"""
        self.frame_data = frame_data
    
    # MARK: - Event Handlers
    def browse_output_dir(self):
        """Browse for output directory"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.output_dir)
        if dir_path:
            self.output_dir = dir_path
            self.output_path.setText(dir_path)
    
    # TODO: Add preview_file method for double-click
    # TODO: Add template loading and {variable} replacement
    # TODO: Add file generation to output directory