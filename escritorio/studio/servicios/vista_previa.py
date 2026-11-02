"""escritorio/studio/servicios/vista_previa.py — qué puede mostrar el espacio de trabajo de un archivo (de entrada o de
salida) y las páginas de un PDF como imágenes (sin Qt, se prueba solo; reingeniería X4).

Imagen y texto se muestran tal cual; audio y vídeo, con QtMultimedia de QML; un PDF, página a página con `pdftoppm`
(poppler) a una caché acotada en la del studio (`paginas/<clave>/`, la clave lleva la fecha del PDF), por demanda.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from escritorio.studio.servicios import archivos as svc_archivos

AUDIO = {".mp3", ".m4a", ".aac", ".flac", ".opus", ".ogg", ".wav"}
VIDEO = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
LIMITE_CACHE = 150 * 1024 * 1024
_TAMANO = re.compile(r"^Page\s+(\d+)\s+size:\s+([\d.]+)\s+x\s+([\d.]+)", re.M)
_PAGINAS = re.compile(r"^Pages:\s+(\d+)", re.M)


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


def clave(pdf: Path) -> str:
    try:
        st = pdf.stat()
        firma = f"{pdf.resolve()}|{st.st_mtime_ns}|{st.st_size}"
    except OSError:
        firma = str(pdf)
    return hashlib.sha1(firma.encode("utf-8")).hexdigest()[:16]


def paginas_pdf(pdf: Path, tope: int = 200) -> list[tuple[float, float]]:
    """El tamaño en puntos de cada página (hasta `tope`) según `pdfinfo`; [] sin PDF o sin poppler."""
    if not Path(pdf).is_file() or not shutil.which("pdfinfo"):
        return []
    try:
        r = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, timeout=20)
        m = _PAGINAS.search(r.stdout)
        total = min(int(m.group(1)), tope) if m else 0
        if total <= 0:
            return []
        r = subprocess.run(["pdfinfo", "-f", "1", "-l", str(total), str(pdf)], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError, ValueError):
        return []
    tamanos = {int(n): (float(a), float(b)) for n, a, b in _TAMANO.findall(r.stdout)}
    defecto = next(iter(tamanos.values()), (595.0, 842.0))
    return [tamanos.get(i, defecto) for i in range(1, total + 1)]


def renderizar(pdf: Path, pagina: int, ppp: int, cache: Path) -> Path | None:
    """La página (1-based) a `ppp` como PNG en `cache/paginas/<clave>/`; si ya está, la misma ruta."""
    carpeta = Path(cache) / "paginas" / clave(Path(pdf))
    destino = carpeta / f"p{pagina}-{ppp}.png"
    if destino.is_file():
        return destino
    if not shutil.which("pdftoppm") or not Path(pdf).is_file():
        return None
    carpeta.mkdir(parents=True, exist_ok=True)
    base = carpeta / f".p{pagina}-{ppp}-{os.getpid()}-{time.monotonic_ns()}"
    try:
        r = subprocess.run(["pdftoppm", "-f", str(pagina), "-l", str(pagina), "-r", str(ppp), "-png", "-singlefile", str(pdf), str(base)],
                           capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    hecho = Path(str(base) + ".png")
    if r.returncode != 0 or not hecho.is_file():
        return None
    os.replace(hecho, destino)
    return destino


def podar(cache: Path, limite: int = LIMITE_CACHE, conservar: str = "") -> int:
    """Borra las carpetas de páginas más antiguas hasta quedar bajo `limite` (nunca la de `conservar`)."""
    raiz = Path(cache) / "paginas"
    if not raiz.is_dir():
        return 0
    carpetas = []
    for d in raiz.iterdir():
        if d.is_dir():
            archivos = [f for f in d.iterdir() if f.is_file()]
            carpetas.append((max((f.stat().st_mtime for f in archivos), default=0.0), sum(f.stat().st_size for f in archivos), d))
    total = sum(b for _u, b, _d in carpetas)
    liberado = 0
    for _u, b, d in sorted(carpetas):
        if total <= limite:
            break
        if d.name != conservar:
            shutil.rmtree(d, ignore_errors=True)
            total -= b
            liberado += b
    return liberado


def describir(ruta: str | Path) -> str:
    """«PDF · 12 KB», «Audio WAV · 16 KB»: lo que la vista previa dice del archivo."""
    p = Path(ruta)
    f = svc_archivos.fila_de(p)
    return f"{f['tipo']} · {f['tamano']}" if f["existe"] else "no existe"
