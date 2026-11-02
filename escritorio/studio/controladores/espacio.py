"""escritorio/studio/controladores/espacio.py — lo transversal: la vista (herramientas · trabajos), la familia y el
grupo de trabajos que filtran la tabla (la navegación), el resumen y el contexto de la barra de estado, y las acciones
sobre una ruta (abrir con el sistema, mostrar en Dolphin, terminal, portapapeles). La vista y los filtros se
recuerdan en QSettings."""
from __future__ import annotations

import os
import shutil
import subprocess

from gui_comun.qt import QGuiApplication, QObject, QSettings, Property, Signal, Slot

from escritorio.studio import familias
from escritorio.studio.servicios import trabajos as svc_trabajos

VISTAS = (("herramientas", "Herramientas", "application-x-executable"), ("trabajos", "Trabajos", "view-task"))
NOMBRES_VISTAS = tuple(v[0] for v in VISTAS)


class Espacio(QObject):
    vistaCambiada = Signal()
    filtroCambiado = Signal()
    resumenCambiado = Signal()
    contextoCambiado = Signal()
    aviso = Signal(str, str)

    def __init__(self, consola, ajustes=None, parent=None):
        super().__init__(parent)
        self.consola, self.ajustes = consola, ajustes
        self._s = QSettings()
        self._vista = str(self._s.value("ventana/vista", "herramientas") or "herramientas")
        if self._vista not in NOMBRES_VISTAS:
            self._vista = "herramientas"
        self._familia = str(self._s.value("ventana/familia", "") or "")
        if self._familia and self._familia not in familias.NOMBRES:
            self._familia = ""
        self._grupo = str(self._s.value("ventana/grupo", "todos") or "todos")
        if self._grupo not in dict(svc_trabajos.GRUPOS):
            self._grupo = "todos"
        self._solo_aceptan = False
        self._resumen = self._contexto = ""

    @Property("QVariantList", constant=True)
    def vistas(self) -> list:
        return [{"nombre": n, "texto": t, "icono": i} for n, t, i in VISTAS]

    @Property(str, notify=vistaCambiada)
    def vista(self) -> str:
        return self._vista

    @Property(int, notify=vistaCambiada)
    def indiceVista(self) -> int:
        return NOMBRES_VISTAS.index(self._vista)

    @Property(str, notify=vistaCambiada)
    def textoVista(self) -> str:
        return next(t for n, t, _i in VISTAS if n == self._vista)

    @Slot(str)
    def fijarVista(self, nombre: str) -> None:
        if nombre in NOMBRES_VISTAS and nombre != self._vista:
            self._vista = nombre
            self._s.setValue("ventana/vista", nombre)
            self.vistaCambiada.emit()

    # ------------------------------------------------------------- los filtros
    @Property(str, notify=filtroCambiado)
    def familia(self) -> str:
        return self._familia

    @Property(str, notify=filtroCambiado)
    def textoFamilia(self) -> str:
        return familias.nombre_de(self._familia) if self._familia else "Todas las herramientas"

    @Slot(str)
    def fijarFamilia(self, nombre: str) -> None:
        nombre = nombre if nombre in familias.NOMBRES else ""
        self.fijarVista("herramientas")
        if nombre != self._familia:
            self._familia = nombre
            self._s.setValue("ventana/familia", nombre)
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

    @Property(str, notify=filtroCambiado)
    def grupo(self) -> str:
        return self._grupo

    @Property(str, notify=filtroCambiado)
    def textoGrupo(self) -> str:
        return dict(svc_trabajos.GRUPOS).get(self._grupo, "Todos")

    @Slot(str)
    def fijarGrupo(self, grupo: str) -> None:
        grupo = grupo if grupo in dict(svc_trabajos.GRUPOS) else "todos"
        self.fijarVista("trabajos")
        if grupo != self._grupo:
            self._grupo = grupo
            self._s.setValue("ventana/grupo", grupo)
            self.filtroCambiado.emit()

    @Property(str, notify=filtroCambiado)
    def nombreNavegacion(self) -> str:
        if self._vista == "trabajos":
            return "trabajos" if self._grupo == "todos" else f"trabajos.{self._grupo}"
        return f"familia.{self._familia}" if self._familia else "familia"

    @Property(str, notify=filtroCambiado)
    def textoFiltro(self) -> str:
        if self._vista == "trabajos":
            return self.textoGrupo.lower()
        partes = [self.textoFamilia.lower()]
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
        if ruta and os.path.exists(ruta):
            subprocess.Popen(["xdg-open", ruta])
            self.consola.registrar("info", f"Abierto con el sistema: {ruta}")
        else:
            self.aviso.emit(f"No existe: {ruta or '(nada seleccionado)'}", "aviso")

    @Slot(str)
    def mostrarEnCarpeta(self, ruta: str) -> None:
        """Dolphin con el archivo seleccionado (`--select`); sin Dolphin, la carpeta con el sistema."""
        if not ruta or not os.path.exists(ruta):
            self.aviso.emit(f"No existe: {ruta or '(nada seleccionado)'}", "aviso")
            return
        if shutil.which("dolphin"):
            subprocess.Popen(["dolphin", "--select", ruta])
        else:
            subprocess.Popen(["xdg-open", ruta if os.path.isdir(ruta) else os.path.dirname(ruta)])

    @Slot(str)
    def abrirDolphin(self, ruta: str) -> None:
        carpeta = ruta if os.path.isdir(ruta) else os.path.dirname(ruta)
        if os.path.isdir(carpeta):
            subprocess.Popen(["xdg-open", carpeta])
        else:
            self.aviso.emit(f"No existe la carpeta: {carpeta}", "aviso")

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
            subprocess.Popen(["konsole", "--workdir", carpeta])
        elif terminal:
            subprocess.Popen([terminal], cwd=carpeta)
        else:
            self.aviso.emit("No se encontró un emulador de terminal (konsole).", "aviso")

    @Slot(str)
    def copiar(self, texto: str) -> None:
        if texto:
            QGuiApplication.clipboard().setText(texto)
            self.consola.registrar("info", f"Copiado: {texto}")

    def entradas_paleta(self, _texto: str) -> list[dict]:
        salida = [{"nombre": "ir.herramientas", "texto": "Ver todas las herramientas", "grupo": "Vistas", "icono": "application-x-executable",
                   "ejecutar": lambda: self.fijarFamilia("")}]
        salida += [{"nombre": f"ir.familia.{f}", "texto": f"Ver {n}", "grupo": "Vistas", "icono": i, "ejecutar": lambda f=f: self.fijarFamilia(f)}
                   for f, n, _p, i in familias.FAMILIAS]
        salida += [{"nombre": f"ir.trabajos.{g}", "texto": f"Ver los trabajos: {t.lower()}", "grupo": "Vistas", "icono": "view-task",
                    "ejecutar": lambda g=g: self.fijarGrupo(g)} for g, t in svc_trabajos.GRUPOS]
        return salida
