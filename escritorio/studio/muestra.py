#!/usr/bin/env python3
"""escritorio/studio/muestra.py — los archivos de muestra para las pruebas y las capturas de Raphi Studio.

Nunca los archivos del usuario. En una carpeta temporal escribe, con el Python del sistema y sin PyMuPDF ni Pillow
(`docs/rediseno.md` S10): un PDF de dos páginas con texto, escrito a mano; un PNG diminuto (zlib y struct); unos
subtítulos SRT; un Markdown; un texto; un WAV de dos segundos (con `wave`, sin ffmpeg); y una carpeta con dos fotos de
juguete. Devuelve las rutas y las variables de
entorno con las que el studio ve la muestra (HOME, configuración, caché y datos temporales: ninguna ruta de la
máquina en pantalla).

    from muestra import crear
    m = crear(Path(carpeta))      # m.archivos: {pdf, otro, png, srt, md, txt, wav, carpeta}; m.entorno
"""
from __future__ import annotations

import math
import struct
import wave
import zlib
from dataclasses import dataclass, field
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[1]


@dataclass
class Muestra:
    raiz: Path
    archivos: dict = field(default_factory=dict)
    entorno: dict = field(default_factory=dict)


def pdf(ruta: Path, textos: list[str]) -> Path:
    """Un PDF válido (pikepdf lo abre) escrito a mano: una página por texto, con Helvetica."""
    objetos: list[bytes] = []

    def objeto(cuerpo: bytes) -> int:
        objetos.append(cuerpo)
        return len(objetos)

    fuente = objeto(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    paginas_ids = []
    kids_marcador = objeto(b"")                      # /Pages, se rellena después
    for texto in textos:
        contenido = f"BT /F1 18 Tf 72 740 Td ({texto}) Tj ET".encode("latin-1", "replace")
        flujo = objeto(b"<< /Length " + str(len(contenido)).encode() + b" >>\nstream\n" + contenido + b"\nendstream")
        pagina = objeto(f"<< /Type /Page /Parent {kids_marcador} 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 {fuente} 0 R >> >> /Contents {flujo} 0 R >>".encode())
        paginas_ids.append(pagina)
    objetos[kids_marcador - 1] = f"<< /Type /Pages /Kids [{' '.join(f'{p} 0 R' for p in paginas_ids)}] /Count {len(paginas_ids)} >>".encode()
    catalogo = objeto(f"<< /Type /Catalog /Pages {kids_marcador} 0 R >>".encode())
    salida = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    posiciones = []
    for i, cuerpo in enumerate(objetos, 1):
        posiciones.append(len(salida))
        salida += f"{i} 0 obj\n".encode() + cuerpo + b"\nendobj\n"
    xref = len(salida)
    salida += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    for p in posiciones:
        salida += f"{p:010d} 00000 n \n".encode()
    salida += f"trailer\n<< /Size {len(objetos) + 1} /Root {catalogo} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    ruta.write_bytes(bytes(salida))
    return ruta


def png(ruta: Path, ancho: int = 64, alto: int = 48, color=(46, 84, 150)) -> Path:
    """Un PNG RGB de un solo color, con una franja clara (sin Pillow)."""
    def trozo(tipo: bytes, datos: bytes) -> bytes:
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", zlib.crc32(tipo + datos) & 0xFFFFFFFF)
    filas = b""
    for y in range(alto):
        c = (235, 235, 235) if alto // 3 <= y < alto // 2 else color
        filas += b"\x00" + bytes(c) * ancho
    datos = b"\x89PNG\r\n\x1a\n" + trozo(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0)) + trozo(b"IDAT", zlib.compress(filas, 9)) + trozo(b"IEND", b"")
    ruta.write_bytes(datos)
    return ruta


def wav(ruta: Path, segundos: float = 2.0, hz: int = 440, tasa: int = 8000) -> Path:
    """Un WAV mono de un tono (la vista previa de audio y las herramientas de audio, sin ffmpeg para crearlo)."""
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(tasa)
        w.writeframes(b"".join(struct.pack("<h", int(6000 * math.sin(2 * math.pi * hz * i / tasa))) for i in range(int(segundos * tasa))))
    return ruta


def crear(raiz: Path) -> Muestra:
    raiz = Path(raiz)
    raiz.mkdir(parents=True, exist_ok=True)
    docs = raiz / "documentos"
    docs.mkdir(exist_ok=True)
    archivos = {
        "pdf": pdf(docs / "oficio.pdf", ["Oficio de prueba, pagina 1", "Oficio de prueba, pagina 2"]),
        "otro": pdf(docs / "anexo.pdf", ["Anexo de prueba"]),
        "png": png(docs / "foto.png"),
        "srt": docs / "entrevista.srt",
        "md": docs / "notas.md",
        "txt": docs / "nota.txt",
    }
    medios = raiz / "medios"
    medios.mkdir(exist_ok=True)
    archivos["wav"] = wav(medios / "entrevista.wav")
    archivos["srt"].write_text("1\n00:00:01,000 --> 00:00:02,500\nHola, buenas tardes.\n\n2\n00:00:03,000 --> 00:00:04,000\nGracias por venir.\n", encoding="utf-8")
    archivos["md"].write_text("# Notas de la reunión\n\n- Acción: enviar el oficio.\n- Número: 42.\n", encoding="utf-8")
    archivos["txt"].write_text("Una nota de oficina con tildes: acción, número, señal.\n", encoding="utf-8")
    fotos = raiz / "fotos"
    fotos.mkdir(exist_ok=True)
    png(fotos / "IMG_0001.png", color=(158, 42, 43))
    png(fotos / "IMG_0002.png", color=(58, 125, 68))
    archivos["carpeta"] = fotos
    hogar = raiz / "hogar"
    for sub in (".config", ".cache", ".local/share", ".local/state"):
        (hogar / sub).mkdir(parents=True, exist_ok=True)
    entorno = {"HOME": str(hogar), "XDG_CONFIG_HOME": str(hogar / ".config"), "XDG_CACHE_HOME": str(hogar / ".cache"),
               "XDG_DATA_HOME": str(hogar / ".local" / "share"), "XDG_STATE_HOME": str(hogar / ".local" / "state"), "RAPHI_DIR": str(hogar / ".local" / "share" / "raphi"),
               "LC_ALL": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}
    return Muestra(raiz=raiz, archivos={k: Path(v) for k, v in archivos.items()}, entorno=entorno)


if __name__ == "__main__":
    import sys
    m = crear(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd() / "muestra-raphi")
    print(m.raiz)
