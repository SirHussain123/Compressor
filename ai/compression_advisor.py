"""
compression_advisor.py
----------------------
Heuristic-based (and optionally model-based) compression advisor.
Analyses source video metadata and suggests optimal FFmpeg settings.
"""


from dataclasses import dataclass
from core.video_probe import VideoMetadata


@dataclass
class CompressionSuggestion:
    """Holds the advisor's recommended compression parameters."""
    codec: str
    crf: int
    preset: str
    reason: str   # Human-readable explanation shown in the UI


class CompressionAdvisor:
    """
    Analyses VideoMetadata and returns a CompressionSuggestion.

    Strategy (heuristic rules — expandable to an ML model later):
    - High bitrate source  → aggressive CRF, slow preset
    - High resolution      → prefer HEVC (libx265) for efficiency
    - Low resolution / web → H.264 (libx264) for compatibility
    - Already compressed   → lighter touch to avoid generation loss
    """

    # Bitrate thresholds in bits per second
    _HIGH_BITRATE = 8_000_000   # 8 Mbps
    _LOW_BITRATE  = 1_000_000   # 1 Mbps

    # Resolution threshold for HEVC recommendation
    _4K_WIDTH = 3000

    def suggest(self, meta: VideoMetadata) -> CompressionSuggestion:
        """
        Analyse metadata and return a compression suggestion.

        Args:
            meta: VideoMetadata from VideoProbe.probe().

        Returns:
            CompressionSuggestion with codec, CRF, preset, and reason.
        """
        codec, crf, preset, reason = self._run_heuristics(meta)
        return CompressionSuggestion(codec=codec, crf=crf, preset=preset, reason=reason)

    # ------------------------------------------------------------------
    # Heuristic rules
    # ------------------------------------------------------------------

    def _run_heuristics(self, meta: VideoMetadata) -> tuple[str, int, str, str]:
        """
        Apply a series of rules to determine the best settings.
        Returns (codec, crf, preset, reason).
        """
        codec  = "libx264"
        crf    = 23
        preset = "medium"
        reason = "Default H.264 settings."

        # Rule 1: 4K+ content → prefer HEVC
        if meta.width >= self._4K_WIDTH:
            codec  = "libx265"
            crf    = 28
            preset = "slow"
            reason = "High-resolution source detected — HEVC (H.265) recommended for better compression efficiency."

        # Rule 2: Very high bitrate → aggressive compression
        elif meta.bitrate >= self._HIGH_BITRATE:
            codec  = "libx265"
            crf    = 26
            preset = "medium"
            reason = "High source bitrate detected — HEVC with moderate CRF will significantly reduce file size."

        # Rule 3: Already low bitrate → gentle compression to avoid quality loss
        elif meta.bitrate <= self._LOW_BITRATE:
            codec  = "libx264"
            crf    = 20
            preset = "fast"
            reason = "Source bitrate is already low — gentle compression applied to preserve quality."

        # Rule 4: Already H.265 → just re-encode lightly or copy
        elif "265" in meta.codec_name or "hevc" in meta.codec_name.lower():
            codec  = "libx265"
            crf    = 28
            preset = "fast"
            reason = "Source is already HEVC — re-encoding lightly to avoid multi-generation loss."

        return codec, crf, preset, reason

    # ------------------------------------------------------------------
    # Future: ML model integration stub
    # ------------------------------------------------------------------

    def suggest_with_model(self, meta: VideoMetadata) -> CompressionSuggestion:
        """
        Placeholder for a trained ML model that predicts optimal CRF/codec
        based on video features (bitrate, resolution, motion complexity, etc).
        """
        raise NotImplementedError("ML model advisor is planned for a future release.")