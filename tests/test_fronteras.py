"""Las fronteras del paquete: el motor no conoce la web, ni Qt, ni a Qillqa ni a ningún módulo de la plataforma."""
from __future__ import annotations

import ast
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1] / "raphi"
PROHIBIDOS_EN_EL_MOTOR = ("fastapi", "starlette", "sqlalchemy", "PySide6", "tiqsi", "raphi.api", "raphi.manifiesto")
PLATAFORMA = ("app", "qillqa", "qillqasqa", "punku", "rimay", "minka", "yupay", "rikchay", "qhawana", "awana", "tullpu",
              "kuyuy", "wayra", "ruray")


def _importa(archivo: Path) -> set[str]:
    nombres = set()
    for nodo in ast.walk(ast.parse(archivo.read_text())):
        if isinstance(nodo, ast.Import):
            nombres |= {a.name for a in nodo.names}
        elif isinstance(nodo, ast.ImportFrom) and nodo.module and not nodo.level:
            nombres.add(nodo.module)
    return nombres


def test_el_motor_es_python_puro():
    for archivo in (RAIZ / "motor").rglob("*.py"):
        for nombre in _importa(archivo):
            assert not nombre.startswith(PROHIBIDOS_EN_EL_MOTOR), f"{archivo.name} importa {nombre}"


def test_nadie_importa_otro_proyecto_de_la_plataforma():
    for archivo in RAIZ.rglob("*.py"):
        for nombre in _importa(archivo):
            assert nombre.split(".")[0] not in PLATAFORMA, f"{archivo.relative_to(RAIZ)} importa {nombre}"
