import os
import typing
from PyQt6.QtWidgets import QMainWindow, QFileDialog, QMessageBox
from PyQt6.QtGui import QActionGroup, QAction, QDesktopServices, QKeySequence
from PyQt6.QtCore import Qt, QUrl, QThreadPool

from .pdf_viewer.pdfviewer import PDFViewer
from .filesystem_viewer.fsviewer import FSViewer
from .filesystem_viewer.tagviewer import TagViewer
from .signals import PMCommunicate
from .database import PMDatabase, Settings


class PMMainWindow(QMainWindow):
    def __init__(self) -> None:
        """Main window of the application"""
        super().__init__()
        self.curr_dir: typing.Optional[str] = None
        self.comm = PMCommunicate()
        self.pool = QThreadPool.globalInstance()
        self.db = PMDatabase()
        self.fsviewer = FSViewer(parent=self, comm=self.comm, db=self.db)
        self.pdfviewer = PDFViewer(parent=self, comm=self.comm)
        self.tagviewer = TagViewer(parent=self, comm=self.comm)

        # Setup layout, menu, etc.
        self.setup()
        self.create_menu()
        self.connect_signals()

    def setup(self) -> None:
        self.setWindowTitle(f"PaperManager")
        self.setCentralWidget(self.fsviewer)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.tagviewer)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.pdfviewer)
        self.fsviewer.set_dir(self.db.get_setting(Settings.LastDirectory))

    def create_menu(self) -> None:
        menuBar = self.menuBar()
        # Menus
        fileMenu = menuBar.addMenu("&File")
        editMenu = menuBar.addMenu("&Edit")
        viewMenu = menuBar.addMenu("&View")
        helpMenu = menuBar.addMenu("&Help")

        # File menu actions
        openAction = QAction("&Open", self)
        openAction.setShortcut(QKeySequence.StandardKey.Open)
        quitAction = QAction("&Quit", self)
        quitAction.setShortcut(QKeySequence.StandardKey.Quit)
        fileMenuActions = [
            openAction,
            quitAction,
        ]
        fileMenu.addActions(fileMenuActions)
        openAction.triggered.connect(self.open_dir)
        quitAction.triggered.connect(self._close)

        # Edit menu actions

        # View menu actions
        viewActionGroup = QActionGroup(self)
        viewActionGroup.setExclusive(True)
        defaultViewAction = QAction("Default view", self)
        defaultViewAction.setChecked(True)
        zenModeViewAction = QAction("Zen mode", self)
        viewMenuActions = [defaultViewAction, zenModeViewAction]
        for act in viewMenuActions:
            act.setCheckable(True)
            viewActionGroup.addAction(act)
        viewMenu.addActions(viewMenuActions)
        defaultViewAction.triggered.connect(self.act_restore_default_view)
        zenModeViewAction.triggered.connect(self.act_enter_zen_mode)

        # Help menu actions
        helpAction = QAction("About PaperManager", self)
        helpQtAction = QAction("About Qt", self)
        helpMenu.addAction(helpAction)
        helpMenu.addAction(helpQtAction)
        helpAction.triggered.connect(self.act_open_homepage)
        helpQtAction.triggered.connect(lambda: QMessageBox.aboutQt(self, "About Qt"))

    def _close(self):
        # Close database
        self.db.close()
        # Close main window
        return self.close()

    def connect_signals(self) -> None:
        self.comm.open_pdf.connect(self.act_load_pdf)

    def check_directory_set(func: typing.Callable):
        """Dectorator to check if the current directory is set

        Args:
            func (typing.Callable): methods of PMMainWindow
        """

        def inner(self: "PMMainWindow", *args, **kwargs):
            if self.curr_dir is None:
                self.show_message_box("Please create a project first.")
            else:
                func(self, *args, **kwargs)

        return inner

    def open_dir(self):
        """Prompt the user to select directory"""
        # Defaults to the current directory
        self.curr_dir = QFileDialog(self).getExistingDirectory(self, directory=".")
        # User didn't select any, self.curr_dir=""
        if not self.curr_dir:
            self.curr_dir = None
            return
        # Change working directory to the selected one
        try:
            os.chdir(self.curr_dir)
        except FileNotFoundError:
            msg = f"Cannot open the directory:\n{self.curr_dir}"
            self.show_message_box(msg, QMessageBox.Icon.Critical)
            return
        # Set project directory and try to load data, if any
        self.fsviewer.set_dir(self.curr_dir)
        self.db.set_setting(Settings.LastDirectory, self.curr_dir)

    def show_message_box(
        self,
        message: str,
        icon=QMessageBox.Icon.Information,
        button=QMessageBox.StandardButton.Ok,
    ) -> int:
        """Display a message box with given message.

        Args:
            message (str): The message to display
            icon (Icon, optional): Icon.
                Defaults to QMessageBox.Icon.Information.
            button (StandardButton, optional): StandardButton.
                Defaults to QMessageBox.StandardButton.Ok.

        Returns:
            int: Return value from QMessageBox.exec()
        """
        dlg = QMessageBox(self)
        dlg.setWindowTitle("PaperManager")
        dlg.setText(message)
        dlg.setIcon(icon)
        dlg.setStandardButtons(button)
        return dlg.exec()

    # ========================== Actions to be invoked ==========================

    def act_open_homepage(self) -> None:
        """Open PaperManager homepage using default browser"""
        __homepage__ = "https://github.com/mgao6767/PaperManager"
        QDesktopServices.openUrl(QUrl(__homepage__))

    def act_restore_default_view(self) -> None:
        """Restore the default view layout"""
        self.fsviewer.show()
        self.pdfviewer.show()
        self.setCentralWidget(self.fsviewer)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.pdfviewer)

    def act_enter_zen_mode(self) -> None:
        """Show only the editor"""
        self.fsviewer.hide()
        self.pdfviewer.hide()

    def act_load_pdf(self, filepath: str) -> None:
        """Load and display PDF given the filepath

        Args:
            filepath (str): path to PDF file
        """
        self.pdfviewer.load_file(filepath, display=True)
