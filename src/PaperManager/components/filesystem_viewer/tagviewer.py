from PyQt6.QtWidgets import QDockWidget, QTreeView
from PyQt6.QtSql import QSqlQueryModel
from PyQt6.QtCore import Qt


class TagViewer(QDockWidget):
    def __init__(self, parent, comm, *args, **kwargs) -> None:
        super().__init__("Tags", parent, *args, **kwargs)
        self.comm = comm
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.model = QSqlQueryModel(self)
        self.model.setQuery(
            """
        SELECT DISTINCT Tags.name, count(paperId) AS freq 
        FROM Tags LEFT JOIN PaperTags
        ON Tags.id=PaperTags.tagId GROUP BY Tags.id ORDER BY freq DESC"""
        )
        self.model.setHeaderData(0, Qt.Orientation.Horizontal, "Tag")
        self.model.setHeaderData(1, Qt.Orientation.Horizontal, "Freq")
        self.view = QTreeView(self)
        self.view.setModel(self.model)
        self.setWidget(self.view)

    def refresh(self):
        # Refresh the view by executing again the query
        self.model.setQuery(self.model.query().executedQuery())
