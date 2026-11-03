"""escritorio/studio/controladores/vista.py — la vista previa del espacio de trabajo (reingeniería X4): un archivo de
entrada o de salida mostrado según su tipo — imagen, PDF (el visor de `gui-comun` 3.2, `gui_comun.visor_pdf.VisorPdf`
con `VistaPdf` en QML: QtPdf o `pdftoppm`, zoom, selección, enlaces y búsqueda; hasta el 2026-11-03, páginas propias
de `pdftoppm`), audio y vídeo (QML, con QtMultimedia), texto — y lo que se puede hacer con él (abrirlo con su
aplicación, mostrarlo en Dolphin)."""
from __future__ import annotations

from pathlib import Path

from gui_comun.qt import QObject, Property, Signal, Slot
from gui_comun.visor_pdf import VisorPdf

from escritorio.studio.servicios import archivos as svc_archivos
from escritorio.studio.servicios import vista_previa as svc


class Vista(QObject):
    cambiado = Signal()

    def __init__(self, cache: Path, parent=None):
        super().__init__(parent)
        self._ruta = ""
        self._tipo = ""
        self._visor = VisorPdf(Path(cache), variable_motor="RAPHI_VISOR", parent=self)
        self._visor.cambiado.connect(self.cambiado)

    visorPdf = Property(QObject, lambda self: self._visor, constant=True)
    paginas = Property(QObject, lambda self: self._visor.paginas, constant=True)

    @Slot(str)
    def mostrar(self, ruta: str) -> None:
        ruta = ruta or ""
        self._ruta = ruta
        self._tipo = svc.tipo(ruta) if ruta and Path(ruta).exists() else ""
        self._visor.abrir(ruta if self._tipo == "pdf" else "")   # el mismo PDF con otra fecha: la vista conserva la página
        self.cambiado.emit()

    @Slot()
    def recargar(self) -> None:
        if self._tipo == "pdf":
            self._visor.recargar()
        self.cambiado.emit()

    def renderizar_ya(self, pagina: int) -> str:
        """En el hilo actual (pruebas): la página con `pdftoppm`, como la pinta el respaldo del visor."""
        return self._visor.renderizar_ya(pagina)

    def apagar(self) -> None:
        self._visor.apagar()

    @Property(str, notify=cambiado)
    def ruta(self) -> str:
        return self._ruta

    @Property(str, notify=cambiado)
    def nombre(self) -> str:
        return Path(self._ruta).name if self._ruta else ""

    @Property(str, notify=cambiado)
    def tipo(self) -> str:
        return self._tipo

    @Property(str, notify=cambiado)
    def url(self) -> str:
        return Path(self._ruta).as_uri() if self._ruta and self._tipo in ("imagen", "audio", "video") else ""

    @Property(str, notify=cambiado)
    def texto(self) -> str:
        return svc_archivos.leer_texto(self._ruta) if self._tipo == "texto" else ""

    @Property(str, notify=cambiado)
    def descripcion(self) -> str:
        if not self._ruta:
            return ""
        d = svc.describir(self._ruta)
        n = self._visor.total
        return d + (f" · {n} página" + ("" if n == 1 else "s") if self._tipo == "pdf" else "")
