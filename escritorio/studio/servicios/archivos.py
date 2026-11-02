"""escritorio/studio/servicios/archivos.py — los archivos de entrada y las salidas: su tipo por la extensión, su
tamaño legible, si la ventana puede mostrarlos (imagen o texto) y la lectura acotada de un texto. Sin Qt."""
from __future__ import annotations

from pathlib import Path

IMAGENES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"}
TEXTOS = {".txt", ".md", ".srt", ".vtt", ".csv", ".json", ".html", ".htm", ".tsv", ".yml", ".yaml", ".tex", ".log"}
TOPE_TEXTO = 200_000
TIPOS = {".pdf": "PDF", ".docx": "Word", ".doc": "Word", ".odt": "Texto ODF", ".xlsx": "Excel", ".xls": "Excel", ".ods": "Hoja ODF",
         ".pptx": "PowerPoint", ".ppt": "PowerPoint", ".odp": "Presentación ODF", ".md": "Markdown", ".txt": "Texto", ".csv": "CSV",
         ".srt": "Subtítulos SRT", ".vtt": "Subtítulos VTT", ".zip": "ZIP", ".7z": "7Z", ".gz": "GZip", ".tar": "TAR"}


def tamano_legible(n: int | None) -> str:
    if n is None:
        return "—"
    for unidad in ("B", "KB", "MB", "GB"):
        if n < 1024 or unidad == "GB":
            return f"{n:.0f} {unidad}" if unidad == "B" else f"{n:.1f} {unidad}".replace(".0 ", " ")
        n /= 1024
    return str(n)


def tipo_de(ruta: Path | str) -> str:
    p = Path(ruta)
    if p.is_dir():
        return "Carpeta"
    ext = p.suffix.lower()
    if ext in TIPOS:
        return TIPOS[ext]
    if ext in IMAGENES or ext in (".heic", ".heif", ".avif", ".tif", ".tiff"):
        return "Imagen " + ext.lstrip(".").upper()
    if ext in (".mp3", ".m4a", ".aac", ".flac", ".opus", ".ogg", ".wav"):
        return "Audio " + ext.lstrip(".").upper()
    if ext in (".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"):
        return "Video " + ext.lstrip(".").upper()
    return ext.lstrip(".").upper() or "Archivo"


def fila_de(ruta: Path | str) -> dict:
    p = Path(ruta)
    try:
        tamano = sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) if p.is_dir() else p.stat().st_size
        existe = True
    except OSError:
        tamano, existe = None, False
    return {"nombre": p.name, "tipo": tipo_de(p), "tamano": tamano_legible(tamano), "carpeta": str(p.parent), "ruta": str(p),
            "existe": existe, "crudo": {"tamano": tamano or 0}, "nivel": "" if existe else "negativo",
            "icono": {"nombre": "folder" if p.is_dir() else ("application-pdf" if p.suffix.lower() == ".pdf" else "text-x-generic")}, "habilitado": True}


def vista_previa(ruta: Path | str) -> str:
    """«imagen», «texto» o «» según lo que la ventana puede mostrar de esa salida."""
    p = Path(ruta)
    if p.is_dir():
        return ""
    ext = p.suffix.lower()
    if ext in IMAGENES:
        return "imagen"
    if ext in TEXTOS:
        return "texto"
    return ""


def leer_texto(ruta: Path | str, tope: int = TOPE_TEXTO) -> str:
    try:
        datos = Path(ruta).read_bytes()
    except OSError as e:
        return f"No se pudo leer: {e}"
    texto = datos[:tope].decode("utf-8", errors="replace")
    return texto + (f"\n\n… ({tamano_legible(len(datos))} en total; se muestran los primeros {tamano_legible(tope)})" if len(datos) > tope else "")
