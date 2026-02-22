"""
video_job.py
------------
Defines the VideoJob dataclass — the single source of truth for all
parameters that describe one compression/conversion/processing task.
"""


import os
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
from core.video_probe import VideoMetadata


class JobStatus(Enum):
    PENDING   = auto()
    RUNNING   = auto()
    DONE      = auto()
    FAILED    = auto()
    CANCELLED = auto()


class InterpolationMode(Enum):
    NONE   = auto()
    TWO_X  = auto()   # 2x frame generation via minterpolate (built-in FFmpeg)
    # RIFE = auto()   # Future: neural interpolation


class UpscaleMode(Enum):
    NONE       = auto()
    LANCZOS    = auto()   # Built-in FFmpeg high-quality resampling
    # REALESRGAN = auto() # Future: AI upscaling


@dataclass
class VideoJob:
    """
    Represents a single video processing job.
    All parameters are optional — only those set by the user are applied.
    """

    # --- I/O ---
    input_path: str = ""
    output_path: str = ""

    # --- Source metadata (populated after probing) ---
    source_metadata: Optional[VideoMetadata] = None

    # --- Basic settings ---
    output_format: Optional[str] = None      # e.g. "mp4", "mkv", "avi"
    target_width: Optional[int] = None       # None = keep source
    target_height: Optional[int] = None      # None = keep source
    target_fps: Optional[float] = None       # None = keep source

    # --- Advanced settings ---
    video_codec: Optional[str] = None        # e.g. "libx264", "libx265", "av1"
    audio_codec: Optional[str] = None        # e.g. "aac", "mp3", "copy"
    crf: Optional[int] = None                # Constant Rate Factor (0-51)
    bitrate_kbps: Optional[int] = None       # Target bitrate in kbps
    preset: Optional[str] = None             # FFmpeg preset ("slow", "medium", "fast", ...)
    strip_audio: bool = False

    # --- Smart compression ---
    use_smart_compression: bool = False      # Use AI/heuristic advisor
    smart_suggestion_applied: bool = False   # Whether advisor was applied

    # --- Frame interpolation ---
    interpolation_mode: InterpolationMode = InterpolationMode.NONE

    # --- Upscaling ---
    upscale_mode: UpscaleMode = UpscaleMode.NONE
    upscale_width: Optional[int] = None
    upscale_height: Optional[int] = None

    # --- Job state ---
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0                    # 0.0 – 100.0
    error_message: Optional[str] = None

    def display_name(self) -> str:
        """Human-readable label for the UI."""
        return os.path.basename(self.input_path) if self.input_path else "Unnamed Job"

    def is_active(self) -> bool:
        return self.status == JobStatus.RUNNING

    def reset(self):
        """Reset job state for re-queuing."""
        self.status = JobStatus.PENDING
        self.progress = 0.0
        self.error_message = None