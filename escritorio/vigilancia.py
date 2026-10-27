"""Carpetas vigiladas (antes «Vigilancia» de la GUI, con `docflow watch`): lo que aparece en la carpeta pasa por una
receta y el resultado queda en su subcarpeta «raphi». Se recuerdan en los ajustes de la aplicación.

Un archivo se procesa una sola vez (se anota su ruta y su tamaño) y solo cuando dejó de crecer (una copia a medias
no se toca). La subcarpeta «raphi» no se vigila, así que no hay bucles.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QObject, QSettings, QTimer

SALIDA = "raphi"


class Vigilancia(QObject):
    def __init__(self, servidor, ajustes: QSettings, avisar) -> None:
        super().__init__()
        self.servidor, self.ajustes, self.avisar = servidor, ajustes, avisar
        self.observador = QFileSystemWatcher(self)
        self.observador.directoryChanged.connect(self._cambio)
        self.vistos: dict[str, int] = {}
        self.espera: dict[str, int] = {}
        self.reloj = QTimer(self, interval=2000, timeout=self._madurar)
        self.reloj.start()
        for v in self.lista():
            self._observar(v["carpeta"], primera=True)

    def lista(self) -> list[dict]:
        return list(self.ajustes.value("vigiladas", []) or [])

    def _guardar(self, lista: list[dict]) -> None:
        self.ajustes.setValue("vigiladas", lista)
        self.ajustes.sync()

    def _observar(self, carpeta: str, primera: bool = False) -> None:
        if Path(carpeta).is_dir():
            self.observador.addPath(carpeta)
            for p in Path(carpeta).iterdir():                 # lo que ya estaba no se procesa
                if p.is_file():
                    self.vistos[str(p)] = p.stat().st_size

    def vigilar(self, carpeta: str, receta: str) -> bool:
        lista = [v for v in self.lista() if v["carpeta"] != carpeta] + [{"carpeta": carpeta, "receta": receta}]
        self._guardar(lista)
        self._observar(carpeta)
        return True

    def dejar(self, carpeta: str) -> bool:
        self._guardar([v for v in self.lista() if v["carpeta"] != carpeta])
        self.observador.removePath(carpeta)
        return True

    def _cambio(self, carpeta: str) -> None:
        for p in Path(carpeta).iterdir():
            if p.is_file() and not p.name.startswith(".") and str(p) not in self.vistos:
                self.espera[str(p)] = -1

    def _madurar(self) -> None:
        """Un archivo nuevo se procesa cuando su tamaño no cambió en dos vueltas del reloj."""
        for ruta, antes in list(self.espera.items()):
            p = Path(ruta)
            if not p.is_file():
                self.espera.pop(ruta)
                continue
            ahora = p.stat().st_size
            if ahora == antes and ahora > 0:
                self.espera.pop(ruta)
                self.vistos[ruta] = ahora
                self._procesar(p)
            else:
                self.espera[ruta] = ahora

    def _procesar(self, p: Path) -> None:
        v = next((x for x in self.lista() if Path(x["carpeta"]) == p.parent), None)
        if v is None:
            return
        try:
            archivo = self.servidor.pedir("/api/raphi/locales", {"rutas": [str(p)]})[0]
            destino = p.parent / SALIDA
            destino.mkdir(exist_ok=True)
            self.servidor.pedir("/api/raphi/trabajos", {"operacion": f"receta:{v['receta']}", "archivos": [archivo["id"]],
                                                        "destino": str(destino)})
            self.avisar("Raphi", f"{p.name}: en camino por «{v['receta']}»")
        except Exception as e:  # noqa: BLE001  una carpeta vigilada nunca tumba la ventana
            self.avisar("Raphi", f"{p.name}: no se pudo procesar ({e})")
