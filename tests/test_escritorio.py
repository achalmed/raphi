"""Raphi escritorio sin pantalla: su servidor con ficha, los menús de Dolphin, la acción de la CLI y su regla
(ninguna pantalla propia: la interfaz es la web)."""
from __future__ import annotations

import ast
import shutil
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]


def test_servidor_con_ficha(tmp_path, monkeypatch):
    monkeypatch.setenv("RAPHI_DIR", str(tmp_path / "raphi"))
    from escritorio.servidor import Servidor
    s = Servidor()
    s.arrancar()
    try:
        d = s.pedir("/api/raphi/operaciones")
        assert d["modo"] == "escritorio" and len(d["operaciones"]) >= 45
        import urllib.error
        import urllib.request
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(f"{s.url}/api/raphi/operaciones", timeout=5)      # sin ficha, no
        with urllib.request.urlopen(f"{s.url}/raphi/mesa", timeout=5) as r:           # la web, en cualquier ruta suya
            assert r.status == 200 and b"<div id=\"root\">" in r.read()
    finally:
        s.detener()


def test_menus_de_dolphin(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    from escritorio import dolphin
    ajeno = dolphin.carpeta_menus() / "otro.desktop"
    ajeno.parent.mkdir(parents=True)
    ajeno.write_text("[Desktop Entry]\n")
    assert dolphin.instalar(True)
    pdf = (dolphin.carpeta_menus() / "raphi-pdf.desktop").read_text()
    assert "MimeType=application/pdf;" in pdf and "accion comprimir" in pdf and "X-KDE-Submenu=Raphi" in pdf
    assert all(p.stat().st_mode & 0o111 for p in dolphin.instalados())
    assert not dolphin.instalar(False) and ajeno.is_file()          # quita solo lo suyo


def test_accion_junto_al_original(corpus, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(shutil, "which", lambda _n: None)            # sin notify-send en la prueba
    from raphi.__main__ import main
    copia = tmp_path / "doc.pdf"
    shutil.copy(corpus["texto"], copia)
    assert main(["accion", "foliar", "--inicio", "3", str(copia)]) == 0
    assert (tmp_path / "doc_foliado.pdf").is_file()


def test_el_escritorio_no_tiene_pantallas_propias():
    """Solo la ventana (que muestra la web) y la zona para soltar: ninguna pantalla con controles propios."""
    clases = set()
    for archivo in (RAIZ / "escritorio").glob("*.py"):
        for nodo in ast.walk(ast.parse(archivo.read_text())):
            if isinstance(nodo, ast.ClassDef) and any(getattr(b, "id", "") in ("QWidget", "QMainWindow", "QDialog")
                                                     for b in nodo.bases):
                clases.add(nodo.name)
    assert clases == {"Ventana", "ZonaSoltar"}
    assert not list((RAIZ / "escritorio").rglob("*.ui"))


def test_raphi_no_importa_el_escritorio():
    for archivo in (RAIZ / "raphi").rglob("*.py"):
        texto = archivo.read_text()
        assert "PySide6" not in texto and "import escritorio" not in texto and "from escritorio" not in texto, archivo
