"""
job_list_widget.py
------------------
Scrollable queue of VideoJob rows. Minimal, clean, informative.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from core.video_job import VideoJob, JobStatus


STATUS_STYLE = {
    JobStatus.PENDING:   ("Pending",    "color: #999999;"),
    JobStatus.RUNNING:   ("Processing", "color: #3388cc;"),
    JobStatus.DONE:      ("Done",       "color: #339944;"),
    JobStatus.FAILED:    ("Failed",     "color: #cc4444;"),
    JobStatus.CANCELLED: ("Cancelled",  "color: #aa7700;"),
}


class JobRowWidget(QWidget):
    """Single row: filename, metadata, progress bar, status, remove button."""

    remove_requested = pyqtSignal(object)

    def __init__(self, job: VideoJob, parent=None):
        super().__init__(parent)
        self.job = job
        self.setObjectName("jobRow")
        self.setFixedHeight(54)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 6, 12, 0)
        outer.setSpacing(3)

        # Top row
        top = QHBoxLayout()
        top.setSpacing(10)

        self._name_label = QLabel(self.job.display_name())
        self._name_label.setObjectName("jobName")
        self._name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._meta_label = QLabel(self._build_meta())
        self._meta_label.setObjectName("jobMeta")

        self._status_label = QLabel("Pending")
        self._status_label.setObjectName("jobMeta")
        self._status_label.setFixedWidth(70)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._status_label.setStyleSheet("color: #999999; font-size: 11px;")

        self._remove_btn = QPushButton("✕")
        self._remove_btn.setObjectName("removeButton")
        self._remove_btn.setFixedSize(22, 22)
        self._remove_btn.setToolTip("Remove from queue")
        self._remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.job))

        top.addWidget(self._name_label)
        top.addWidget(self._meta_label)
        top.addWidget(self._status_label)
        top.addWidget(self._remove_btn)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(3)

        # Bottom border
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)

        outer.addLayout(top)
        outer.addWidget(self._progress_bar)
        outer.addWidget(line)

    def _build_meta(self) -> str:
        m = self.job.source_metadata
        if not m:
            return ""
        fps = f"{m.fps:.2f}".rstrip("0").rstrip(".")
        mb = m.file_size / (1024 * 1024)
        return f"{m.width}×{m.height}  {fps} fps  {m.codec_name.upper()}  {mb:.0f} MB"

    def set_progress(self, pct: float):
        self._progress_bar.setValue(int(pct))

    def set_status(self, status: JobStatus):
        text, style = STATUS_STYLE.get(status, ("Unknown", ""))
        self._status_label.setText(text)
        self._status_label.setStyleSheet(f"{style} font-size: 11px;")
        if status == JobStatus.DONE:
            self._progress_bar.setValue(100)
            self._progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #339944; }")
        elif status == JobStatus.FAILED:
            self._progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #cc4444; }")
        self._remove_btn.setEnabled(status != JobStatus.RUNNING)


class JobListWidget(QWidget):
    """Scrollable container of JobRowWidgets with header and empty state."""

    job_remove_requested = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: dict[str, JobRowWidget] = {}
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(26)
        header.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #e0e0e0;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 0, 12, 0)

        lbl = QLabel("Queue")
        lbl.setObjectName("sectionLabel")
        self._count_label = QLabel("0 files")
        self._count_label.setObjectName("metaLabel")
        self._count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        h_layout.addWidget(lbl)
        h_layout.addStretch()
        h_layout.addWidget(self._count_label)
        outer.addWidget(header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background-color: #ffffff;")

        self._container = QWidget()
        self._container.setStyleSheet("background-color: #ffffff;")
        self._list_layout = QVBoxLayout(self._container)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._list_layout.setSpacing(0)
        self._list_layout.setContentsMargins(0, 0, 0, 0)

        # Empty state
        self._empty_label = QLabel("No files added yet.\nDrop videos above or click to browse.")
        self._empty_label.setObjectName("metaLabel")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #cccccc; padding: 24px;")
        self._list_layout.addWidget(self._empty_label)

        scroll.setWidget(self._container)
        outer.addWidget(scroll)

    def _refresh_count(self):
        n = len(self._rows)
        self._count_label.setText(f"{n} file{'s' if n != 1 else ''}")
        self._empty_label.setVisible(n == 0)

    def add_job(self, job: VideoJob):
        self._empty_label.setVisible(False)
        row = JobRowWidget(job)
        row.remove_requested.connect(self.job_remove_requested)
        self._rows[job.input_path] = row
        self._list_layout.addWidget(row)
        self._refresh_count()

    def update_progress(self, job: VideoJob, pct: float):
        if row := self._rows.get(job.input_path):
            row.set_progress(pct)

    def update_status(self, job: VideoJob):
        if row := self._rows.get(job.input_path):
            row.set_status(job.status)

    def remove_job(self, job: VideoJob):
        if row := self._rows.pop(job.input_path, None):
            self._list_layout.removeWidget(row)
            row.deleteLater()
        self._refresh_count()