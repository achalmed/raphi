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


MAS = "Más opciones"


@operacion("descargar", "Medios", "Descargar video o audio",
           "Pega el enlace de YouTube, Facebook, TikTok, Instagram, X, Vimeo u otro de más de mil sitios: Raphi muestra qué "
           "video es y baja el video o solo el audio, entero o un tramo; también de una transmisión que sigue en vivo.",
           entrada="ninguna", lote=False, minimo_entradas=0, extensiones=(), requiere=("yt-dlp", "ffmpeg"),
           parametros=(Parametro("url", "Enlace del video (o varios, uno por línea)", "multilinea", obligatorio=True,
                                 vista="enlace"),
                       Parametro("modo", "Qué bajar", "opcion", "video",
                                 opciones=(("video", "Video"), ("audio", "Solo el audio"))),
                       Parametro("calidad", "Calidad", "opcion", "1080",
                                 opciones=(("best", "La mejor que haya"), ("2160", "4K"), ("1440", "1440p"),
                                           ("1080", "1080p (Full HD)"), ("720", "720p"), ("480", "480p"), ("360", "360p")),
                                 ayuda="como mucho; en un video vertical cuenta el lado corto", si=("modo", "video")),
                       Parametro("formato_audio", "Formato del audio", "opcion", "mp3",
                                 opciones=(("mp3", "MP3"), ("m4a", "M4A"), ("opus", "Opus"), ("flac", "FLAC (sin pérdida)"),
                                           ("wav", "WAV")), si=("modo", "audio")),
                       Parametro("tramo", "Tramo", "texto", "", vista="tramo",
                                 ayuda="vacío: todo. 1:02:00-1:05:30 desde el comienzo; en vivo, @11:20-@11:22:35 por la "
                                       "hora o -16:30--14:08 hacia atrás desde el vivo"),
                       Parametro("subtitulos", "Bajar subtítulos (es, en)", "casilla", False, grupo=MAS),
                       Parametro("subtitulos_auto", "También los subtítulos automáticos", "casilla", False, grupo=MAS,
                                 si=("subtitulos", True)),
                       Parametro("lista", "Si el enlace es una lista", "opcion", "todo", grupo=MAS,
                                 opciones=(("todo", "Bajar la lista entera"), ("solo_video", "Solo este video"))),
                       Parametro("elementos", "Elementos de la lista (p. ej. 1:10 o 1,3,5)", "texto", "", grupo=MAS,
                                 ayuda="vacío: todos", si=("lista", "todo")),
                       Parametro("caratula", "Incrustar la carátula", "casilla", False, grupo=MAS),
                       Parametro("sponsorblock", "Quitar patrocinios y autopromoción (SponsorBlock)", "casilla", False,
                                 grupo=MAS),
                       Parametro("cookies", "Con la sesión de tu navegador (videos privados)", "opcion", "", grupo=MAS,
                                 opciones=NAVEGADORES, ayuda="usa las cookies del navegador elegido; nada sale de tu máquina")),
           palabras=("youtube", "facebook", "tiktok", "instagram", "bajar", "yt-dlp", "descargar audio", "recortar tramo",
                     "playlist", "lista", "video downloader", "privado", "en vivo", "transmisión", "directo"),
           accion="Descargar")
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
        leer_tramo(ctx.p("tramo"))          # un error claro antes de bajar nada
        orden += ["--clip", ctx.p("tramo").strip()]
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
    estado: dict = {"item": 1, "items": 1, "nombre": ""}

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
        elif partes := re.search(r"(\d+)/(\d+) segmentos", linea):      # el tramo de un directo, parte por parte
            n, m = int(partes[1]), max(1, int(partes[2]))
            estado["f"] = 0.05 + 0.7 * n / m
            ctx.avisar(estado["f"], f"Bajando el tramo: {n} de {m} partes")
        elif "lista renovada" in linea:
            ctx.avisar(estado.get("f", 0.05), "El sitio pidió una pausa; se sigue con una lista nueva…")
        elif "Recortando" in linea:
            ctx.avisar(0.8, "Recortando el tramo exacto (re-codifica el video)…")
        elif "Verificado con ffprobe" in linea:
            ctx.avisar(0.95, "Tramo verificado")
        elif "Directo: bajando" in linea:
            ctx.avisar(0.04, "Directo: buscando el tramo en la transmisión…")
    correr_en_vivo(orden + urls, leer, timeout=6 * HORAS, mensaje="La descarga falló")
    ctx.avisar(0.97, "Ordenando lo descargado")
    destino.mkdir(parents=True, exist_ok=True)
    return Resultado(_traer(ctx, temporal, destino))


_T = r"\d+(?::\d{1,2}){0,2}(?:\.\d+)?"
_EXTREMO = rf"(?:@{_T}|-?{_T})"
_RANGO = re.compile(rf"^\s*({_EXTREMO})\s*(?:\.\.|\s+a\s+|-)\s*({_EXTREMO})\s*$")


def leer_tramo(texto: str) -> dict:
    """«1:02:00-1:05:30», «-16:30--14:08» o «@11:20-@11:22:35» → {clase, inicio, fin} (segundos; en «reloj», del día).
    La misma gramática que `backends/video-downloader` (`clip_parse_range` y `lib/hls_tramo.py`)."""
    m = _RANGO.match(texto or "")
    if not m:
        raise ErrorOperacion(f"El tramo «{texto}» no se entiende. Ejemplos: 1:02:00-1:05:30 (desde el comienzo), "
                             "@11:20-@11:22:35 (por la hora, en vivo) o -16:30--14:08 (hacia atrás desde el vivo).")

    def extremo(t: str) -> tuple[str, float]:
        clase = "reloj" if t[0] == "@" else "vivo" if t[0] == "-" else "abs"
        cuerpo = t.lstrip("@-")
        if clase == "reloj" and cuerpo.count(":") == 1:
            cuerpo += ":00"
        total = 0.0
        for parte in cuerpo.split(":"):
            total = total * 60 + float(parte)
        return clase, total

    (ca, a), (cb, b) = extremo(m[1]), extremo(m[2])
    if ca != cb:
        raise ErrorOperacion("Los dos extremos del tramo deben ser de la misma clase (desde el comienzo, por la hora o "
                             "desde el vivo).")
    if ca == "vivo":
        a, b = -a, -b
    if ca == "reloj" and b <= a:
        b += 86400
    if b <= a:
        raise ErrorOperacion(f"En el tramo «{texto}», el final debe ir después del inicio.")
    return {"clase": ca, "inicio": a, "fin": b}


_LIMPIAR_TITULO = (re.compile(r"^[\d.,]+[KkMm]? (views|vistas|reproducciones)( · [\d.,]+[KkMm]? (reactions|reacciones))? *[|｜] *"),
                   re.compile(r" *(on Reels|[|｜] *Facebook)$"))
_CONSULTAS: dict[tuple[str, str], tuple[float, dict]] = {}


def _miniatura(url: str) -> str:
    """La miniatura como data: URI (la página no pide nada a otro sitio); "" si no se puede."""
    import base64
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            datos = r.read(600_000)
            tipo = r.headers.get_content_type() or "image/jpeg"
        if not tipo.startswith("image/") or len(datos) >= 600_000:
            return ""
        return f"data:{tipo};base64,{base64.b64encode(datos).decode()}"
    except Exception:  # noqa: BLE001 — sin miniatura no pasa nada
        return ""


def _ventana_en_vivo(url: str, cookies: str) -> dict:
    """De un directo HLS: desde qué hora y hasta qué hora se puede bajar (la ventana de rebobinado)."""
    import importlib.util
    import urllib.request
    ruta = BACKENDS / "video-downloader" / "lib" / "hls_tramo.py"
    spec = importlib.util.spec_from_file_location("hls_tramo", ruta)
    h = importlib.util.module_from_spec(spec)
    sys.modules["hls_tramo"] = h
    spec.loader.exec_module(h)
    extra = ["--cookies-from-browser", cookies] if cookies else []
    lista_url = h.url_de_la_lista(url, "b[protocol^=m3u8]", extra)
    lista = h.leer_lista(h.pedir(lista_url).decode("utf-8", "replace"), lista_url)
    primero, ultimo = lista.segmentos[0], lista.segmentos[-1]
    fin = ultimo.inicio + ultimo.duracion
    return {"segundos": round(fin, 1), "desde": primero.hora, "hasta": (primero.hora + fin) if primero.hora else None}


def consultar_enlace(url: str, cookies: str = "") -> dict:
    """Qué hay detrás de un enlace, sin bajarlo: título, canal, sitio, miniatura, duración, si es una lista, si está en
    vivo y, si lo está, la ventana que se puede bajar (con la hora de inicio y de fin). Lo usa la vista «enlace».
    Se guarda 30 s (un directo cambia)."""
    import json
    import time
    url = (url or "").strip()
    if not re.match(r"^https?://", url):
        raise ErrorOperacion("Eso no parece un enlace (debe empezar por http:// o https://).")
    clave = (url, cookies or "")
    guardada = _CONSULTAS.get(clave)
    if guardada and time.time() - guardada[0] < 30:
        return guardada[1]
    orden = ["yt-dlp", "-J", "--flat-playlist", "--no-warnings", "--no-playlist"]
    if cookies:
        orden += ["--cookies-from-browser", cookies]
    import subprocess
    try:
        r = subprocess.run(orden + ["--", url], capture_output=True, text=True, timeout=90)
    except FileNotFoundError as e:
        raise ErrorOperacion("Falta el programa «yt-dlp».") from e
    except subprocess.TimeoutExpired as e:
        raise ErrorOperacion("El sitio tardó más de 90 s en responder.") from e
    if r.returncode != 0 or not r.stdout.strip():
        ultimo = (r.stderr or "").strip().splitlines()[-1:] or ["sin respuesta"]
        texto = ultimo[0].removeprefix("ERROR: ")
        if "login" in texto.lower() or "cookies" in texto.lower() or "private" in texto.lower():
            texto += " — prueba con «Con la sesión de tu navegador» (Más opciones)."
        raise ErrorOperacion(f"No se pudo leer el enlace: {texto}")
    d = json.loads(r.stdout)
    titulo = d.get("title") or ""
    for patron in _LIMPIAR_TITULO:
        titulo = patron.sub("", titulo)
    if d.get("live_status") == "is_live":   # yt-dlp añade la hora de la consulta al título de un directo
        titulo = re.sub(r" \d{4}-\d{2}-\d{2} \d{2}:\d{2}$", "", titulo)
    info = {"url": url, "titulo": titulo.strip() or "(sin título)", "canal": d.get("uploader") or d.get("channel") or "",
            "sitio": d.get("extractor_key") or d.get("extractor") or "", "lista": d.get("_type") == "playlist",
            "elementos": len(d.get("entries") or []) if d.get("_type") == "playlist" else 0,
            "duracion": d.get("duration"), "en_vivo": d.get("live_status") == "is_live",
            "miniatura": "", "vertical": False, "calidades": [], "ventana": None, "zona": time.localtime().tm_gmtoff}
    videos = [f for f in d.get("formats") or [] if f.get("height") and f.get("width") and f.get("vcodec") != "none"]
    if videos:
        mayor = max(videos, key=lambda f: f["height"] * f["width"])
        info["vertical"] = mayor["height"] > mayor["width"]
        info["calidades"] = sorted({min(f["height"], f["width"]) for f in videos}, reverse=True)
    miniaturas = [t for t in d.get("thumbnails") or [] if t.get("url")]
    if d.get("thumbnail") or miniaturas:
        info["miniatura"] = _miniatura(d.get("thumbnail") or miniaturas[-1]["url"])
    if info["en_vivo"]:
        try:
            info["ventana"] = _ventana_en_vivo(url, cookies)
        except Exception:  # noqa: BLE001 — sin ventana, el tramo se pide a mano
            info["ventana"] = None
    _CONSULTAS[clave] = (time.time(), info)
    return info


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
