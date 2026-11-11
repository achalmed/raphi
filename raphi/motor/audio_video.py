"""Audio y video que no son conversión: descargar de la red, transcribir con Whisper y acortar subtítulos.

Las tres operaciones envuelven los backends que llegaron del repo de utilidades de Linux el 2026-10-31 (`backends/video-downloader`,
`backends/whisper-transcriber`), que siguen siendo CLI completas. Cada backend escribe en una carpeta temporal y
de ahí cada archivo pasa a su destino con `ctx.salida`, así que nada se pisa (principio 2 de `base.py`).
"""
from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

from raphi.motor.base import ErrorOperacion, Parametro, Resultado, operacion
from raphi.motor.medios import AUD, VID
from raphi.motor.utiles import correr, correr_en_vivo

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


NAVEGADORES = (("", "Ninguno (vídeos públicos)"), ("firefox", "Firefox"), ("chrome", "Chrome"), ("chromium", "Chromium"),
               ("brave", "Brave"), ("edge", "Edge"), ("opera", "Opera"), ("vivaldi", "Vivaldi"))


@operacion("descargar", "Medios", "Descargar video o audio",
           "De YouTube, Facebook, Instagram, TikTok, X, Vimeo y más de mil sitios (yt-dlp): vídeo a la calidad que se "
           "elija, solo el audio, un tramo exacto, listas enteras o algunos de sus elementos, subtítulos (también los "
           "automáticos), carátula y capítulos, sin los patrocinios; y lo privado o con sesión, con las cookies de tu navegador.",
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
                       Parametro("subtitulos", "Bajar subtítulos (es, en)", "casilla", False),
                       Parametro("subtitulos_auto", "También los subtítulos automáticos", "casilla", False),
                       Parametro("lista", "Si el enlace es una lista", "opcion", "todo",
                                 opciones=(("todo", "Bajar la lista entera"), ("solo_video", "Solo este vídeo"))),
                       Parametro("elementos", "Elementos de la lista (p. ej. 1:10 o 1,3,5)", "texto", "",
                                 ayuda="vacío: todos"),
                       Parametro("caratula", "Incrustar la carátula", "casilla", False),
                       Parametro("sponsorblock", "Quitar patrocinios y autopromoción (SponsorBlock)", "casilla", False),
                       Parametro("cookies", "Con la sesión de tu navegador (vídeos privados)", "opcion", "",
                                 opciones=NAVEGADORES, ayuda="usa las cookies del navegador elegido; nada sale de tu máquina")),
           palabras=("youtube", "facebook", "tiktok", "instagram", "bajar", "yt-dlp", "descargar audio", "recortar tramo",
                     "playlist", "lista", "video downloader", "privado"))
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
    if ctx.p("subtitulos") or ctx.p("subtitulos_auto"):
        orden += ["--subs"] + (["--auto-subs"] if ctx.p("subtitulos_auto") else [])
    if ctx.p("lista") == "solo_video":
        orden += ["--no-playlist"]
    if ctx.p("elementos"):
        orden += ["--items", ctx.p("elementos")]
    if ctx.p("caratula"):
        orden += ["--thumbnail"]
    if ctx.p("sponsorblock"):
        orden += ["--sponsorblock"]
    if ctx.p("cookies"):
        orden += ["--cookies-browser", ctx.p("cookies")]
    ctx.avisar(0.01, f"Preparando {len(urls)} enlace(s)…")
    estado = {"item": 1, "items": 1, "nombre": ""}

    def leer(linea: str) -> None:
        item = re.search(r"Downloading (?:item|video) (\d+) of (\d+)", linea)
        if item:
            estado["item"], estado["items"] = int(item[1]), int(item[2])
        destino_linea = re.search(r"Destination:\s*(.+)$", linea)
        if destino_linea:
            estado["nombre"] = Path(destino_linea[1]).name
        avance = re.search(r"\[download\]\s+([\d.]+)%", linea)
        if avance:
            parte = float(avance[1]) / 100
            total = (estado["item"] - 1 + parte) / max(1, estado["items"])
            velocidad = re.search(r"at\s+(\S+)", linea)
            eta = re.search(r"ETA\s+(\S+)", linea)
            ctx.avisar(0.02 + 0.9 * total, " · ".join(x for x in (
                f"{avance[1]} %", estado["nombre"][:50],
                f"{estado['item']} de {estado['items']}" if estado["items"] > 1 else "",
                velocidad[1] if velocidad else "", f"quedan {eta[1]}" if eta else "") if x))
        elif "Merging" in linea or "ExtractAudio" in linea or "[ffmpeg]" in linea:
            ctx.avisar(0.93, "Uniendo y convirtiendo…")
    correr_en_vivo(orden + urls, leer, timeout=6 * HORAS, mensaje="La descarga falló")
    ctx.avisar(0.97, "Ordenando lo descargado")
    destino.mkdir(parents=True, exist_ok=True)
    return Resultado(_traer(ctx, temporal, destino))


def opciones_para_enlaces(urls: list[str]) -> list[dict]:
    """Lo que la rueda ofrece para enlaces (soltados desde el navegador o pegados): la calidad en el anillo interior
    (Mejor, 4K, 1080p… MP3, M4A…) y en el exterior las maneras (con subtítulos, sin patrocinios, solo este vídeo de la
    lista, un tramo, con la sesión del navegador, todas las opciones). `enlace` dice qué parámetro recibe los enlaces;
    `pide`, si se abren las opciones antes; `fijos`, qué parámetros no se preguntan."""
    from raphi.motor.base import REGISTRO
    if "descargar" not in REGISTRO or REGISTRO["descargar"].faltan() or not urls:
        return []
    titulo = REGISTRO["descargar"].titulo
    calidades = (("Mejor", "best", "La mejor calidad que haya"), ("4K", "2160", "Hasta 4K (2160p)"), ("1080p", "1080", "Hasta 1080p"),
                 ("720p", "720", "Hasta 720p (más liviano)"), ("480p", "480", "Hasta 480p (para el móvil)"))
    salida = [{"a": "mp4", "etiqueta": e, "titulo": f"Vídeo · {t}", "params": {"modo": "video", "calidad": c}} for e, c, t in calidades]
    salida += [{"a": f, "etiqueta": f.upper(), "titulo": f"Solo el audio en {f.upper()}", "params": {"modo": "audio", "formato_audio": f}}
               for f in ("mp3", "m4a", "opus", "flac")]
    maneras = (("Con subtítulos", "media-subtitle", "Vídeo 1080p con subtítulos (también los automáticos)",
                {"modo": "video", "calidad": "1080", "subtitulos": True, "subtitulos_auto": True}, False),
               ("Sin patrocinios", "edit-cut", "Vídeo 1080p sin patrocinios ni autopromoción (SponsorBlock)",
                {"modo": "video", "calidad": "1080", "sponsorblock": True}, False),
               ("Solo este vídeo", "video-x-generic", "Solo este vídeo, aunque el enlace sea de una lista",
                {"modo": "video", "calidad": "1080", "lista": "solo_video"}, False),
               ("Un tramo…", "edit-cut", "Un tramo exacto (desde, hasta)", {"modo": "video", "calidad": "1080"}, True),
               ("Con tu sesión…", "dialog-password", "Privado o con sesión: con las cookies de tu navegador",
                {"modo": "video", "calidad": "1080", "cookies": "firefox"}, True),
               ("Todas las opciones…", "configure", f"{titulo}: todas las opciones", {}, True))
    for i, (etiqueta, icono, texto, params, pide) in enumerate(maneras):
        salida.append({"a": None, "etiqueta": etiqueta, "icono": icono, "titulo": texto, "params": params, "pide": pide,
                       "fijos": [] if pide else list(params), "clave": f"descargar|manera-{i}"})
    for o in salida:
        o.update({"operacion": "descargar", "enlace": "url", "junta": len(urls) > 1})
        o.setdefault("pide", False)
    return salida


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
