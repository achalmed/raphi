"""Raphi Studio (escritorio/studio, 2026-10-31): la ventana nativa de la familia de los studios, armada de las fichas.

Necesita `gui_comun` (el paquete gui-comun, instalado o el repo del espacio de trabajo): sin él, estas pruebas se
saltan y `raphi` abre la ventana web.
"""
from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from escritorio.studio import hay_gui_comun  # noqa: E402

pytestmark = pytest.mark.skipif(not hay_gui_comun(), reason="sin gui_comun (Raphi fuera del espacio de trabajo)")


@pytest.fixture(scope="module")
def app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    QApplication.setOrganizationName("raphi-pruebas")
    QApplication.setApplicationName("raphi-studio-pruebas")
    return QApplication.instance() or QApplication([])


@pytest.fixture(scope="module")
def ventana(app, tmp_path_factory):
    os.environ["XDG_CONFIG_HOME"] = str(tmp_path_factory.mktemp("config"))
    from escritorio.studio.ventana import Ventana
    v = Ventana()
    v.show()
    yield v
    v.ui.close()


def esperar(app, condicion, tope=60.0):
    inicio = time.monotonic()
    while not condicion() and time.monotonic() - inicio < tope:
        app.processEvents()
        time.sleep(0.02)
    return condicion()


def test_cada_operacion_en_una_familia(ventana):
    from escritorio.studio.familias import FAMILIAS, familia_de
    ids = {f[0] for f in FAMILIAS}
    for ficha in ventana.fichas:
        assert familia_de(ficha) in ids, ficha["id"]
    assert ventana._page_order == ["dashboard", *ids, "recetas", "sistema"] or set(ventana._page_order) >= ids


def test_cada_herramienta_tiene_su_pagina(ventana):
    for ficha in ventana.fichas:
        ventana.abrir_herramienta(ficha)
        assert ventana.ui.stack.currentWidget() is ventana._herramientas[ficha["id"]]


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="falta ffmpeg")
def test_ejecutar_desde_la_pagina_no_toca_el_original(app, ventana, tmp_path):
    audio = tmp_path / "nota.opus"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "sine=duration=1", "-c:a", "libopus",
                    str(audio)], check=True)
    antes = audio.read_bytes()
    ficha = next(f for f in ventana.fichas if f["id"] == "convertir_audio")
    ventana.abrir_herramienta(ficha, rutas=[str(audio)])
    pagina = ventana._herramientas["convertir_audio"]
    pagina.ejecutar()
    assert esperar(app, lambda: pagina._informe is not None)
    assert pagina._informe.ok and (tmp_path / "nota.mp3").is_file()
    assert audio.read_bytes() == antes


def test_lo_soltado_abre_lo_que_sirve(ventana, tmp_path):
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    ventana.entregar([str(pdf)])
    assert ventana.ui.stack.currentWidget() is ventana.para_archivos
    assert any(f["id"] == "comprimir" for f, _m in ventana.para_archivos._mosaicos)


def test_ninguna_pantalla_a_mano():
    """Las páginas salen de las fichas: el código del Studio no nombra operaciones salvo en el mapa de familias."""
    from raphi import motor
    ids = {f["id"] for f in motor.operaciones()} - {"info", "ok", "error", "aviso"}   # niveles de un aviso, no herramientas
    for archivo in (RAIZ / "escritorio" / "studio").glob("*.py"):
        if archivo.name == "familias.py":
            continue
        cadenas = {n.value for n in ast.walk(ast.parse(archivo.read_text())) if isinstance(n, ast.Constant)
                   and isinstance(n.value, str)}
        assert not cadenas & ids, f"{archivo.name} nombra {sorted(cadenas & ids)}"
    assert not list((RAIZ / "escritorio").rglob("*.ui"))


def test_arranca_y_sale(tmp_path):
    entorno = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "XDG_CONFIG_HOME": str(tmp_path),
               "PYTHONPATH": str(RAIZ)}
    r = subprocess.run([sys.executable, "-m", "escritorio", "--smoke"], cwd=tmp_path, env=entorno,
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]
