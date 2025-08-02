"""
Profile Tab

Simplified profile selection tab that works with centralized main_window data management.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Signal, Qt

from ..widgets.themed_widgets import ThemedSplitter, ThemedLabel, BlueButton, PurpleButton, GreenButton
from .widgets.profile_grid import ProfileGrid


class ProfileTab(QWidget):
    """Simplified profile selection tab that uses main_window for all data management"""
    next_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.selected_hinge = None
        self.selected_lock = None

        self.setup_ui()
        self.apply_styling()
        self.connect_signals()
        
        # Subscribe to main_window events
        if self.main_window:
            self.main_window.events.subscribe('profiles', self.on_profiles_updated)
            self.main_window.events.subscribe('variables', self.on_variables_updated)
    
    def apply_styling(self):
        """Apply dark theme styling"""
        self.setStyleSheet("""
            ProfileTab {
                background-color: #282a36;
                color: #ffffff;
            }
        """)
    
    def setup_ui(self):
        """Initialize user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Top toolbar
        toolbar_layout = QHBoxLayout()
        layout.addLayout(toolbar_layout)
        
        # Project buttons (blue)
        self.save_project_button = BlueButton("Save Project")
        toolbar_layout.addWidget(self.save_project_button)
        
        self.load_project_button = BlueButton("Load Project")
        toolbar_layout.addWidget(self.load_project_button)
        
        toolbar_layout.addSpacing(20)
        
        # Profile set buttons (purple)
        self.save_button = PurpleButton("Save Set")
        toolbar_layout.addWidget(self.save_button)
        
        self.load_button = PurpleButton("Load Set")
        toolbar_layout.addWidget(self.load_button)
        
        toolbar_layout.addStretch()
        
        # Profile grids with splitter
        splitter = ThemedSplitter(Qt.Horizontal)
        layout.addWidget(splitter, 1)
        
        # Create hinge and lock grids - they get data from main_window
        self.hinge_grid = ProfileGrid("hinge", self.main_window)
        self.lock_grid = ProfileGrid("lock", self.main_window)
        
        splitter.addWidget(self.hinge_grid)
        splitter.addWidget(self.lock_grid)
        
        # Set initial splitter sizes (50/50)
        splitter.setSizes([400, 400])
        
        # Bottom controls
        bottom_layout = QHBoxLayout()
        layout.addLayout(bottom_layout)
        
        self.selection_label = ThemedLabel("Selected: [Hinge: None] [Lock: None]")
        self.selection_label.setStyleSheet("QLabel { font-weight: bold; padding: 5px; }")
        bottom_layout.addWidget(self.selection_label)
        
        bottom_layout.addStretch()
        
        self.next_button = GreenButton("Next →")
        self.next_button.setEnabled(False)
        bottom_layout.addWidget(self.next_button)
    
    def connect_signals(self):
        """Connect widget signals"""
        self.hinge_grid.selection_changed.connect(self.on_hinge_selected)
        self.lock_grid.selection_changed.connect(self.on_lock_selected)
        self.next_button.clicked.connect(self.on_next_clicked)
        
        # Connect main_window buttons to main_window methods
        if self.main_window:
            self.save_project_button.clicked.connect(self.main_window.save_project)
            self.load_project_button.clicked.connect(self.main_window.load_project)
            self.save_button.clicked.connect(lambda: self.main_window.save_profile_set(current=False))
            self.load_button.clicked.connect(lambda: self.main_window.load_profile_set(current=False))
    
    def on_profiles_updated(self):
        """Handle profiles updated from main_window"""
        # Refresh grids with new data
        self.hinge_grid.refresh_from_main_window()
        self.lock_grid.refresh_from_main_window()
        
        # Update selection display
        self.update_selection_from_main_window()
    
    def on_variables_updated(self):
        """Handle variables updated from main_window"""
        # Update grids with new $ variables
        dollar_vars = self.main_window.get_dollar_variable()
        self.hinge_grid.set_dollar_variables_info(dollar_vars)
        self.lock_grid.set_dollar_variables_info(dollar_vars)
    
    def update_selection_from_main_window(self):
        """Update selection display from main_window state"""
        self.selected_hinge = self.main_window.get_dollar_variable("selected_hinge")
        self.selected_lock = self.main_window.get_dollar_variable("selected_lock")
        
        # Update grid selections
        self.hinge_grid.set_selection(self.selected_hinge)
        self.lock_grid.set_selection(self.selected_lock)
        
        self.update_selection_display()
    
    def on_hinge_selected(self, name):
        """Handle hinge profile selection"""
        self.selected_hinge = name if name else None
        
        # Update main_window
        if self.main_window:
            self.main_window.update_dollar_variable("selected_hinge", self.selected_hinge)
            
            # If both profiles selected, update main_window with profiles
            if self.selected_hinge and self.selected_lock:
                self.main_window.select_profiles(self.selected_hinge, self.selected_lock)
        
        self.update_selection_display()
    
    def on_lock_selected(self, name):
        """Handle lock profile selection"""
        self.selected_lock = name if name else None
        
        # Update main_window
        if self.main_window:
            self.main_window.update_dollar_variable("selected_lock", self.selected_lock)
            
            # If both profiles selected, update main_window with profiles
            if self.selected_hinge and self.selected_lock:
                self.main_window.select_profiles(self.selected_hinge, self.selected_lock)
        
        self.update_selection_display()
    
    def update_selection_display(self):
        """Update selection display and controls"""
        hinge_text = self.selected_hinge or "None"
        lock_text = self.selected_lock or "None"
        self.selection_label.setText(f"Selected: [Hinge: {hinge_text}] [Lock: {lock_text}]")
        
        # Enable next button when both profiles selected
        both_selected = bool(self.selected_hinge and self.selected_lock)
        self.next_button.setEnabled(both_selected)
    
    def on_next_clicked(self):
        """Handle next button click"""
        if self.selected_hinge and self.selected_lock:
            # Make sure main_window has latest selections
            if self.main_window:
                self.main_window.select_profiles(self.selected_hinge, self.selected_lock)
            self.next_clicked.emit()
    
    def get_app_config(self):
        """Get tab configuration for saving"""
        return {
            "selected_hinge": self.selected_hinge,
            "selected_lock": self.selected_lock
        }
    
    def set_app_config(self, config):
        """Set tab configuration from loading"""
        self.selected_hinge = config.get("selected_hinge")
        self.selected_lock = config.get("selected_lock")
        
        # Update main_window
        if self.main_window:
            if self.selected_hinge:
                self.main_window.update_dollar_variable("selected_hinge", self.selected_hinge)
            if self.selected_lock:
                self.main_window.update_dollar_variable("selected_lock", self.selected_lock)
        
        self.update_selection_display()