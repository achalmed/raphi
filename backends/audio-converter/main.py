#!/usr/bin/env python3
"""audio-converter — audios de WhatsApp (y cualquier otro) a MP3 por lotes.

Orchestration only — the logic lives in lib/:

  1. Parse arguments             (lib/cli.py)
  2. Init logging                (lib/logger.py)
  3. Validate deps/inputs/flags  (lib/validator.py)
  4. Discover sources + plan     (lib/scanner.py)
  5. Convert each file           (lib/converter.py)
  6. Summary; exit 1 if any conversion failed.

Pipeline siblings: script_video_downloader (URL -> mp3/mp4) and
script_whisper_transcriber (mp3 -> txt/srt). Version: 1.0.0
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # run from any CWD

import config
from lib import validator
from lib.cli import build_argument_parser
from lib.converter import convert_file
from lib.logger import setup_logger
from lib.scanner import discover_audio_files, plan_conversions


def print_summary(logger, counts: Counter, dry_run: bool) -> None:
    """Final report of the batch."""
    if dry_run:
        logger.info("Simulación terminada: %d conversión(es) planificada(s), "
                    "%d omitida(s); nada se escribió.",
                    counts["planned"], counts["skipped"])
        return
    logger.info("Resumen: %d convertida(s), %d omitida(s) (ya existían), "
                "%d fallida(s).",
                counts["converted"], counts["skipped"], counts["failed"])
    if counts["failed"]:
        logger.error("Revisa los errores anteriores.")


def main() -> int:
    args = build_argument_parser().parse_args()
    logger = setup_logger(config.APP_NAME, args.verbose, config.LOG_FILE)
    if args.dry_run:
        logger.info("Modo simulación: no se escribirá nada.")
    validator.validate_dependencies(args.dry_run, logger)
    bitrate = validator.validate_bitrate(args.bitrate, logger)
    inputs = validator.validate_inputs(args.inputs, logger)
    output_dir = validator.validate_output_dir(args.output_dir,
                                               args.dry_run, logger)
    sources = discover_audio_files(inputs, args.recursive, logger)
    if not sources:
        logger.warning("No se encontró ningún audio que convertir.")
        return config.EXIT_OK
    plan = plan_conversions(sources, output_dir, logger)
    logger.info("%d audio(s) a procesar (bitrate %s).", len(plan), bitrate)
    counts: Counter = Counter()
    for source, target in plan:
        status = convert_file(source, target, bitrate, args.overwrite,
                              logger, args.dry_run)
        counts[status] += 1
    print_summary(logger, counts, args.dry_run)
    return config.EXIT_GENERAL if counts["failed"] else config.EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.", file=sys.stderr)
        sys.exit(130)  # convención del shell para SIGINT
