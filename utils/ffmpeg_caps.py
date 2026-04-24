"""
ffmpeg_caps.py
--------------
Lightweight cached detection of available FFmpeg encoders.
"""

from __future__ import annotations

from functools import lru_cache
import subprocess


@lru_cache(maxsize=1)
def available_encoders() -> set[str]:
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            timeout=6,
            check=False,
        )
    except Exception:
        return set()

    if result.returncode != 0:
        return set()

    encoders: set[str] = set()
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].startswith("V"):
            encoders.add(parts[1].strip())
    return encoders


def first_available_encoder(candidates: list[str]) -> str | None:
    encoders = available_encoders()
    for candidate in candidates:
        if candidate in encoders:
            return candidate
    return None
