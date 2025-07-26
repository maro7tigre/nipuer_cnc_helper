from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                             QLabel, QGroupBox, QLineEdit, QFileDialog, QMessageBox,
                             QScrollArea, QGridLayout, QFrame, QSplitter)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from .generated_file_item import GeneratedFileItem
import os

class GenerateTab(QWidget):
    """Complete file generation tab with real-time updates"""
    back_clicked = Signal()
    generate_clicked = Signal()
    
    def __init__(self):
        super().__init__()
        self.generator = None  # Will be set from main window
        self.output_dir = os.path.expanduser("~/CNC/Output")
        
        # File items organized by side and type
        self.file_items = {
            'left': {},
            'right': {}
        }
        
        self.setup_ui()
        self.apply_styling()
        self.connect_signals()
    
    def apply_styling(self):
        """Apply dark theme styling"""
        self.setStyleSheet("""
            GenerateTab {
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
                background-color: transparent;
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
            QPushButton#generate_button {
                color: #23c87b;
                border: 2px solid #23c87b;
            }
            QPushButton#generate_button:hover {
                color: #1a945b;
                border: 2px solid #1a945b;
            }
            QPushButton#generate_button:pressed {
                background-color: #23c87b;
                color: #1d1f28;
            }
            QPushButton#export_button {
                color: #ff8c00;
                border: 2px solid #ff8c00;
            }
            QPushButton#export_button:hover {
                color: #e67300;
                border: 2px solid #e67300;
            }
            QPushButton#export_button:pressed {
                background-color: #ff8c00;
                color: #1d1f28;
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
        """Initialize user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Top toolbar
        toolbar_layout = QHBoxLayout()
        main_layout.addLayout(toolbar_layout)
        
        # Title
        title_label = QLabel("Generated G-Code Files")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        toolbar_layout.addWidget(title_label)
        
        toolbar_layout.addStretch()
        
        # Action buttons
        self.generate_button = QPushButton("Generate Files")
        self.generate_button.setObjectName("generate_button")
        self.generate_button.clicked.connect(self.generate_clicked)
        toolbar_layout.addWidget(self.generate_button)
        
        self.export_button = QPushButton("Export Files")
        self.export_button.setObjectName("export_button")
        self.export_button.clicked.connect(self.export_files)
        toolbar_layout.addWidget(self.export_button)
        
        # Main content area with splitter
        content_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(content_splitter, 1)
        
        # Left side files
        left_widget = self.create_side_panel("Left Side", "left")
        content_splitter.addWidget(left_widget)
        
        # Right side files
        right_widget = self.create_side_panel("Right Side", "right")
        content_splitter.addWidget(right_widget)
        
        # Set equal sizes
        content_splitter.setSizes([400, 400])
        
        # Output directory section
        output_layout = QHBoxLayout()
        main_layout.addLayout(output_layout)
        
        output_layout.addWidget(QLabel("Output Directory:"))
        self.output_path = QLineEdit(self.output_dir)
        self.output_path.setReadOnly(True)
        output_layout.addWidget(self.output_path)
        
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(browse_button)
        
        # Bottom navigation
        nav_layout = QHBoxLayout()
        main_layout.addLayout(nav_layout)
        
        nav_layout.addStretch()
        
        back_button = QPushButton("← Back")
        back_button.clicked.connect(self.back_clicked)
        nav_layout.addWidget(back_button)
    
    def create_side_panel(self, title, side):
        """Create a panel for left or right side files"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Group box
        group = QGroupBox(title)
        group_layout = QVBoxLayout(group)
        layout.addWidget(group)
        
        # File grid
        grid_layout = QGridLayout()
        group_layout.addLayout(grid_layout)
        
        # Create file items
        file_types = [
            ('frame', f'{title.split()[0]} Frame'),
            ('lock', 'Lock'),
            ('hinge', 'Hinge')
        ]
        
        for i, (file_type, display_name) in enumerate(file_types):
            file_item = GeneratedFileItem(display_name, file_type, side)
            file_item.content_changed.connect(
                lambda content, s=side, ft=file_type: self.on_file_content_changed(s, ft, content)
            )
            
            self.file_items[side][file_type] = file_item
            grid_layout.addWidget(file_item, i // 2, i % 2)
        
        # Add stretch to push items to top
        group_layout.addStretch()
        
        return widget
    
    def connect_signals(self):
        """Connect widget signals"""
        pass  # Signals are connected in setup_ui
    
    def set_generator(self, generator):
        """Set the G-code generator instance"""
        self.generator = generator
        if generator:
            generator.files_updated.connect(self.on_files_updated)
    
    def on_files_updated(self, files_data):
        """Handle updated files from generator"""
        for side in ['left', 'right']:
            for file_type in ['frame', 'lock', 'hinge']:
                if side in files_data and file_type in files_data[side]:
                    file_data = files_data[side][file_type]
                    content = file_data.get('content', '')
                    original = file_data.get('original', '')
                    
                    file_item = self.file_items[side][file_type]
                    file_item.update_content(content, original)
    
    def on_file_content_changed(self, side, file_type, new_content):
        """Handle manual file content changes"""
        if self.generator:
            self.generator.update_file_content(side, file_type, new_content)
    
    def export_files(self):
        """Export all files to the output directory"""
        if not self.generator:
            QMessageBox.warning(self, "No Generator", "Generator not initialized.")
            return
        
        # Check if we have any files to export
        has_files = False
        for side in ['left', 'right']:
            for file_type in ['frame', 'lock', 'hinge']:
                if self.file_items[side][file_type].has_content():
                    has_files = True
                    break
            if has_files:
                break
        
        if not has_files:
            QMessageBox.warning(self, "No Files", 
                              "No files available to export. Please generate files first.")
            return
        
        try:
            # Ensure output directory exists
            os.makedirs(self.output_dir, exist_ok=True)
            
            exported_files, project_dir = self.generator.export_files(self.output_dir)
            
            # Show success message
            file_count = len(exported_files)
            QMessageBox.information(self, "Export Successful", 
                                  f"Exported {file_count} files to:\n{project_dir}")
            
            # Optionally open the directory
            reply = QMessageBox.question(self, "Open Directory", 
                                       "Would you like to open the export directory?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                import subprocess
                import platform
                
                if platform.system() == "Windows":
                    subprocess.run(["explorer", project_dir])
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", project_dir])
                else:  # Linux
                    subprocess.run(["xdg-open", project_dir])
        
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", 
                               f"Failed to export files:\n{str(e)}")
    
    def browse_output_dir(self):
        """Browse for output directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.output_dir
        )
        if dir_path:
            self.output_dir = dir_path
            self.output_path.setText(dir_path)
    
    def set_profiles(self, hinge_profile, lock_profile):
        """Set selected profiles (called from main window)"""
        # This will be used when connecting to the generator
        pass
    
    def set_frame_data(self, frame_data):
        """Set frame configuration data (called from main window)"""
        # This will be used when connecting to the generator
        pass
    
    def update_file_borders(self):
        """Update all file item borders based on modification status"""
        for side in ['left', 'right']:
            for file_type in ['frame', 'lock', 'hinge']:
                file_item = self.file_items[side][file_type]
                if self.generator:
                    is_modified = self.generator.is_file_modified(side, file_type)
                    if is_modified != file_item.is_modified:
                        file_item.is_modified = is_modified
                        file_item.update_style()