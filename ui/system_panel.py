"""
system_panel.py
---------------
System page for hardware visibility and CPU/GPU load profiles.
"""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFormLayout, QGroupBox, QLabel, QVBoxLayout, QWidget

from core.video_job import VideoJob
from ui.widgets import ConsistentComboBox, apply_surface_shadow
from utils.system_info import detect_cpu_name, detect_gpu_names


LOAD_LEVELS = ["Low", "Balanced", "High", "Maximum"]

CPU_NOTES = {
    "Low": "Lightest encode pressure. Best for keeping the PC responsive, but slowest.",
    "Balanced": "Moderate thread use. Good default for most machines.",
    "High": "Pushes the CPU harder during extraction and encoding. Faster, but hotter.",
    "Maximum": "Lets FFmpeg use as much CPU as it wants. Highest stress and heat.",
}

GPU_NOTES = {
    "Low": "Gentlest AI workload profile. Best for quieter systems and weaker GPUs.",
    "Balanced": "Moderate AI processing pressure. Recommended default for RIFE and Real-ESRGAN.",
    "High": "Heavier AI worker profile. Faster on capable GPUs, but may run hotter.",
    "Maximum": "Most aggressive AI worker profile. Highest GPU stress and VRAM pressure.",
}


class SystemPanel(QWidget):
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 6, 4, 10)
        root.setSpacing(18)
        root.addWidget(self._make_hardware_group())
        root.addWidget(self._make_load_group())
        root.addWidget(self._make_quality_group())
        root.addStretch()

    def _make_hardware_group(self) -> QGroupBox:
        box = QGroupBox("Detected Hardware")
        apply_surface_shadow(box, blur=24.0, offset_y=5.0)
        form = QFormLayout(box)
        form.setSpacing(8)

        self._cpu_label = QLabel(detect_cpu_name())
        self._cpu_label.setWordWrap(True)

        gpus = detect_gpu_names()
        gpu_text = "\n".join(gpus) if gpus else "GPU not identified"
        self._gpu_label = QLabel(gpu_text)
        self._gpu_label.setWordWrap(True)

        form.addRow("CPU:", self._cpu_label)
        form.addRow("GPU:", self._gpu_label)
        return box

    def _make_load_group(self) -> QGroupBox:
        box = QGroupBox("Workload Intensity")
        apply_surface_shadow(box, blur=24.0, offset_y=5.0)
        form = QFormLayout(box)
        form.setSpacing(8)

        self._cpu_combo = ConsistentComboBox()
        self._cpu_combo.addItems(LOAD_LEVELS)
        self._cpu_combo.setCurrentText("Balanced")
        self._cpu_combo.currentIndexChanged.connect(self._update_notes)
        self._cpu_combo.currentIndexChanged.connect(self.settings_changed)
        form.addRow("CPU Load:", self._cpu_combo)

        self._gpu_combo = ConsistentComboBox()
        self._gpu_combo.addItems(LOAD_LEVELS)
        self._gpu_combo.setCurrentText("Balanced")
        self._gpu_combo.currentIndexChanged.connect(self._update_notes)
        self._gpu_combo.currentIndexChanged.connect(self.settings_changed)
        form.addRow("GPU Load:", self._gpu_combo)

        self._cpu_note = QLabel("")
        self._cpu_note.setWordWrap(True)
        self._cpu_note.setObjectName("infoLabel")
        form.addRow("CPU Impact:", self._cpu_note)

        self._gpu_note = QLabel("")
        self._gpu_note.setWordWrap(True)
        self._gpu_note.setObjectName("infoLabel")
        form.addRow("GPU Impact:", self._gpu_note)

        self._update_notes()
        return box

    def _make_quality_group(self) -> QGroupBox:
        box = QGroupBox("Frame Gen Output Presets")
        apply_surface_shadow(box, blur=24.0, offset_y=5.0)
        form = QFormLayout(box)
        form.setSpacing(8)

        smaller = QLabel("Lowest output size. Best when smoother motion matters more than detail.")
        smaller.setWordWrap(True)
        smaller.setObjectName("infoLabel")

        balanced = QLabel("Recommended default. Tries to keep size growth under control without looking too rough.")
        balanced.setWordWrap(True)
        balanced.setObjectName("infoLabel")

        quality = QLabel("Keeps more visual detail, but file sizes can rise much faster.")
        quality.setWordWrap(True)
        quality.setObjectName("infoLabel")

        form.addRow("Smaller:", smaller)
        form.addRow("Balanced:", balanced)
        form.addRow("Higher Quality:", quality)
        return box

    def _update_notes(self):
        self._cpu_note.setText(CPU_NOTES[self._cpu_combo.currentText()])
        self._gpu_note.setText(GPU_NOTES[self._gpu_combo.currentText()])

    def apply_to_job(self, job: VideoJob):
        job.cpu_load = self._cpu_combo.currentText()
        job.gpu_load = self._gpu_combo.currentText()
