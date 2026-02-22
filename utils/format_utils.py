"""
format_utils.py
---------------
Codec/container compatibility maps and format helper functions.
"""


# Which video codecs are compatible with which containers
CONTAINER_CODEC_MAP: dict[str, list[str]] = {
    "mp4":  ["libx264", "libx265", "libaom-av1", "copy"],
    "mkv":  ["libx264", "libx265", "libvpx-vp9", "libaom-av1", "copy"],
    "webm": ["libvpx-vp9", "libaom-av1"],
    "avi":  ["libx264", "copy"],
    "mov":  ["libx264", "libx265", "copy"],
    "flv":  ["libx264", "copy"],
    "wmv":  ["copy"],
}

# Human-readable codec labels
CODEC_LABELS: dict[str, str] = {
    "libx264":    "H.264 (libx264)",
    "libx265":    "H.265 / HEVC (libx265)",
    "libvpx-vp9": "VP9 (libvpx-vp9)",
    "libaom-av1": "AV1 (libaom-av1)",
    "copy":        "Copy (no re-encode)",
}


class FormatUtils:

    @staticmethod
    def compatible_codecs(container: str) -> list[str]:
        """
        Return the list of video codecs compatible with a given container.

        Args:
            container: Extension without dot, e.g. "mp4".

        Returns:
            List of FFmpeg codec strings. Empty list if container is unknown.
        """
        return CONTAINER_CODEC_MAP.get(container.lower(), [])

    @staticmethod
    def codec_label(codec: str) -> str:
        """Return a human-readable label for an FFmpeg codec string."""
        return CODEC_LABELS.get(codec, codec)

    @staticmethod
    def extension_for_format(fmt: str) -> str:
        """
        Return the file extension for a given format name.
        Handles minor mismatches (e.g. 'h264' → 'mp4').
        """
        mapping = {
            "h264": "mp4",
            "hevc": "mp4",
            "vp9":  "webm",
            "av1":  "mkv",
        }
        return mapping.get(fmt.lower(), fmt.lower())

    @staticmethod
    def all_supported_formats() -> list[str]:
        """Return all supported output container formats."""
        return list(CONTAINER_CODEC_MAP.keys())