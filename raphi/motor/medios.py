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
IMG_DESTINO = ("jpg", "png", "webp", "avif", "heic", "tiff", "bmp", "gif", "ico", "pdf")
TAMANOS_ICO = (16, 24, 32, 48, 64, 128, 256)
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
    if nombre == "ICO":                                  # un .ico con todos sus tamaños (16 a 256), cuadrado
        lado = max(img.size)
        if img.size[0] != img.size[1]:
            cuadro = _pil().new("RGBA", (lado, lado), (0, 0, 0, 0))
            cuadro.paste(img.convert("RGBA"), ((lado - img.width) // 2, (lado - img.height) // 2))
            img = cuadro
        opciones["sizes"] = [(t, t) for t in TAMANOS_ICO if t <= lado] or [(lado, lado)]
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


MEDIDAS = (("", "La de abajo (ancho y alto)"), ("16x16", "Icono 16"), ("32x32", "Icono 32"), ("48x48", "Icono 48"),
           ("64x64", "Icono 64"), ("128x128", "Icono 128"), ("256x256", "Icono 256"), ("512x512", "Icono 512"),
           ("640x480", "VGA 640×480"), ("800x600", "SVGA 800×600"), ("1024x768", "XGA 1024×768"),
           ("1280x720", "HD 1280×720"), ("1920x1080", "Full HD 1920×1080"), ("2560x1440", "QHD 2560×1440"),
           ("3840x2160", "4K 3840×2160"), ("7680x4320", "8K 7680×4320"), ("1080x1080", "Instagram cuadrada"),
           ("1080x1350", "Instagram vertical 4:5"), ("1080x1920", "Historias y reels 9:16"), ("1200x630", "Enlace (Facebook, X)"))


@operacion("redimensionar_imagen", "Medios", "Redimensionar imagen", "Cambia el tamaño por ancho, alto o porcentaje, sin deformar.",
           entrada="medios", extensiones=IMG, sufijo="redimensionada", requiere=("py:PIL",),
           parametros=(Parametro("medida", "Medida", "opcion", "",
                                 opciones=MEDIDAS, ayuda="una medida lista manda sobre el ancho y el alto"),
                       Parametro("ancho", "Ancho máximo (px, 0 = libre)", "entero", 1600, minimo=0),
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
    elif ctx.p("medida"):                             # cabe en esa medida, sin deformar (y puede agrandar)
        aw, ah = (int(v) for v in ctx.p("medida").split("x"))
        escala = min(aw / w, ah / h)
        nuevo = (max(1, round(w * escala)), max(1, round(h * escala)))
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
                       Parametro("caja", "Rectángulo (x,y,ancho,alto)", "texto", "", vista="caja",
                                 ayuda="En píxeles; si se da, manda sobre la proporción"),
                       Parametro("calidad", "Calidad", "entero", 90, minimo=10, maximo=100)),
           palabras=("crop", "cuadrado", "historias", "proporción"))
def recortar_imagen(ctx):
    img = _abrir_imagen(ctx.entrada, ctx)
    w, h = img.size
    if ctx.p("caja") or ctx.p("proporcion") == "libre":
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


@operacion("fondo_imagen", "Medios", "Poner fondo",
           "Pone la imagen sobre un fondo de color o degradado, con margen, esquinas redondeadas, sombra y la proporción "
           "del lienzo (1:1, 4:5, 9:16…): capturas y fotos listas para publicar.",
           entrada="medios", extensiones=IMG, sufijo="con_fondo", requiere=("py:PIL",),
           parametros=(Parametro("color", "Fondo", "color", "#F2994A"),
                       Parametro("color2", "Degradado hacia", "color", "", ayuda="Vacío: fondo liso"),
                       Parametro("margen", "Margen (% del lado menor)", "entero", 8, minimo=0, maximo=100),
                       Parametro("esquinas", "Esquinas (% del lado menor)", "entero", 4, minimo=0, maximo=50),
                       Parametro("sombra", "Sombra (% del lado menor)", "entero", 3, minimo=0, maximo=30),
                       Parametro("proporcion", "Lienzo", "opcion", "auto",
                                 opciones=(("auto", "Como la imagen"), "1:1", "4:5", "9:16", "16:9", "4:3", "3:2")),
                       Parametro("formato", "Formato", "opcion", "png", opciones=("png", "jpg", "webp")),
                       Parametro("calidad", "Calidad", "entero", 92, minimo=10, maximo=100)),
           palabras=("add bg", "background", "marco", "captura", "sombra", "esquinas", "publicar"))
def fondo_imagen(ctx):
    formato = ctx.p("formato")
    destino = ctx.salida(extension=f".{formato}")
    if ctx.simular:
        lienzo = "como la imagen" if ctx.p("proporcion") == "auto" else ctx.p("proporcion")
        return Resultado(plan=[f"fondo {ctx.p('color')}{(' → ' + ctx.p('color2')) if ctx.p('color2') else ''}, margen "
                               f"{ctx.p('margen')} %, esquinas {ctx.p('esquinas')} %, sombra {ctx.p('sombra')} %, lienzo "
                               f"{lienzo} → {destino.name}"])
    img = _abrir_imagen(ctx.entrada, ctx).convert("RGBA")
    salida = componer_fondo(img, ctx.p("color"), ctx.p("color2"), ctx.p("margen"), ctx.p("esquinas"), ctx.p("sombra"),
                            ctx.p("proporcion"))
    return Resultado([_guardar_imagen(salida, destino, formato, ctx.p("calidad"))], {"tamano": list(salida.size)})


def _color(texto: str) -> tuple[int, int, int]:
    from PIL import ImageColor
    try:
        return ImageColor.getrgb(texto)[:3]
    except ValueError as e:
        raise ErrorOperacion(f"Color no válido: {texto!r}.") from e


def componer_fondo(img, color: str, color2: str, margen: int, esquinas: int, sombra: int, proporcion: str):
    """La imagen (RGBA) centrada en un lienzo de color o degradado diagonal, con esquinas y sombra. Los tamaños son
    porcentajes del lado menor: el mismo ajuste da lo mismo en una captura pequeña y en una foto de 24 MP."""
    from PIL import ImageDraw, ImageFilter
    Image = _pil()
    w, h = img.size
    lado = min(w, h)
    pad, radio, difuso = (round(lado * v / 100) for v in (margen, esquinas, sombra))
    ancho, alto = w + 2 * pad, h + 2 * pad
    if proporcion and proporcion != "auto":
        a, b = (int(v) for v in proporcion.split(":"))
        if ancho / alto < a / b:
            ancho = round(alto * a / b)
        else:
            alto = round(ancho * b / a)
    x, y = (ancho - w) // 2, (alto - h) // 2
    c1 = _color(color)
    lienzo = Image.new("RGBA", (ancho, alto), c1 + (255,))
    if color2:
        rampa = Image.linear_gradient("L").rotate(45, expand=True, resample=Image.BICUBIC)
        lado_r = round(256 / 2 ** 0.5)
        m = (rampa.width - lado_r) // 2
        rampa = rampa.crop((m, m, m + lado_r, m + lado_r)).resize((ancho, alto), Image.BICUBIC)
        lienzo = Image.composite(Image.new("RGBA", (ancho, alto), _color(color2) + (255,)), lienzo, rampa)
    mascara = Image.new("L", (w, h), 255)
    if radio:
        radio = min(radio, w // 2, h // 2)
        grande = Image.new("L", (radio * 8, radio * 8), 0)        # el círculo a 4× y reducido: bordes suaves
        ImageDraw.Draw(grande).ellipse((0, 0, radio * 8 - 1, radio * 8 - 1), fill=255)
        circulo = grande.resize((radio * 2, radio * 2), Image.LANCZOS)
        for cx, cy, px, py in ((0, 0, 0, 0), (radio, 0, w - radio, 0), (0, radio, 0, h - radio), (radio, radio, w - radio, h - radio)):
            mascara.paste(circulo.crop((cx, cy, cx + radio, cy + radio)), (px, py))
    if "A" in img.getbands():
        from PIL import ImageChops
        mascara = ImageChops.multiply(mascara, img.getchannel("A"))
    if difuso:
        capa = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
        negra = Image.new("RGBA", (w, h), (0, 0, 0, 120))
        capa.paste(negra, (x, y + difuso // 2), mascara)
        lienzo = Image.alpha_composite(lienzo, capa.filter(ImageFilter.GaussianBlur(difuso)))
    lienzo.paste(img, (x, y), mascara)
    return lienzo


FOTOS_DOCUMENTO = {"35x45": ("Pasaporte o visa Schengen, 35×45 mm", 35, 45), "51x51": ("Visa de EE. UU., 2×2 pulgadas", 51, 51),
                   "30x40": ("Carné 30×40 mm", 30, 40), "25x30": ("Carné 25×30 mm", 25, 30),
                   "40x50": ("40×50 mm", 40, 50)}


@operacion("foto_documento", "Medios", "Foto de documento",
           "La foto a la medida de un pasaporte, una visa o un carné (35×45 mm, 2×2 pulgadas, 30×40 mm…), a 300 ppp: "
           "recortada para llenar sin deformar, con un poco más de arriba (la cara) y el fondo que se elija detrás.",
           entrada="medios", extensiones=IMG, sufijo="documento", requiere=("py:PIL",),
           parametros=(Parametro("medida", "Medida", "opcion", "35x45",
                                 opciones=tuple((k, v[0]) for k, v in FOTOS_DOCUMENTO.items())),
                       Parametro("ppp", "Resolución (ppp)", "entero", 300, minimo=150, maximo=1200),
                       Parametro("fondo", "Fondo (si la foto tiene transparencia)", "color", "#FFFFFF"),
                       Parametro("formato", "Formato", "opcion", "jpg", opciones=("jpg", "png"))),
           palabras=("pasaporte", "visa", "carné", "dni", "foto carnet", "id", "35x45"))
def foto_documento(ctx):
    _, mm_ancho, mm_alto = FOTOS_DOCUMENTO[ctx.p("medida")]
    ppp = ctx.p("ppp")
    ancho, alto = round(mm_ancho / 25.4 * ppp), round(mm_alto / 25.4 * ppp)
    formato = ctx.p("formato")
    destino = ctx.salida(extension=f".{formato}")
    if ctx.simular:
        return Resultado(plan=[f"{ancho}×{alto} px ({mm_ancho}×{mm_alto} mm a {ppp} ppp) → {destino.name}"])
    Image = _pil()
    img = _abrir_imagen(ctx.entrada, ctx).convert("RGBA")
    fondo = Image.new("RGBA", img.size, _color(ctx.p("fondo")) + (255,))
    img = Image.alpha_composite(fondo, img).convert("RGB")
    w, h = img.size
    escala = max(ancho / w, alto / h)                     # llenar: lo que sobra se recorta
    img = img.resize((max(ancho, round(w * escala)), max(alto, round(h * escala))), Image.LANCZOS)
    x = (img.width - ancho) // 2
    y = round((img.height - alto) * 0.3)                  # más de arriba que de abajo: la cara suele estar arriba
    img = img.crop((x, y, x + ancho, y + alto))
    if formato == "jpg":
        img.save(destino, "JPEG", quality=95, dpi=(ppp, ppp))
    else:
        img.save(destino, "PNG", dpi=(ppp, ppp))
    return Resultado([destino], {"pixeles": f"{ancho}×{alto}", "milimetros": f"{mm_ancho}×{mm_alto}", "ppp": ppp})


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
    # Comprimir es bajar el peso: si no baja (un PNG de colores planos pesa más como JPG), se conserva el original.
    if final >= original:
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


def _ffmpeg(ctx, orden: list[str], destino: Path, total: float | None = None) -> Path:
    """ffmpeg sin preguntar, con el avance leído de su salida (-progress) y la cancelación respetada. `total`: la
    duración que se espera (por omisión, la de la entrada; al unir varios, la suma)."""
    import subprocess
    total = total or duracion(ctx.entrada) or 1.0
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


TASAS = ("auto", "96k", "128k", "160k", "192k", "256k", "320k")


@operacion("convertir_audio", "Medios", "Convertir audio", "MP3, M4A, FLAC, Opus, OGG o WAV, con sus etiquetas.",
           entrada="medios", extensiones=AUD + VID, sufijo="audio", requiere=("ffmpeg", "ffprobe"),
           parametros=(Parametro("formato", "A", "opcion", "mp3", opciones=AUD_DESTINO),
                       Parametro("tasa", "Tasa de bits", "opcion", "auto", opciones=TASAS,
                                 ayuda="«auto»: calidad variable alta; un valor fijo (p. ej. 192k), tasa constante")),
           palabras=("mp3", "audio", "música", "podcast", "extraer audio", "nota de voz", "whatsapp", "opus"))
def convertir_audio(ctx):
    # absorbe el conversor de notas de voz que se retiró el 2026-10-31: tasa fija y etiquetas del original
    formato, tasa = ctx.p("formato"), ctx.p("tasa") or "auto"
    destino = ctx.salida(nombre=ctx.entrada.stem, extension=f".{formato}")
    if ctx.simular:
        return Resultado(plan=[f"{ctx.entrada.name} → {destino.name}" + ("" if tasa == "auto" else f" ({tasa})")])
    codec = list(CODECS_AUDIO[formato])
    if tasa != "auto" and formato not in ("flac", "wav"):
        codec = codec[:2] + ["-b:a", tasa]            # sin pérdida (flac, wav) no lleva tasa
    # Ogg y Opus guardan las etiquetas en la pista de audio, no en el contenedor: se copian de ahí
    origen = "0:s:a:0" if ctx.entrada.suffix.lower() in (".ogg", ".opus") else "0"
    etiquetas = ["-map_metadata", origen] + (["-id3v2_version", "3"] if formato == "mp3" else [])
    return Resultado([_ffmpeg(ctx, ["-i", str(ctx.entrada), "-vn", *codec, *etiquetas], destino)])


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


OFICINA_ZIP = (".docx", ".xlsx", ".pptx", ".dotx", ".odt", ".ods", ".odp")
# Lo que queda en lugar de las propiedades de un documento de oficina: el archivo vacío que exige cada formato.
_CORE_VACIO = (b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<cp:coreProperties '
               b'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
               b'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
               b'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"/>')
_APP_VACIO = (b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Properties '
              b'xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
              b'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"/>')
_META_VACIO = (b'<?xml version="1.0" encoding="UTF-8"?>\n<office:document-meta '
               b'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
               b'xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" office:version="1.2"><office:meta/></office:document-meta>')


def _limpiar_oficina(origen: Path, destino: Path) -> int:
    """Un docx/xlsx/pptx u odt/ods/odp sin sus propiedades (autor, empresa, fechas, programa, miniatura): se reescribe
    el ZIP con `docProps/core.xml`, `docProps/app.xml` o `meta.xml` vacíos y sin la miniatura. exiftool no escribe
    estos formatos. El contenido no se toca."""
    import zipfile
    quitados = 0
    try:
        with zipfile.ZipFile(origen) as z, zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as w:
            for item in z.infolist():
                nombre = item.filename
                datos = z.read(nombre)
                if nombre == "docProps/core.xml":
                    datos, quitados = _CORE_VACIO, quitados + 1
                elif nombre == "docProps/app.xml":
                    datos, quitados = _APP_VACIO, quitados + 1
                elif nombre == "meta.xml":
                    datos, quitados = _META_VACIO, quitados + 1
                elif nombre in ("docProps/thumbnail.jpeg", "docProps/thumbnail.png", "Thumbnails/thumbnail.png"):
                    quitados += 1
                    continue
                w.writestr(item, datos)         # con su ZipInfo: el «mimetype» de ODF sigue sin comprimir y primero
    except zipfile.BadZipFile as e:
        destino.unlink(missing_ok=True)
        raise ErrorOperacion(f"{origen.name} no es un documento de oficina válido.") from e
    return quitados


@operacion("quitar_metadatos_archivo", "Archivos", "Quitar metadatos (cualquier archivo)",
           "Borra EXIF, GPS, autor, programa, miniaturas y lo demás que delate a quien lo hizo, de fotos, audio, vídeo y "
           "documentos, antes de compartirlos: con mat2 si está (a fondo) o exiftool, en una copia, y después comprueba "
           "qué quedó. Los PDF se limpian sin rasterizar (sus textos siguen seleccionables).",
           entrada="archivos", extensiones=(), sufijo="limpio", requiere=("exiftool",),
           parametros=(Parametro("motor", "Con", "opcion", "auto",
                                 opciones=(("auto", "El más a fondo que haya (mat2; si no, exiftool)"), ("mat2", "mat2"),
                                           ("exiftool", "exiftool"))),
                       Parametro("ligero", "Limpieza ligera (mat2 no recodifica: deja algún dato técnico)", "casilla", False)),
           palabras=("gps", "exif", "privacidad", "ubicación", "anonimizar", "mat2", "metadata cleaner", "limpiar"))
def quitar_metadatos_archivo(ctx):
    ext = ctx.entrada.suffix.lower()
    if ctx.entrada.is_dir():
        raise ErrorOperacion(f"{ctx.entrada.name} es una carpeta: elige sus archivos.")
    if ext == ".pdf":
        # exiftool edita un PDF de forma reversible (lo viejo queda dentro) y mat2 lo rasteriza: un PDF, con «quitar_metadatos»
        from raphi.motor.pdf_editar import quitar_metadatos
        return quitar_metadatos(ctx)
    pedido = ctx.p("motor") or "auto"
    con_mat2 = pedido == "mat2" or (pedido == "auto" and disponible("mat2") and ext not in OFICINA_ZIP)
    if pedido == "mat2" and not disponible("mat2"):
        raise ErrorOperacion("mat2 no está instalado (sudo apt install mat2).")
    destino = ctx.salida()
    if ctx.simular:
        como = ("mat2" + (" --lightweight" if ctx.p("ligero") else "")) if con_mat2 else \
            "sin sus propiedades (reescrito el ZIP)" if ext in OFICINA_ZIP else "exiftool -all="
        return Resultado(plan=[f"{como} → {destino.name}"])
    from raphi.motor.archivos import TECNICOS, contar_personales, leer_metadatos
    antes = contar_personales(leer_metadatos(ctx.entrada))
    if con_mat2:
        copia = ctx.carpeta_temporal() / f"limpio{ext}"
        shutil.copy2(ctx.entrada, copia)
        orden = ["mat2", "--inplace"] + (["--lightweight"] if ctx.p("ligero") else []) + [str(copia)]
        correr(orden, timeout=1800, mensaje="mat2 no pudo limpiarlo")
        shutil.move(str(copia), destino)
    elif ext in OFICINA_ZIP:
        _limpiar_oficina(ctx.entrada, destino)
    else:
        correr(["exiftool", "-q", "-all=", "-o", str(destino), str(ctx.entrada)], timeout=300,
               mensaje="exiftool no pudo limpiarlo")
    quedan = {f"{g} › {c}": v for g, campos in leer_metadatos(destino).items() if g not in TECNICOS for c, v in campos.items()}
    despues = len(quedan)
    datos = {"motor": "mat2" if con_mat2 else "exiftool" if ext not in OFICINA_ZIP else "Raphi (ZIP de oficina)",
             "campos antes": antes, "campos después": despues}
    if quedan:
        datos["lo que queda (estructura del formato)"] = dict(list(quedan.items())[:60])
    return Resultado([destino], datos, [f"quitados {max(0, antes - despues)} de {antes} campos; quedan {despues}"])


# --- el menú de Tangerine ----------------------------------------------------------------------------------------


def formatos_de(ruta: str | Path) -> list[dict]:
    """A qué se puede convertir este archivo: [{"a": "jpg", "operacion": "convertir_imagen", "params": {...}}, …],
    más las herramientas que le sirven (comprimir, recortar, quitar metadatos…). Es lo que muestra el menú al soltar."""
    from raphi.motor.base import REGISTRO
    from raphi.motor.documentos import OFIMATICA, destinos_de
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
        for op in ("comprimir_imagen", "recortar_imagen", "fondo_imagen", "redimensionar_imagen", "quitar_metadatos_archivo",
                   "ver_metadatos", "foto_documento"):
            a(None, op)
    elif ext in VID:
        for f in VID_DESTINO:
            if f != ext.lstrip("."):
                a(f, "convertir_video", formato=f)
        a("srt", "transcribir", formato="srt")
        a("txt", "transcribir", formato="txt")
        for op in ("recortar_medio", "comprimir_video", "rotar_video", "extraer_subtitulos", "normalizar_audio", "info_medio",
                   "dividir_medio", "quitar_metadatos_archivo", "ver_metadatos"):
            a(None, op)
    elif ext in AUD:
        for f in AUD_DESTINO:
            if f != ext.lstrip("."):
                a(f, "convertir_audio", formato=f)
        a("srt", "transcribir", formato="srt")
        a("txt", "transcribir", formato="txt")
        for op in ("recortar_medio", "normalizar_audio", "info_medio", "dividir_medio", "quitar_metadatos_archivo", "ver_metadatos"):
            a(None, op)
    elif ext in SUB:
        a("vtt" if ext == ".srt" else "srt", "convertir_subtitulos")
    elif ext in ARC:
        a(None, "extraer_archivo")
        a(None, "verificar_comprimido")
    elif ext == ".pdf":
        for f, op, kw in (("docx", "pdf_a_word", {}), ("txt", "pdf_a_texto", {}), ("png", "pdf_a_imagen", {"formato": "png"}),
                          ("jpg", "pdf_a_imagen", {"formato": "jpg"}), ("html", "pdf_a_html", {}),
                          ("md", "a_markdown", {}), ("pdf/a", "pdfa", {})):
            a(f, op, **kw)
        for op in ("comprimir", "ocr", "tachar", "nota", "marca_agua", "rotar", "dividir", "metadatos", "foliar", "sello",
                   "resaltar", "cifrar", "quitar_metadatos", "info", "ver_metadatos", "firmas", "tablas_a_excel",
                   "leer_comprobante", "reparar", "descifrar"):
            a(None, op)
    elif ext in OFIMATICA:
        a("pdf", "a_pdf")
        a("md", "a_markdown")
        for f in destinos_de(ext)[1]:
            a(f, "ofimatica", formato=f)
        a(None, "quitar_metadatos_archivo")
        a(None, "ver_metadatos")
    elif ext in (".md5", ".sha1", ".sha256", ".sha512", ".md5sum", ".sha1sum", ".sha256sum", ".sha512sum"):
        a(None, "verificar_suma")
    if ext not in ARC:
        a("zip", "comprimir_archivos", formato="zip")
    if p.suffix:                                         # un archivo (no una carpeta): su huella
        a(None, "suma_verificacion")
    return salida


def opciones_para(rutas: list[str | Path]) -> list[dict]:
    """Lo que se ofrece para varios archivos juntos (la rueda de soltar): lo que `formatos_de` da para todos, más lo
    que trabaja con todos a la vez (unir PDF, comparar dos). Cada opción lleva `junta`: True si da UNA salida con
    todos (imágenes a un PDF, un ZIP), False si da una por archivo."""
    import json
    from raphi.motor.base import REGISTRO
    rutas = [Path(r) for r in rutas]
    if not rutas:
        return []
    clave = lambda o: (o["operacion"], json.dumps(o["params"], sort_keys=True))  # noqa: E731
    listas = [formatos_de(r) for r in rutas]
    otras = [{clave(o) for o in lista} for lista in listas[1:]]
    salida = [dict(o) for o in listas[0] if all(clave(o) in c for c in otras)]
    exts = [r.suffix.lower() for r in rutas]
    juntar = []
    if len(rutas) > 1:
        videos, subs = [e for e in exts if e in VID], [e for e in exts if e in SUB + (".ass", ".ssa")]
        audios, imagenes = [e for e in exts if e in AUD], [e for e in exts if e in IMG]
        if len(videos) == 1 and subs and len(videos) + len(subs) == len(exts):
            juntar.append(("incrustar_subtitulos", None))
        if audios and len(imagenes) == 1 and len(audios) + 1 == len(exts) and set(audios) <= {".mp3", ".m4a", ".flac"}:
            juntar.append(("portada_audio", None))
        if len(audios) == len(exts) or len(videos) == len(exts):
            juntar.append(("unir_medios", (audios or videos)[0].lstrip(".")))
    for op, formato in juntar:
        if op in REGISTRO and not REGISTRO[op].faltan():
            salida.insert(0, {"a": formato, "operacion": op, "params": {}, "titulo": REGISTRO[op].titulo})
    if len(rutas) > 1 and {r.suffix.lower() for r in rutas} == {".pdf"}:
        for op, formato in (("unir", "pdf"),) + ((("comparar", None),) if len(rutas) == 2 else ()):
            if op in REGISTRO and not REGISTRO[op].faltan():
                salida.insert(0, {"a": formato, "operacion": op, "params": {}, "titulo": REGISTRO[op].titulo})
    for o in salida:
        o["junta"] = len(rutas) > 1 and not REGISTRO[o["operacion"]].lote
    return salida
