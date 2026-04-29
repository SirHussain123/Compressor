"""
logger.py
---------
App-wide logging configuration.
Call setup_logging() once at startup in Main.py.
"""

import logging
import os
from pathlib import Path


LOG_FILE = Path("vidkomp.log")
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.DEBUG):
    """
    Configure root logger with console and file handlers.

    Args:
        level: Logging level (default DEBUG during development).
    """
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=[
            logging.StreamHandler(),                          # Console output
            logging.FileHandler(LOG_FILE, encoding="utf-8"), # Log file
        ]
    )
    logging.getLogger("ffmpeg").setLevel(logging.WARNING)    # Suppress ffmpeg-python noise


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger. Use this in every module:
        from utils.logger import get_logger
        log = get_logger(__name__)
    """
    return logging.getLogger(name)
