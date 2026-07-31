"""Centralized logging for audio-converter.

All progress messages go through this logger so formatting stays
consistent. Records go to stderr, keeping stdout clean for data output
and shell pipelines. Same logging module as its sibling tool
script_whisper_transcriber (each tool ships self-contained, per repo
convention).
"""
from __future__ import annotations

import copy
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import config

# Align the level tag with the Bash tools of this repo ([WARN], not [WARNING]).
logging.addLevelName(logging.WARNING, "WARN")


class _AnsiFormatter(logging.Formatter):
    """Colors the level tag on TTYs; plain text elsewhere (files, pipes)."""

    def __init__(self, fmt: str, datefmt: str, use_color: bool) -> None:
        super().__init__(fmt, datefmt)
        self._use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        color = config.LEVEL_COLORS.get(record.levelname, "")
        if self._use_color and color:
            # Work on a copy: mutating the record would leak ANSI codes
            # into other handlers (the plain-text log file).
            record = copy.copy(record)
            record.levelname = f"{color}{record.levelname}{config.ANSI_RESET}"
        return super().format(record)


def _color_enabled(stream) -> bool:
    """Honors config.USE_COLOR, the NO_COLOR convention and non-TTY streams."""
    if not config.USE_COLOR or os.environ.get("NO_COLOR"):
        return False
    return hasattr(stream, "isatty") and stream.isatty()


def setup_logger(name: str, verbose: bool = False,
                 log_file: Optional[Path] = None) -> logging.Logger:
    """Configures a logger with console output and optional file output.

    Args:
        name: Logger name, typically the tool name.
        verbose: If True, lowers the threshold to DEBUG.
        log_file: When given, also appends records to this file
            (persistent audit trail).

    Returns:
        The configured logger. Calling this twice with the same name
        returns the existing instance without duplicating handlers.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        # Re-configuring would attach duplicate handlers and print
        # every record twice; return the already-configured instance.
        return logger

    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    log_format = "[%(levelname)s] %(asctime)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(_AnsiFormatter(
        log_format, date_format, _color_enabled(sys.stderr)))
    logger.addHandler(console)

    if log_file is not None:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        logger.addHandler(file_handler)

    return logger
