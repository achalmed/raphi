"""Logging centralizado (INFO / WARNING / ERROR).

Toda la salida al usuario pasa por aquí para mantener un formato uniforme.
Los mensajes van en español; el código, en inglés técnico.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional


def setup_logger(name: str, verbose: bool = False,
                 log_file: Optional[Path] = None) -> logging.Logger:
    """Configura un logger con salida a consola y, opcionalmente, a archivo.

    Args:
        name: Nombre del logger, normalmente el de la herramienta.
        verbose: Si es True baja el umbral a DEBUG.
        log_file: Si se indica, añade los registros a este archivo
            (traza de auditoría persistente).

    Returns:
        El logger configurado. Llamarlo dos veces con el mismo nombre
        devuelve la instancia existente sin duplicar manejadores.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        # Reconfigurar añadiría manejadores duplicados y cada línea se
        # imprimiría dos veces; devolvemos la instancia ya configurada.
        return logger

    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    formatter = logging.Formatter(
        "[%(levelname)s] %(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    if log_file is not None:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
