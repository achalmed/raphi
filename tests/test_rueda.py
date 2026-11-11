"""Lo que la rueda de Muyu (repo `muyu`) usa del motor de Raphi: lo nuevo del motor para ella («Poner fondo», el recorte
por rectángulo, lo que se ofrece para varios archivos) y los pedidos `rueda` y `vista` del corredor, que son su API de
proceso. La rueda misma (anillos, ventana, instalador) se prueba en Muyu."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from raphi import motor
from raphi.motor.base import ErrorOperacion, Parametro
from raphi.motor.medios import formatos_de, opciones_para

RAIZ = Path(__file__).resolve().parents[1]
CORREDOR = RAIZ / "escritorio" / "studio" / "corredor.py"


@pytest.fixture
def foto(tmp_path) -> Path:
    ruta = tmp_path / "Página 001.png"            # con espacio y tilde: así llegan de Dolphin
    Image.new("RGB", (400, 300), "white").save(ruta)
    return ruta


# --- el motor ----------------------------------------------------------------------------------------------------


def test_poner_fondo_simula_y_aplica(foto):
    simulado = motor.ejecutar("fondo_imagen", [foto], {"proporcion": "1:1"}, simular=True)
    assert simulado.ok and "lienzo 1:1" in simulado.elementos[0].resultado.plan[0]
    assert sorted(p.name for p in foto.parent.iterdir()) == [foto.name]           # simular no escribe
    informe = motor.ejecutar("fondo_imagen", [foto], {"proporcion": "1:1", "color2": "#EB5757", "margen": 10})
    assert informe.ok
    salida = informe.archivos[0]
    assert salida.name == "Página 001_con_fondo.png"
    with Image.open(salida) as img:
        assert img.size[0] == img.size[1] == 400 + 2 * 30                         # 10 % del lado menor (300) a cada lado
        assert img.getpixel((0, 0))[:3] != (255, 255, 255)                        # la esquina es fondo, no la imagen


def test_poner_fondo_rechaza_un_color_malo(foto):
    informe = motor.ejecutar("fondo_imagen", [foto], {"color": "naranjoso"})
    assert not informe.ok and "Color no válido" in informe.elementos[0].error


def test_el_rectangulo_manda_sobre_la_proporcion(foto):
    informe = motor.ejecutar("recortar_imagen", [foto], {"proporcion": "1:1", "caja": "10,20,120,80"})
    assert informe.ok
    with Image.open(informe.archivos[0]) as img:
        assert img.size == (120, 80)
    fuera = motor.ejecutar("recortar_imagen", [foto], {"caja": "300,200,200,200"})
    assert not fuera.ok and "se sale" in fuera.elementos[0].error


def test_la_vista_de_un_parametro_es_conocida():
    assert Parametro("caja", "Caja", vista="caja").ficha()["vista"] == "caja"
    with pytest.raises(ValueError):
        Parametro("x", "X", vista="lienzo")
    recortar = {p["clave"]: p for p in motor.obtener("recortar_imagen").ficha()["parametros"]}
    assert recortar["caja"]["vista"] == "caja"


def test_opciones_para_varios_archivos(tmp_path):
    jpg, png, pdf1, pdf2 = (tmp_path / n for n in ("a.jpg", "b.png", "c.pdf", "d.pdf"))
    imagenes = opciones_para([jpg, png])
    destinos = {o["a"] for o in imagenes if o["a"]}
    assert "pdf" in destinos and "jpg" not in destinos and "png" not in destinos  # solo lo común a los dos
    juntas = {o["operacion"]: o["junta"] for o in imagenes}
    assert juntas["imagenes_a_pdf"] and juntas["comprimir_archivos"] and not juntas["convertir_imagen"]
    pdfs = [o["operacion"] for o in opciones_para([pdf1, pdf2])]
    assert pdfs[:2] == ["comparar", "unir"]
    assert "unir" not in [o["operacion"] for o in opciones_para([pdf1])]
    assert not any(o["junta"] for o in opciones_para([pdf1]))
    assert opciones_para([]) == []


def test_formatos_de_una_imagen_trae_poner_fondo(foto):
    assert "fondo_imagen" in [f["operacion"] for f in formatos_de(foto) if not f["a"]]


# --- el corredor -------------------------------------------------------------------------------------------------


def _corredor(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(CORREDOR), *args], capture_output=True, text=True, timeout=120, cwd=RAIZ)


def test_corredor_rueda(foto):
    r = _corredor("rueda", str(foto))
    assert r.returncode == 0, r.stderr
    datos = json.loads(r.stdout)
    assert datos["version"]
    fondo = next(o for o in datos["opciones"] if o["operacion"] == "fondo_imagen")
    assert fondo["parametros"] and fondo["categoria"] == "Medios" and fondo["junta"] is False and fondo["faltan"] == []


def test_corredor_vista_no_escribe_junto_al_original(foto, tmp_path):
    cache = tmp_path / "cache"
    trabajo = tmp_path / "t.json"
    trabajo.write_text(json.dumps({"operacion": "fondo_imagen", "archivos": [str(foto)], "params": {"proporcion": "9:16"},
                                   "destino": str(cache), "reducir": 200}))
    r = _corredor("vista", str(trabajo))
    assert r.returncode == 0, r.stdout + r.stderr
    datos = json.loads(next(l for l in r.stdout.splitlines() if l.startswith("## vista "))[9:])
    assert datos["tipo"] == "imagen"
    with Image.open(datos["archivo"]) as img:
        assert max(img.size) < 400 and abs(img.size[0] / img.size[1] - 9 / 16) < 0.02   # reducida, y con su lienzo
    assert sorted(p.name for p in foto.parent.iterdir()) == sorted([foto.name, "cache", "t.json"])
    assert [p.name for p in cache.iterdir()] == [Path(datos["archivo"]).name]          # la copia y su salida, borradas


def test_corredor_vista_de_un_pdf_y_sus_errores(corpus, tmp_path):
    cache = tmp_path / "cache"
    trabajo = tmp_path / "t.json"
    trabajo.write_text(json.dumps({"operacion": "marca_agua", "archivos": [str(corpus["texto"])], "params": {},
                                   "destino": str(cache)}))
    r = _corredor("vista", str(trabajo))
    assert r.returncode == 1 and "raphi: Falta «Texto»." in r.stdout and "Traceback" not in r.stderr
    assert list(cache.iterdir()) == []
    trabajo.write_text(json.dumps({"operacion": "marca_agua", "archivos": [str(corpus["texto"])],
                                   "params": {"texto": "COPIA"}, "destino": str(cache)}))
    r = _corredor("vista", str(trabajo))
    assert r.returncode == 0, r.stdout + r.stderr
    datos = json.loads(next(l for l in r.stdout.splitlines() if l.startswith("## vista "))[9:])
    assert datos["tipo"] == "pdf" and datos["archivo"].endswith(".pdf") and datos["nombre"].endswith(".pdf") and datos["tamano"] > 0
    import pikepdf
    with pikepdf.open(datos["archivo"]) as pdf:          # el PDF entero, para el visor (zoom, páginas, búsqueda)
        assert len(pdf.pages) >= 1


def test_errores_de_operacion_siguen_siendo_por_archivo(foto, tmp_path):
    roto = tmp_path / "roto.png"
    roto.write_bytes(b"no soy una imagen")
    informe = motor.ejecutar("fondo_imagen", [roto, foto], {})
    assert [e.ok for e in informe.elementos] == [False, True]
    with pytest.raises(ErrorOperacion):
        motor.ejecutar("fondo_imagen", [foto], {"margen": 500})
