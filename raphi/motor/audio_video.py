"""Audio y video que no son conversión: descargar de la red, transcribir con Whisper y acortar subtítulos.

Las tres operaciones envuelven los backends que llegaron de scripts-linux el 2026-10-31 (`backends/video-downloader`,
`backends/whisper-transcriber`), que siguen siendo CLI completas. Cada backend escribe en una carpeta temporal y
de ahí cada archivo pasa a su destino con `ctx.salida`, así que nada se pisa (principio 2 de `base.py`).
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from raphi.motor.base import ErrorOperacion, Parametro, Resultado, operacion
from raphi.motor.medios import AUD, VID
from raphi.motor.utiles import correr

BACKENDS = Path(__file__).resolve().parents[2] / "backends"
DESCARGADOR = BACKENDS / "video-downloader" / "main.sh"
TRANSCRIPTOR = BACKENDS / "whisper-transcriber" / "main.py"
HORAS = 3600


def carpeta_de_descargas() -> Path:
    """La carpeta de descargas del usuario (la de XDG si está; si no, ~/Descargas o ~/Downloads)."""
    xdg = os.environ.get("XDG_DOWNLOAD_DIR")
    if xdg:
        return Path(xdg).expanduser()
    for nombre in ("Descargas", "Downloads"):
        if (Path.home() / nombre).is_dir():
            return Path.home() / nombre
    return Path.home()


def _traer(ctx, temporal: Path, destino: Path | None, nombre=lambda p: p.stem) -> list[Path]:
    """Mueve lo que dejó un backend en `temporal` a su lugar final, sin pisar nada."""
    salidas = []
    for archivo in sorted(p for p in temporal.rglob("*") if p.is_file()):
        base = (destino / archivo.name) if destino else None
        final = ctx.salida(nombre=nombre(archivo), extension=archivo.suffix, base=base)
        shutil.move(str(archivo), final)
        salidas.append(final)
    if not salidas:
        raise ErrorOperacion("El programa terminó sin dejar ningún archivo.")
    return salidas


@operacion("descargar", "Medios", "Descargar video o audio",
           "De YouTube, Facebook, TikTok y más (yt-dlp): video, solo audio o un tramo exacto.",
           entrada="ninguna", lote=False, minimo_entradas=0, extensiones=(), requiere=("yt-dlp", "ffmpeg"),
           parametros=(Parametro("url", "Enlaces (uno por línea)", "multilinea", obligatorio=True),
                       Parametro("modo", "Qué bajar", "opcion", "video",
                                 opciones=(("video", "Video"), ("audio", "Solo audio"))),
                       Parametro("calidad", "Altura máxima", "opcion", "1080",
                                 opciones=("2160", "1440", "1080", "720", "480", "360", "best")),
                       Parametro("formato_audio", "Formato del audio", "opcion", "mp3",
                                 opciones=("mp3", "m4a", "opus", "flac", "wav")),
                       Parametro("tramo", "Tramo (INI-FIN, p. ej. 1:02:00-1:05:30)", "texto", "",
                                 ayuda="vacío: todo el video"),
                       Parametro("subtitulos", "Bajar subtítulos (es, en)", "casilla", False)),
           palabras=("youtube", "facebook", "tiktok", "bajar", "yt-dlp", "descargar audio", "recortar tramo"))
def descargar(ctx):
    urls = [u.strip() for u in (ctx.p("url") or "").splitlines() if u.strip()]
    if not urls:
        raise ErrorOperacion("Falta al menos un enlace.")
    destino = ctx.destino or carpeta_de_descargas()
    if ctx.simular:
        return Resultado(plan=[f"{u} → {destino}" for u in urls])
    temporal = ctx.carpeta_temporal()
    orden = ["bash", str(DESCARGADOR), "--no-confirm", "-o", str(temporal), "-m", ctx.p("modo"),
             "-q", ctx.p("calidad")]
    if ctx.p("modo") == "audio":
        orden += ["--audio-format", ctx.p("formato_audio")]
    if ctx.p("tramo"):
        orden += ["--clip", ctx.p("tramo")]
    if ctx.p("subtitulos"):
        orden += ["--subs"]
    ctx.avisar(0.05, f"Descargando {len(urls)} enlace(s)…")
    correr(orden + urls, timeout=6 * HORAS, mensaje="La descarga falló")
    ctx.avisar(0.95, "Ordenando lo descargado")
    destino.mkdir(parents=True, exist_ok=True)
    return Resultado(_traer(ctx, temporal, destino))


@operacion("transcribir", "Medios", "Transcribir con Whisper",
           "Audio o video a texto y subtítulos, en esta máquina (Whisper); también traduce al inglés.",
           entrada="medios", extensiones=AUD + VID, sufijo="transcripcion", requiere=("whisper", "ffmpeg"),
           parametros=(Parametro("idioma", "Idioma del audio (código)", "texto", "es"),
                       Parametro("modelo", "Modelo", "opcion", "small",
                                 opciones=("tiny", "base", "small", "medium", "large", "turbo"),
                                 ayuda="más grande: más exacto y más lento"),
                       Parametro("tarea", "Tarea", "opcion", "transcribe",
                                 opciones=(("transcribe", "Transcribir"), ("translate", "Traducir al inglés"))),
                       Parametro("formato", "Salida", "opcion", "srt",
                                 opciones=(("txt", "Texto"), ("srt", "Subtítulos SRT"), ("vtt", "Subtítulos VTT"),
                                           ("all", "Todos (txt, srt, vtt, tsv, json)"))),
                       Parametro("cortos", "Subtítulos de líneas cortas", "casilla", True)),
           palabras=("whisper", "transcripción", "subtítulos", "texto", "dictado", "entrevista", "traducir"))
def transcribir(ctx):
    if ctx.simular:
        return Resultado(plan=[f"{ctx.entrada.name} → {ctx.entrada.stem}.{ctx.p('formato')} "
                               f"(Whisper {ctx.p('modelo')}, {ctx.p('idioma')})"])
    temporal = ctx.carpeta_temporal()
    orden = [sys.executable, str(TRANSCRIPTOR), str(ctx.entrada), "-o", str(temporal), "-m", ctx.p("modelo"),
             "-l", ctx.p("idioma"), "-t", ctx.p("tarea"), "-f", ctx.p("formato")]
    if ctx.p("cortos") and ctx.p("formato") in ("srt", "all"):
        orden.append("--shorten-srt")
    ctx.avisar(0.05, f"Transcribiendo {ctx.entrada.name} (puede tardar)")
    correr(orden, timeout=12 * HORAS, mensaje="Whisper falló")
    return Resultado(_traer(ctx, temporal, ctx.destino, nombre=lambda p: p.stem))


@operacion("ajustar_subtitulos", "Medios", "Acortar líneas de subtítulos",
           "Reparte el texto de un SRT en líneas de un largo máximo, por palabras y sin perder texto.",
           entrada="archivos", extensiones=(".srt",), sufijo="cortos", requiere=("py:pysrt",),
           parametros=(Parametro("largo", "Caracteres por línea", "entero", 42, minimo=10, maximo=120),),
           palabras=("srt", "subtítulos", "líneas", "acortar"))
def ajustar_subtitulos(ctx):
    if ctx.simular:
        return Resultado(plan=[f"{ctx.entrada.name}: líneas de {ctx.p('largo')} caracteres como mucho"])
    # el backend deja «<nombre>_acortado.srt» junto al .srt que recibe (no usa -o): se le da una copia en un temporal
    copia = ctx.carpeta_temporal() / ctx.entrada.name
    shutil.copy2(ctx.entrada, copia)
    correr([sys.executable, str(TRANSCRIPTOR), str(copia), "--max-line-length", str(ctx.p("largo"))],
           mensaje="No se pudieron acortar los subtítulos")
    acortado = copia.with_name(f"{copia.stem}_acortado.srt")
    if not acortado.is_file():
        raise ErrorOperacion("El programa terminó sin dejar el .srt acortado.")
    final = ctx.salida(extension=".srt")
    shutil.move(str(acortado), final)
    return Resultado([final])
