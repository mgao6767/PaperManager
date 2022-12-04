from dataclasses import dataclass

from PyQt6.QtCore import QRunnable

from .signals import PMCommunicate
from .database import PMDatabase


class PMTask(QRunnable):
    """Base class for a QRunnable task"""

    def __post_init__(self):
        super().__init__()


@dataclass
class PMUpdateDirectory(PMTask):
    """Task to add pdfs in the given directory to database

    Args:
        comm (FTCommunicate): communication
        db (PMDatabase): database
        directory_path (str): directory
    """

    comm: PMCommunicate
    db: PMDatabase
    directory_path: str

    def run(self):
        self.db.update_dir(self.directory_path)
        # Emit signal on completion
        self.comm.update_directory_done.emit(self.directory_path)
