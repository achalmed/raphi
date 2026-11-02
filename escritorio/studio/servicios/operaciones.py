"""escritorio/studio/servicios/operaciones.py — el catálogo de operaciones de la ventana (sin Qt): lo que F5 simula o
lee y lo que Ctrl+Intro aplica tras confirmar. Cada operación existe una sola vez aquí; `aplicacion.py` la registra
como acción y `controladores/operaciones.py` la corre. Simular y aplicar son la herramienta actual sobre los archivos
con las opciones (un trabajo del corredor, en la cola); doctor, lista y formatos son la CLI del motor de solo lectura;
los menús de Dolphin y las carpetas vigiladas escriben en la configuración del escritorio, no en archivos del usuario."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from escritorio.studio.servicios import rutas


@dataclass
class Orden:
    argv: list
    cwd: Path

    def texto(self) -> str:
        return " ".join(("python" if str(a) == rutas.interprete_motor() else (Path(a).name if str(a).startswith("/") and Path(a).suffix == ".py" else str(a))) for a in self.argv)


@dataclass
class Operacion:
    id: str
    titulo: str
    descripcion: str
    verbo: str = "Ejecutar"                 # lo que hace F5
    trabajo: bool = False                   # F5 encola el trabajo simulado; Ctrl+Intro, el de verdad
    escribe: bool = False
    toca: str = "solo lee"
    cli: object = None                      # f(ctx) -> Orden: la CLI del motor, de solo lectura
    sobre_archivos: bool = False
    icono: str = "system-run"


def _cli(*args: str) -> Orden:
    return Orden([rutas.interprete_motor(), "-m", "raphi", *args], rutas.REPO)


OPERACIONES: tuple[Operacion, ...] = (
    Operacion("herramienta", "La herramienta sobre los archivos", "F5 simula: el plan del motor (qué se producirá, dónde, con qué programa) como trabajo en la cola; "
              "Ctrl+Intro aplica tras confirmar: el mismo trabajo de verdad, con su progreso y su cancelación",
              verbo="Simular", trabajo=True, escribe=True, toca="escribe las salidas junto a cada original o en la carpeta elegida; el original nunca se toca",
              icono="media-playback-start"),
    Operacion("doctor", "Doctor: qué falta en esta máquina", "raphi doctor: cada programa o módulo que las herramientas necesitan, con ✓ o ✗",
              cli=lambda c: _cli("doctor"), icono="checkmark"),
    Operacion("lista", "Lista de operaciones", "raphi lista: las operaciones del motor por categoría, con lo que les falta", cli=lambda c: _cli("lista"),
              icono="view-list-text"),
    Operacion("formatos", "Formatos: a qué se puede convertir", "raphi formatos: a qué formatos se convierte cada archivo de la lista y con qué herramienta",
              cli=lambda c: _cli("formatos", *c), sobre_archivos=True, icono="document-export"),
)


def operacion(id_: str) -> Operacion | None:
    return next((o for o in OPERACIONES if o.id == id_), None)
