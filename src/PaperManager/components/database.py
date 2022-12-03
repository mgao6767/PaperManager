from enum import Enum
from PyQt6.QtSql import QSqlDatabase, QSqlQuery, QSql


class Settings(str, Enum):
    LastDirectory = "lastDirectory"


class PMDatabase:
    def __init__(self, databaseName="db.sqlite") -> None:
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(databaseName)
        self.db.open()
        self.init()

    def close(self):
        """Close database"""
        name = self.db.connectionName()
        self.db.close()
        del self.db
        QSqlDatabase.removeDatabase(name)

    def init(self):
        """Create necessary tables"""

        if not self.db.isOpen():
            return

        createTableQuery = QSqlQuery(self.db)
        createTableQuery.exec(
            """
        CREATE TABLE IF NOT EXISTS Settings (
            key TEXT PRIMARY KEY UNIQUE NOT NULL,
            value TEXT NOT NULL
        )
        """
        )
        createTableQuery.exec(
            """
        CREATE TABLE IF NOT EXISTS Tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
            name TEXT NOT NULL
        )
        """
        )
        createTableQuery.exec(
            """
        CREATE TABLE IF NOT EXISTS Papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
            name TEXT NOT NULL
        )
        """
        )
        createTableQuery.exec(
            """
        CREATE TABLE IF NOT EXISTS PaperTags (
            paperId INTEGER NOT NULL,
            tagId INTEGER NOT NULL,
            PRIMARY KEY (paperId, tagId),
            FOREIGN KEY (paperId) REFERENCES Papers(id),
            FOREIGN KEY (tagId) REFERENCES Tags(id)
        )
        """
        )
        createTableQuery.finish()

    def get_setting(self, key: Settings):
        """Get the value of setting from database"""

        assert isinstance(key, Settings)
        query = QSqlQuery(self.db)
        query.prepare(
            """
        SELECT value FROM Settings WHERE key=?
        """
        )
        query.addBindValue(key.value)
        query.exec()
        result = query.value(0) if query.next() else ""
        query.finish()
        return result

    def set_setting(self, key: Settings, value: str):
        """Set the value of setting from database"""

        assert isinstance(key, Settings)
        query = QSqlQuery(self.db)
        query.prepare(
            """
        INSERT OR REPLACE INTO Settings(key,value) VALUES(?,?)
        """
        )
        query.addBindValue(key.value)
        query.addBindValue(value)
        query.exec()
        query.finish()
