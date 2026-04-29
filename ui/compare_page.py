"""
compare_page.py
---------------
Side-by-side video comparison page with synchronized playback and seeking.
"""

import os

from PyQt6.QtCore import QUrl, Qt, pyqtSignal
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.widgets import ConsistentComboBox, apply_surface_shadow


class ComparePage(QWidget):
    """Import two videos and compare them side by side with one timeline."""

    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("contentPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._duration_ms = 0
        self._seeking = False

        self._left_player = QMediaPlayer(self)
        self._right_player = QMediaPlayer(self)
        self._left_audio = QAudioOutput(self)
        self._right_audio = QAudioOutput(self)
        self._left_audio.setMuted(False)
        self._right_audio.setMuted(True)
        self._left_player.setAudioOutput(self._left_audio)
        self._right_player.setAudioOutput(self._right_audio)

        self._build_ui()
        self._connect_player(self._left_player, "Source A")
        self._connect_player(self._right_player, "Source B")

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 16)
        layout.setSpacing(16)

        layout.addWidget(
            self._make_page_header(
                "Compare Videos",
                "Load two files, scrub one shared timeline, and judge compression or enhancement changes side by side.",
            )
        )

        compare_card = QFrame()
        compare_card.setObjectName("compareCard")
        card_layout = QVBoxLayout(compare_card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(14)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)

        self._left_stack, self._left_video, self._left_name = self._make_video_pane("Source A")
        self._right_stack, self._right_video, self._right_name = self._make_video_pane("Source B")
        self._left_player.setVideoOutput(self._left_video)
        self._right_player.setVideoOutput(self._right_video)

        grid.addWidget(self._left_name, 0, 0)
        grid.addWidget(self._right_name, 0, 1)
        grid.addWidget(self._left_stack, 1, 0)
        grid.addWidget(self._right_stack, 1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        card_layout.addLayout(grid, 1)

        card_layout.addLayout(self._make_controls())
        layout.addWidget(compare_card, 1)
        apply_surface_shadow(compare_card)

    def _make_page_header(self, title: str, subtitle: str) -> QWidget:
        header = QWidget()
        header.setObjectName("pageHeader")
        layout = QVBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("pageSubtitle")
        subtitle_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        return header

    def _make_video_pane(self, label: str) -> tuple[QStackedWidget, QVideoWidget, QLabel]:
        name = QLabel(f"{label}: no file loaded")
        name.setObjectName("compareVideoName")
        name.setWordWrap(True)

        stack = QStackedWidget()
        stack.setObjectName("compareVideoStack")
        stack.setMinimumHeight(300)
        stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        placeholder = QFrame()
        placeholder.setObjectName("compareVideoPlaceholder")
        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_layout.setContentsMargins(18, 18, 18, 18)
        placeholder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label = QLabel(f"Import {label[-1]} to preview")
        placeholder_label.setObjectName("comparePlaceholderLabel")
        placeholder_layout.addWidget(placeholder_label)

        video = QVideoWidget()
        video.setObjectName("compareVideo")
        video.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        stack.addWidget(placeholder)
        stack.addWidget(video)
        return stack, video, name

    def _make_controls(self) -> QVBoxLayout:
        controls = QVBoxLayout()
        controls.setSpacing(10)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self._load_left_btn = QPushButton("Import A")
        self._load_left_btn.clicked.connect(lambda: self._choose_video(self._left_player, self._left_name, "Source A"))
        self._load_right_btn = QPushButton("Import B")
        self._load_right_btn.clicked.connect(lambda: self._choose_video(self._right_player, self._right_name, "Source B"))

        self._audio_combo = ConsistentComboBox()
        self._audio_combo.addItem("Audio: A", "left")
        self._audio_combo.addItem("Audio: B", "right")
        self._audio_combo.addItem("Audio: Muted", "muted")
        self._audio_combo.setFixedWidth(132)
        self._audio_combo.setEnabled(False)
        self._audio_combo.currentIndexChanged.connect(self._sync_audio_source)

        self._play_btn = QPushButton("Play")
        self._play_btn.setObjectName("primaryButton")
        self._play_btn.clicked.connect(self._toggle_playback)
        self._play_btn.setEnabled(False)

        self._time_label = QLabel("00:00 / 00:00")
        self._time_label.setObjectName("compareTimeLabel")
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        button_row.addWidget(self._load_left_btn)
        button_row.addWidget(self._load_right_btn)
        button_row.addStretch()
        button_row.addWidget(self._audio_combo)
        button_row.addWidget(self._play_btn)
        button_row.addWidget(self._time_label)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 0)
        self._slider.sliderPressed.connect(self._on_slider_pressed)
        self._slider.sliderReleased.connect(self._on_slider_released)
        self._slider.sliderMoved.connect(self._seek_preview)

        hint = QLabel("Tip: for the cleanest comparison, use videos with the same duration and frame rate.")
        hint.setObjectName("compareHint")
        hint.setWordWrap(True)

        controls.addLayout(button_row)
        controls.addWidget(self._slider)
        controls.addWidget(hint)
        return controls

    def _connect_player(self, player: QMediaPlayer, label: str):
        player.durationChanged.connect(lambda duration, p=player: self._on_duration_changed(p, duration))
        player.positionChanged.connect(lambda position, p=player: self._on_position_changed(p, position))
        player.errorOccurred.connect(lambda _error, message, name=label: self._on_player_error(name, message))

    def _choose_video(self, player: QMediaPlayer, name_label: QLabel, source_label: str):
        path, _ = QFileDialog.getOpenFileName(
            self,
            f"Import {source_label}",
            "",
            "Video Files (*.mp4 *.mov *.mkv *.avi *.webm *.m4v);;All Files (*)",
        )
        if not path:
            return

        player.setSource(QUrl.fromLocalFile(path))
        player.pause()
        name_label.setText(f"{source_label}: {os.path.basename(path)}")
        self._stack_for_player(player).setCurrentIndex(1)
        self._sync_audio_source()
        self._update_controls_enabled()
        self.status_message.emit(f"Loaded {source_label}: {os.path.basename(path)}")

    def _toggle_playback(self):
        if not self._has_both_sources():
            return

        if self._left_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._pause()
            return

        position = self._slider.value()
        self._set_both_positions(position)
        self._left_player.play()
        self._right_player.play()
        self._sync_audio_source()
        self._play_btn.setText("Pause")
        self.status_message.emit("Comparison playback started.")

    def _pause(self):
        self._left_player.pause()
        self._right_player.pause()
        self._play_btn.setText("Play")
        self.status_message.emit("Comparison playback paused.")

    def _on_duration_changed(self, player: QMediaPlayer, duration: int):
        del player
        durations = [
            item.duration()
            for item in (self._left_player, self._right_player)
            if item.source().isValid() and item.duration() > 0
        ]
        self._duration_ms = min(durations) if durations else 0
        self._slider.setRange(0, self._duration_ms)
        self._update_time_label(self._slider.value())
        self._update_controls_enabled()

    def _on_position_changed(self, player: QMediaPlayer, position: int):
        del player
        if self._seeking:
            return
        bounded = min(position, self._duration_ms) if self._duration_ms else position
        self._slider.setValue(bounded)
        self._update_time_label(bounded)

    def _on_slider_pressed(self):
        self._seeking = True
        self._pause()

    def _on_slider_released(self):
        position = self._slider.value()
        self._set_both_positions(position)
        self._update_time_label(position)
        self._seeking = False

    def _seek_preview(self, position: int):
        self._update_time_label(position)

    def _set_both_positions(self, position: int):
        self._left_player.setPosition(position)
        self._right_player.setPosition(position)

    def _on_player_error(self, label: str, message: str):
        if message:
            self.status_message.emit(f"{label} playback error: {message}")

    def _update_controls_enabled(self):
        ready = self._has_both_sources()
        self._play_btn.setEnabled(ready)
        self._audio_combo.setEnabled(ready)

    def _has_both_sources(self) -> bool:
        return self._left_player.source().isValid() and self._right_player.source().isValid()

    def _sync_audio_source(self):
        selected = self._audio_combo.currentData()
        self._left_audio.setMuted(selected != "left")
        self._right_audio.setMuted(selected != "right")

    def _stack_for_player(self, player: QMediaPlayer) -> QStackedWidget:
        if player is self._left_player:
            return self._left_stack
        return self._right_stack

    def _update_time_label(self, position: int):
        self._time_label.setText(f"{self._format_ms(position)} / {self._format_ms(self._duration_ms)}")

    @staticmethod
    def _format_ms(value: int) -> str:
        total_seconds = max(0, value // 1000)
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
