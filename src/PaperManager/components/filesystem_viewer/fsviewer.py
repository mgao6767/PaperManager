from PyQt6.QtWidgets import QDockWidget, QTreeView, QHeaderView
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtCore import QDir, Qt

from ..signals import PMCommunicate


class FSTreeView(QTreeView):
    def __init__(self, parent, comm: PMCommunicate) -> None:
        super().__init__(parent)
        self.comm = comm

    def currentChanged(self, current, previous):
        if not current:
            return
        selected_file_path = self.model().filePath(current)
        self.comm.open_pdf.emit(selected_file_path)
        super().currentChanged(current, previous)


class FSViewer(QDockWidget):
    def __init__(self, parent, comm, *args, **kwargs) -> None:
        super().__init__("File System", parent, *args, **kwargs)
        self.comm = comm
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )

        self.fsmodel = QFileSystemModel(self)
        self.fsmodel.setRootPath(QDir.homePath())
        self.treeView = FSTreeView(self, comm)
        self.treeView.setModel(self.fsmodel)
        self.treeView.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.setWidget(self.treeView)

    def set_dir(self, path: str) -> None:
        """Update the filesystem TreeView to show the given directory path

        Args:
            path (str): directory path
        """
        self.treeView.setRootIndex(self.fsmodel.index(path))
