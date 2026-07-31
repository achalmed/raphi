"""ffmpeg invocation for audio-converter.

One function converts one file; batching and tallying live in main.py.
The command is always an argv list executed without a shell, so WhatsApp
filenames with spaces ('WhatsApp Audio 2026-07-30 at 10.15.03.ogg') can
never break the invocation.
"""
from __future__ import annotations

import subprocess
from logging import Logger
from pathlib import Path

import config


def build_ffmpeg_command(source: Path, target: Path, bitrate: str) -> list:
    """Builds the ffmpeg argv for one conversion."""
    # -y is safe here: the existence/overwrite policy was already decided
    # by convert_file(); without it ffmpeg would try to prompt and abort.
    return ["ffmpeg", *config.FFMPEG_BASE_ARGS, "-y",
            "-i", str(source),
            *config.FFMPEG_CODEC_ARGS, "-b:a", bitrate,
            str(target)]


def convert_file(source: Path, target: Path, bitrate: str, overwrite: bool,
                 logger: Logger, dry_run: bool = False) -> str:
    """Converts one audio file to MP3.

    Returns:
        'converted', 'skipped' (target existed), 'planned' (dry-run) or
        'failed' — main.py tallies these for the summary and exit code.
    """
    if target.exists() and not overwrite:
        logger.info("Ya existe, se omite: %s (usa --overwrite para rehacer)",
                    target)
        return "skipped"
    if dry_run:
        logger.info("[SIMULACIÓN] Convertiría: '%s' -> '%s' (%s)",
                    source, target, bitrate)
        return "planned"
    command = build_ffmpeg_command(source, target, bitrate)
    logger.debug("Ejecutando: %s", " ".join(command))
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        detail = stderr.splitlines()[-1] if stderr else f"código {result.returncode}"
        logger.error("ffmpeg falló con '%s': %s", source.name, detail)
        target.unlink(missing_ok=True)  # never leave a half-written mp3
        return "failed"
    if not target.exists() or target.stat().st_size == 0:
        logger.error("La conversión de '%s' no produjo un mp3 válido.",
                     source.name)
        target.unlink(missing_ok=True)
        return "failed"
    logger.info("Convertido: %s -> %s", source.name, target)
    return "converted"
