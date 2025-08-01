"""
Generate Tab

Complete file generation tab with dual content tracking and proper export.
Now simplified using extracted widgets.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QFileDialog, QMessageBox
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
import os
import shutil

from ..widgets.themed_widgets import (ThemedSplitter, ThemedLabel, ThemedLineEdit, ThemedGroupBox,
                                    PurpleButton, GreenButton, OrangeButton)
from .widgets.generated_file_item import GeneratedFileItem


class GenerateTab(QWidget):
    """Complete file generation tab with dual content tracking and proper export"""
    back_clicked = Signal()
    generate_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.generator = None  # Will be set from main window
        self.output_dir = os.path.expanduser("~/CNC/Output")
        self.dollar_variables_info = {}  # Store $ variables info
        
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
        """)
    
    def setup_ui(self):
        """Initialize user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Top toolbar
        toolbar_layout = QHBoxLayout()
        main_layout.addLayout(toolbar_layout)
        
        # Title
        title_label = ThemedLabel("Generated G-Code Files")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        toolbar_layout.addWidget(title_label)
        
        toolbar_layout.addStretch()
        
        # Generate button
        self.generate_button = GreenButton("Generate Files")
        self.generate_button.clicked.connect(self.on_generate_clicked)
        toolbar_layout.addWidget(self.generate_button)
        
        # Main content area with splitter
        content_splitter = ThemedSplitter(Qt.Horizontal)
        main_layout.addWidget(content_splitter, 1)
        
        # Left side files
        left_widget = self.create_side_panel("Left Side", "left")
        content_splitter.addWidget(left_widget)
        
        # Right side files
        right_widget = self.create_side_panel("Right Side", "right")
        content_splitter.addWidget(right_widget)
        
        # Set equal sizes
        content_splitter.setSizes([400, 400])
        
        # Output directory section with export button
        output_layout = QHBoxLayout()
        main_layout.addLayout(output_layout)
        
        output_layout.addWidget(ThemedLabel("Output Directory:"))
        self.output_path = ThemedLineEdit(self.output_dir)
        self.output_path.setReadOnly(True)
        output_layout.addWidget(self.output_path)
        
        browse_button = PurpleButton("Browse")
        browse_button.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(browse_button)
        
        # Export button next to browse
        self.export_button = OrangeButton("Export Files")
        self.export_button.clicked.connect(self.export_files)
        output_layout.addWidget(self.export_button)
        
        # Bottom navigation
        nav_layout = QHBoxLayout()
        main_layout.addLayout(nav_layout)
        
        nav_layout.addStretch()
        
        back_button = PurpleButton("← Back")
        back_button.clicked.connect(self.back_clicked)
        nav_layout.addWidget(back_button)
    
    def create_side_panel(self, title, side):
        """Create a panel for left or right side files"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Group box
        group = ThemedGroupBox(title)
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
            file_item = GeneratedFileItem(display_name, file_type, side, self.dollar_variables_info)
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
    
    def set_dollar_variables_info(self, dollar_variables_info):
        """Update $ variables information for all file items"""
        self.dollar_variables_info = dollar_variables_info
        # Update all file items
        for side in ['left', 'right']:
            for file_type in ['frame', 'lock', 'hinge']:
                if side in self.file_items and file_type in self.file_items[side]:
                    self.file_items[side][file_type].set_dollar_variables_info(dollar_variables_info)
    
    def update_dollar_variables_in_items(self, dollar_variables_info):
        """Update $ variables in all file items (called from main window)"""
        self.set_dollar_variables_info(dollar_variables_info)
    
    def on_files_updated(self, files_data):
        """Handle updated files from generator - dual content tracking"""
        for side in ['left', 'right']:
            for file_type in ['frame', 'lock', 'hinge']:
                if side in files_data and file_type in files_data[side]:
                    file_data = files_data[side][file_type]
                    auto_content = file_data.get('original', '')  # Auto-generated content
                    manual_content = file_data.get('content', '')  # Manual/displayed content
                    
                    file_item = self.file_items[side][file_type]
                    
                    # Update both auto and manual content
                    file_item.update_auto_content(auto_content)
                    file_item.update_manual_content(manual_content)
                    
                    # Update visual state
                    file_item.update_visual_state()
    
    def on_file_content_changed(self, side, file_type, new_content):
        """Handle manual file content changes"""
        if self.generator:
            self.generator.update_file_content(side, file_type, new_content)
            
        # Update file item state
        file_item = self.file_items[side][file_type]
        file_item.set_manual_content(new_content)
        file_item.update_visual_state()
    
    def on_generate_clicked(self):
        """Handle generate button click - regenerate all files"""
        # Emit signal to trigger main window generation
        self.generate_clicked.emit()
        
        # All file items will be updated via on_files_updated signal
    
    def export_files(self):
        """Export all files to the output directory with proper cnc structure"""
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
            
            # Remove existing cnc directory if it exists
            cnc_dir = os.path.join(self.output_dir, "cnc")
            if os.path.exists(cnc_dir):
                shutil.rmtree(cnc_dir)
            
            # Create new cnc directory structure
            os.makedirs(cnc_dir, exist_ok=True)
            
            exported_files = []
            
            for side_en, side_fr in [('left', 'gauche'), ('right', 'droite')]:
                side_dir = os.path.join(cnc_dir, side_fr)
                os.makedirs(side_dir, exist_ok=True)
                
                for file_type in ['frame', 'lock', 'hinge']:
                    file_item = self.file_items[side_en][file_type]
                    content = file_item.get_manual_content()
                    
                    if content:
                        # Convert line endings to Windows format
                        content_windows = content.replace('\n', '\r\n').replace('\r\r\n', '\r\n')
                        
                        filename = f"{side_en}_{file_type}.txt"
                        filepath = os.path.join(side_dir, filename)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content_windows)
                        
                        exported_files.append(filepath)
            
            # Show success message
            file_count = len(exported_files)
            QMessageBox.information(self, "Export Successful", 
                                  f"Exported {file_count} files to:\n{cnc_dir}")
            
            # Optionally open the directory
            reply = QMessageBox.question(self, "Open Directory", 
                                       "Would you like to open the export directory?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                import subprocess
                import platform
                
                if platform.system() == "Windows":
                    subprocess.run(["explorer", cnc_dir])
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", cnc_dir])
                else:  # Linux
                    subprocess.run(["xdg-open", cnc_dir])
        
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
    
    def set_main_window(self, main_window):
        pass