#!/usr/bin/env python3
"""hls_tramo.py — baja solo los segmentos HLS de un tramo de una transmisión en vivo (YouTube y otros sitios HLS).

Por qué existe: en un directo, `--download-sections` de yt-dlp falla («This format cannot be partially downloaded»)
y ffmpeg no puede saltar dentro de la lista HLS. Pero la lista de un directo trae la ventana de rebobinado
(en YouTube, hasta 12 h) con la hora real de cada segmento (`#EXT-X-PROGRAM-DATE-TIME`), así que un tramo se puede
pedir de tres maneras y bajar solo sus segmentos:

    1:02:00-1:05:30      desde el comienzo de la ventana (en YouTube, el comienzo de la emisión)
    -16:30--14:08        hacia atrás desde el vivo, en el momento de la orden
    @11:20-@11:22:35     por la hora del reloj (la hora local; la del rótulo del canal, si lo trae)

Lo que se aprendió con YouTube (2026-11-19): la lista caduca al rato y, tras unos once segmentos bajados con la
misma lista, el servidor responde 403; en paralelo, aún antes. Por eso los segmentos se bajan uno tras otro y, ante
un 403 o cualquier fallo, se pide una lista nueva a yt-dlp y se sigue por el número de secuencia del segmento.

Uso (lo llama lib/clipper_hls.sh):
    hls_tramo.py --formato SEL --inicio X --fin Y --salida tramo.ts [--yt-dlp-arg A ...] URL
Escribe en --salida los segmentos pegados (MPEG-TS, o fMP4 tras su init) y, en la salida estándar, una línea
`desplazamiento=<s> duracion=<s> hora=<HH:MM:SS>`: el -ss del tramo dentro del archivo, su duración y la hora real del
inicio. El avance va a la salida de errores.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

AGENTE = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
RENOVACIONES_MAX = 60      # listas nuevas que se piden como mucho en un tramo


class ErrorTramo(Exception):
    pass


@dataclass
class Segmento:
    secuencia: int
    inicio: float           # segundos desde el primer segmento de la ventana
    duracion: float
    hora: float | None      # hora real (época) del comienzo, si la lista la trae
    url: str


@dataclass
class Lista:
    segmentos: list[Segmento]
    mapa: str | None        # init de fMP4 (#EXT-X-MAP), si lo hay
    vivo: bool              # sin #EXT-X-ENDLIST

    def por_secuencia(self) -> dict[int, Segmento]:
        return {s.secuencia: s for s in self.segmentos}


# --- Tiempos -----------------------------------------------------------------------------------------------------
_T = r"\d+(?::\d{1,2}){0,2}(?:\.\d+)?"
_EXTREMO = rf"(?:@{_T}|-?{_T})"
RANGO = re.compile(rf"^\s*({_EXTREMO})\s*(?:\.\.|\s+a\s+|-)\s*({_EXTREMO})\s*$")


def segundos(texto: str) -> float:
    """«1:02:03», «2:03», «45» o «45.5» → segundos."""
    partes = [float(p) for p in texto.split(":")]
    total = 0.0
    for p in partes:
        total = total * 60 + p
    return total


def leer_extremo(texto: str) -> tuple[str, float]:
    """Devuelve (clase, valor): «abs» (desde el comienzo), «vivo» (segundos hacia atrás) o «reloj» (segundos del día)."""
    if texto.startswith("@"):
        hora = texto[1:]
        if hora.count(":") == 1:          # en la hora, «11:20» es HH:MM, no MM:SS
            hora += ":00"
        return "reloj", segundos(hora)
    if texto.startswith("-"):
        return "vivo", segundos(texto[1:])
    return "abs", segundos(texto)


def leer_rango(texto: str) -> tuple[tuple[str, float], tuple[str, float]]:
    m = RANGO.match(texto)
    if not m:
        raise ErrorTramo(f"tramo no válido: {texto!r} (ej.: 1:02:00-1:05:30, -16:30--14:08, @11:20-@11:22:35)")
    a, b = leer_extremo(m[1]), leer_extremo(m[2])
    if a[0] != b[0]:
        raise ErrorTramo("los dos extremos del tramo deben ser de la misma clase (los dos desde el comienzo, "
                         "los dos desde el vivo o los dos por la hora)")
    return a, b


def a_epoca_del_reloj(segundos_del_dia: float, referencia: float) -> float:
    """La hora local HH:MM:SS más reciente que no pase de `referencia` (+5 min de holgura) → época."""
    ref = dt.datetime.fromtimestamp(referencia).astimezone()
    medianoche = ref.replace(hour=0, minute=0, second=0, microsecond=0)
    t = medianoche.timestamp() + segundos_del_dia
    if t > referencia + 300:          # p. ej. pedir 23:50 pasada la medianoche: es la de ayer
        t -= 86400
    return t


# --- Red ---------------------------------------------------------------------------------------------------------
def pedir(url: str, timeout: float = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def url_de_la_lista(enlace: str, formato: str, extra: list[str]) -> str:
    orden = ["yt-dlp", "--no-warnings", "--no-playlist", "-g", "-f", formato, *extra, "--", enlace]
    r = subprocess.run(orden, capture_output=True, text=True, timeout=120)
    urls = [l for l in r.stdout.splitlines() if l.startswith("http")]
    if not urls:
        raise ErrorTramo("yt-dlp no dio la lista HLS del directo: " + (r.stderr.strip().splitlines() or ["?"])[-1])
    return urls[0]


def leer_lista(texto: str, base: str) -> Lista:
    """Lee una lista HLS de medios. Si es maestra, el que llama debe elegir la variante (aquí se toma la de mayor
    ancho de banda)."""
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    if any(l.startswith("#EXT-X-STREAM-INF") for l in lineas):
        mejor, bw = None, -1
        for i, l in enumerate(lineas):
            if l.startswith("#EXT-X-STREAM-INF"):
                m = re.search(r"BANDWIDTH=(\d+)", l)
                if m and int(m[1]) > bw and i + 1 < len(lineas):
                    mejor, bw = urllib.parse.urljoin(base, lineas[i + 1]), int(m[1])
        if not mejor:
            raise ErrorTramo("lista maestra sin variantes")
        return leer_lista(pedir(mejor).decode("utf-8", "replace"), mejor)
    secuencia, inicio, hora, dur = 0, 0.0, None, None
    mapa, vivo = None, True
    segs: list[Segmento] = []
    for l in lineas:
        if l.startswith("#EXT-X-MEDIA-SEQUENCE:"):
            secuencia = int(l.split(":", 1)[1])
        elif l.startswith("#EXT-X-PROGRAM-DATE-TIME:"):
            valor = l.split(":", 1)[1].replace("Z", "+00:00")
            hora = dt.datetime.fromisoformat(valor).timestamp()
        elif l.startswith("#EXT-X-MAP:"):
            m = re.search(r'URI="([^"]+)"', l)
            mapa = urllib.parse.urljoin(base, m[1]) if m else None
        elif l.startswith("#EXTINF:"):
            dur = float(l.split(":", 1)[1].split(",")[0])
        elif l.startswith("#EXT-X-ENDLIST"):
            vivo = False
        elif not l.startswith("#") and dur is not None:
            segs.append(Segmento(secuencia, inicio, dur, hora, urllib.parse.urljoin(base, l)))
            secuencia += 1
            inicio += dur
            hora = hora + dur if hora is not None else None
            dur = None
    if not segs:
        raise ErrorTramo("la lista HLS no trae segmentos")
    return Lista(segs, mapa, vivo)


# --- El tramo ----------------------------------------------------------------------------------------------------
def limites(lista: Lista, a: tuple[str, float], b: tuple[str, float], ahora: float) -> tuple[float, float]:
    """Traduce el tramo a segundos desde el primer segmento de la ventana."""
    clase = a[0]
    ultimo = lista.segmentos[-1]
    fin_ventana = ultimo.inicio + ultimo.duracion
    if clase == "abs":
        # En YouTube la secuencia 0 es el comienzo de la emisión; si la ventana ya no la tiene, se descuenta
        primero = lista.segmentos[0]
        corrimiento = primero.secuencia * primero.duracion
        ini, fin = a[1] - corrimiento, b[1] - corrimiento
    elif clase == "vivo":
        ini, fin = fin_ventana - a[1], fin_ventana - b[1]
    else:
        primero = lista.segmentos[0]
        if primero.hora is None:
            raise ErrorTramo("esta transmisión no trae la hora de sus segmentos: usa el tramo desde el vivo (-MM:SS)")
        ini = a_epoca_del_reloj(a[1], ahora) - primero.hora
        fin = a_epoca_del_reloj(b[1], ahora) - primero.hora
        if fin <= ini:
            fin += 86400
    if fin <= ini:
        raise ErrorTramo("el FIN del tramo debe ser posterior al INICIO")
    if ini < 0 or fin > fin_ventana + 1:
        raise ErrorTramo(f"el tramo cae fuera de la ventana del directo (hay {fin_ventana / 60:.0f} min hacia atrás)")
    return ini, fin


def bajar(enlace: str, formato: str, extra: list[str], a, b, salida: str) -> str:
    url = url_de_la_lista(enlace, formato, extra)
    lista = leer_lista(pedir(url).decode("utf-8", "replace"), url)
    ini, fin = limites(lista, a, b, time.time())
    dentro = [i for i, s in enumerate(lista.segmentos) if s.inicio + s.duracion > ini and s.inicio < fin]
    # Un segmento de margen a cada lado: el video de un segmento suele durar algo menos que su #EXTINF y, sin
    # margen, al tramo le faltarían uno o dos segundos de imagen al final (lo vio la verificación el 2026-11-19)
    elegidos = lista.segmentos[max(0, dentro[0] - 1):dentro[-1] + 2]
    pendientes = [s.secuencia for s in elegidos]
    primero = elegidos[0]
    datos: dict[int, bytes] = {}
    renovaciones = 0
    por_sec = lista.por_secuencia()
    while pendientes:
        sec = pendientes[0]
        seg = por_sec.get(sec)
        try:
            if seg is None:
                raise ErrorTramo(f"el segmento {sec} ya salió de la ventana del directo")
            datos[sec] = pedir(seg.url)
            pendientes.pop(0)
            print(f"[tramo] {len(datos)}/{len(elegidos)} segmentos", file=sys.stderr, flush=True)
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            renovaciones += 1
            if renovaciones > RENOVACIONES_MAX:
                raise ErrorTramo(f"el servidor sigue rechazando los segmentos ({e})") from e
            print(f"[tramo] lista renovada ({e})", file=sys.stderr, flush=True)
            url = url_de_la_lista(enlace, formato, extra)
            lista = leer_lista(pedir(url).decode("utf-8", "replace"), url)
            por_sec = lista.por_secuencia()
    with open(salida, "wb") as f:
        if lista.mapa:
            f.write(pedir(lista.mapa))
        for s in elegidos:
            f.write(datos[s.secuencia])
    hora = dt.datetime.fromtimestamp(primero.hora + (ini - primero.inicio)).strftime("%H:%M:%S") if primero.hora else ""
    return f"desplazamiento={ini - primero.inicio:.3f} duracion={fin - ini:.3f} hora={hora}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--formato", default="b[protocol^=m3u8]")
    ap.add_argument("--inicio", required=True)
    ap.add_argument("--fin", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--yt-dlp-arg", action="append", default=[], dest="extra")
    ap.add_argument("enlace")
    o = ap.parse_args(argv)
    try:
        a, b = leer_rango(f"{o.inicio}..{o.fin}")
        print(bajar(o.enlace, o.formato, o.extra, a, b, o.salida))
    except ErrorTramo as e:
        print(f"[tramo] {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
