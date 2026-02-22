"""
file_drop_widget.py
-------------------
Drag-and-drop zone for video files. Clean, minimal, bordered.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFileDialog, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent


class FileDropWidget(QWidget):
    """
    Drop zone. Click or drag to add video files.

    Signals:
        files_dropped(list[str]): Valid file paths the user supplied.
    """

    files_dropped = pyqtSignal(list)

    ACCEPTED_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm",
                           ".flv", ".wmv", ".m4v", ".ts", ".mpg", ".mpeg"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("fileDropWidget")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(160)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(4)
        layout.setContentsMargins(24, 24, 24, 24)

        self._label = QLabel("Drop video files here, or click to browse")
        self._label.setObjectName("dropLabel")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._sub = QLabel("MP4 · MKV · MOV · AVI · WEBM · FLV · WMV")
        self._sub.setObjectName("dropSubLabel")
        self._sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self._label)
        layout.addWidget(self._sub)

    # ------------------------------------------------------------------
    # Drag events
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._label.setText("Release to add files")
            self._sub.setText("")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._reset_text()

    def dropEvent(self, event: QDropEvent):
        self._reset_text()
        paths = [
            url.toLocalFile() for url in event.mimeData().urls()
            if url.isLocalFile() and
            any(url.toLocalFile().lower().endswith(e) for e in self.ACCEPTED_EXTENSIONS)
        ]
        if paths:
            self.files_dropped.emit(paths)

    def _reset_text(self):
        self._label.setText("Drop video files here, or click to browse")
        self._sub.setText("MP4 · MKV · MOV · AVI · WEBM · FLV · WMV")

    # ------------------------------------------------------------------
    # Click to browse
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._open_dialog()

    def _open_dialog(self):
        ext_filter = "Video Files (" + " ".join(f"*{e}" for e in self.ACCEPTED_EXTENSIONS) + ")"
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Video Files", "", ext_filter)
        if paths:
            self.files_dropped.emit(paths)