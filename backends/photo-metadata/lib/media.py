"""Capa de medios: unifica fotos y videos sobre el mismo pipeline de OCR.

Para una foto se lee directamente; para un video se extrae un fotograma y se le
aplica el mismo OCR. Así la lógica de reconocimiento vive en un solo sitio.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from config import Settings
from lib import video
from lib.ocr import OcrResult, extract_timestamp


def is_video(path: Path, settings: Settings) -> bool:
    """Indica si la ruta corresponde a un video según la configuración."""
    return path.suffix.lower() in settings.video_extensions


def _read_video(path: Path, settings: Settings) -> OcrResult:
    """Lee la marca del video probando varios fotogramas hasta lograr una lectura."""
    last = OcrResult(str(path), None, "fail", {})
    for frame_time in settings.ffmpeg_frame_times:
        try:
            frame = video.extract_frame(path, settings, frame_time)
        except OSError as exc:
            last = OcrResult(str(path), None, "error", {"error": str(exc)})
            continue
        try:
            result = extract_timestamp(frame, settings)
        finally:
            frame.unlink(missing_ok=True)
        # El fotograma en t=0 da la hora de inicio; en cuanto uno sea legible
        # lo tomamos y dejamos de probar los siguientes.
        if result.stamp:
            return OcrResult(str(path), result.stamp, result.status, result.votes)
        last = OcrResult(str(path), None, result.status, result.votes)
    return last


def read_timestamp(path: Path, settings: Settings) -> OcrResult:
    """Lee la marca de fecha/hora de una foto o un video."""
    if is_video(path, settings):
        return _read_video(path, settings)
    return extract_timestamp(path, settings)


def load_image(path: Path, settings: Settings) -> Image.Image:
    """Devuelve una imagen RGB para montajes: la foto, o un fotograma del video."""
    if not is_video(path, settings):
        return Image.open(path).convert("RGB")
    frame = video.extract_frame(path, settings, settings.ffmpeg_frame_times[0])
    try:
        with Image.open(frame) as handle:
            return handle.convert("RGB")  # convert() carga los píxeles en memoria
    finally:
        frame.unlink(missing_ok=True)
