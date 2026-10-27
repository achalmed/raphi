"""El corpus de las pruebas, generado en cada corrida (nada binario en el repo): PDF de texto, largo, escaneado,
cifrado y dañado; imágenes, audio, video, subtítulos y un documento de oficina."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


def _pdf_texto(ruta: Path, paginas: int = 3, prefijo: str = "Página") -> Path:
    import pymupdf
    doc = pymupdf.open()
    for i in range(paginas):
        p = doc.new_page(width=595, height=842)
        p.insert_text((72, 100), f"{prefijo} {i + 1} de prueba con tildes: acción, número, señal.", fontsize=14)
        p.insert_text((72, 140), "Lorem ipsum dolor sit amet " * 3, fontsize=10)
    doc.save(ruta)
    doc.close()
    return ruta


@pytest.fixture(scope="session")
def corpus(tmp_path_factory) -> dict[str, Path]:
    import pymupdf
    from PIL import Image, ImageDraw
    d = tmp_path_factory.mktemp("corpus")
    c: dict[str, Path] = {}
    c["texto"] = _pdf_texto(d / "texto.pdf")
    c["otro"] = _pdf_texto(d / "otro.pdf", 2, "Hoja")
    c["largo"] = _pdf_texto(d / "largo.pdf", 300)
    # Un «escaneo»: una página que es solo una imagen con texto dibujado.
    img = Image.new("RGB", (1240, 1754), "white")
    dib = ImageDraw.Draw(img)
    from PIL import ImageFont
    try:
        fuente = ImageFont.truetype("DejaVuSans.ttf", 48)
    except OSError:
        fuente = ImageFont.load_default(size=48)
    for i, linea in enumerate(("OFICIO MULTIPLE", "Asunto: prueba de reconocimiento", "Lima, octubre de 2026")):
        dib.text((120, 200 + 90 * i), linea, fill="black", font=fuente)
    img.save(d / "escaneo.png")
    doc = pymupdf.open()
    p = doc.new_page(width=595, height=842)
    p.insert_image(p.rect, filename=str(d / "escaneo.png"))
    doc.save(d / "escaneo.pdf")
    doc.close()
    c["escaneo"] = d / "escaneo.pdf"
    c["png"] = d / "escaneo.png"
    Image.new("RGB", (800, 600), (30, 120, 200)).save(d / "foto.jpg", quality=95)
    c["jpg"] = d / "foto.jpg"
    # Cifrado y dañado
    import pikepdf
    with pikepdf.open(c["texto"]) as pdf:
        pdf.save(d / "cifrado.pdf", encryption=pikepdf.Encryption(user="clave123", owner="clave123", R=6))
    c["cifrado"] = d / "cifrado.pdf"
    datos = c["texto"].read_bytes()
    (d / "danado.pdf").write_bytes(datos[: len(datos) - 400])
    c["danado"] = d / "danado.pdf"
    (d / "nopdf.pdf").write_text("esto no es un PDF")
    c["nopdf"] = d / "nopdf.pdf"
    (d / "subs.srt").write_text("1\n00:00:01,000 --> 00:00:02,500\nHola\n\n2\n00:00:03,000 --> 00:00:04,000\nMundo\n",
                                encoding="utf-8")
    c["srt"] = d / "subs.srt"
    (d / "nota.txt").write_text("Una nota de oficina con tildes: acción.\n", encoding="utf-8")
    c["txt"] = d / "nota.txt"
    if shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
                        str(d / "tono.wav")], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=duration=2:size=320x240:rate=15",
                        "-f", "lavfi", "-i", "sine=duration=2", "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", str(d / "video.mp4")], check=True)
        c["wav"], c["mp4"] = d / "tono.wav", d / "video.mp4"
    return c


@pytest.fixture
def salida(tmp_path) -> Path:
    return tmp_path / "salida"
