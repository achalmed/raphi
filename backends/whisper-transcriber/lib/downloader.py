"""URL audio extraction via yt-dlp for whisper-transcriber.

Replaces the notebook's `!yt-dlp {LINK}` / os.system(f"yt-dlp {LINK}")
cells. The command is always an argv list executed without a shell, so
URLs containing '&', quotes or spaces can neither break the command nor
inject shell syntax.
"""
from __future__ import annotations

import shutil
import subprocess
from logging import Logger
from pathlib import Path
from typing import Optional

import config


def build_download_command(url: str, work_dir: Path) -> list:
    """Builds the yt-dlp argv that extracts the audio into work_dir."""
    command = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", config.DOWNLOAD_AUDIO_FORMAT,
        "--restrict-filenames",
        "--output", str(work_dir / config.YTDLP_OUTPUT_TEMPLATE),
    ]
    if config.YTDLP_NO_PLAYLIST:
        command.append("--no-playlist")
    command.append(url)
    return command


def _locate_downloaded_audio(work_dir: Path, logger: Logger) -> Optional[Path]:
    """Finds the produced audio file; work_dir is fresh, so it must be alone."""
    produced = sorted(work_dir.glob(f"*.{config.DOWNLOAD_AUDIO_FORMAT}"))
    if not produced:
        logger.error("La descarga no produjo ningún archivo .%s en '%s'.",
                     config.DOWNLOAD_AUDIO_FORMAT, work_dir)
        return None
    if len(produced) > 1:
        logger.warning("La descarga produjo %d archivos; se usará '%s'.",
                       len(produced), produced[0].name)
    return produced[0]


def download_audio(url: str, work_dir: Path, logger: Logger,
                   dry_run: bool = False,
                   keep_dir: Optional[Path] = None) -> Optional[Path]:
    """Downloads the audio of a URL as mp3 and returns its path.

    Args:
        url: Page/video URL understood by yt-dlp.
        work_dir: Fresh, private directory for this download.
        keep_dir: When given (--keep-audio), the file is moved there so it
            survives the temporary-directory cleanup.

    Returns:
        Path of the audio file, or None on failure (already logged).
    """
    command = build_download_command(url, work_dir)
    if dry_run:
        logger.info("[SIMULACIÓN] Descargaría el audio con: %s",
                    " ".join(command))
        if keep_dir is not None:
            logger.info("[SIMULACIÓN] El audio descargado se conservaría "
                        "en '%s'.", keep_dir)
        return None
    logger.info("Descargando audio de: %s", url)
    work_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(command)  # progress streams to the terminal
    if result.returncode != 0:
        logger.error("yt-dlp terminó con código %d para '%s'.",
                     result.returncode, url)
        return None
    audio_path = _locate_downloaded_audio(work_dir, logger)
    if audio_path is not None and keep_dir is not None:
        kept_path = keep_dir / audio_path.name
        shutil.move(str(audio_path), kept_path)
        audio_path = kept_path
    if audio_path is not None:
        logger.info("Audio descargado: %s", audio_path)
    return audio_path
