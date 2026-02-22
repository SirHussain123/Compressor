"""
advanced_settings.py
--------------------
Panel for advanced FFmpeg parameters: codec, CRF, bitrate, preset, audio.
Intended to live inside a collapsible "Advanced" tab or section.
"""


from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QComboBox, QSlider,
    QSpinBox, QCheckBox, QLabel, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from core.video_job import VideoJob
from core.compression import SPEED_PRESETS, CRF_DEFAULTS


VIDEO_CODECS = ["libx264", "libx265", "libvpx-vp9", "libaom-av1", "copy"]
AUDIO_CODECS = ["copy", "aac", "mp3", "opus", "flac", "none"]


class AdvancedSettingsPanel(QWidget):
    """
    Exposes low-level FFmpeg controls to the user.

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

        # Video codec
        self._codec_combo = QComboBox()
        self._codec_combo.addItems(VIDEO_CODECS)
        self._codec_combo.currentIndexChanged.connect(self._on_codec_changed)
        layout.addRow("Video Codec:", self._codec_combo)

        # CRF slider + label
        crf_widget = QWidget()
        crf_layout = QHBoxLayout(crf_widget)
        crf_layout.setContentsMargins(0, 0, 0, 0)
        self._crf_slider = QSlider(Qt.Orientation.Horizontal)
        self._crf_slider.setRange(0, 51)
        self._crf_slider.setValue(23)
        self._crf_value_label = QLabel("23")
        self._crf_slider.valueChanged.connect(
            lambda v: (self._crf_value_label.setText(str(v)), self.settings_changed.emit())
        )
        crf_layout.addWidget(self._crf_slider)
        crf_layout.addWidget(self._crf_value_label)
        layout.addRow("CRF (quality):", crf_widget)

        # Encoding preset
        self._preset_combo = QComboBox()
        self._preset_combo.addItems(SPEED_PRESETS)
        self._preset_combo.setCurrentText("medium")
        self._preset_combo.currentIndexChanged.connect(self.settings_changed)
        layout.addRow("Encoding Speed:", self._preset_combo)

        # Target bitrate (optional override)
        self._bitrate_spin = QSpinBox()
        self._bitrate_spin.setRange(0, 100_000)
        self._bitrate_spin.setValue(0)
        self._bitrate_spin.setSuffix(" kbps")
        self._bitrate_spin.setSpecialValueText("Auto (use CRF)")
        self._bitrate_spin.valueChanged.connect(self.settings_changed)
        layout.addRow("Target Bitrate:", self._bitrate_spin)

        # Audio codec
        self._audio_combo = QComboBox()
        self._audio_combo.addItems(AUDIO_CODECS)
        self._audio_combo.currentIndexChanged.connect(self.settings_changed)
        layout.addRow("Audio Codec:", self._audio_combo)

        # Strip audio
        self._strip_audio_check = QCheckBox("Strip audio (video only)")
        self._strip_audio_check.stateChanged.connect(self.settings_changed)
        layout.addRow("", self._strip_audio_check)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_codec_changed(self):
        codec = self._codec_combo.currentText()
        default_crf = CRF_DEFAULTS.get(codec, 23)
        self._crf_slider.setValue(default_crf)
        self.settings_changed.emit()

    # ------------------------------------------------------------------
    # Apply / read settings
    # ------------------------------------------------------------------

    def apply_to_job(self, job: VideoJob):
        """Write current panel values into a VideoJob."""
        codec = self._codec_combo.currentText()
        job.video_codec = None if codec == "copy" else codec

        bitrate = self._bitrate_spin.value()
        if bitrate > 0:
            job.bitrate_kbps = bitrate
            job.crf = None
        else:
            job.crf = self._crf_slider.value()
            job.bitrate_kbps = None

        job.preset = self._preset_combo.currentText()

        audio = self._audio_combo.currentText()
        job.strip_audio = (audio == "none")
        job.audio_codec = None if audio in ("none", "copy") else audio

    def populate_from_job(self, job: VideoJob):
        """Reverse-populate controls from an existing VideoJob."""
        if job.video_codec:
            idx = self._codec_combo.findText(job.video_codec)
            if idx >= 0:
                self._codec_combo.setCurrentIndex(idx)
        if job.crf is not None:
            self._crf_slider.setValue(job.crf)
        if job.bitrate_kbps:
            self._bitrate_spin.setValue(job.bitrate_kbps)
        if job.preset:
            self._preset_combo.setCurrentText(job.preset)
        self._strip_audio_check.setChecked(job.strip_audio)