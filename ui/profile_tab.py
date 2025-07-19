from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                             QLabel, QScrollArea, QGridLayout, QFrame)
from PySide6.QtCore import Signal, Qt


class ProfileItem(QFrame):
    """Individual profile item widget"""
    clicked = Signal(str)
    
    # MARK: - Initialization
    def __init__(self, name, is_add_button=False):
        super().__init__()
        self.name = name
        self.is_add_button = is_add_button
        self.selected = False
        
        # TODO: Setup basic styling and layout
        # TODO: Add image placeholder
        # TODO: Add name label
    
    # MARK: - Selection
    def set_selected(self, selected):
        """Update selection state"""
        self.selected = selected
        # TODO: Update visual styling based on selection state
    
    # MARK: - Event Handlers
    def mousePressEvent(self, event):
        """Handle mouse clicks"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.name)
        # TODO: Add right-click context menu support


class ProfileGrid(QWidget):
    """Grid container for profile items"""
    selection_changed = Signal(str)
    
    # MARK: - Initialization
    def __init__(self, profile_type):
        super().__init__()
        self.profile_type = profile_type  # "hinge" or "lock"
        self.selected_profile = None
        self.profiles = {}
        
        # TODO: Setup layout with title and scroll area
        # TODO: Create grid layout for profile items
        self.populate_profiles()
    
    # MARK: - Profile Management
    def populate_profiles(self):
        """Load and display profiles"""
        # TODO: Clear existing items
        # TODO: Add "+" button for new profiles
        # TODO: Load profiles from data source
        # TODO: Create ProfileItem widgets and add to grid
        pass
    
    def add_new_profile(self):
        """Create new profile"""
        # TODO: Open profile editor dialog
        # TODO: Save new profile
        # TODO: Refresh grid
        pass
    
    # MARK: - Event Handlers
    def on_item_clicked(self, name):
        """Handle profile selection"""
        # TODO: Update selection state
        # TODO: Emit selection signal
        pass


class ProfileTab(QWidget):
    """Main profile selection tab"""
    profiles_selected = Signal(str, str)  # hinge_profile, lock_profile
    next_clicked = Signal()
    
    # MARK: - Initialization
    def __init__(self):
        super().__init__()
        self.selected_hinge = None
        self.selected_lock = None
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Initialize user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Profile grids
        grids_layout = QHBoxLayout()
        layout.addLayout(grids_layout)
        
        # TODO: Create hinge and lock grids
        self.hinge_grid = ProfileGrid("hinge")
        self.lock_grid = ProfileGrid("lock")
        
        grids_layout.addWidget(self.hinge_grid)
        grids_layout.addWidget(self.lock_grid)
        
        # Bottom controls
        bottom_layout = QHBoxLayout()
        layout.addLayout(bottom_layout)
        
        self.selection_label = QLabel("Selected: [None] [None]")
        bottom_layout.addWidget(self.selection_label)
        
        bottom_layout.addStretch()
        
        self.next_button = QPushButton("Next →")
        self.next_button.setEnabled(False)
        bottom_layout.addWidget(self.next_button)
    
    def connect_signals(self):
        """Connect widget signals"""
        self.hinge_grid.selection_changed.connect(self.on_hinge_selected)
        self.lock_grid.selection_changed.connect(self.on_lock_selected)
        self.next_button.clicked.connect(self.next_clicked)
    
    # MARK: - Event Handlers
    def on_hinge_selected(self, name):
        """Handle hinge profile selection"""
        self.selected_hinge = name
        self.update_selection_display()
    
    def on_lock_selected(self, name):
        """Handle lock profile selection"""
        self.selected_lock = name
        self.update_selection_display()
    
    # MARK: - UI Updates
    def update_selection_display(self):
        """Update selection display and controls"""
        hinge_text = self.selected_hinge or "None"
        lock_text = self.selected_lock or "None"
        self.selection_label.setText(f"Selected: [Hinge: {hinge_text}] [Lock: {lock_text}]")
        
        # Enable next button when both profiles selected
        both_selected = self.selected_hinge and self.selected_lock
        self.next_button.setEnabled(both_selected)
        
        if both_selected:
            self.profiles_selected.emit(self.selected_hinge, self.selected_lock)