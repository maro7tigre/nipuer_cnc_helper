import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from theme_manager import ThemeManager


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CNC Frame Wizard")
    
    # Apply theme - change this line to switch themes
    theme = ThemeManager("purple")  # Just change "purple" to another theme name
    theme.apply_theme(app)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()