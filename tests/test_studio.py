"""Raphi Studio (escritorio/studio, QML + Kirigami sobre gui-comun 2.7 desde el 2026-11-02): lo que se prueba con el
.venv del repo (este pytest), sin Qt: cada operación cae en una familia por su ficha, el corredor del motor devuelve
las fichas y corre un trabajo simulado, y la regla de R4/R9: ninguna pantalla a mano (el studio no nombra operaciones
salvo en familias.py). La ventana (QML, el Python del sistema) se prueba con tests/run.sh (tests/studio/)."""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
STUDIO = RAIZ / "escritorio" / "studio"
sys.path.insert(0, str(RAIZ))

from escritorio.studio import familias  # noqa: E402


def test_cada_operacion_en_una_familia():
    from raphi import motor
    ids = set(familias.NOMBRES)
    for ficha in motor.operaciones():
        assert familias.familia_de(ficha) in ids, ficha["id"]
        assert familias.icono_de(ficha)


def test_el_corredor_da_las_fichas_y_corre_un_trabajo(tmp_path, corpus):
    r = subprocess.run([sys.executable, str(STUDIO / "corredor.py"), "fichas"], capture_output=True, text=True, timeout=120, cwd=str(RAIZ))
    assert r.returncode == 0, r.stderr[-1500:]
    datos = json.loads(r.stdout)
    assert len(datos["operaciones"]) >= 60 and datos["recetas"] and datos["version"]
    trabajo = tmp_path / "t.json"
    trabajo.write_text(json.dumps({"operacion": "rotar", "archivos": [str(corpus["texto"])], "params": {"angulo": "90"}, "destino": str(tmp_path), "simular": True}))
    r = subprocess.run([sys.executable, str(STUDIO / "corredor.py"), "ejecutar", str(trabajo)], capture_output=True, text=True, timeout=120, cwd=str(RAIZ))
    assert r.returncode == 0, r.stderr[-1500:]
    informe = json.loads(trabajo.with_suffix(".informe.json").read_text(encoding="utf-8"))
    assert informe["ok"] and informe["simulado"] and "## informe" in r.stdout and not list(tmp_path.glob("*.pdf"))


def test_ninguna_pantalla_a_mano():
    """Las pantallas salen de las fichas: el código del Studio (Python y QML) no nombra operaciones salvo en el mapa de familias."""
    from raphi import motor
    ids = {f["id"] for f in motor.operaciones()} - {"info", "ok", "error", "aviso", "lista"}
    for archivo in STUDIO.rglob("*.py"):
        if archivo.name == "familias.py" or archivo.parent.name == "__pycache__":
            continue
        cadenas = {n.value for n in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        assert not cadenas & ids, f"{archivo.name} nombra {sorted(cadenas & ids)}"
    for qml in (STUDIO / "qml").rglob("*.qml"):
        texto = "\n".join(l.split("//")[0] for l in qml.read_text(encoding="utf-8").splitlines())
        assert not {i for i in ids if re.search(rf'"{re.escape(i)}"', texto)}, qml.name
    assert not list((RAIZ / "escritorio").rglob("*.ui"))
