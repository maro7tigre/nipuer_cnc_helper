"""
CNC Frame Wizard - Main Entry Point

A complete CNC frame processing application with profile management,
frame configuration, and G-code generation capabilities.
"""

import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from theme_manager import ThemeManager


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("CNC Frame Wizard")
    
    # Apply theme - change this line to switch themes
    theme = ThemeManager("purple")  # Just change "purple" to another theme name
    theme.apply_theme(app)
    
    # Force application-wide background color for Linux compatibility
    app.setStyleSheet(app.styleSheet() + """
        QMainWindow {
            background-color: #282a36;
        }
        QWidget {
            background-color: #282a36;
        }
        QTabWidget > QWidget {
            background-color: #282a36;
        }
    """)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()