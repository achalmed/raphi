"""Escaneo paralelo de una carpeta de fotos y videos con reporte de progreso."""
from __future__ import annotations

import os
from multiprocessing import Pool
from pathlib import Path
from typing import Callable, Optional

from config import Settings
from lib.media import read_timestamp
from lib.ocr import OcrResult


def selected_extensions(settings: Settings) -> set[str]:
    """Extensiones a procesar según el filtro media_filter (all/images/videos)."""
    images = set(settings.image_extensions)
    videos = set(settings.video_extensions)
    if settings.media_filter == "images":
        return images
    if settings.media_filter == "videos":
        return videos
    return images | videos


def find_media(folder: Path, settings: Settings) -> list[Path]:
    """Lista los medios de la carpeta según el filtro (orden determinista)."""
    extensions = selected_extensions(settings)
    media = [entry for entry in folder.iterdir()
             if entry.is_file() and entry.suffix.lower() in extensions]
    media.sort()
    return media[:settings.limit] if settings.limit else media


def has_videos(folder: Path, settings: Settings) -> bool:
    """Indica si se procesará al menos un video (para exigir ffmpeg)."""
    if settings.media_filter == "images":
        return False
    video_extensions = set(settings.video_extensions)
    return any(entry.is_file() and entry.suffix.lower() in video_extensions
               for entry in folder.iterdir())


def _worker(task: tuple) -> OcrResult:
    """Procesa un archivo aislando fallos para no abortar todo el lote."""
    path, settings = task
    try:
        return read_timestamp(path, settings)
    except (OSError, ValueError) as exc:
        # Un archivo corrupto o ilegible no debe detener el escaneo completo.
        return OcrResult(str(path), None, "error", {"error": str(exc)})


def scan_folder(folder: Path, settings: Settings,
                on_progress: Optional[Callable[[int, int], None]] = None
                ) -> list[OcrResult]:
    """Escanea fotos y videos en paralelo y devuelve un resultado por archivo.

    Args:
        folder: Carpeta a escanear.
        settings: Configuración de ejecución.
        on_progress: Callback opcional (procesadas, total) para mostrar avance.

    Returns:
        Lista de OcrResult, una por archivo (foto o video) encontrado.
    """
    # Un solo hilo por proceso de tesseract evita saturar los núcleos
    # (cada worker ya usa un núcleo); sin esto el lote se vuelve ~10x lento.
    os.environ["OMP_THREAD_LIMIT"] = settings.omp_thread_limit
    media = find_media(folder, settings)
    total = len(media)
    workers = settings.workers or os.cpu_count() or 1
    results: list[OcrResult] = []
    with Pool(workers) as pool:
        tasks = ((path, settings) for path in media)
        for done, result in enumerate(
                pool.imap_unordered(_worker, tasks, chunksize=2), start=1):
            results.append(result)
            if on_progress and (done % settings.progress_every == 0 or done == total):
                on_progress(done, total)
    return results
