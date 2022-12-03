from PyQt6.QtWidgets import QDockWidget, QTreeView, QHeaderView
from PyQt6.QtGui import QFileSystemModel, QColor
from PyQt6.QtCore import QDir, Qt, QModelIndex

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


class FSModel(QFileSystemModel):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        # Show only PDF files
        self.setNameFilters(["*.pdf", "*.PDF"])
        self.setNameFilterDisables(False)

    def columnCount(self, parent=QModelIndex()):
        # Add one more column for tags
        return super().columnCount(parent) + 1

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
            and section == self.columnCount() - 1
        ):
            return "Tags"
        return super().headerData(section, orientation, role)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        isTagCol = False
        if index.isValid():
            isTagCol = index.column() == self.columnCount(index.parent()) - 1
            info = self.fileInfo(index)
            path = info.absoluteFilePath()
            if path:
                if isTagCol:
                    if role == Qt.ItemDataRole.DecorationRole:
                        pass
                    elif role == Qt.ItemDataRole.DisplayRole:
                        return f"JFE; Open Access;"
                    elif role == Qt.ItemDataRole.ForegroundRole:
                        return QColor("blue")
        if not isTagCol:
            return super().data(index, role)


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

        self.fsmodel = FSModel(self)
        self.fsmodel.setRootPath(QDir.homePath())
        self.treeView = FSTreeView(self, comm)
        self.treeView.setModel(self.fsmodel)
        # self.treeView.header().moveSection(self.fsmodel.columnCount() - 1, 1)
        self.treeView.header().hideSection(1)  # size
        self.treeView.header().hideSection(2)  # type
        self.treeView.header().hideSection(3)  # date modified
        self.treeView.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.treeView.setAlternatingRowColors(True)
        self.setWidget(self.treeView)

    def set_dir(self, path: str) -> None:
        """Update the filesystem TreeView to show the given directory path

        Args:
            path (str): directory path
        """
        self.treeView.setRootIndex(self.fsmodel.index(path))
