"""
compression.py
--------------
Compression logic and preset management.
Works in tandem with the AI advisor (ai/compression_advisor.py) to apply
smart or manual compression settings onto a VideoJob.
"""


from core.video_job import VideoJob
from core.video_probe import VideoMetadata


# Codec presets ordered from fastest to slowest (libx264/libx265 compatible)
SPEED_PRESETS = ["ultrafast", "superfast", "veryfast", "faster", "fast",
                 "medium", "slow", "slower", "veryslow"]

# Recommended CRF ranges per codec
CRF_DEFAULTS = {
    "libx264": 23,
    "libx265": 28,
    "libvpx-vp9": 33,
    "libaom-av1": 35,
}


class CompressionEngine:
    """
    Applies compression parameters to a VideoJob.
    Can operate in manual mode (user-defined settings) or smart mode
    (delegating to the AI advisor for suggestions).
    """

    def apply_manual(self, job: VideoJob,
                     codec: str,
                     crf: int,
                     preset: str,
                     bitrate_kbps: int | None = None):
        """
        Apply user-defined compression settings directly to a job.

        Args:
            job:          The VideoJob to configure.
            codec:        FFmpeg video codec string (e.g. "libx264").
            crf:          Constant Rate Factor value.
            preset:       FFmpeg speed preset.
            bitrate_kbps: Optional target bitrate. Overrides CRF if set.
        """
        job.video_codec = codec
        job.crf = crf
        job.preset = preset
        job.bitrate_kbps = bitrate_kbps

    def apply_smart(self, job: VideoJob):
        """
        Use the AI/heuristic advisor to suggest and apply optimal settings.
        Requires job.source_metadata to be populated first.

        Args:
            job: The VideoJob to configure.
        """
        from ai.compression_advisor import CompressionAdvisor
        advisor = CompressionAdvisor()
        suggestion = advisor.suggest(job.source_metadata)

        job.video_codec = suggestion.codec
        job.crf = suggestion.crf
        job.preset = suggestion.preset
        job.smart_suggestion_applied = True

    def estimate_output_size_mb(self, job: VideoJob) -> float | None:
        """
        Rough estimate of the output file size based on bitrate and duration.
        Returns None if insufficient data is available.
        """
        if not job.source_metadata:
            return None

        bitrate = job.bitrate_kbps * 1000 if job.bitrate_kbps else None
        if not bitrate:
            # Estimate from CRF if no bitrate is set (rough heuristic)
            return None

        duration = job.source_metadata.duration
        size_bytes = (bitrate * duration) / 8
        return round(size_bytes / (1024 ** 2), 2)