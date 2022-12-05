from PyQt6.QtWidgets import QDockWidget, QTreeView
from PyQt6.QtSql import QSqlQueryModel
from PyQt6.QtCore import Qt
from uuid import getnode as getMacAddr


class FileViewer(QDockWidget):
    def __init__(self, parent, comm, *args, **kwargs) -> None:
        super().__init__("Papers", parent, *args, **kwargs)
        self.comm = comm
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.model = QSqlQueryModel(self)
        query = f"""
        SELECT DISTINCT Papers.name, GROUP_CONCAT(Tags.name, ', ') as Tags
        FROM Papers, PaperTags, Tags, PaperPaths
        WHERE
            Papers.id=PaperTags.paperId 
            AND Tags.id=PaperTags.tagId 
            AND PaperPaths.deviceMacAddr='{hex(getMacAddr())}'
            AND PaperPaths.paperId=Papers.id
        GROUP BY Papers.name
        ORDER BY Papers.name
        """

        self.model.setQuery(query)
        self.model.setHeaderData(0, Qt.Orientation.Horizontal, "Name")
        self.model.setHeaderData(1, Qt.Orientation.Horizontal, "Tags")

        self.view = QTreeView(self)
        self.view.setModel(self.model)
        self.view.setAlternatingRowColors(True)
        self.setWidget(self.view)

    def refresh(self):
        self.model.setQuery(self.model.query().executedQuery())
