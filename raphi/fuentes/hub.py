"""La fuente «blogs del hub»: el caso de `page-counter`, ahora como fuente de «Inventario de páginas».

Lee la raíz y el hub por `core/env.py` y la lista de blogs por `core/py-common/pubs.py` (el registro
`<hub>/_pubs/pubs.yml`); los blogs internos del hub (`blog`, `teching`) cuelgan de `<hub>/_site/`. Nada de rutas
escritas a mano: si `core/` no está (fuera del espacio de trabajo), `hay()` es False y la fuente no se ofrece.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from raphi.motor.base import ErrorOperacion

INTERNOS = ("blog", "teching")       # los blogs que viven dentro de <hub>/_site/ (los de page-counter)


def _core() -> Path | None:
    for padre in Path(__file__).resolve().parents:
        if (padre / "core" / "env.py").is_file() and (padre / "core" / "py-common" / "pubs.py").is_file():
            return padre / "core"
    return None


def _cargar(nombre: str, ruta: Path):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def hay() -> bool:
    return _core() is not None


def blogs() -> dict[str, Path]:
    """Nombre del blog → su carpeta `_site` (los que no se han renderizado no están)."""
    core = _core()
    if core is None:
        raise ErrorOperacion("La fuente «blogs del hub» solo existe dentro del espacio de trabajo (falta core/).")
    env = _cargar("raphi_core_env", core / "env.py")
    pubs = _cargar("raphi_core_pubs", core / "py-common" / "pubs.py")
    hub = Path(env.INDEX_DIR)
    salida = {p.nombre: Path(p.ruta) / "_site" for p in pubs.pubs()}
    salida.update({n: hub / "_site" / n for n in INTERNOS})
    return {n: r for n, r in salida.items() if r.is_dir()}


def grupos(solo_index: bool, blogs: list[str]) -> list:
    todos = globals()["blogs"]()
    elegidos = blogs or list(todos)
    desconocidos = [b for b in elegidos if b not in todos]
    if desconocidos:
        raise ErrorOperacion(f"Blogs desconocidos o sin renderizar: {', '.join(desconocidos)}. "
                             f"Hay: {', '.join(sorted(todos))}.")
    salida = []
    for nombre in elegidos:
        raiz = todos[nombre]
        patron = "index.pdf" if solo_index else "*.pdf"
        pdfs = sorted(p for p in raiz.rglob(patron) if p.is_file())
        salida.append((nombre, [(raiz, p) for p in pdfs]))
    return [g for g in salida if g[1]]
