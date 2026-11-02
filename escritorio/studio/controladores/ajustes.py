"""escritorio/studio/controladores/ajustes.py — «Configurar Raphi Studio…»: la terminal, qué hacer con lo que llega
(abrir la tabla con lo que lo acepta), el intérprete del motor y el entorno, sobre QSettings."""
from __future__ import annotations

from gui_comun.qt import QObject, QSettings, Property, Signal, Slot

from escritorio.studio.servicios import rutas


class Ajustes(QObject):
    cambiado = Signal()
    guardado = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._s = QSettings()

    def _get(self, clave: str, defecto: str = "") -> str:
        return str(self._s.value(clave, defecto) or defecto)

    def _set(self, clave: str, v) -> None:
        if str(v) != self._get(clave):
            self._s.setValue(clave, v)
            self.cambiado.emit()

    terminal = Property(str, lambda self: self._get("sistema/terminal", "konsole"), lambda self, v: self._set("sistema/terminal", (v or "").strip() or "konsole"), notify=cambiado)
    filtrarAlRecibir = Property(bool, lambda self: self._get("ventana/filtrar_al_recibir", "true") == "true",
                                lambda self, v: self._set("ventana/filtrar_al_recibir", "true" if v else "false"), notify=cambiado)
    abrirSalidas = Property(bool, lambda self: self._get("ventana/abrir_salidas", "false") == "true",
                            lambda self, v: self._set("ventana/abrir_salidas", "true" if v else "false"), notify=cambiado)

    @Property(str, constant=True)
    def interpreteMotor(self) -> str:
        return rutas.interprete_motor()

    @Property(bool, constant=True)
    def hayVenv(self) -> bool:
        return rutas.hay_venv()

    @Property(str, constant=True)
    def ordenVenv(self) -> str:
        return rutas.orden_crear_venv()

    @Slot()
    def guardar(self) -> None:
        self.cambiado.emit()
        self.guardado.emit()
