"""
config.py — Configuración centralizada de pdf_page_counter.

Todas las rutas y constantes editables por el usuario viven aquí;
los módulos de lib/ nunca llevan rutas hardcodeadas.
"""

from pathlib import Path

SCRIPT_NAME = "pdf-page-counter"
SCRIPT_VERSION = "2.0.0"

# ---------------------------------------------------------------------------
# Rutas de los blogs
# ---------------------------------------------------------------------------
# Raíz del workspace. Los blogs "pub_<nombre>" son submódulos git del hub
# website-achalma y viven en RUTA_BASE_PUBLICACIONES / SUBDIR_PUBS
# (reorganización 2026-09-06; antes colgaban directamente de ~/Documents).
# La raíz y el hub los da core/env.py (normativa 5.1-5.2); los blogs, el registro _pubs/pubs.yml del hub por
# core/py-common/pubs.py (ola 6, 6f): nada se lista a mano ni se descubre por el prefijo de carpeta.
import importlib.util as _ilu


def _core_dir() -> Path:
    d = Path(__file__).resolve()
    while d != d.parent and not (d / "core" / "env.py").is_file():
        d = d.parent
    return d / "core"


def _cargar(nombre, ruta):
    spec = _ilu.spec_from_file_location(nombre, ruta)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_env = _cargar("core_env", _core_dir() / "env.py")
_pubs = _cargar("core_pubs", _core_dir() / "py-common" / "pubs.py")
RUTA_BASE_PUBLICACIONES = Path(_env.DOCS_ROOT)
DIR_HUB = Path(_env.INDEX_DIR).relative_to(RUTA_BASE_PUBLICACIONES).as_posix()   # carpeta del hub (repo website-achalma)
SUBDIR_PUBS = f"{DIR_HUB}/_pubs"
# Blogs estándar: nombre lógico → carpeta (cada uno tiene su _site/)
CARPETA_BLOG = {p.nombre: p.ruta for p in _pubs.pubs()}
BLOGS_ESTANDAR = list(CARPETA_BLOG)

# Blogs dentro de website-achalma (no tienen _site propio; cuelgan de
# website-achalma/_site). Nombre lógico -> ruta relativa a la ruta base.
BLOGS_WEBSITE_ACHALMA = {
    "blog": f"{DIR_HUB}/_site/blog",
    "teching": f"{DIR_HUB}/_site/teching",
}

# Alias que seleccionan todos los blogs de website-achalma a la vez
ALIAS_WEBSITE_ACHALMA = "website-achalma"

# ---------------------------------------------------------------------------
# Salida
# ---------------------------------------------------------------------------
# Directorio (relativo a este script) donde se guardan los reportes Excel
DIRECTORIO_EXCEL = "excel_databases"

# ---------------------------------------------------------------------------
# Códigos de salida estándar
# ---------------------------------------------------------------------------
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_NOT_FOUND = 3
EXIT_MISSING_DEPENDENCY = 5
