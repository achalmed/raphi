"""escritorio/studio/servicios/vista_previa.py — qué puede mostrar el espacio de trabajo de un archivo (de entrada o de
salida) y cómo se describe (sin Qt, se prueba solo; reingeniería X4).

Imagen y texto se muestran tal cual; audio y vídeo, con QtMultimedia de QML; un PDF, con el visor de `gui-comun` 3.2
(`gui_comun.visor_pdf`: QtPdf o `pdftoppm` a la caché del studio; hasta el 2026-11-03 las páginas las renderizaba este
módulo).
"""
from __future__ import annotations

from pathlib import Path

from escritorio.studio.servicios import archivos as svc_archivos

AUDIO = {".mp3", ".m4a", ".aac", ".flac", ".opus", ".ogg", ".wav"}
VIDEO = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}


def tipo(ruta: str | Path) -> str:
    """imagen · pdf · audio · video · texto · carpeta · «» (nada que mostrar)."""
    p = Path(ruta)
    if p.is_dir():
        return "carpeta"
    ext = p.suffix.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in AUDIO:
        return "audio"
    if ext in VIDEO:
        return "video"
    return svc_archivos.vista_previa(p)


def describir(ruta: str | Path) -> str:
    """«PDF · 12 KB», «Audio WAV · 16 KB»: lo que la vista previa dice del archivo."""
    p = Path(ruta)
    f = svc_archivos.fila_de(p)
    return f"{f['tipo']} · {f['tamano']}" if f["existe"] else "no existe"
