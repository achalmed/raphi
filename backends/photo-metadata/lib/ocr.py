"""Extracción de la marca de fecha/hora impresa en la imagen.

Estrategia: recortar la región configurable (por defecto la esquina superior
izquierda), ampliarla, barrer varios umbrales binarizando el texto y pasar
cada variante por tesseract. Los resultados válidos se votan; el más repetido
gana. Si el barrido "claro" (texto blanco) no da nada, se intenta la polaridad
"oscura" (contorno del texto) para fotogramas sobreexpuestos.
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

from config import Settings


@dataclass
class OcrResult:
    """Resultado del OCR para un archivo.

    status: 'confident' | 'weak' | 'dark' | 'fail' | 'error'.
    """

    file: str
    stamp: Optional[str]
    status: str
    votes: dict = field(default_factory=dict)


def crop_for_display(image: Image.Image, settings: Settings) -> Image.Image:
    """Recorta (sin binarizar) la región de análisis, para montajes de revisión."""
    width, height = image.size
    right = min(width, int(width * (settings.crop_left_frac + settings.crop_width_frac)))
    bottom = min(height, int(height * (settings.crop_top_frac + settings.crop_height_frac)))
    box = (int(width * settings.crop_left_frac), int(height * settings.crop_top_frac),
           right, bottom)
    return image.crop(box)


def _analysis_array(image: Image.Image, settings: Settings) -> np.ndarray:
    """Devuelve el recorte en escala de grises, ampliado, como array numpy."""
    crop = crop_for_display(image, settings)
    scaled = crop.resize(
        (max(1, crop.width * settings.upscale_factor),
         max(1, crop.height * settings.upscale_factor)),
        Image.Resampling.LANCZOS)
    return np.asarray(scaled)


def _binarize(array: np.ndarray, threshold: int, keep_bright: bool) -> np.ndarray:
    """Binariza a texto negro sobre fondo blanco (lo que tesseract espera).

    keep_bright=True conserva los píxeles claros (texto blanco); False conserva
    los oscuros (contorno del texto en fondos sobreexpuestos).
    """
    mask = array > threshold if keep_bright else array < threshold
    return np.where(mask, 0, 255).astype("uint8")


def _run_tesseract(array: np.ndarray, psm: int, settings: Settings) -> str:
    """Ejecuta tesseract sobre un array y devuelve el texto crudo."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        tmp_path = handle.name
    Image.fromarray(array).save(tmp_path)
    try:
        command = ["tesseract", tmp_path, "-", "--psm", str(psm),
                   "-c", f"tessedit_char_whitelist={settings.tesseract_whitelist}"]
        if settings.tesseract_lang:
            command += ["-l", settings.tesseract_lang]
        return subprocess.run(command, capture_output=True, text=True,
                              check=False).stdout
    finally:
        os.unlink(tmp_path)


def _parse_stamp(text: str, settings: Settings) -> Optional[str]:
    """Extrae 'AAAAMMDD_HHMMSS' del texto si contiene una fecha/hora válida."""
    match = re.search(settings.timestamp_regex, text)
    if not match:
        return None
    year, month, day, hour, minute, second = match.groups()
    if not _in_valid_range(match.groups(), settings):
        return None
    return f"{year}{month}{day}_{hour}{minute}{second}"


def _in_valid_range(parts: tuple, settings: Settings) -> bool:
    """Valida rangos de calendario para descartar lecturas absurdas."""
    year, month, day, hour, minute, second = (int(value) for value in parts)
    return (settings.year_min <= year <= settings.year_max
            and 1 <= month <= 12 and 1 <= day <= 31
            and hour <= 23 and minute <= 59 and second <= 59)


def _collect_votes(array: np.ndarray, thresholds: list, keep_bright: bool,
                   settings: Settings) -> Counter:
    """Barre umbrales y PSMs acumulando cada lectura válida como un voto."""
    votes: Counter = Counter()
    for threshold in thresholds:
        binary = _binarize(array, threshold, keep_bright)
        for psm in settings.tesseract_psms:
            stamp = _parse_stamp(_run_tesseract(binary, psm, settings), settings)
            if stamp:
                votes[stamp] += 1
    return votes


def _decide(path: str, votes: Counter, settings: Settings, dark: bool) -> OcrResult:
    """Convierte los votos en un resultado con su nivel de confianza."""
    winner, count = votes.most_common(1)[0]
    runner_up = votes.most_common(2)[1][1] if len(votes) > 1 else 0
    if dark:
        status = "dark"
    else:
        status = ("confident"
                  if count >= settings.confident_min_votes and count > runner_up
                  else "weak")
    return OcrResult(path, winner, status, dict(votes))


def extract_timestamp(path: Path, settings: Settings) -> OcrResult:
    """Lee la marca de fecha/hora de una imagen. No lanza en fotos ilegibles.

    Args:
        path: Ruta de la imagen.
        settings: Configuración de recorte y OCR.

    Returns:
        OcrResult con el sello detectado o status 'fail' si no se pudo leer.
    """
    array = _analysis_array(Image.open(path).convert("L"), settings)
    bright_votes = _collect_votes(array, settings.bright_thresholds, True, settings)
    if bright_votes:
        return _decide(str(path), bright_votes, settings, dark=False)
    dark_votes = _collect_votes(array, settings.dark_thresholds, False, settings)
    if dark_votes:
        return _decide(str(path), dark_votes, settings, dark=True)
    return OcrResult(str(path), None, "fail", {})
