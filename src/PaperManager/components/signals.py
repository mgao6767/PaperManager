from PyQt6.QtCore import QObject, pyqtSignal


class PMCommunicate(QObject):
    """Communication signals"""

    open_pdf = pyqtSignal(str, name="open pdf")
    update_directory_done = pyqtSignal(str, name="pdfs in directory added to database")
    tags_updated = pyqtSignal(name="tags updated")
    pdf_selected = pyqtSignal(bool, name="a pdf file is selected")
