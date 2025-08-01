"""
Widgets Package

Reusable widget components for the CNC Frame Wizard application.
"""

from .themed_widgets import *
from .simple_widgets import *
from .variable_editor import VariableEditor
from .custom_editor import CustomEditor

__all__ = [
    # Themed widgets
    'PurpleButton', 'GreenButton', 'BlueButton', 'OrangeButton',
    'ThemedLineEdit', 'ThemedTextEdit', 'ThemedSpinBox', 'ThemedGroupBox',
    'ThemedScrollArea', 'ThemedSplitter', 'ThemedLabel', 'ThemedCheckBox',
    'ThemedRadioButton', 'ThemedListWidget', 'ThemedMenu',
    
    # Simple widgets
    'ClickableLabel', 'ScaledImageLabel', 'ClickableImageLabel',
    'ErrorLineEdit', 'PlaceholderPixmap',
    
    # Complex widgets
    'VariableEditor', 'CustomEditor'
]