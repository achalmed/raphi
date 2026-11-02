"""escritorio/studio/controladores/vista.py — la vista previa del espacio de trabajo (reingeniería X4): un archivo de
entrada o de salida mostrado según su tipo — imagen, PDF (páginas de `pdftoppm` en hilos aparte, por demanda), audio y
vídeo (QML, con QtMultimedia), texto — y lo que se puede hacer con él (abrirlo con su aplicación, mostrarlo en Dolphin).
Los hilos solo corren `pdftoppm`; el modelo se toca en el hilo de la interfaz (la señal `_hecha` cruza de hilo)."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from gui_comun.modelos import ModeloLista
from gui_comun.qt import QObject, Property, Signal, Slot

from escritorio.studio.servicios import archivos as svc_archivos
from escritorio.studio.servicios import vista_previa as svc

ROLES = ("pagina", "ancho", "alto", "imagen")
PPP = 96


class Vista(QObject):
    cambiado = Signal()
    _hecha = Signal(str, int, str)          # clave del PDF, página, ruta del PNG

    def __init__(self, cache: Path, parent=None):
        super().__init__(parent)
        self._cache = Path(cache)
        self._ruta = ""
        self._tipo = ""
        self._clave = ""
        self._paginas = ModeloLista(ROLES, parent=self)
        self._pedidas: set = set()
        self._hilos = ThreadPoolExecutor(max_workers=2, thread_name_prefix="pdftoppm")
        self._hecha.connect(self._poner)

    paginas = Property(QObject, lambda self: self._paginas, constant=True)

    @Slot(str)
    def mostrar(self, ruta: str) -> None:
        ruta = ruta or ""
        if ruta == self._ruta and (self._tipo != "pdf" or self._clave == svc.clave(Path(ruta))):
            return
        self._ruta = ruta
        self._tipo = svc.tipo(ruta) if ruta and Path(ruta).exists() else ""
        self._pedidas.clear()
        if self._tipo == "pdf":
            self._clave = svc.clave(Path(ruta))
            self._paginas.poner([{"pagina": i, "ancho": a, "alto": b, "imagen": ""} for i, (a, b) in enumerate(svc.paginas_pdf(Path(ruta)), start=1)])
            svc.podar(self._cache, conservar=self._clave)
        else:
            self._clave = ""
            self._paginas.poner([])
        self.cambiado.emit()

    @Slot()
    def recargar(self) -> None:
        ruta, self._ruta = self._ruta, ""
        self.mostrar(ruta)

    @Slot(int)
    def pedir(self, pagina: int) -> None:
        if self._tipo != "pdf" or (self._clave, pagina) in self._pedidas or not (1 <= pagina <= self._paginas.filas):
            return
        self._pedidas.add((self._clave, pagina))
        pdf, clave, cache = Path(self._ruta), self._clave, self._cache

        def trabajo():
            hecho = svc.renderizar(pdf, pagina, PPP, cache)
            self._hecha.emit(clave, pagina, str(hecho) if hecho else "")

        self._hilos.submit(trabajo)

    def renderizar_ya(self, pagina: int) -> str:
        hecho = svc.renderizar(Path(self._ruta), pagina, PPP, self._cache)
        self._poner(self._clave, pagina, str(hecho) if hecho else "")
        return str(hecho) if hecho else ""

    def _poner(self, clave: str, pagina: int, ruta: str) -> None:
        if clave == self._clave and ruta and 1 <= pagina <= self._paginas.filas:
            self._paginas.actualizar(pagina - 1, imagen=Path(ruta).as_uri())

    def apagar(self) -> None:
        self._hilos.shutdown(wait=False, cancel_futures=True)

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
        return d + (f" · {self._paginas.filas} página" + ("" if self._paginas.filas == 1 else "s") if self._tipo == "pdf" else "")
