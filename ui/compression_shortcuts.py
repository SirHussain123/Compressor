"""
compression_shortcuts.py
------------------------
Shared app shortcut presets for queue rows and related UI.
"""

from dataclasses import dataclass

from core.video_job import SizeMode


@dataclass(frozen=True)
class CompressionShortcut:
    label: str
    description: str
    size_mode: SizeMode
    size_value: float


SHORTCUT_PRESETS = {
    "Custom": None,
    "Discord": CompressionShortcut(
        label="Discord",
        description="Standard Discord upload target.",
        size_mode=SizeMode.MB,
        size_value=10.0,
    ),
    "Discord Basic": CompressionShortcut(
        label="Discord Basic",
        description="Discord Nitro Basic upload target.",
        size_mode=SizeMode.MB,
        size_value=50.0,
    ),
    "Discord Nitro": CompressionShortcut(
        label="Discord Nitro",
        description="Discord Nitro upload target.",
        size_mode=SizeMode.MB,
        size_value=500.0,
    ),
    "WhatsApp": CompressionShortcut(
        label="WhatsApp",
        description="Conservative media-sharing target for WhatsApp.",
        size_mode=SizeMode.MB,
        size_value=16.0,
    ),
    "X": CompressionShortcut(
        label="X",
        description="Standard non-Premium web upload target for X.",
        size_mode=SizeMode.MB,
        size_value=512.0,
    ),
}
