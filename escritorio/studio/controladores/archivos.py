"""escritorio/studio/controladores/archivos.py — los archivos de entrada del espacio (`docs/rediseno.md` S5): lo
soltado sobre la ventana, lo elegido con el diálogo y lo que llega de Dolphin o de otra instancia va a una sola lista
(`ModeloTabla`), que sigue ahí al cambiar de herramienta; quitar, vaciar, abrir y mostrar en la carpeta."""
from __future__ import annotations

from pathlib import Path

from gui_comun.modelos import ModeloTabla
from gui_comun.qt import QObject, Property, Signal, Slot

from escritorio.studio.servicios import archivos as svc

COLUMNAS = [("Nombre", "nombre"), ("Tipo", "tipo"), ("Tamaño", "tamano"), ("Carpeta", "carpeta")]


class Archivos(QObject):
    cambiado = Signal()
    recibidos = Signal(int)              # cuántos llegaron de fuera (soltados, Dolphin, otra instancia)
    aviso = Signal(str, str)

    def __init__(self, consola, parent=None):
        super().__init__(parent)
        self.consola = consola
        self._tabla = ModeloTabla(COLUMNAS, parent=self)
        self._rutas: list[str] = []
        self._fila = -1

    modelo = Property(QObject, lambda self: self._tabla, constant=True)

    @Property("QVariantList", notify=cambiado)
    def rutas(self) -> list:
        return list(self._rutas)

    @Property(int, notify=cambiado)
    def total(self) -> int:
        return len(self._rutas)

    @Property(str, notify=cambiado)
    def resumen(self) -> str:
        n = len(self._rutas)
        if n == 0:
            return "sin archivos"
        nombres = ", ".join(Path(r).name for r in self._rutas[:2])
        return f"{n} archivo{'s' if n != 1 else ''}: {nombres}" + (f" y {n - 2} más" if n > 2 else "")

    @Property(str, notify=cambiado)
    def carpetaComun(self) -> str:
        """La carpeta del primer archivo (donde quedan las salidas «junto al original»)."""
        return str(Path(self._rutas[0]).parent) if self._rutas else ""

    @Slot("QVariantList", result=int)
    def agregar(self, rutas) -> int:
        """Añade las rutas que existan y no estén; devuelve cuántas entraron."""
        nuevas = []
        for r in rutas or []:
            r = str(r)
            if r.startswith("file://"):
                from urllib.parse import unquote, urlparse
                r = unquote(urlparse(r).path)
            if r and r not in self._rutas and r not in nuevas and Path(r).exists():
                nuevas.append(r)
        if not nuevas:
            return 0
        self._rutas += nuevas
        for r in nuevas:
            self._tabla.anadir(svc.fila_de(r))
        self.consola.registrar("info", f"{len(nuevas)} archivo(s) añadido(s): " + ", ".join(Path(r).name for r in nuevas[:5]))
        self.cambiado.emit()
        return len(nuevas)

    @Slot("QVariantList", result=int)
    def recibir(self, rutas) -> int:
        """Lo que llega de fuera (soltado, Dolphin, otra instancia): a la lista, y `recibidos` para que la ventana reaccione."""
        n = self.agregar(rutas)
        if n:
            self.recibidos.emit(n)
        return n

    @Slot(int)
    def quitar(self, fila: int) -> None:
        if 0 <= fila < len(self._rutas):
            del self._rutas[fila]
            self._tabla.quitar(fila)
            self.cambiado.emit()

    @Slot("QVariantList")
    def quitarFilas(self, filas) -> None:
        for fila in sorted({int(f) for f in filas or []}, reverse=True):
            if 0 <= fila < len(self._rutas):
                del self._rutas[fila]
                self._tabla.quitar(fila)
        self.cambiado.emit()

    @Slot()
    def vaciar(self) -> None:
        if self._rutas:
            self._rutas = []
            self._tabla.poner([])
            self.cambiado.emit()

    @Slot(int)
    def fijarFila(self, fila: int) -> None:
        self._fila = fila
        self.cambiado.emit()

    @Property(int, notify=cambiado)
    def fila(self) -> int:
        return self._fila

    @Property(str, notify=cambiado)
    def rutaActual(self) -> str:
        return self._rutas[self._fila] if 0 <= self._fila < len(self._rutas) else ""

    def entradas_paleta(self, _texto: str) -> list[dict]:
        return [{"nombre": "archivos.vaciar", "texto": "Quitar todos los archivos", "grupo": "Archivos", "icono": "edit-clear-list", "ejecutar": self.vaciar}]
