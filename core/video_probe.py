"""
video_probe.py
--------------
Handles FFmpeg-based probing and metadata extraction for video files.
"""

import ffmpeg
from dataclasses import dataclass
from typing import Optional


@dataclass
class VideoMetadata:
    """Holds all extracted metadata for a single video file."""
    path: str
    codec_name: str
    codec_long_name: str
    width: int
    height: int
    fps: float
    duration: float        # seconds
    bitrate: int           # bits per second
    file_size: int         # bytes
    audio_codec: Optional[str] = None
    audio_sample_rate: Optional[int] = None
    audio_channels: Optional[int] = None
    format_name: Optional[str] = None


class VideoProbe:
    """Probes a video file and returns structured metadata."""

    @staticmethod
    def probe(file_path: str) -> VideoMetadata:
        """
        Probe a video file using ffmpeg-python and return a VideoMetadata object.

        Args:
            file_path: Absolute or relative path to the video file.

        Returns:
            VideoMetadata dataclass populated with stream info.

        Raises:
            ffmpeg.Error: If FFmpeg cannot probe the file.
            StopIteration: If no video stream is found.
        """
        raw = ffmpeg.probe(file_path)

        video_stream = next(
            s for s in raw["streams"] if s["codec_type"] == "video"
        )

        audio_stream = next(
            (s for s in raw["streams"] if s["codec_type"] == "audio"), None
        )

        fmt = raw["format"]

        # Parse FPS safely (can be a fraction string like "30000/1001")
        fps_raw = video_stream.get("r_frame_rate", "0/1")
        fps = VideoProbe._parse_fraction(fps_raw)

        return VideoMetadata(
            path=file_path,
            codec_name=video_stream.get("codec_name", "unknown"),
            codec_long_name=video_stream.get("codec_long_name", "unknown"),
            width=int(video_stream.get("width", 0)),
            height=int(video_stream.get("height", 0)),
            fps=fps,
            duration=float(fmt.get("duration", 0)),
            bitrate=int(fmt.get("bit_rate", 0)),
            file_size=int(fmt.get("size", 0)),
            audio_codec=audio_stream.get("codec_name") if audio_stream else None,
            audio_sample_rate=int(audio_stream["sample_rate"]) if audio_stream else None,
            audio_channels=int(audio_stream["channels"]) if audio_stream else None,
            format_name=fmt.get("format_name"),
        )

    @staticmethod
    def _parse_fraction(value: str) -> float:
        """Convert a fraction string like '30000/1001' to a float."""
        try:
            if "/" in value:
                num, den = value.split("/")
                return float(num) / float(den) if float(den) != 0 else 0.0
            return float(value)
        except (ValueError, ZeroDivisionError):
            return 0.0