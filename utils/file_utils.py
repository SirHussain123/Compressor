"""
file_utils.py
-------------
Path helpers, output path generation, and temp directory management.
"""

import os
import tempfile
import shutil
from pathlib import Path


class FileUtils:

    # ------------------------------------------------------------------
    # Output path generation
    # ------------------------------------------------------------------

    @staticmethod
    def build_output_path(input_path: str,
                          output_folder: str | None,
                          output_format: str,
                          suffix: str = "_compressed") -> str:
        """
        Construct the output file path for a job.

        Args:
            input_path:    Full path to the source video.
            output_folder: Target directory; if None, uses the source directory.
            output_format: File extension without dot (e.g. "mp4").
            suffix:        Appended to the stem before the extension.

        Returns:
            Absolute output path string.
        """
        p = Path(input_path)
        folder = Path(output_folder) if output_folder else p.parent
        stem = p.stem + suffix
        return str(folder / f"{stem}.{output_format}")

    @staticmethod
    def ensure_unique(path: str) -> str:
        """
        If the given path already exists, append a numeric counter until unique.
        e.g. "video_compressed.mp4" → "video_compressed_1.mp4"
        """
        p = Path(path)
        if not p.exists():
            return path
        counter = 1
        while True:
            candidate = p.parent / f"{p.stem}_{counter}{p.suffix}"
            if not candidate.exists():
                return str(candidate)
            counter += 1

    # ------------------------------------------------------------------
    # Temp directory management
    # ------------------------------------------------------------------

    @staticmethod
    def create_temp_dir(prefix: str = "compressor_") -> str:
        """Create and return a temporary working directory."""
        return tempfile.mkdtemp(prefix=prefix)

    @staticmethod
    def cleanup_temp_dir(path: str):
        """Safely delete a temporary directory and all its contents."""
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
        except OSError as e:
            # Non-fatal — log but don't crash
            import logging
            logging.warning(f"Failed to clean up temp dir '{path}': {e}")

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def is_video_file(path: str) -> bool:
        """Return True if the path has a recognised video extension."""
        VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm",
                            ".flv", ".wmv", ".m4v", ".ts", ".mpg", ".mpeg"}
        return Path(path).suffix.lower() in VIDEO_EXTENSIONS

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Convert byte count to a human-readable string."""
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes //= 1024
        return f"{size_bytes:.1f} PB"