"""Validación de dependencias, rutas y parámetros ANTES de ejecutar lógica."""
from __future__ import annotations

import shutil
from pathlib import Path

from config import Settings
from lib.errors import DependencyError


def require_tesseract() -> None:
    """Verifica que el binario `tesseract` esté en el PATH.

    Raises:
        DependencyError: Si tesseract no está instalado.
    """
    if shutil.which("tesseract") is None:
        raise DependencyError(
            "'tesseract' no está instalado. Instálalo con: "
            "sudo apt install tesseract-ocr")


def require_ffmpeg(binary: str = "ffmpeg") -> None:
    """Verifica que `ffmpeg` esté disponible (necesario solo para videos).

    Raises:
        DependencyError: Si ffmpeg no está instalado.
    """
    if shutil.which(binary) is None:
        raise DependencyError(
            f"'{binary}' no está instalado (se necesita para videos). "
            "Instálalo con: sudo apt install ffmpeg")


def require_exiftool(binary: str = "exiftool") -> None:
    """Verifica que `exiftool` esté disponible (necesario para embed-date).

    Raises:
        DependencyError: Si exiftool no está instalado.
    """
    if shutil.which(binary) is None:
        raise DependencyError(
            f"'{binary}' no está instalado (se necesita para embed-date). "
            "Instálalo con: sudo apt install libimage-exiftool-perl")


def validate_folder(folder: str | Path) -> Path:
    """Comprueba que la ruta exista y sea un directorio.

    Returns:
        La ruta resuelta como Path.

    Raises:
        FileNotFoundError: Si la ruta no existe.
        NotADirectoryError: Si existe pero no es un directorio.
    """
    path = Path(folder).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"La carpeta '{path}' no existe.")
    if not path.is_dir():
        raise NotADirectoryError(f"'{path}' no es una carpeta.")
    return path


def validate_crop(settings: Settings) -> None:
    """Valida que la región de recorte quede dentro de la imagen.

    Raises:
        ValueError: Si alguna fracción está fuera de 0..1 o se sale del borde.
    """
    fractions = {
        "crop_left_frac": settings.crop_left_frac,
        "crop_top_frac": settings.crop_top_frac,
        "crop_width_frac": settings.crop_width_frac,
        "crop_height_frac": settings.crop_height_frac,
    }
    for name, value in fractions.items():
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name}={value} debe estar entre 0 y 1.")
    if settings.crop_left_frac + settings.crop_width_frac > 1.0:
        raise ValueError("crop_left_frac + crop_width_frac supera el borde derecho.")
    if settings.crop_top_frac + settings.crop_height_frac > 1.0:
        raise ValueError("crop_top_frac + crop_height_frac supera el borde inferior.")
