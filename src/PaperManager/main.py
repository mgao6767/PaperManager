import os
import sys
import ctypes
import platform

from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QApplication

try:
    from .components.mainwindow import PMMainWindow
except ImportError:
    from components.mainwindow import PMMainWindow


class PaperManagerApplication:
    """The application class that holds all UI components together"""

    def __init__(self, *args, **kwargs):
        self.app = QApplication(*args, **kwargs)

        # Set application icon
        app_icon = self._create_icon()
        self.app.setWindowIcon(app_icon)

        # A fix to set the taskbar icon on Windows
        self.appID = "PaperManager"
        if platform.system() == "Windows":
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(self.appID)

        # Global font setting
        self.app.setFont(QFont("Arial"))
        self.app.font().setStyleStrategy(QFont.StyleStrategy.PreferAntialias)

        # Application mainwindow
        self.win = PMMainWindow()

    def run(self):
        """Display main window and start running"""
        self.win.showMaximized()
        self.app.exec()
        self.win.close()

    @staticmethod
    def _create_icon() -> QIcon:
        """Load application icon from local files

        Returns:
            QIcon: Application icon
        """
        icon = QIcon()
        icon_dir = os.path.join(os.path.dirname(__file__), "icon")
        if os.path.exists(icon_dir):
            for size in [256]:
                icon_path = os.path.join(icon_dir, f"favicon-{size}x{size}.png")
                icon.addFile(icon_path, QSize(size, size))
        return icon


def run():
    """Entry point for starting the application"""
    # Prevent the window from being blurry if Windows scales
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    PaperManagerApplication(sys.argv).run()


if __name__ == "__main__":
    run()
