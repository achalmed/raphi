"""Medios y archivos (R5, al estilo Tangerine): convertir cualquier archivo a lo que se pueda, y sus herramientas.

- imágenes (JPG, PNG, WebP, HEIC, AVIF, TIFF, BMP, GIF; SVG de entrada): convertir, redimensionar, recortar, comprimir;
- audio (MP3, M4A, FLAC, Opus, OGG, WAV) y video (MP4, MOV, MKV, WebM, GIF): convertir, recortar, comprimir, extraer
  el audio, video a GIF; con ffmpeg;
- subtítulos (SRT ↔ VTT);
- archivos comprimidos (ZIP, TAR, TAR.GZ, 7Z; RAR solo de entrada): comprimir y extraer, con 7-Zip o bsdtar;
- quitar metadatos de cualquier archivo (exiftool; los PDF, por «quitar_metadatos»).

`formatos_de(ruta)` es el menú de Tangerine: a qué se puede convertir ese archivo y con qué operación.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from raphi.motor.base import ErrorOperacion, Parametro, Resultado, disponible, operacion
from raphi.motor.utiles import correr

IMG = (".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".avif", ".tif", ".tiff", ".bmp", ".gif", ".svg")
IMG_DESTINO = ("jpg", "png", "webp", "avif", "heic", "tiff", "bmp", "gif", "pdf")
AUD = (".mp3", ".m4a", ".aac", ".flac", ".opus", ".ogg", ".wav")
AUD_DESTINO = ("mp3", "m4a", "flac", "opus", "ogg", "wav")
VID = (".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v", ".gif")
VID_DESTINO = ("mp4", "mov", "mkv", "webm", "gif", "mp3", "m4a")
SUB = (".srt", ".vtt")
ARC = (".zip", ".tar", ".gz", ".tgz", ".7z", ".rar", ".xz", ".bz2")


def _pil():
    from PIL import Image
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass
    return Image


def _abrir_imagen(ruta: Path, ctx=None):
    """Una imagen como objeto de Pillow, girada según su EXIF; SVG, rasterizado antes con ImageMagick."""
    Image = _pil()
    from PIL import ImageOps
    if ruta.suffix.lower() == ".svg":
        if not disponible("magick"):
            raise ErrorOperacion("Para leer SVG hace falta ImageMagick.")
        png = ctx.temporal(".png") if ctx else ruta.with_suffix(".tmp.png")
        correr(["magick", "-density", "192", "-background", "none", str(ruta), str(png)])
        ruta = png
    try:
        with Image.open(ruta) as img:
            img.load()
            return ImageOps.exif_transpose(img)
    except OSError as e:
        raise ErrorOperacion(f"{ruta.name}: no se puede leer como imagen.") from e


def _guardar_imagen(img, destino: Path, formato: str, calidad: int, conservar_metadatos: bool = False, origen=None):
    formato = formato.lower()
    if formato in ("jpg", "jpeg", "bmp", "pdf") and img.mode in ("RGBA", "LA", "P"):
        fondo = _pil().new("RGB", img.size, "white")
        fondo.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[-1])
        img = fondo
    elif img.mode not in ("RGB", "RGBA", "L"):
        img = img.convert("RGBA" if "A" in img.mode else "RGB")
    nombre = {"jpg": "JPEG", "jpeg": "JPEG", "tiff": "TIFF", "heic": "HEIF", "avif": "AVIF"}.get(formato, formato.upper())
    opciones: dict = {}
    if nombre in ("JPEG", "WEBP", "AVIF", "HEIF"):
        opciones["quality"] = calidad
    if nombre == "JPEG":
        opciones.update(optimize=True, progressive=True)
    if nombre == "PNG":
        opciones["optimize"] = True
    if conservar_metadatos and origen is not None and "exif" in getattr(origen, "info", {}):
        opciones["exif"] = origen.info["exif"]
    try:
        img.save(destino, nombre, **opciones)
    except (OSError, KeyError, ValueError) as e:
        raise ErrorOperacion(f"No se pudo escribir {formato.upper()}: {e}") from e
    return destino


# --- imágenes -------------------------------------------------------------------------------------------------


@operacion("convertir_imagen", "Medios", "Convertir imagen", "JPG, PNG, WebP, AVIF, HEIC, TIFF, BMP, GIF o PDF; también desde SVG.",
           entrada="medios", extensiones=IMG, sufijo="convertida", requiere=("py:PIL",),
           parametros=(Parametro("formato", "A", "opcion", "jpg", opciones=IMG_DESTINO),
                       Parametro("calidad", "Calidad", "entero", 85, minimo=10, maximo=100),
                       Parametro("metadatos", "Conservar EXIF", "casilla", False)),
           palabras=("heic a jpg", "png a jpg", "webp", "avif", "foto", "imagen"))
def convertir_imagen(ctx):
    formato = ctx.p("formato")
    destino = ctx.salida(nombre=ctx.entrada.stem, extension=f".{formato}")
    if ctx.simular:
        return Resultado(plan=[f"{ctx.entrada.name} → {destino.name}"])
    img = _abrir_imagen(ctx.entrada, ctx)
    return Resultado([_guardar_imagen(img, destino, formato, ctx.p("calidad"), ctx.p("metadatos"), img)])


@operacion("redimensionar_imagen", "Medios", "Redimensionar imagen", "Cambia el tamaño por ancho, alto o porcentaje, sin deformar.",
           entrada="medios", extensiones=IMG, sufijo="redimensionada", requiere=("py:PIL",),
           parametros=(Parametro("ancho", "Ancho máximo (px, 0 = libre)", "entero", 1600, minimo=0),
                       Parametro("alto", "Alto máximo (px, 0 = libre)", "entero", 0, minimo=0),
                       Parametro("porcentaje", "O porcentaje (0 = no)", "entero", 0, minimo=0, maximo=1000),
                       Parametro("formato", "Formato (vacío = el mismo)", "texto", ""),
                       Parametro("calidad", "Calidad", "entero", 85, minimo=10, maximo=100)),
           palabras=("tamaño", "achicar", "escalar", "resize", "redes"))
def redimensionar_imagen(ctx):
    from PIL import Image
    formato = (ctx.p("formato") or ctx.entrada.suffix.lstrip(".")).lower().replace("jpeg", "jpg")
    if formato == "svg":
        formato = "png"
    destino = ctx.salida(extension=f".{formato}")
    img = _abrir_imagen(ctx.entrada, ctx)
    w, h = img.size
    if ctx.p("porcentaje"):
        nuevo = (max(1, w * ctx.p("porcentaje") // 100), max(1, h * ctx.p("porcentaje") // 100))
    else:
        aw, ah = ctx.p("ancho") or 10**9, ctx.p("alto") or 10**9
        escala = min(aw / w, ah / h, 1.0 if not ctx.p("porcentaje") else 10.0)
        nuevo = (max(1, round(w * escala)), max(1, round(h * escala)))
    if ctx.simular:
        return Resultado(plan=[f"{w}×{h} → {nuevo[0]}×{nuevo[1]} · {destino.name}"])
    img = img.resize(nuevo, Image.LANCZOS)
    return Resultado([_guardar_imagen(img, destino, formato, ctx.p("calidad"))], {"tamano": list(nuevo)})


@operacion("recortar_imagen", "Medios", "Recortar imagen", "Recorta un rectángulo o a una proporción (1:1, 4:5, 9:16, 16:9…), centrado.",
           entrada="medios", extensiones=IMG, sufijo="recortada", requiere=("py:PIL",),
           parametros=(Parametro("proporcion", "Proporción", "opcion", "1:1",
                                 opciones=("1:1", "4:5", "9:16", "16:9", "3:2", "2:3", "4:3", "libre")),
                       Parametro("caja", "Rectángulo (x,y,ancho,alto; con «libre»)", "texto", ""),
                       Parametro("calidad", "Calidad", "entero", 90, minimo=10, maximo=100)),
           palabras=("crop", "cuadrado", "historias", "proporción"))
def recortar_imagen(ctx):
    img = _abrir_imagen(ctx.entrada, ctx)
    w, h = img.size
    if ctx.p("proporcion") == "libre":
        try:
            x, y, cw, ch = (int(v) for v in ctx.p("caja").split(","))
        except (ValueError, AttributeError) as e:
            raise ErrorOperacion("Con «libre», escriba el rectángulo como x,y,ancho,alto.") from e
    else:
        a, b = (int(v) for v in ctx.p("proporcion").split(":"))
        cw, ch = (w, round(w * b / a)) if w / h < a / b else (round(h * a / b), h)
        x, y = (w - cw) // 2, (h - ch) // 2
    if x < 0 or y < 0 or x + cw > w or y + ch > h or cw < 1 or ch < 1:
        raise ErrorOperacion(f"El rectángulo se sale de la imagen ({w}×{h}).")
    formato = ctx.entrada.suffix.lstrip(".").lower().replace("jpeg", "jpg").replace("svg", "png")
    destino = ctx.salida(extension=f".{formato}")
    if ctx.simular:
        return Resultado(plan=[f"recorte {cw}×{ch} en ({x},{y}) → {destino.name}"])
    return Resultado([_guardar_imagen(img.crop((x, y, x + cw, y + ch)), destino, formato, ctx.p("calidad"))])


@operacion("comprimir_imagen", "Medios", "Comprimir imagen", "Baja el peso: con pérdida (calidad) o sin ella (PNG optimizado).",
           entrada="medios", extensiones=IMG, sufijo="comprimida", requiere=("py:PIL",),
           parametros=(Parametro("modo", "Modo", "opcion", "con_perdida",
                                 opciones=(("con_perdida", "Con pérdida (JPG/WebP)"), ("sin_perdida", "Sin pérdida"))),
                       Parametro("calidad", "Calidad", "entero", 75, minimo=10, maximo=100),
                       Parametro("ancho", "Ancho máximo (px, 0 = igual)", "entero", 0, minimo=0)),
           palabras=("peso", "optimizar", "tinypng", "reducir"))
def comprimir_imagen(ctx):
    from PIL import Image
    original = ctx.entrada.stat().st_size
    img = _abrir_imagen(ctx.entrada, ctx)
    if ctx.p("ancho") and img.width > ctx.p("ancho"):
        img = img.resize((ctx.p("ancho"), round(img.height * ctx.p("ancho") / img.width)), Image.LANCZOS)
    ext = ctx.entrada.suffix.lstrip(".").lower().replace("jpeg", "jpg")
    if ctx.p("modo") == "sin_perdida":
        formato = "png" if ext not in ("webp",) else "webp"
    else:
        formato = ext if ext in ("jpg", "webp", "avif", "heic") else "jpg"
    destino = ctx.salida(extension=f".{formato}")
    if ctx.simular:
        return Resultado(plan=[f"{ctx.p('modo')} → {destino.name}"])
    if formato == "webp" and ctx.p("modo") == "sin_perdida":
        img.save(destino, "WEBP", lossless=True, method=6)
    else:
        _guardar_imagen(img, destino, formato, ctx.p("calidad"))
    final = destino.stat().st_size
    if final >= original and formato == ext:
        destino.unlink()
        return Resultado(sin_cambio=True, mensajes=["No se ganó peso: se conserva el original."])
    return Resultado([destino], {"original": original, "final": final,
                                 "ganancia": round(100 * (original - final) / original, 1)})


# --- audio y video --------------------------------------------------------------------------------------------


def duracion(ruta: Path) -> float:
    r = correr(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ruta)], timeout=60)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def _ffmpeg(ctx, orden: list[str], destino: Path) -> Path:
    """ffmpeg sin preguntar, con el avance leído de su salida (-progress) y la cancelación respetada."""
    import subprocess
    total = duracion(ctx.entrada) or 1.0
    proceso = subprocess.Popen(["ffmpeg", "-hide_banner", "-nostdin", "-y", "-progress", "pipe:1", "-nostats", *orden,
                                str(destino)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        for linea in proceso.stdout:
            m = re.match(r"out_time_us=(\d+)", linea)
            if m:
                ctx.avisar(int(m[1]) / 1e6 / total, "ffmpeg")
        proceso.wait(timeout=7200)
    except BaseException:
        proceso.kill()
        destino.unlink(missing_ok=True)
        raise
    if proceso.returncode != 0:
        detalle = proceso.stderr.read().strip().splitlines()[-2:]
        destino.unlink(missing_ok=True)
        raise ErrorOperacion("ffmpeg falló: " + " · ".join(detalle))
    return destino


CODECS_AUDIO = {"mp3": ["-c:a", "libmp3lame", "-q:a", "2"], "m4a": ["-c:a", "aac", "-b:a", "192k"],
                "flac": ["-c:a", "flac"], "opus": ["-c:a", "libopus", "-b:a", "128k"], "ogg": ["-c:a", "libvorbis", "-q:a", "5"],
                "wav": ["-c:a", "pcm_s16le"]}
CODECS_VIDEO = {"mp4": ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-c:a", "aac", "-b:a", "160k",
                        "-movflags", "+faststart", "-pix_fmt", "yuv420p"],
                "mov": ["-c:v", "libx264", "-crf", "20", "-c:a", "aac", "-pix_fmt", "yuv420p"],
                "mkv": ["-c:v", "libx264", "-crf", "22", "-c:a", "libopus"],
                "webm": ["-c:v", "libvpx-vp9", "-crf", "33", "-b:v", "0", "-c:a", "libopus"]}


@operacion("convertir_audio", "Medios", "Convertir audio", "MP3, M4A, FLAC, Opus, OGG o WAV.",
           entrada="medios", extensiones=AUD + VID, sufijo="audio", requiere=("ffmpeg", "ffprobe"),
           parametros=(Parametro("formato", "A", "opcion", "mp3", opciones=AUD_DESTINO),),
           palabras=("mp3", "audio", "música", "podcast", "extraer audio"))
def convertir_audio(ctx):
    destino = ctx.salida(nombre=ctx.entrada.stem, extension=f".{ctx.p('formato')}")
    if ctx.simular:
        return Resultado(plan=[f"{ctx.entrada.name} → {destino.name}"])
    return Resultado([_ffmpeg(ctx, ["-i", str(ctx.entrada), "-vn", *CODECS_AUDIO[ctx.p("formato")]], destino)])


@operacion("convertir_video", "Medios", "Convertir video", "MP4, MOV, MKV, WebM o GIF (o solo su audio en MP3/M4A).",
           entrada="medios", extensiones=VID, sufijo="video", requiere=("ffmpeg", "ffprobe"),
           parametros=(Parametro("formato", "A", "opcion", "mp4", opciones=VID_DESTINO),
                       Parametro("ancho", "Ancho máximo (px, 0 = igual)", "entero", 0, minimo=0)),
           palabras=("mp4", "mov", "webm", "video", "gif"))
def convertir_video(ctx):
    formato = ctx.p("formato")
    destino = ctx.salida(nombre=ctx.entrada.stem, extension=f".{formato}")
    if ctx.simular:
        return Resultado(plan=[f"{ctx.entrada.name} → {destino.name}"])
    escala = ["-vf", f"scale='min({ctx.p('ancho')},iw)':-2"] if ctx.p("ancho") else []
    if formato in CODECS_AUDIO:
        return Resultado([_ffmpeg(ctx, ["-i", str(ctx.entrada), "-vn", *CODECS_AUDIO[formato]], destino)])
    if formato == "gif":
        ancho = ctx.p("ancho") or 480
        filtro = f"fps=12,scale={ancho}:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse"
        return Resultado([_ffmpeg(ctx, ["-i", str(ctx.entrada), "-vf", filtro, "-loop", "0"], destino)])
    return Resultado([_ffmpeg(ctx, ["-i", str(ctx.entrada), *escala, *CODECS_VIDEO[formato]], destino)])


def _segundos(texto: str) -> float:
    """«90», «1:30», «00:01:30.5» → segundos."""
    partes = [float(p) for p in str(texto).strip().split(":")]
    s = 0.0
    for p in partes:
        s = s * 60 + p
    return s


@operacion("recortar_medio", "Medios", "Recortar audio o video", "Deja solo el tramo entre dos tiempos (sin recodificar si se puede).",
           entrada="medios", extensiones=AUD + VID, sufijo="recorte", requiere=("ffmpeg", "ffprobe"),
           parametros=(Parametro("desde", "Desde (s o mm:ss)", "texto", "0"), Parametro("hasta", "Hasta (vacío = el final)", "texto", ""),
                       Parametro("exacto", "Corte exacto (recodifica)", "casilla", False)),
           palabras=("trim", "cortar", "tramo", "clip"))
def recortar_medio(ctx):
    try:
        desde = _segundos(ctx.p("desde") or "0")
        hasta = _segundos(ctx.p("hasta")) if ctx.p("hasta") else None
    except ValueError as e:
        raise ErrorOperacion("Escriba los tiempos como 90, 1:30 o 00:01:30.") from e
    if hasta is not None and hasta <= desde:
        raise ErrorOperacion("«Hasta» debe ser mayor que «Desde».")
    destino = ctx.salida()
    if ctx.simular:
        return Resultado(plan=[f"{desde:g}s → {hasta if hasta is not None else 'fin'} · {destino.name}"])
    orden = ["-ss", f"{desde}", "-i", str(ctx.entrada)] + (["-t", f"{hasta - desde}"] if hasta is not None else [])
    ext = ctx.entrada.suffix.lower().lstrip(".")
    if ctx.p("exacto"):
        orden += CODECS_VIDEO.get(ext, CODECS_AUDIO.get(ext, []))
    else:
        orden += ["-c", "copy", "-avoid_negative_ts", "make_zero"]
    return Resultado([_ffmpeg(ctx, orden, destino)])


@operacion("comprimir_video", "Medios", "Comprimir video", "Baja el peso (H.264) a una calidad o hasta un tamaño, para enviarlo por chat o subirlo.",
           entrada="medios", extensiones=VID, sufijo="comprimido", requiere=("ffmpeg", "ffprobe"),
           parametros=(Parametro("calidad", "Calidad (CRF: 18 alta · 28 baja)", "entero", 26, minimo=16, maximo=40),
                       Parametro("hasta", "O que pese menos de (MB, 0 = sin tope)", "tamano", 0, minimo=0),
                       Parametro("ancho", "Ancho máximo (px, 0 = igual)", "entero", 1280, minimo=0)),
           palabras=("whatsapp", "peso", "reducir video"))
def comprimir_video(ctx):
    destino = ctx.salida(extension=".mp4")
    if ctx.simular:
        return Resultado(plan=[f"H.264 → {destino.name}"])
    escala = ["-vf", f"scale='min({ctx.p('ancho')},iw)':-2"] if ctx.p("ancho") else []
    if ctx.p("hasta"):
        segundos = duracion(ctx.entrada) or 1
        kbps = max(150, int(ctx.p("hasta") * 8192 / segundos) - 128)
        video = ["-c:v", "libx264", "-b:v", f"{kbps}k", "-maxrate", f"{kbps}k", "-bufsize", f"{2 * kbps}k"]
    else:
        video = ["-c:v", "libx264", "-crf", str(ctx.p("calidad"))]
    _ffmpeg(ctx, ["-i", str(ctx.entrada), *escala, *video, "-preset", "medium", "-c:a", "aac", "-b:a", "128k",
                  "-movflags", "+faststart", "-pix_fmt", "yuv420p"], destino)
    original, final = ctx.entrada.stat().st_size, destino.stat().st_size
    return Resultado([destino], {"original": original, "final": final,
                                 "ganancia": round(100 * (original - final) / original, 1)})


# --- subtítulos -----------------------------------------------------------------------------------------------


@operacion("convertir_subtitulos", "Medios", "Convertir subtítulos", "SRT ↔ VTT.",
           entrada="medios", extensiones=SUB, sufijo="subtitulos",
           palabras=("srt", "vtt", "subtítulos", "captions"))
def convertir_subtitulos(ctx):
    origen = ctx.entrada.suffix.lower()
    destino_ext = ".vtt" if origen == ".srt" else ".srt"
    destino = ctx.salida(nombre=ctx.entrada.stem, extension=destino_ext)
    if ctx.simular:
        return Resultado(plan=[f"{ctx.entrada.name} → {destino.name}"])
    texto = ctx.entrada.read_text(encoding="utf-8-sig", errors="replace").replace("\r\n", "\n")
    if destino_ext == ".vtt":
        cuerpo = re.sub(r"(\d{2}:\d{2}:\d{2}),(\d{3})", r"\1.\2", texto)
        destino.write_text("WEBVTT\n\n" + cuerpo.strip() + "\n", encoding="utf-8")
    else:
        bloques = [b for b in re.split(r"\n\s*\n", re.sub(r"^WEBVTT.*?\n", "", texto, flags=re.S)) if "-->" in b]
        salida = []
        for i, b in enumerate(bloques, 1):
            lineas = [l for l in b.strip().splitlines() if l.strip()]
            tiempo = next(l for l in lineas if "-->" in l)
            tiempo = re.sub(r"(\d{2}:\d{2}:\d{2})\.(\d{3})", r"\1,\2", tiempo)
            tiempo = re.sub(r"(?<![:\d])(\d{2}:\d{2})[.,](\d{3})", r"00:\1,\2", tiempo).split(" align")[0]
            texto_b = lineas[lineas.index(next(l for l in lineas if "-->" in l)) + 1:]
            salida.append(f"{i}\n{tiempo}\n" + "\n".join(texto_b))
        destino.write_text("\n\n".join(salida) + "\n", encoding="utf-8")
    return Resultado([destino])


# --- archivos comprimidos ------------------------------------------------------------------------------------


@operacion("comprimir_archivos", "Archivos", "Comprimir en un archivo", "ZIP, TAR.GZ o 7Z con lo elegido (archivos y carpetas).",
           entrada="archivos", lote=False, extensiones=(), sufijo="archivo",
           parametros=(Parametro("formato", "Formato", "opcion", "zip", opciones=("zip", "tar.gz", "7z")),
                       Parametro("nombre", "Nombre", "texto", "archivo"),
                       Parametro("clave", "Contraseña (zip y 7z; vacío = sin)", "clave", "")),
           palabras=("zip", "comprimir", "empaquetar", "7z", "tar"))
def comprimir_archivos(ctx):
    formato = ctx.p("formato")
    destino = ctx.salida(nombre=ctx.p("nombre") or "archivo", extension=f".{formato}", base=ctx.entradas[0])
    if ctx.simular:
        return Resultado(plan=[f"{len(ctx.entradas)} elementos → {destino.name}"])
    if formato == "tar.gz":
        import tarfile
        with tarfile.open(destino, "w:gz") as tar:
            for e in ctx.entradas:
                tar.add(e, arcname=e.name)
    elif disponible("7z"):
        orden = ["7z", "a", "-y", f"-t{'zip' if formato == 'zip' else '7z'}"]
        if ctx.p("clave"):
            orden += [f"-p{ctx.p('clave')}"] + (["-mhe=on"] if formato == "7z" else ["-mem=AES256"])
        correr(orden + [str(destino), *map(str, ctx.entradas)], timeout=3600)
    elif formato == "zip" and not ctx.p("clave"):
        import zipfile
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
            for e in ctx.entradas:
                for p in ([e] if e.is_file() else [x for x in e.rglob("*") if x.is_file()]):
                    z.write(p, p.relative_to(e.parent))
    else:
        raise ErrorOperacion("Para 7z o con contraseña hace falta 7-Zip (7z).")
    return Resultado([destino], {"bytes": destino.stat().st_size})


@operacion("extraer_archivo", "Archivos", "Extraer archivo comprimido", "ZIP, TAR, TAR.GZ, 7Z o RAR a una carpeta.",
           entrada="archivos", extensiones=ARC, sufijo="extraido",
           parametros=(Parametro("clave", "Contraseña (si la tiene)", "clave", ""),),
           palabras=("descomprimir", "unzip", "rar", "abrir zip"))
def extraer_archivo(ctx):
    tallo = re.sub(r"\.(tar)$", "", ctx.entrada.stem)
    carpeta = ctx.salida(nombre=tallo, extension="")
    if ctx.simular:
        return Resultado(plan=[f"{ctx.entrada.name} → {carpeta.name}/"])
    carpeta.mkdir(parents=True)
    if disponible("7z") and not ctx.entrada.name.endswith((".tar.gz", ".tgz")):
        correr(["7z", "x", "-y", f"-o{carpeta}", f"-p{ctx.p('clave')}", str(ctx.entrada)], timeout=3600,
               mensaje="7-Zip no pudo extraerlo (¿contraseña?)")
    elif disponible("bsdtar"):
        correr(["bsdtar", "-xf", str(ctx.entrada), "-C", str(carpeta)], timeout=3600)
    else:
        shutil.unpack_archive(str(ctx.entrada), str(carpeta))
    # Un archivo que trae una sola carpeta dentro no se anida dos veces.
    hijos = list(carpeta.iterdir())
    if len(hijos) == 1 and hijos[0].is_dir() and hijos[0].name == carpeta.name:
        for x in hijos[0].iterdir():
            shutil.move(str(x), carpeta / x.name)
        hijos[0].rmdir()
    return Resultado([carpeta], {"elementos": sum(1 for _ in carpeta.rglob("*"))})


@operacion("quitar_metadatos_archivo", "Archivos", "Quitar metadatos (cualquier archivo)",
           "Borra EXIF, GPS, autor y programa de fotos, videos y documentos antes de compartirlos.",
           entrada="archivos", extensiones=(), sufijo="limpio", requiere=("exiftool",),
           palabras=("gps", "exif", "privacidad", "ubicación", "anonimizar"))
def quitar_metadatos_archivo(ctx):
    destino = ctx.salida()
    if ctx.simular:
        return Resultado(plan=[f"exiftool -all= → {destino.name}"])
    correr(["exiftool", "-q", "-all=", "-o", str(destino), str(ctx.entrada)], timeout=300,
           mensaje="exiftool no pudo limpiarlo")
    return Resultado([destino])


# --- el menú de Tangerine ----------------------------------------------------------------------------------------


def formatos_de(ruta: str | Path) -> list[dict]:
    """A qué se puede convertir este archivo: [{"a": "jpg", "operacion": "convertir_imagen", "params": {...}}, …],
    más las herramientas que le sirven (comprimir, recortar, quitar metadatos…). Es lo que muestra el menú al soltar."""
    from raphi.motor.base import REGISTRO
    from raphi.motor.documentos import DESTINOS, OFIMATICA
    p = Path(ruta)
    ext = p.suffix.lower()
    if p.name.lower().endswith((".tar.gz", ".tgz")):
        ext = ".gz"
    salida: list[dict] = []

    def a(formato, op, /, **params):
        if op in REGISTRO and not REGISTRO[op].faltan():
            salida.append({"a": formato, "operacion": op, "params": params, "titulo": REGISTRO[op].titulo})

    if ext in IMG:
        for f in IMG_DESTINO:
            if f != ext.lstrip(".").replace("jpeg", "jpg"):
                a(f, "convertir_imagen", formato=f) if f != "pdf" else a("pdf", "imagenes_a_pdf")
        for op in ("redimensionar_imagen", "recortar_imagen", "comprimir_imagen", "quitar_metadatos_archivo"):
            a(None, op)
    elif ext in VID:
        for f in VID_DESTINO:
            if f != ext.lstrip("."):
                a(f, "convertir_video", formato=f)
        for op in ("recortar_medio", "comprimir_video", "quitar_metadatos_archivo"):
            a(None, op)
    elif ext in AUD:
        for f in AUD_DESTINO:
            if f != ext.lstrip("."):
                a(f, "convertir_audio", formato=f)
        a(None, "recortar_medio")
    elif ext in SUB:
        a("vtt" if ext == ".srt" else "srt", "convertir_subtitulos")
    elif ext in ARC:
        a(None, "extraer_archivo")
    elif ext == ".pdf":
        for f, op, kw in (("docx", "pdf_a_word", {}), ("txt", "pdf_a_texto", {}), ("png", "pdf_a_imagen", {"formato": "png"}),
                          ("jpg", "pdf_a_imagen", {"formato": "jpg"}), ("html", "pdf_a_html", {}),
                          ("md", "a_markdown", {}), ("pdf/a", "pdfa", {})):
            a(f, op, **kw)
        for op in ("comprimir", "ocr", "dividir", "rotar", "foliar", "sello", "cifrar", "quitar_metadatos"):
            a(None, op)
    elif ext in OFIMATICA:
        a("pdf", "a_pdf")
        a("md", "a_markdown")
        for f in DESTINOS:
            if f != ext.lstrip("."):
                a(f, "ofimatica", formato=f)
    if ext not in ARC:
        a("zip", "comprimir_archivos", formato="zip")
    return salida
