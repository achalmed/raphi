"""Audio y vídeo, más allá de convertir y recortar (`medios.py`): lo de KDE-Services («Audio/Video Info», «MKV Extract
Subtitle», «Multiplex Subtitle», «Volume Normalize», «Rotate Video», «Concatenate Media Files», «Attach Cover to MP3»,
«AVI Split») para cualquier formato que lea ffmpeg, no solo AVI, MKV o MP3:

- `info_medio`: duración, contenedor, tasa, y cada pista (vídeo, audio, subtítulos) con sus códecs e idiomas;
- `extraer_subtitulos`: cada pista de subtítulos de un vídeo, a SRT (o VTT o ASS);
- `incrustar_subtitulos`: un vídeo y uno o más SRT/VTT/ASS → como pista que se activa y desactiva, o quemados;
- `normalizar_audio`: el volumen al estándar (EBU R128 con loudnorm): podcast, radio, plataformas;
- `rotar_video`: 90°, 180°, 270° o espejo;
- `unir_medios`: varios audios o vídeos en uno, sin recodificar si se puede;
- `portada_audio`: una imagen como carátula de MP3, M4A o FLAC;
- `dividir_medio`: en partes de N minutos, sin recodificar.

Ninguna toca el original: la salida va a su lado con un sufijo (principios del núcleo).
"""
from __future__ import annotations

import json
from pathlib import Path

from raphi.motor.base import ErrorOperacion, Parametro, Resultado, operacion
from raphi.motor.medios import AUD, IMG, VID, _ffmpeg, duracion
from raphi.motor.utiles import correr

SUBS = (".srt", ".vtt", ".ass", ".ssa")
REQ = ("ffmpeg", "ffprobe")


def sondear(ruta: Path) -> dict:
    """ffprobe en JSON (formato y pistas)."""
    r = correr(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(ruta)],
               timeout=120, mensaje=f"ffprobe no pudo leer {ruta.name}")
    try:
        return json.loads(r.stdout or "{}")
    except ValueError as e:
        raise ErrorOperacion(f"ffprobe no devolvió datos de {ruta.name}.") from e


def _hms(segundos: float) -> str:
    s = int(round(segundos))
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}"


def _tasa(texto: str | None) -> str:
    try:
        n, d = (texto or "0/1").split("/")
        return f"{float(n) / float(d):.3g} fps" if float(d) else ""
    except (ValueError, ZeroDivisionError):
        return ""


@operacion("info_medio", "Información", "Información del medio",
           "Duración, contenedor, tasa de bits y cada pista (vídeo con su resolución y fotogramas, audio con sus canales, "
           "subtítulos con su idioma), y sus etiquetas. No escribe nada.",
           entrada="medios", extensiones=AUD + VID, requiere=("ffprobe",),
           palabras=("ffprobe", "mediainfo", "códec", "resolución", "duración", "pistas", "bitrate"))
def info_medio(ctx):
    if ctx.simular:
        return Resultado(plan=[f"ffprobe {ctx.entrada.name}"])
    datos = sondear(ctx.entrada)
    f = datos.get("format", {})
    resumen = {"contenedor": f.get("format_long_name", ""), "duración": _hms(float(f.get("duration") or 0)),
               "tamaño": f"{int(f.get('size') or 0) / 1e6:.1f} MB",
               "tasa de bits": f"{int(f.get('bit_rate') or 0) // 1000} kb/s" if f.get("bit_rate") else "—"}
    pistas = {}
    for s in datos.get("streams", []):
        tipo = {"video": "vídeo", "audio": "audio", "subtitle": "subtítulos"}.get(s.get("codec_type"), s.get("codec_type", "otra"))
        if tipo == "vídeo" and (s.get("disposition") or {}).get("attached_pic"):
            tipo = "carátula"
        idioma = (s.get("tags") or {}).get("language", "")
        partes = [s.get("codec_long_name") or s.get("codec_name", "")]
        if tipo == "vídeo":
            partes += [f"{s.get('width')}×{s.get('height')}", _tasa(s.get("avg_frame_rate")), s.get("pix_fmt", "")]
        elif tipo == "audio":
            partes += [f"{s.get('sample_rate', '?')} Hz", f"{s.get('channels', '?')} canales ({s.get('channel_layout', '')})"]
        if s.get("bit_rate"):
            partes.append(f"{int(s['bit_rate']) // 1000} kb/s")
        if idioma:
            partes.append(idioma)
        pistas[f"{s.get('index')} · {tipo}"] = " · ".join(p for p in partes if p)
    etiquetas = {k: v for k, v in (f.get("tags") or {}).items()}
    return Resultado(datos={"Resumen": resumen, "Pistas": pistas, **({"Etiquetas": etiquetas} if etiquetas else {})},
                     mensajes=[f"{len(pistas)} pista(s), {resumen['duración']}"])


@operacion("extraer_subtitulos", "Medios", "Extraer subtítulos",
           "Cada pista de subtítulos del vídeo (MKV, MP4, WebM…) a su propio archivo, con su idioma en el nombre.",
           entrada="medios", extensiones=VID, sufijo="subtitulos", requiere=REQ,
           parametros=(Parametro("formato", "A", "opcion", "srt", opciones=("srt", "vtt", "ass")),),
           palabras=("mkv", "srt", "subtítulos", "mkvextract", "pistas"))
def extraer_subtitulos(ctx):
    pistas = [s for s in sondear(ctx.entrada).get("streams", []) if s.get("codec_type") == "subtitle"]
    if not pistas:
        raise ErrorOperacion(f"{ctx.entrada.name} no tiene pistas de subtítulos.")
    formato = ctx.p("formato")
    destinos = []
    for n, s in enumerate(pistas):
        idioma = (s.get("tags") or {}).get("language") or str(n + 1)
        destinos.append((n, ctx.salida(nombre=f"{ctx.entrada.stem}.{idioma}" + (f"-{n + 1}" if sum(
            ((x.get('tags') or {}).get('language') or '') == idioma for x in pistas) > 1 else ""), extension=f".{formato}")))
    if ctx.simular:
        return Resultado(plan=[f"pista {n + 1} → {d.name}" for n, d in destinos])
    salidas = []
    for n, destino in destinos:
        if pistas[n].get("codec_name") in ("hdmv_pgs_subtitle", "dvd_subtitle", "dvb_subtitle"):
            ctx.avisar(n / len(destinos), f"la pista {n + 1} es una imagen (PGS/VobSub): no se pasa a texto")
            continue
        correr(["ffmpeg", "-hide_banner", "-nostdin", "-y", "-i", str(ctx.entrada), "-map", f"0:s:{n}", str(destino)],
               timeout=1800, mensaje=f"ffmpeg no pudo extraer la pista {n + 1}")
        salidas.append(destino)
    if not salidas:
        raise ErrorOperacion("Las pistas de subtítulos son imágenes (PGS o VobSub): hace falta OCR de subtítulos.")
    return Resultado(salidas)


@operacion("incrustar_subtitulos", "Medios", "Incrustar subtítulos",
           "Un vídeo y sus subtítulos (SRT, VTT o ASS) en un solo archivo: como pista que el reproductor activa y "
           "desactiva (al instante, sin recodificar) o quemados en la imagen (para redes sociales).",
           entrada="archivos", lote=False, minimo_entradas=2, extensiones=VID + SUBS, sufijo="subtitulado", requiere=REQ,
           parametros=(Parametro("modo", "Cómo", "opcion", "pista",
                                 opciones=(("pista", "Como pista (se activa y desactiva)"), ("quemar", "Quemados en la imagen"))),
                       Parametro("idioma", "Idioma de la pista (código)", "texto", "spa")),
           palabras=("mux", "multiplex", "subtítulos", "srt", "quemar", "hardsub"))
def incrustar_subtitulos(ctx):
    videos = [e for e in ctx.entradas if e.suffix.lower() in VID]
    subs = [e for e in ctx.entradas if e.suffix.lower() in SUBS]
    if len(videos) != 1 or not subs:
        raise ErrorOperacion("Hace falta un vídeo y al menos un archivo de subtítulos (SRT, VTT o ASS).")
    video = videos[0]
    quemar = ctx.p("modo") == "quemar"
    ext = video.suffix.lower() if quemar or video.suffix.lower() in (".mkv", ".mp4", ".mov", ".m4v") else ".mkv"
    destino = ctx.salida(extension=ext, base=video)
    if ctx.simular:
        return Resultado(plan=[f"{video.name} + {', '.join(s.name for s in subs)} ({'quemados' if quemar else 'como pista'}) → {destino.name}"])
    if quemar:
        filtro = "subtitles=" + str(subs[0]).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
        orden = ["-i", str(video), "-vf", filtro, "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "copy"]
    else:
        codec = "mov_text" if ext in (".mp4", ".mov", ".m4v") else "srt" if ext == ".mkv" else "webvtt"
        orden = ["-i", str(video)]
        for s in subs:
            orden += ["-i", str(s)]
        orden += ["-map", "0:v?", "-map", "0:a?"] + [x for i in range(len(subs)) for x in ("-map", f"{i + 1}:0")]
        orden += ["-c:v", "copy", "-c:a", "copy", "-c:s", codec]
        for i in range(len(subs)):
            orden += [f"-metadata:s:s:{i}", f"language={ctx.p('idioma') or 'spa'}"]
    return Resultado([_ffmpeg(ctx, orden, destino, total=duracion(video))])


NIVELES = {"podcast": -16, "plataformas": -14, "radio": -23}


@operacion("normalizar_audio", "Medios", "Normalizar volumen",
           "El volumen al nivel estándar (loudnorm, EBU R128): todo el audio parejo, sin saturar. En un vídeo, la imagen "
           "no se toca.",
           entrada="medios", extensiones=AUD + VID, sufijo="normalizado", requiere=REQ,
           parametros=(Parametro("nivel", "Nivel", "opcion", "podcast",
                                 opciones=(("podcast", "Podcast y voz (−16 LUFS)"), ("plataformas", "Spotify, YouTube (−14 LUFS)"),
                                           ("radio", "Radio y TV, EBU R128 (−23 LUFS)"))),),
           palabras=("volumen", "loudnorm", "lufs", "mp3gain", "normalize", "nivelar"))
def normalizar_audio(ctx):
    ext = ctx.entrada.suffix.lower()
    destino = ctx.salida(extension=".m4a" if ext in (".aac",) else ext)
    objetivo = NIVELES[ctx.p("nivel")]
    if ctx.simular:
        return Resultado(plan=[f"loudnorm I={objetivo} LUFS → {destino.name}"])
    filtro = f"loudnorm=I={objetivo}:TP=-1.5:LRA=11"
    from raphi.motor.medios import CODECS_AUDIO
    codec = CODECS_AUDIO.get(ext.lstrip("."), ["-c:a", "aac", "-b:a", "192k"])
    orden = ["-i", str(ctx.entrada), "-af", filtro, "-ar", "48000"]
    if ext in VID:
        orden += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k"]
    else:
        orden += codec + ["-map_metadata", "0"]
    return Resultado([_ffmpeg(ctx, orden, destino)])


GIROS = {"90": "transpose=1", "180": "transpose=1,transpose=1", "270": "transpose=2", "espejo": "hflip", "vertical": "vflip"}


@operacion("rotar_video", "Medios", "Rotar vídeo",
           "Gira el vídeo 90°, 180° o 270° (un vídeo grabado de lado), o lo voltea en espejo.",
           entrada="medios", extensiones=VID, sufijo="rotado", requiere=REQ,
           parametros=(Parametro("giro", "Giro", "opcion", "90",
                                 opciones=(("90", "90° a la derecha"), ("270", "90° a la izquierda"), ("180", "180°"),
                                           ("espejo", "Espejo horizontal"), ("vertical", "Espejo vertical"))),),
           palabras=("girar", "rotate", "de lado", "vertical", "transpose", "espejo"))
def rotar_video(ctx):
    ext = ctx.entrada.suffix.lower()
    destino = ctx.salida(extension=ext if ext in (".mp4", ".mkv", ".mov", ".webm") else ".mp4")
    if ctx.simular:
        return Resultado(plan=[f"{GIROS[ctx.p('giro')]} → {destino.name}"])
    codec = ["-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0"] if destino.suffix == ".webm" else \
        ["-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p"]
    return Resultado([_ffmpeg(ctx, ["-i", str(ctx.entrada), "-vf", GIROS[ctx.p("giro")], *codec, "-c:a", "copy",
                                    "-metadata:s:v", "rotate=0"], destino)])


@operacion("unir_medios", "Medios", "Unir audios o vídeos",
           "Varios audios o vídeos, uno tras otro, en un solo archivo (en el orden dado). Sin recodificar si todos tienen "
           "el mismo formato; si no, se recodifican al del primero.",
           entrada="medios", lote=False, minimo_entradas=2, extensiones=AUD + VID, sufijo="unido", requiere=REQ,
           parametros=(Parametro("nombre", "Nombre del archivo (sin extensión)", "texto", "unido"),
                       Parametro("recodificar", "Recodificar siempre (si los formatos no coinciden)", "casilla", False)),
           palabras=("concatenar", "juntar", "concat", "audios", "clips", "capítulos"))
def unir_medios(ctx):
    primero = ctx.entradas[0]
    ext = primero.suffix.lower()
    destino = ctx.salida(nombre=ctx.p("nombre") or "unido", extension=ext)
    firmas = []
    for e in ctx.entradas:
        pistas = sondear(e).get("streams", [])
        firmas.append(tuple(sorted((s.get("codec_type"), s.get("codec_name"), s.get("width"), s.get("sample_rate")) for s in pistas)))
    iguales = len(set(firmas)) == 1 and len({e.suffix.lower() for e in ctx.entradas}) == 1
    copiar = iguales and not ctx.p("recodificar")
    if ctx.simular:
        return Resultado(plan=[f"{len(ctx.entradas)} archivos {'sin recodificar' if copiar else 'recodificados'} → {destino.name}"])
    total = sum(duracion(e) for e in ctx.entradas) or 1.0
    if copiar:
        lista = ctx.temporal(".txt")
        lista.write_text("".join("file '" + str(e).replace("'", "'\\''") + "'\n" for e in ctx.entradas), encoding="utf-8")
        orden = ["-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy"]
    else:
        hay_video = ext in VID
        orden = [x for e in ctx.entradas for x in ("-i", str(e))]
        n = len(ctx.entradas)
        if hay_video:
            ancho, alto = next(((s["width"], s["height"]) for s in sondear(primero).get("streams", []) if s.get("codec_type") == "video"), (1280, 720))
            escalas = "".join(f"[{i}:v:0]scale={ancho}:{alto}:force_original_aspect_ratio=decrease,pad={ancho}:{alto}:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}];" for i in range(n))
            filtro = escalas + "".join(f"[v{i}][{i}:a:0]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]"
            orden += ["-filter_complex", filtro, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac"]
        else:
            from raphi.motor.medios import CODECS_AUDIO
            filtro = "".join(f"[{i}:a:0]" for i in range(n)) + f"concat=n={n}:v=0:a=1[a]"
            orden += ["-filter_complex", filtro, "-map", "[a]", *CODECS_AUDIO.get(ext.lstrip("."), ["-c:a", "aac"])]
    return Resultado([_ffmpeg(ctx, orden, destino, total=total)])


@operacion("portada_audio", "Medios", "Poner carátula",
           "Una imagen (JPG o PNG) como carátula de un MP3, M4A o FLAC (la que muestran los reproductores y el móvil).",
           entrada="archivos", lote=False, minimo_entradas=2, extensiones=(".mp3", ".m4a", ".flac") + IMG,
           sufijo="caratula", requiere=REQ,
           palabras=("cover", "carátula", "portada", "album art", "id3", "mp3"))
def portada_audio(ctx):
    audios = [e for e in ctx.entradas if e.suffix.lower() in (".mp3", ".m4a", ".flac")]
    imagenes = [e for e in ctx.entradas if e.suffix.lower() in IMG]
    if not audios or len(imagenes) != 1:
        raise ErrorOperacion("Hace falta una imagen y al menos un audio (MP3, M4A o FLAC).")
    imagen = imagenes[0]
    if ctx.simular:
        return Resultado(plan=[f"{a.name} + {imagen.name} → {ctx.salida(base=a).name}" for a in audios])
    salidas = []
    for i, audio in enumerate(audios):
        ctx.avisar(i / len(audios), audio.name)
        destino = ctx.salida(base=audio)
        orden = ["ffmpeg", "-hide_banner", "-nostdin", "-y", "-i", str(audio), "-i", str(imagen), "-map", "0:a", "-map", "1:v",
                 "-c:a", "copy", "-map_metadata", "0", "-disposition:v:0", "attached_pic",
                 "-metadata:s:v", "title=Album cover", "-metadata:s:v", "comment=Cover (front)"]
        orden += ["-c:v", "mjpeg"] if audio.suffix.lower() != ".flac" else ["-c:v", "copy" if imagen.suffix.lower() in (".jpg", ".jpeg", ".png") else "mjpeg"]
        if audio.suffix.lower() == ".mp3":
            orden += ["-id3v2_version", "3"]
        correr(orden + [str(destino)], timeout=600, mensaje=f"ffmpeg no pudo poner la carátula a {audio.name}")
        salidas.append(destino)
    return Resultado(salidas)


@operacion("dividir_medio", "Medios", "Dividir en partes",
           "Corta un audio o vídeo largo en partes de N minutos, sin recodificar (cada corte, en el fotograma clave más "
           "cercano). Las partes van a una carpeta.",
           entrada="medios", extensiones=AUD + VID, sufijo="partes", requiere=REQ,
           parametros=(Parametro("minutos", "Minutos por parte", "decimal", 10, minimo=0.01),),
           palabras=("split", "partir", "trozos", "segmentos", "cortar"))
def dividir_medio(ctx):
    total = duracion(ctx.entrada)
    segundos = ctx.p("minutos") * 60
    partes = max(1, int(-(-total // segundos))) if total else 0
    carpeta = ctx.carpeta_salida()
    if ctx.simular:
        return Resultado(plan=[f"{partes or '?'} partes de {ctx.p('minutos'):g} min → {carpeta.name}/"])
    plantilla = carpeta / f"{ctx.entrada.stem}_%03d{ctx.entrada.suffix.lower()}"
    correr(["ffmpeg", "-hide_banner", "-nostdin", "-y", "-i", str(ctx.entrada), "-map", "0", "-c", "copy", "-f", "segment",
            "-segment_time", f"{segundos:g}", "-reset_timestamps", "1", str(plantilla)], timeout=7200,
           mensaje="ffmpeg no pudo dividirlo")
    return Resultado([carpeta], {"partes": len(list(carpeta.iterdir()))})

