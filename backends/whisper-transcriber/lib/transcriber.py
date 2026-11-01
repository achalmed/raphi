"""Whisper invocation and output management for whisper-transcriber.

Shells out to the `whisper` CLI (as the original notebook did) instead
of importing the Python API: startup stays instant and torch is only
loaded inside the child process.

Whisper names its outputs after the input stem for BOTH tasks, so a
translation of `audio.mp3` and a transcription of the same file both
target `audio.srt`. To keep them from clobbering each other, a
translation run writes into a private temp dir first and its outputs are
then MOVED into place tagged `audio.en.srt`. Renaming after the fact is
not enough: whisper overwrites the transcription file the instant it
writes, before any rename could run.
"""
from __future__ import annotations

import shutil
import tempfile
from logging import Logger
from pathlib import Path
from subprocess import run
from typing import List, Optional

import config


def build_whisper_command(media_path: Path, task: str, model: str,
                          language: Optional[str], output_dir: Path,
                          output_format: str) -> list:
    """Builds the whisper argv for one media file."""
    command = [
        "whisper", str(media_path),
        "--model", model,
        "--task", task,
        "--output_dir", str(output_dir),
        "--output_format", output_format,
    ]
    if language is not None:
        command += ["--language", language]
    return command


def expected_outputs(media_path: Path, output_dir: Path,
                     output_format: str) -> List[Path]:
    """Paths Whisper will write: <output_dir>/<stem>.<fmt> per format."""
    formats = (config.CONCRETE_FORMATS if output_format == "all"
               else (output_format,))
    return [output_dir / f"{media_path.stem}.{fmt}" for fmt in formats]


def tagged_target(path: Path, final_dir: Path) -> Path:
    """audio.srt -> <final_dir>/audio.en.srt (language-tagged translation)."""
    return final_dir / f"{path.stem}.{config.TRANSLATION_TAG}{path.suffix}"


def _move_tagged_outputs(paths: List[Path], final_dir: Path,
                         logger: Logger) -> List[Path]:
    """Moves temp-dir translation outputs into final_dir tagged '.en'.

    Uses shutil.move so it also works if the temp dir ever lands on a
    different filesystem; overwrites any previous translation.
    """
    tagged = []
    for path in paths:
        target = tagged_target(path, final_dir)
        target.unlink(missing_ok=True)  # shutil.move won't overwrite dirs/files
        shutil.move(str(path), str(target))
        logger.debug("Salida de traducción movida: %s -> %s",
                     path.name, target.name)
        tagged.append(target)
    return tagged


def transcribe_file(media_path: Path, task: str, model: str,
                    language: Optional[str], output_dir: Path,
                    output_format: str, logger: Logger,
                    dry_run: bool = False) -> Optional[List[Path]]:
    """Runs Whisper on one file and returns the generated output paths.

    Returns:
        List of produced files ([] in dry-run), or None if Whisper failed.
    """
    if dry_run:
        command = build_whisper_command(
            media_path, task, model, language, output_dir, output_format)
        logger.info("[SIMULACIÓN] Ejecutaría: %s", " ".join(command))
        if task == "translate":
            logger.info("[SIMULACIÓN] Las salidas llevarían la marca '.%s' "
                        "para no pisar la transcripción.",
                        config.TRANSLATION_TAG)
        return []

    # For translate, whisper writes into a private temp dir so it can never
    # overwrite a transcription's <stem>.<fmt> in output_dir (see module doc).
    is_translate = task == "translate"
    write_dir = (Path(tempfile.mkdtemp(prefix="whisper-translate-",
                                       dir=output_dir))
                 if is_translate else output_dir)
    try:
        command = build_whisper_command(
            media_path, task, model, language, write_dir, output_format)
        logger.info("Procesando '%s' (tarea: %s, modelo: %s)...",
                    media_path.name, task, model)
        result = run(command)  # Whisper prints segments live, like in Colab
        if result.returncode != 0:
            logger.error("whisper terminó con código %d para '%s'.",
                         result.returncode, media_path.name)
            return None
        produced = [p for p in expected_outputs(media_path, write_dir,
                                                output_format) if p.exists()]
        if is_translate:
            produced = _move_tagged_outputs(produced, output_dir, logger)
    finally:
        if is_translate:
            shutil.rmtree(write_dir, ignore_errors=True)
    if not produced:
        logger.warning("Whisper no generó los archivos esperados en '%s'.",
                       output_dir)
    for path in produced:
        logger.info("Generado: %s", path)
    return produced
