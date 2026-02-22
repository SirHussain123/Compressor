"""
basic_settings.py
-----------------
Panel for basic output settings: resolution, FPS, format, output path,
and the smart compression toggle.
"""


from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QLineEdit, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import pyqtSignal
from core.video_job import VideoJob


COMMON_RESOLUTIONS = [
    "Original", "3840x2160 (4K)", "2560x1440 (1440p)",
    "1920x1080 (1080p)", "1280x720 (720p)", "854x480 (480p)", "Custom"
]

OUTPUT_FORMATS = ["mp4", "mkv", "avi", "mov", "webm", "flv", "wmv"]


class BasicSettingsPanel(QWidget):
    """
    Displays and collects basic user preferences for a VideoJob.

    Signals:
        settings_changed(): Emitted whenever any control value changes.
    """

    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(10)

        # Output format
        self._format_combo = QComboBox()
        self._format_combo.addItems(OUTPUT_FORMATS)
        self._format_combo.currentIndexChanged.connect(self.settings_changed)
        layout.addRow("Output Format:", self._format_combo)

        # Resolution
        self._resolution_combo = QComboBox()
        self._resolution_combo.addItems(COMMON_RESOLUTIONS)
        self._resolution_combo.currentIndexChanged.connect(self._on_resolution_changed)
        layout.addRow("Resolution:", self._resolution_combo)

        # Custom resolution (hidden unless "Custom" selected)
        self._custom_w = QSpinBox()
        self._custom_w.setRange(1, 7680)
        self._custom_w.setValue(1920)
        self._custom_h = QSpinBox()
        self._custom_h.setRange(1, 4320)
        self._custom_h.setValue(1080)
        res_row = QWidget()
        res_row_layout = QHBoxLayout(res_row)
        res_row_layout.setContentsMargins(0, 0, 0, 0)
        res_row_layout.addWidget(self._custom_w)
        res_row_layout.addWidget(QWidget())   # spacer label "x" todo
        res_row_layout.addWidget(self._custom_h)
        self._custom_res_widget = res_row
        self._custom_res_widget.setVisible(False)
        layout.addRow("Custom (W×H):", self._custom_res_widget)

        # FPS
        self._fps_spin = QDoubleSpinBox()
        self._fps_spin.setRange(1.0, 240.0)
        self._fps_spin.setValue(30.0)
        self._fps_spin.setSuffix(" fps")
        self._fps_spin.setSpecialValueText("Original")
        self._fps_spin.valueChanged.connect(self.settings_changed)
        layout.addRow("Frame Rate:", self._fps_spin)

        # Smart compression toggle
        self._smart_check = QCheckBox("Use AI smart compression")
        self._smart_check.stateChanged.connect(self.settings_changed)
        layout.addRow("", self._smart_check)

        # Output path
        self._output_edit = QLineEdit()
        self._output_edit.setPlaceholderText("Same folder as source")
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_output)
        path_row = QWidget()
        path_layout = QHBoxLayout(path_row)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.addWidget(self._output_edit)
        path_layout.addWidget(browse_btn)
        layout.addRow("Output Folder:", path_row)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_resolution_changed(self, index: int):
        is_custom = self._resolution_combo.currentText() == "Custom"
        self._custom_res_widget.setVisible(is_custom)
        self.settings_changed.emit()

    def _browse_output(self):
        from PyQt6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self._output_edit.setText(folder)
            self.settings_changed.emit()

    # ------------------------------------------------------------------
    # Apply / read settings
    # ------------------------------------------------------------------

    def apply_to_job(self, job: VideoJob):
        """Write the current panel values into a VideoJob."""
        job.output_format = self._format_combo.currentText()
        job.use_smart_compression = self._smart_check.isChecked()

        res_text = self._resolution_combo.currentText()
        if res_text == "Custom":
            job.target_width = self._custom_w.value()
            job.target_height = self._custom_h.value()
        elif res_text != "Original":
            # Parse "1920x1080 (1080p)" → 1920, 1080
            try:
                dims = res_text.split(" ")[0].split("x")
                job.target_width = int(dims[0])
                job.target_height = int(dims[1])
            except (IndexError, ValueError):
                pass

        if self._fps_spin.value() > 1.0:
            job.target_fps = self._fps_spin.value()

    def populate_from_job(self, job: VideoJob):
        """Populate controls from an existing VideoJob (e.g. when user selects a row)."""
        # TODO: reverse-apply job values back to UI controls
        pass