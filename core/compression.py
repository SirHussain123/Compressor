"""
compression.py
--------------
Size-based compression planning with decoder-safety limits.

Two modes:
  - Percentage: reduce file size by X%
  - MB: target a specific output size in megabytes

The lower bound here is intentionally about "still likely decodes cleanly",
not "still looks good".
"""

from dataclasses import dataclass
from typing import Optional

from core.video_probe import VideoMetadata


SPEED_PRESETS = ["veryslow", "slower", "slow", "medium", "fast", "faster", "veryfast"]

CRF_DEFAULTS = {
    "libx264": 26,
    "libx265": 30,
    "libvpx-vp9": 34,
    "libaom-av1": 38,
}


@dataclass
class CompressionPlan:
    codec: str
    preset: str
    two_pass: bool = True
    target_bitrate_kbps: Optional[int] = None
    reason: str = ""


@dataclass
class CompressionLimits:
    min_target_mb: float
    max_reduction_pct: float
    min_video_bitrate_kbps: int
    min_audio_bitrate_kbps: int
    min_total_bitrate_kbps: int
    min_target_bytes: int


class CompressionEngine:
    def get_limits(self, meta: VideoMetadata) -> CompressionLimits:
        if not meta.file_size:
            raise ValueError("Source file size unknown - cannot compute safety limits.")
        if not meta.duration or meta.duration <= 0:
            raise ValueError("Source duration unknown - cannot compute safety limits.")

        audio_kbps = self._safe_audio_floor_kbps(meta)
        src_total_kbps = max(1, int(meta.bitrate / 1000)) if meta.bitrate else 0
        src_video_kbps = max(0, src_total_kbps - audio_kbps)
        pixel_rate = max(1.0, meta.width * meta.height * max(meta.fps, 24.0))

        dynamic_floor_kbps = int(pixel_rate * 0.00075 / 1000)
        source_ratio_floor_kbps = int(src_video_kbps * 0.01) if src_video_kbps else 0

        min_video_kbps = max(
            self._resolution_floor_kbps(meta),
            dynamic_floor_kbps,
            source_ratio_floor_kbps,
            12,
        )
        min_total_kbps = max(24, min_video_kbps + audio_kbps + 6)
        min_target_bytes = int(meta.duration * min_total_kbps * 1000 / 8)

        min_target_bytes = min(min_target_bytes, int(meta.file_size * 0.99))
        min_target_bytes = max(min_target_bytes, 32 * 1024)

        max_reduction_pct = max(
            1.0,
            min(99.0, (1.0 - (min_target_bytes / meta.file_size)) * 100.0),
        )

        return CompressionLimits(
            min_target_mb=min_target_bytes / (1024 * 1024),
            max_reduction_pct=max_reduction_pct,
            min_video_bitrate_kbps=min_video_kbps,
            min_audio_bitrate_kbps=audio_kbps,
            min_total_bitrate_kbps=min_total_kbps,
            min_target_bytes=min_target_bytes,
        )

    def plan_percent(
        self,
        meta: VideoMetadata,
        codec: str,
        preset: str,
        reduction_pct: float,
    ) -> CompressionPlan:
        if not meta.file_size:
            raise ValueError("Source file size unknown - cannot compute percentage target.")
        if not 1 <= reduction_pct <= 99:
            raise ValueError(f"Reduction must be 1-99%, got {reduction_pct}%.")

        limits = self.get_limits(meta)
        if reduction_pct > limits.max_reduction_pct:
            raise ValueError(
                f"This target is below the decoder-safety floor for this file. "
                f"Try staying under about {limits.max_reduction_pct:.0f}% reduction "
                f"or above {limits.min_target_mb:.1f} MB."
            )

        target_bytes = meta.file_size * (1.0 - reduction_pct / 100.0)
        src_kbps = meta.bitrate / 1000 if meta.bitrate else 0

        return self._plan_from_bytes(
            meta,
            codec,
            preset,
            target_bytes,
            reason=(
                f"{reduction_pct:.0f}% reduction - "
                f"source {meta.file_size / 1024 / 1024:.1f} MB at {src_kbps:.0f} kbps"
            ),
        )

    def plan_mb(
        self,
        meta: VideoMetadata,
        codec: str,
        preset: str,
        target_mb: float,
    ) -> CompressionPlan:
        if target_mb <= 0:
            raise ValueError("Target size must be greater than 0 MB.")

        target_bytes = target_mb * 1024 * 1024
        src_mb = meta.file_size / 1024 / 1024 if meta.file_size else 0

        if meta.file_size and target_bytes >= meta.file_size:
            raise ValueError(
                f"Target ({target_mb:.1f} MB) must be smaller than "
                f"the source ({src_mb:.1f} MB)."
            )

        limits = self.get_limits(meta)
        if target_bytes < limits.min_target_bytes:
            raise ValueError(
                f"This target is below the decoder-safety floor for this file. "
                f"Try staying at or above {limits.min_target_mb:.1f} MB."
            )

        return self._plan_from_bytes(
            meta,
            codec,
            preset,
            target_bytes,
            reason=f"Target {target_mb:.1f} MB - source was {src_mb:.1f} MB",
        )

    def _plan_from_bytes(
        self,
        meta: VideoMetadata,
        codec: str,
        preset: str,
        target_bytes: float,
        reason: str,
    ) -> CompressionPlan:
        if not meta.duration or meta.duration <= 0:
            raise ValueError("Source duration unknown - cannot compute bitrate target.")

        duration = meta.duration
        audio_kbps = self._safe_audio_floor_kbps(meta)
        video_bits = (target_bytes * 8) - (audio_kbps * 1000 * duration)

        if video_bits <= 0:
            raise ValueError(
                f"Target size is too small to fit the audio track "
                f"({audio_kbps} kbps x {duration:.0f}s)."
            )

        video_kbps = max(8, int(video_bits / duration / 1000))

        return CompressionPlan(
            codec=codec,
            preset=preset,
            two_pass=True,
            target_bitrate_kbps=video_kbps,
            reason=f"{reason} -> {video_kbps} kbps video bitrate. Two-pass.",
        )

    def _safe_audio_floor_kbps(self, meta: VideoMetadata) -> int:
        if not meta.audio_codec:
            return 0
        if meta.audio_channels and meta.audio_channels >= 6:
            return 96
        if meta.audio_channels and meta.audio_channels == 1:
            return 24
        return 48

    def _resolution_floor_kbps(self, meta: VideoMetadata) -> int:
        pixels = meta.width * meta.height
        if pixels >= 3840 * 2160:
            return 120
        if pixels >= 2560 * 1440:
            return 80
        if pixels >= 1920 * 1080:
            return 55
        if pixels >= 1280 * 720:
            return 38
        if pixels >= 854 * 480:
            return 24
        return 16
