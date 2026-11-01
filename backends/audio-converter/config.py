"""Central configuration for audio-converter.

Every user-tunable value lives here. Edit this file to change default
behavior without touching the logic in `lib/`; most values can also be
overridden per run via CLI flags (see `lib/cli.py`).
"""
from __future__ import annotations

APP_NAME = "audio-converter"
VERSION = "1.0.0"

# --- Project exit codes (126/127 are reserved by the shell) ---
EXIT_OK = 0
EXIT_GENERAL = 1
EXIT_USAGE = 2
EXIT_NOT_FOUND = 3
EXIT_PERMISSION = 4
EXIT_DEPENDENCY = 5

# --- Input discovery ---
# Extensions picked up when scanning DIRECTORIES. Covers WhatsApp audio
# (.opus voice notes, .ogg/.oga, iPhone .m4a, old .amr) plus common formats.
# Files named explicitly on the CLI are converted regardless of extension
# (ffmpeg decides); .mp3 inputs are always skipped (nothing to convert).
AUDIO_EXTENSIONS = (
    ".opus", ".ogg", ".oga", ".m4a", ".aac", ".amr",
    ".wav", ".flac", ".wma",
)
DEFAULT_RECURSIVE = False  # WhatsApp stores voice notes in year-week subdirs

# --- Conversion (ffmpeg) ---
TARGET_EXTENSION = ".mp3"
DEFAULT_BITRATE = "128k"  # plenty for voice notes; fine for music too
MIN_BITRATE_KBPS = 32
MAX_BITRATE_KBPS = 320
# -nostdin: ffmpeg must never steal the terminal inside batch loops.
FFMPEG_BASE_ARGS = ("-hide_banner", "-loglevel", "error", "-nostdin")
# -map_metadata 0 keeps original tags; ID3v2.3 maximizes player compatibility.
FFMPEG_CODEC_ARGS = ("-codec:a", "libmp3lame",
                     "-map_metadata", "0", "-id3v2_version", "3")

# --- Logging ---
LOG_FILE = None  # e.g. "audio_converter.log" for a persistent audit trail
USE_COLOR = True  # ANSI colors on TTYs; auto-disabled for pipes and NO_COLOR
ANSI_RESET = "\033[0m"
LEVEL_COLORS = {
    "DEBUG": "\033[90m",
    "INFO": "\033[32m",
    "WARN": "\033[33m",
    "ERROR": "\033[31m",
}
