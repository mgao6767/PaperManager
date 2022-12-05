import os
from pathlib import Path
from enum import Enum
from uuid import getnode as getMacAddr
from PyQt6.QtSql import QSqlDatabase, QSqlQuery


class Settings(str, Enum):
    LastDirectory = "lastDirectory"


class PMDatabase:
    def __init__(self, databaseName="db.sqlite") -> None:
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(databaseName)
        self.db.open()
        self.init()
        # cache
        self.papers = {}  # paperId to a set of paths
        self.paperTags = {}
        self.load_paper_tags()

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
            name TEXT UNIQUE NOT NULL,
            hexColor VARCHAR(8)
        )
        """
        )
        createTableQuery.exec(
            """
        CREATE TABLE IF NOT EXISTS Papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
            name TEXT UNIQUE NOT NULL
        )
        """
        )
        createTableQuery.exec(
            """
        CREATE TABLE IF NOT EXISTS PaperPaths (
            paperId INTEGER NOT NULL,
            path TEXT NOT NULL,
            deviceMacAddr TEXT NOT NULL,
            PRIMARY KEY (paperId,path),
            FOREIGN KEY (paperId) REFERENCES Papers(id)
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

    def load_paper_tags(self):
        query = QSqlQuery(self.db)
        query.exec(
            """
        SELECT DISTINCT PaperPaths.paperId, PaperPaths.path, Tags.name
        FROM PaperPaths, PaperTags, Tags
        WHERE PaperPaths.paperId=PaperTags.paperId AND PaperTags.tagId=Tags.id
        """
        )
        query.exec()
        paperId, paper_path, tag_name = range(3)
        while query.next():
            i, p, n = (
                query.value(paperId),
                query.value(paper_path),
                query.value(tag_name),
            )
            if p not in self.paperTags:
                self.paperTags[p] = []
            self.paperTags[p].append(n)
            if i not in self.papers:
                self.papers[i] = set()
            self.papers[i].add(p)

    def get_paper_tags(self, paper_path: str):
        tags = self.paperTags.get(paper_path, [])
        return list(sorted(tags))

    def set_paper_tags(self, paper_path: str, tags: list):
        if paper_path not in self.paperTags:
            self.paperTags[paper_path] = list()
        self.paperTags[paper_path].extend(tags)
        self.paperTags[paper_path] = list(set(self.paperTags[paper_path]))
        # same paper may have duplicates in other locations
        for papper_id, paths in self.papers.items():
            if paper_path in paths:
                for path in paths:
                    if path == paper_path:
                        continue
                    if path not in self.paperTags:
                        self.paperTags[path] = list()
                    self.paperTags[path].extend(tags)
                    self.paperTags[path] = list(set(self.paperTags[path]))

    def update_paper_tags(self):
        # Write cache into the database
        query = QSqlQuery(self.db)
        for paper_path, tags in self.paperTags.items():
            query.prepare(
                """
            SELECT DISTINCT paperId FROM PaperPaths WHERE path=? 
            """
            )
            query.addBindValue(paper_path)
            query.exec()
            if query.next():
                paperId = query.value(0)
            else:
                continue
            for tag in tags:
                query.prepare(
                    """
                INSERT INTO Tags(name) VALUES (?)
                """
                )
                query.addBindValue(tag)
                query.exec()
                tagId = query.lastInsertId()
                # Tag already in database
                if tagId is None:
                    query.prepare("SELECT id FROM Tags WHERE name=?")
                    query.addBindValue(tag)
                    query.exec()
                    query.next()
                    tagId = query.value(0)
                query.prepare(
                    """
                INSERT INTO PaperTags(paperId,tagId) VALUES (?,?)
                """
                )
                query.addBindValue(paperId)
                query.addBindValue(tagId)
                query.exec()
        query.finish()

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

    def update_dir(self, directory_path: str):
        deviceMacAddr = hex(getMacAddr())
        for root, dirs, files in os.walk(directory_path):
            query = QSqlQuery(self.db)
            for file in files:
                if "pdf" not in file.lower():
                    continue
                query.prepare(
                    """
                INSERT INTO Papers(name) VALUES(?)
                """
                )
                query.addBindValue(file)
                query.exec()
                paperId = query.lastInsertId()
                # Paper name already in databse
                if paperId is None:
                    query.prepare("SELECT id FROM Papers WHERE name=?")
                    query.addBindValue(file)
                    query.exec()
                    query.next()
                    paperId = query.value(0)
                if paperId:
                    pdf_path = Path(os.path.join(root, file)).resolve().as_posix()
                    query = QSqlQuery(self.db)
                    query.prepare(
                        """
                    INSERT INTO PaperPaths(paperId,path,deviceMacAddr) 
                    VALUES(?,?,?)
                    """
                    )
                    query.addBindValue(paperId)
                    query.addBindValue(pdf_path)
                    query.addBindValue(deviceMacAddr)
                    query.exec()
