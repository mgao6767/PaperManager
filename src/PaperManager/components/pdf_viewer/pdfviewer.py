import os
import pathlib

import fitz
from PyQt6.QtWidgets import (
    QWidget,
    QDockWidget,
    QLabel,
    QVBoxLayout,
    QToolBar,
    QStyle,
    QLineEdit,
)
from PyQt6.QtGui import (
    QPixmap,
    QImage,
    QPainter,
    QColor,
    QPen,
    QAction,
    QIntValidator,
    QMouseEvent,
    QCursor,
    QWheelEvent,
    QDesktopServices,
    QResizeEvent,
)
from PyQt6.QtCore import Qt, QByteArray, QRectF, QUrl

from ..signals import PMCommunicate


class PDFViewer(QDockWidget):
    def __init__(self, parent, comm: PMCommunicate, *args, **kwargs):
        super().__init__("PDF Viewer", parent, *args, **kwargs)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.comm = comm
        self.height = self.parent().height()
        self.curr_page = 1  # 1 indexed
        self.total_pages = 0
        self.doc = None
        self.curr_page_links = []
        # Keep track of which link on the page the mouse is hovering on
        self.curr_link_idx = -1
        self.cursor_normal = QCursor(Qt.CursorShape.ArrowCursor)
        self.cursor_pointing_hand = QCursor(Qt.CursorShape.PointingHandCursor)
        # ToolBar for navigation
        self.toolBar = self._create_tool_bar()
        # QLabel to hold the QPixmap of PDF page
        self.viewArea = QLabel(self)
        self.viewArea.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Enable mouse tracking to know if it hovers on a link
        self.viewArea.setMouseTracking(True)
        # Override default events of the view area, not this widget itself
        self.viewArea.mouseMoveEvent = self._mouseMoveEvent
        self.viewArea.mouseReleaseEvent = self._mouseReleaseEvent
        self.viewArea.wheelEvent = self._wheelEvent
        layout = QVBoxLayout()
        layout.addWidget(self.toolBar)
        layout.addWidget(self.viewArea)
        container = QWidget(self)
        container.setLayout(layout)
        self.setWidget(container)
        self.load_file("", display=True)

    def resizeEvent(self, evt: QResizeEvent) -> None:
        if self.doc:
            self.show_pdf(self.curr_page)
        return super().resizeEvent(evt)

    def _mouseMoveEvent(self, evt: QMouseEvent) -> None:
        pos = evt.position()
        for idx, link in enumerate(self.curr_page_links):
            # The Rectangle of the link
            rectf: QRectF = link["from_qrectf"]
            # Mouse in this rectangle
            if rectf.contains(pos):
                self.setCursor(self.cursor_pointing_hand)
                self.curr_link_idx = idx
                break
        else:
            # Mouse in none of the links
            self.setCursor(self.cursor_normal)
            self.curr_link_idx = -1
        return super().mouseMoveEvent(evt)

    def _mouseReleaseEvent(self, evt: QMouseEvent) -> None:
        # If click on a link, navigate to the page
        if self.curr_link_idx != -1:
            link = self.curr_page_links[self.curr_link_idx]
            self.setCursor(self.cursor_normal)
            if link["kind"] == fitz.LINK_URI:
                url = QUrl(link["uri"])
                QDesktopServices.openUrl(url)
            elif link["kind"] == fitz.LINK_GOTO:
                self.show_pdf(int(link["page"]) + 1)
            elif link["kind"] == fitz.LINK_NAMED:
                # link["name"] is like 'page=1&zoom=nan,92,484'
                page_no = int(link["name"].split("&")[0].split("=")[-1])
                self.show_pdf(page_no)
        return super().mouseReleaseEvent(evt)

    def _wheelEvent(self, evt: QWheelEvent) -> None:
        ang = evt.angleDelta()
        delta = -1 + 2 * int(ang.y() < 0 == evt.inverted())
        self.show_pdf(self.curr_page + delta)
        return super().wheelEvent(evt)

    def _create_tool_bar(self) -> QToolBar:
        toolBar = QToolBar("Nav")
        # Prev page
        iconBackward = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack)
        actionBackward = QAction(iconBackward, "Back", self)
        actionBackward.triggered.connect(lambda: self.show_pdf(self.curr_page - 1))
        toolBar.addAction(actionBackward)
        # Next page
        iconForward = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward)
        actionForward = QAction(iconForward, "Next", self)
        actionForward.triggered.connect(lambda: self.show_pdf(self.curr_page + 1))
        toolBar.addAction(actionForward)
        # Nav based on page number
        self.page_num_line_edit = QLineEdit()
        self.page_num_validator = QIntValidator(0, self.total_pages)
        self.page_num_line_edit.setValidator(self.page_num_validator)
        self.page_num_line_edit.setFixedWidth(33)
        self.page_num_line_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.page_num_line_edit.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.lb_total_pages = QLabel()
        self._update_nav_info()
        self.page_num_line_edit.returnPressed.connect(
            lambda: self.show_pdf(self.page_num_line_edit.text())
        )
        toolBar.addWidget(self.page_num_line_edit)
        toolBar.addWidget(self.lb_total_pages)
        return toolBar

    def show_pdf(self, page_number=1) -> None:
        if not page_number is int:
            try:
                page_number = int(page_number)
            except ValueError:
                return
        page_number = max(page_number, 1)
        page_number = min(page_number, self.total_pages)
        self.curr_page = page_number
        page_number -= 1
        # First page of the loaded PDF file
        dl = self.doc[page_number].get_displaylist()
        # Get pixmap but scaled a bit to avoid blur
        pix = self.doc.get_page_pixmap(page_number, matrix=fitz.Matrix(2, 2))
        # Get the pixmap as byte array
        data = QByteArray(pix.tobytes())
        img = QImage()
        img.loadFromData(data)

        pixmap = QPixmap.fromImage(img)
        del img

        # Scale the image before the painting,
        # but needs to note down the scale ratio (after/before)
        pixmap_scaleRatio = self.viewArea.height() / pixmap.height()
        pixmap = pixmap.scaledToHeight(
            self.viewArea.height(), Qt.TransformationMode.SmoothTransformation
        )

        # Print links onto the pixmap
        if pixmap.isNull():
            return
        painter = QPainter(pixmap)
        pen = QPen()
        pen.setWidth(2)
        pen.setColor(QColor(0, 255, 0, 155))
        painter.setPen(pen)
        pg_ir: fitz.IRect = dl.rect.irect

        pg_w = pg_ir.x1 - pg_ir.x0
        pg_h = pg_ir.y1 - pg_ir.y0
        self.zoom_w = pix.w / pg_w * pixmap_scaleRatio
        self.zoom_h = pix.h / pg_h * pixmap_scaleRatio
        self.curr_page_links = self.doc[page_number].get_links()
        for i in range(len(self.curr_page_links)):
            link = self.curr_page_links[i]
            r = link["from"].irect
            rect = QRectF(
                r.x0 * self.zoom_w,
                r.y0 * self.zoom_h,
                r.width * self.zoom_w,
                r.height * self.zoom_h,
            )
            link["from_qrectf"] = rect
            painter.drawRect(rect)
        painter.end()

        # Display the pixmap
        self.viewArea.setPixmap(pixmap)

        # Update nav info
        self._update_nav_info()

    def load_file(self, filepath: str, display=False) -> None:
        if not filepath or "pdf" not in filepath.lower():
            return
        else:
            self.filepath = pathlib.Path(filepath).resolve().as_posix()

        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Cannot load PDF: {self.filepath}")

        # Use PyMuPDF to load file
        try:
            self.doc = fitz.open(self.filepath)
        except fitz.FileDataError:
            return
        self.total_pages = self.doc.page_count
        self._update_nav_info()
        if display:
            self.show_pdf()

    def _update_nav_info(self):
        """Update navigation info"""
        self.page_num_validator.setRange(1, self.total_pages)
        self.lb_total_pages.setText(f" / {self.total_pages}")
        if self.doc:
            self.page_num_line_edit.setText(str(self.curr_page))
        else:
            self.page_num_line_edit.setText("")
        self.page_num_line_edit.clearFocus()

    def close_file(self) -> None:
        if self.doc:
            self.doc.close()

    def close(self) -> None:
        self.close_file()
