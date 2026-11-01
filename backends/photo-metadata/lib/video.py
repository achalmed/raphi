"""Extracción de un fotograma de video con ffmpeg, para leerle la marca.

El fotograma se guarda en un archivo temporal que el llamador debe borrar.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from config import Settings


def extract_frame(video_path: Path, settings: Settings,
                  frame_time: str = "0") -> Path:
    """Extrae un fotograma del video en el segundo `frame_time`.

    Args:
        video_path: Ruta del video.
        settings: Configuración (binario de ffmpeg).
        frame_time: Posición en segundos desde el inicio.

    Returns:
        Ruta del PNG temporal generado (el llamador es responsable de borrarlo).

    Raises:
        OSError: Si ffmpeg falla o el fotograma sale vacío.
    """
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        frame_path = Path(handle.name)
    # -ss antes de -i hace un seek rápido; -frames:v 1 toma un solo fotograma.
    command = [settings.ffmpeg_binary, "-y", "-ss", frame_time,
               "-i", str(video_path), "-frames:v", "1", str(frame_path)]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0 or frame_path.stat().st_size == 0:
        frame_path.unlink(missing_ok=True)
        raise OSError(
            f"ffmpeg no pudo extraer un fotograma de '{video_path.name}' "
            f"en t={frame_time}s.")
    return frame_path
