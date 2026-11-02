"""escritorio/studio/controladores/espacio.py — lo transversal (reingeniería, `docs/reingenieria.md`): la vista
(Catálogo · Herramienta · Cola), el área y la búsqueda que filtran el catálogo, el grupo que filtra la cola, el
resumen y el contexto de la barra de estado, y lo que se hace con una ruta: abrir con su aplicación y mostrar en
Dolphin (las funciones de `escritorio` de gui-comun 3.0), la terminal y el portapapeles. La vista, el área y el grupo
se recuerdan en QSettings."""
from __future__ import annotations

import os
import shutil
import subprocess

from gui_comun.qt import QGuiApplication, QObject, QSettings, Property, Signal, Slot

from escritorio.studio import familias
from escritorio.studio.servicios import trabajos as svc_trabajos

VISTAS = (("catalogo", "Catálogo", "view-grid"), ("herramienta", "Herramienta", "tool-animator"), ("cola", "Cola", "view-task"))
NOMBRES_VISTAS = tuple(v[0] for v in VISTAS)


class Espacio(QObject):
    vistaCambiada = Signal()
    filtroCambiado = Signal()
    resumenCambiado = Signal()
    contextoCambiado = Signal()
    aviso = Signal(str, str)

    def __init__(self, consola, ajustes=None, escritorio=None, parent=None):
        super().__init__(parent)
        self.consola, self.ajustes, self.escritorio = consola, ajustes, escritorio
        self._s = QSettings()
        self._vista = str(self._s.value("ventana/vista3", "catalogo") or "catalogo")
        if self._vista not in NOMBRES_VISTAS or self._vista == "herramienta":
            self._vista = "catalogo"                     # la herramienta se abre eligiéndola, no al arrancar
        self._area = str(self._s.value("ventana/area", "") or "")
        if self._area and self._area not in familias.NOMBRES_AREA:
            self._area = ""
        self._grupo = str(self._s.value("ventana/grupo", "todos") or "todos")
        if self._grupo not in dict(svc_trabajos.GRUPOS):
            self._grupo = "todos"
        self._busqueda = ""
        self._solo_aceptan = False
        self._resumen = self._contexto = ""

    # ------------------------------------------------------------- la vista
    @Property("QVariantList", constant=True)
    def vistas(self) -> list:
        return [{"nombre": n, "texto": t, "icono": i} for n, t, i in VISTAS]

    @Property(str, notify=vistaCambiada)
    def vista(self) -> str:
        return self._vista

    @Property(int, notify=vistaCambiada)
    def indiceVista(self) -> int:
        return NOMBRES_VISTAS.index(self._vista)

    @Slot(str)
    def fijarVista(self, nombre: str) -> None:
        if nombre in NOMBRES_VISTAS and nombre != self._vista:
            self._vista = nombre
            self._s.setValue("ventana/vista3", nombre)
            self.vistaCambiada.emit()

    # ------------------------------------------------------------- los filtros del catálogo
    @Property("QVariantList", constant=True)
    def areas(self) -> list:
        return [{"nombre": "", "texto": "Todas", "icono": "view-grid"}] + [{"nombre": a, "texto": n, "icono": i, "descripcion": d}
                                                                           for a, n, d, i in familias.AREAS]

    @Property(str, notify=filtroCambiado)
    def area(self) -> str:
        return self._area

    @Property(str, notify=filtroCambiado)
    def textoArea(self) -> str:
        return familias.nombre_area(self._area) if self._area else "Todas las herramientas"

    @Slot(str)
    def fijarArea(self, area: str) -> None:
        area = area if area in familias.NOMBRES_AREA else ""
        self.fijarVista("catalogo")
        if area != self._area:
            self._area = area
            self._s.setValue("ventana/area", area)
            self.filtroCambiado.emit()

    @Property(str, notify=filtroCambiado)
    def busqueda(self) -> str:
        return self._busqueda

    @Slot(str)
    def fijarBusqueda(self, texto: str) -> None:
        texto = (texto or "").strip()
        if texto != self._busqueda:
            self._busqueda = texto
            if texto:
                self.fijarVista("catalogo")
            self.filtroCambiado.emit()

    @Property(bool, notify=filtroCambiado)
    def soloAceptan(self) -> bool:
        """Solo las herramientas que aceptan los archivos de la lista (lo soltado sobre la ventana)."""
        return self._solo_aceptan

    @Slot(bool)
    def fijarSoloAceptan(self, v: bool) -> None:
        if bool(v) != self._solo_aceptan:
            self._solo_aceptan = bool(v)
            self.filtroCambiado.emit()

    # ------------------------------------------------------------- el filtro de la cola
    @Property(str, notify=filtroCambiado)
    def grupo(self) -> str:
        return self._grupo

    @Property(str, notify=filtroCambiado)
    def textoGrupo(self) -> str:
        return dict(svc_trabajos.GRUPOS).get(self._grupo, "Todos")

    @Slot(str)
    def fijarGrupo(self, grupo: str) -> None:
        grupo = grupo if grupo in dict(svc_trabajos.GRUPOS) else "todos"
        if grupo != self._grupo:
            self._grupo = grupo
            self._s.setValue("ventana/grupo", grupo)
            self.filtroCambiado.emit()

    @Property(str, notify=filtroCambiado)
    def textoFiltro(self) -> str:
        partes = [self.textoArea.lower()]
        if self._busqueda:
            partes.append(f"«{self._busqueda}»")
        if self._solo_aceptan:
            partes.append("las que aceptan los archivos")
        return " · ".join(partes)

    # ------------------------------------------------------------- barra de estado
    @Property(str, notify=resumenCambiado)
    def resumen(self) -> str:
        return self._resumen

    @Slot(str)
    def fijarResumen(self, texto: str) -> None:
        if texto != self._resumen:
            self._resumen = texto
            self.resumenCambiado.emit()

    @Property(str, notify=contextoCambiado)
    def contexto(self) -> str:
        return self._contexto

    @Slot(str)
    def fijarContexto(self, texto: str) -> None:
        if texto != self._contexto:
            self._contexto = texto
            self.contextoCambiado.emit()

    # ------------------------------------------------------------- sobre una ruta
    @Slot(str)
    def abrir(self, ruta: str) -> None:
        """Con la aplicación que KDE asocia a su tipo (gui-comun 3.0, `escritorio.abrirConAplicacion`)."""
        if not ruta or not os.path.exists(ruta):
            self.aviso.emit(f"No existe: {ruta or '(nada seleccionado)'}", "aviso")
        elif self.escritorio is not None:
            self.escritorio.abrirConAplicacion(ruta)
        else:
            subprocess.Popen(["xdg-open", ruta], start_new_session=True)

    @Slot(str)
    def mostrarEnCarpeta(self, ruta: str) -> None:
        """Dolphin con el archivo señalado (gui-comun 3.0, `escritorio.mostrarEnDolphin`)."""
        if not ruta or not os.path.exists(ruta):
            self.aviso.emit(f"No existe: {ruta or '(nada seleccionado)'}", "aviso")
        elif self.escritorio is not None:
            self.escritorio.mostrarEnDolphin(ruta)
        else:
            subprocess.Popen(["xdg-open", ruta if os.path.isdir(ruta) else os.path.dirname(ruta)], start_new_session=True)

    def _terminal(self) -> str:
        preferido = (self.ajustes.terminal if self.ajustes is not None else "konsole") or "konsole"
        for candidato in (preferido, "konsole", "x-terminal-emulator"):
            if shutil.which(candidato):
                return candidato
        return ""

    @Slot(str)
    def abrirTerminal(self, ruta: str) -> None:
        carpeta = ruta if os.path.isdir(ruta) else os.path.dirname(ruta)
        if not os.path.isdir(carpeta):
            return
        terminal = self._terminal()
        if terminal == "konsole":
            subprocess.Popen(["konsole", "--workdir", carpeta], start_new_session=True)
        elif terminal:
            subprocess.Popen([terminal], cwd=carpeta, start_new_session=True)
        else:
            self.aviso.emit("No se encontró un emulador de terminal (konsole).", "aviso")

    @Slot(str)
    def copiar(self, texto: str) -> None:
        if texto:
            QGuiApplication.clipboard().setText(texto)
            self.consola.registrar("info", f"Copiado: {texto}")

    def entradas_paleta(self, _texto: str) -> list[dict]:
        salida = [{"nombre": "ir.catalogo", "texto": "Ver todas las herramientas", "grupo": "Vistas", "icono": "view-grid",
                   "ejecutar": lambda: self.fijarArea("")}]
        salida += [{"nombre": f"ir.area.{a}", "texto": f"Ver {n}", "grupo": "Áreas", "icono": i, "ejecutar": lambda a=a: self.fijarArea(a)}
                   for a, n, _d, i in familias.AREAS]
        salida += [{"nombre": f"ir.cola.{g}", "texto": f"Cola: {t.lower()}", "grupo": "Vistas", "icono": "view-task",
                    "ejecutar": lambda g=g: (self.fijarGrupo(g), self.fijarVista("cola"))} for g, t in svc_trabajos.GRUPOS]
        return salida
