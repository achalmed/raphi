#!/usr/bin/env python3
"""Punto de entrada de camera-timestamp-renamer (solo orquestación).

Renombra fotos de cámara según la fecha/hora impresa en la imagen. Traduce
las excepciones conocidas a códigos de salida estables (ver config.py).
"""
from __future__ import annotations

import sys
from pathlib import Path

from config import (EXIT_DEPENDENCY, EXIT_GENERAL, EXIT_NOT_FOUND,
                    EXIT_PERMISSION, EXIT_USAGE, APP_NAME)
from lib import commands
from lib.cli import build_argument_parser, settings_from_args
from lib.errors import DependencyError, PlanError
from lib.logger import setup_logger


def _dispatch(args, settings, logger) -> int:
    """Enruta el subcomando ya parseado a su manejador."""
    if args.command == "analyze":
        return commands.cmd_analyze(args.folder, settings, logger)
    if args.command == "apply":
        return commands.cmd_apply(args.folder, settings, logger,
                                  args.execute, args.from_plan)
    if args.command == "verify":
        return commands.cmd_verify(args.folder, settings, logger, args.from_plan)
    if args.command == "embed-date":
        return commands.cmd_embed_date(args.folder, settings, logger, args.execute)
    if args.command == "audit-dates":
        return commands.cmd_audit_dates(args.folder, settings, logger, args.year)
    if args.command == "fix-names":
        return commands.cmd_fix_names(args.folder, settings, logger, args.execute)
    if args.command == "sync-digikam":
        return commands.cmd_sync_digikam(args.folder, settings, logger,
                                         args.execute)
    return commands.cmd_undo(args.folder, settings, logger, args.execute)


def main(argv: list[str] | None = None) -> int:
    """Analiza argumentos, prepara el entorno y ejecuta el subcomando."""
    args = build_argument_parser().parse_args(argv)
    log_file = Path(args.log_file) if getattr(args, "log_file", None) else None
    logger = setup_logger(APP_NAME, getattr(args, "verbose", False), log_file)
    settings = settings_from_args(args)
    try:
        return _dispatch(args, settings, logger)
    except DependencyError as error:
        logger.error("%s", error)
        return EXIT_DEPENDENCY
    except FileNotFoundError as error:
        logger.error("%s", error)
        return EXIT_NOT_FOUND
    except PermissionError as error:
        logger.error("Sin permisos: %s", error)
        return EXIT_PERMISSION
    except (PlanError, NotADirectoryError, ValueError) as error:
        logger.error("%s", error)
        return EXIT_USAGE
    except OSError as error:
        logger.error("Error de E/S: %s", error)
        return EXIT_GENERAL


if __name__ == "__main__":
    sys.exit(main())
