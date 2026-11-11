"""Las operaciones que llegaron con la rueda ampliada (2026-11-11): las de archivos (ver metadatos, sumas de
verificación, verificar una suma, comprobar un comprimido), las de audio y vídeo (información, subtítulos, volumen,
rotar, unir, carátula, dividir), las de imagen (foto de documento, ICO, medidas listas), la limpieza de metadatos con
mat2 y su comprobación, las descargas (opciones, enlaces, avance en vivo) y los valores actuales de una operación.
Los medios se generan con ffmpeg en cada corrida; nada baja de la red."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from raphi import motor
from raphi.motor.base import ErrorOperacion, actuales, disponible
from raphi.motor.medios import formatos_de, opciones_para

RAIZ = Path(__file__).resolve().parents[1]
hay_ffmpeg = pytest.mark.skipif(not (disponible("ffmpeg") and disponible("ffprobe")), reason="sin ffmpeg")
hay_exiftool = pytest.mark.skipif(not disponible("exiftool"), reason="sin exiftool")


def _ff(*args: str) -> None:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y", *args], check=True, timeout=120)


@pytest.fixture(scope="module")
def medios(tmp_path_factory) -> dict[str, Path]:
    if not disponible("ffmpeg"):
        pytest.skip("sin ffmpeg")
    d = tmp_path_factory.mktemp("medios")
    m = {"mp4": d / "clip.mp4", "srt": d / "clip.srt", "mkv": d / "clip.mkv", "mp3": d / "uno.mp3", "mp3b": d / "dos.mp3",
         "jpg": d / "foto.jpg"}
    _ff("-f", "lavfi", "-i", "testsrc=duration=3:size=320x240:rate=10", "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(m["mp4"]))
    m["srt"].write_text("1\n00:00:00,500 --> 00:00:02,000\nHola desde la rueda\n", encoding="utf-8")
    _ff("-i", str(m["mp4"]), "-i", str(m["srt"]), "-map", "0", "-map", "1", "-c", "copy", "-c:s", "srt",
        "-metadata:s:s:0", "language=spa", str(m["mkv"]))
    for clave, f in (("mp3", 440), ("mp3b", 660)):
        _ff("-f", "lavfi", "-i", f"sine=frequency={f}:duration=2", "-c:a", "libmp3lame", "-q:a", "4", str(m[clave]))
    img = Image.new("RGB", (400, 300), (200, 60, 60))
    exif = Image.Exif()
    exif[0x013B] = "Ana Perez"           # Artist
    exif[0x0131] = "Programa X 1.0"      # Software
    img.save(m["jpg"], "JPEG", exif=exif)
    return m


def _pistas(ruta: Path) -> list[dict]:
    from raphi.motor.multimedia import sondear
    return sondear(ruta).get("streams", [])


# --- audio y vídeo -----------------------------------------------------------------------------------------------


@hay_ffmpeg
def test_info_medio(medios):
    informe = motor.ejecutar("info_medio", [medios["mkv"]])
    assert informe.ok and not informe.archivos
    datos = informe.elementos[0].resultado.datos
    pistas = " ".join(datos["Pistas"].values())
    assert "320×240" in pistas and "Hz" in pistas and "spa" in pistas and datos["Resumen"]["duración"] == "0:00:03"


@hay_ffmpeg
def test_extraer_e_incrustar_subtitulos(medios, tmp_path):
    copia = tmp_path / medios["mkv"].name
    shutil.copy2(medios["mkv"], copia)
    informe = motor.ejecutar("extraer_subtitulos", [copia])
    assert informe.ok, informe.elementos[0].error
    srt = informe.archivos[0]
    assert srt.name == "clip.spa.srt" and "Hola desde la rueda" in srt.read_text(encoding="utf-8")
    sin = motor.ejecutar("extraer_subtitulos", [medios["mp4"]], destino=tmp_path)
    assert not sin.ok and "no tiene pistas" in sin.elementos[0].error
    junto = motor.ejecutar("incrustar_subtitulos", [medios["mp4"], medios["srt"]], {"idioma": "spa"}, destino=tmp_path)
    assert junto.ok, junto.elementos[0].error
    tipos = [s["codec_type"] for s in _pistas(junto.archivos[0])]
    assert "subtitle" in tipos and "video" in tipos and junto.archivos[0].suffix == ".mp4"


@hay_ffmpeg
def test_normalizar_rotar_y_dividir(medios, tmp_path):
    normal = motor.ejecutar("normalizar_audio", [medios["mp3"]], {"nivel": "radio"}, destino=tmp_path)
    assert normal.ok and normal.archivos[0].name == "uno_normalizado.mp3"
    girado = motor.ejecutar("rotar_video", [medios["mp4"]], {"giro": "90"}, destino=tmp_path)
    assert girado.ok, girado.elementos[0].error
    video = next(s for s in _pistas(girado.archivos[0]) if s["codec_type"] == "video")
    assert (video["width"], video["height"]) == (240, 320)
    partes = motor.ejecutar("dividir_medio", [medios["mp3"]], {"minutos": 0.015}, destino=tmp_path)
    assert partes.ok, partes.elementos[0].error
    assert len(list(partes.archivos[0].iterdir())) >= 2


@hay_ffmpeg
def test_unir_y_caratula(medios, tmp_path):
    from raphi.motor.medios import duracion
    unido = motor.ejecutar("unir_medios", [medios["mp3"], medios["mp3b"]], {"nombre": "juntos"}, destino=tmp_path)
    assert unido.ok, unido.elementos[0].error
    assert unido.archivos[0].name == "juntos.mp3" and abs(duracion(unido.archivos[0]) - 4) < 0.5
    con = motor.ejecutar("portada_audio", [medios["mp3"], medios["jpg"]], destino=tmp_path)
    assert con.ok, con.elementos[0].error
    assert any((s.get("disposition") or {}).get("attached_pic") for s in _pistas(con.archivos[0]))
    with pytest.raises(ErrorOperacion):
        motor.ejecutar("portada_audio", [medios["mp3"]])            # necesita dos entradas


@hay_ffmpeg
def test_la_rueda_ofrece_lo_nuevo(medios):
    assert {"transcribir", "rotar_video", "extraer_subtitulos", "info_medio", "suma_verificacion"} <= {f["operacion"] for f in formatos_de(medios["mp4"])}
    assert [f["a"] for f in formatos_de(medios["mp3"]) if f["operacion"] == "transcribir"] == ["srt", "txt"]
    assert opciones_para([medios["mp4"], medios["srt"]])[0]["operacion"] == "incrustar_subtitulos"
    assert opciones_para([medios["mp3"], medios["mp3b"], medios["jpg"]])[0]["operacion"] == "portada_audio"
    assert opciones_para([medios["mp3"], medios["mp3b"]])[0]["operacion"] == "unir_medios"


# --- archivos ----------------------------------------------------------------------------------------------------


def test_suma_y_verificacion(tmp_path):
    archivo = tmp_path / "datos.bin"
    archivo.write_bytes(b"raphi" * 1000)
    informe = motor.ejecutar("suma_verificacion", [archivo], {"algoritmo": "todas"})
    assert informe.ok
    sha = hashlib.sha256(archivo.read_bytes()).hexdigest()
    datos = informe.elementos[0].resultado.datos
    assert datos["SHA256"] == sha and datos["MD5"] == hashlib.md5(archivo.read_bytes()).hexdigest()
    lado = tmp_path / "datos.bin.sha256"
    assert lado.read_text() == f"{sha}  datos.bin\n" and len(informe.archivos) == 4
    bien = motor.ejecutar("verificar_suma", [lado])
    assert bien.ok and bien.elementos[0].resultado.datos == {"datos.bin": "correcto (SHA256)"}
    bsd = tmp_path / "bsd.sha256"
    bsd.write_text(f"SHA256 (datos.bin) = {sha}\n")
    assert motor.ejecutar("verificar_suma", [bsd]).ok
    archivo.write_bytes(b"cambiado")
    mal = motor.ejecutar("verificar_suma", [lado])
    assert not mal.ok and "NO COINCIDE" in mal.elementos[0].error


@pytest.mark.skipif(not disponible("7z"), reason="sin 7z")
def test_verificar_comprimido(tmp_path):
    zip_ = tmp_path / "a.zip"
    with zipfile.ZipFile(zip_, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("hola.txt", "hola " * 2000)
    sano = motor.ejecutar("verificar_comprimido", [zip_])
    assert sano.ok and sano.elementos[0].resultado.datos["archivos"] == "1"
    roto = tmp_path / "roto.zip"
    datos = bytearray(zip_.read_bytes())
    datos[60:80] = b"\x00" * 20
    roto.write_bytes(bytes(datos))
    assert not motor.ejecutar("verificar_comprimido", [roto]).ok


@hay_exiftool
def test_ver_y_quitar_metadatos(medios, tmp_path):
    visto = motor.ejecutar("ver_metadatos", [medios["jpg"]])
    assert visto.ok and not visto.archivos
    datos = visto.elementos[0].resultado.datos
    assert any("Ana Perez" in v for v in datos["Lo que te delata"].values())
    limpio = motor.ejecutar("quitar_metadatos_archivo", [medios["jpg"]], destino=tmp_path)
    assert limpio.ok, limpio.elementos[0].error
    resumen = limpio.elementos[0].resultado.datos
    assert resumen["campos antes"] > resumen["campos después"]
    from raphi.motor.archivos import leer_metadatos
    texto = json.dumps(leer_metadatos(limpio.archivos[0]), ensure_ascii=False)
    assert "Ana Perez" not in texto and "Programa X" not in texto
    assert "Ana Perez" in json.dumps(leer_metadatos(medios["jpg"]), ensure_ascii=False)   # el original, intacto


@hay_exiftool
def test_quitar_metadatos_con_exiftool_a_pedido(medios, tmp_path):
    limpio = motor.ejecutar("quitar_metadatos_archivo", [medios["jpg"]], {"motor": "exiftool"}, destino=tmp_path)
    assert limpio.ok and limpio.elementos[0].resultado.datos["motor"] == "exiftool"


# --- imágenes ----------------------------------------------------------------------------------------------------


def test_foto_documento_ico_y_medidas(medios, tmp_path):
    foto = motor.ejecutar("foto_documento", [medios["jpg"]], {"medida": "35x45"}, destino=tmp_path)
    assert foto.ok
    with Image.open(foto.archivos[0]) as img:
        assert img.size == (413, 531) and round(img.info["dpi"][0]) == 300
    ico = motor.ejecutar("convertir_imagen", [medios["jpg"]], {"formato": "ico"}, destino=tmp_path)
    assert ico.ok and ico.archivos[0].suffix == ".ico"
    with Image.open(ico.archivos[0]) as img:
        assert (256, 256) in img.info.get("sizes", {(256, 256)}) or img.size == (256, 256)
    medida = motor.ejecutar("redimensionar_imagen", [medios["jpg"]], {"medida": "1080x1080"}, destino=tmp_path)
    with Image.open(medida.archivos[0]) as img:
        assert img.size == (1080, 810)                     # cabe en 1080×1080 sin deformar (400×300 agrandada)


# --- descargas (sin red) -----------------------------------------------------------------------------------------


def test_opciones_de_un_enlace_y_simulacion():
    from raphi.motor.audio_video import opciones_para_enlaces
    opciones = opciones_para_enlaces(["https://example.org/v"])
    if not opciones:
        pytest.skip("sin yt-dlp")
    etiquetas = [o["etiqueta"] for o in opciones]
    assert etiquetas[:3] == ["Mejor", "4K", "1080p"] and "MP3" in etiquetas
    assert all(o["enlace"] == "url" and o["operacion"] == "descargar" for o in opciones)
    tramo = next(o for o in opciones if o["etiqueta"] == "Un tramo…")
    assert tramo["pide"] and tramo["fijos"] == []
    assert len({o.get("clave") or json.dumps(o["params"], sort_keys=True) for o in opciones}) == len(opciones)
    plan = motor.ejecutar("descargar", [], {"url": "https://example.org/v", "cookies": "firefox", "lista": "solo_video",
                                            "elementos": "1:3"}, simular=True)
    assert plan.ok and "example.org" in plan.elementos[0].resultado.plan[0]


def test_correr_en_vivo_lee_cada_linea():
    from raphi.motor.utiles import correr_en_vivo
    lineas = []
    correr_en_vivo([sys.executable, "-c", "import sys; [print(f'[download]  {p}.0% of 1MiB', end='\\r', flush=True) for p in (10, 50, 100)]"],
                   lineas.append, timeout=30)
    assert lineas == ["[download]  10.0% of 1MiB", "[download]  50.0% of 1MiB", "[download]  100.0% of 1MiB"]
    with pytest.raises(ErrorOperacion, match="falló"):
        correr_en_vivo([sys.executable, "-c", "print('algo'); raise SystemExit(3)"], lambda _: None, mensaje="falló")


# --- valores actuales --------------------------------------------------------------------------------------------


def test_valores_actuales_de_un_pdf(tmp_path):
    import pikepdf
    ruta = tmp_path / "a.pdf"
    pdf = pikepdf.new()
    pdf.add_blank_page()
    pdf.docinfo["/Title"] = "Informe anual"
    pdf.docinfo["/Author"] = "Despacho"
    pdf.save(ruta)
    assert actuales("metadatos", ruta) == {"titulo": "Informe anual", "autor": "Despacho"}
    assert actuales("rotar", ruta) == {} and actuales("metadatos", tmp_path / "no.pdf") == {}
    assert motor.obtener("metadatos").ficha()["con_actuales"] and not motor.obtener("rotar").ficha()["con_actuales"]
    r = subprocess.run([sys.executable, str(RAIZ / "escritorio" / "studio" / "corredor.py"), "actuales", "metadatos", str(ruta)],
                       capture_output=True, text=True, timeout=60)
    assert json.loads(r.stdout) == {"titulo": "Informe anual", "autor": "Despacho"}
