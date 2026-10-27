"""El puente que la web ve como `window.raphiEscritorio` (QWebChannel). Cada método de `web/src/lib/escritorio.ts`
tiene aquí su `@Slot`; los valores vuelven a la web como JSON (texto), que el guion de `ventana.py` convierte.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog

from escritorio import dolphin


class Puente(QObject):
    def __init__(self, ventana, vigilancia, avisar) -> None:
        super().__init__()
        self.ventana, self.vigilancia, self.avisar = ventana, vigilancia, avisar

    @Slot(str, result=str)
    def elegirArchivos(self, filtro: str) -> str:
        filtro_qt = f"Archivos ({filtro});;Todos (*)" if filtro.strip() else "Todos (*)"
        rutas, _ = QFileDialog.getOpenFileNames(self.ventana, "Elegir archivos", "", filtro_qt)
        return json.dumps(rutas)

    @Slot(result=str)
    def elegirCarpeta(self) -> str:
        return json.dumps(QFileDialog.getExistingDirectory(self.ventana, "Elegir carpeta") or None)

    @Slot(str, result=str)
    def abrirCarpeta(self, ruta: str) -> str:
        p = Path(ruta)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(p if p.is_dir() else p.parent)))
        return "null"

    @Slot(str, result=str)
    def abrirArchivo(self, ruta: str) -> str:
        QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))
        return "null"

    @Slot(str, str, result=str)
    def copiarA(self, rutas_json: str, carpeta: str) -> str:
        hechas = []
        for r in json.loads(rutas_json):
            origen, destino = Path(r), Path(carpeta) / Path(r).name
            n = 2
            while destino.exists():
                destino = Path(carpeta) / f"{origen.stem}-{n}{origen.suffix}"
                n += 1
            (shutil.copytree if origen.is_dir() else shutil.copy2)(origen, destino)
            hechas.append(str(destino))
        return json.dumps(hechas)

    @Slot(str, str, result=str)
    def vigilar(self, carpeta: str, receta: str) -> str:
        return json.dumps(self.vigilancia.vigilar(carpeta, receta))

    @Slot(str, result=str)
    def dejarDeVigilar(self, carpeta: str) -> str:
        return json.dumps(self.vigilancia.dejar(carpeta))

    @Slot(result=str)
    def vigiladas(self) -> str:
        return json.dumps(self.vigilancia.lista())

    @Slot(bool, result=str)
    def menusDolphin(self, instalar: bool) -> str:
        return json.dumps(dolphin.instalar(instalar))

    @Slot(result=str)
    def hayMenusDolphin(self) -> str:
        return json.dumps(dolphin.hay())

    @Slot(str, str, result=str)
    def notificar(self, titulo: str, texto: str) -> str:
        self.avisar(titulo, texto)
        return "null"


# El lado de la web: crea `window.raphiEscritorio` en el acto (para que `hayEscritorio()` sea cierto desde el primer
# pintado) y cada método espera a que el canal esté listo. Los argumentos que no son texto viajan como JSON.
GUION = r"""
(() => {
  const listo = new Promise((ok) => {
    const conectar = () => new QWebChannel(qt.webChannelTransport, (canal) => ok(canal.objects.puente));
    if (window.qt && window.qt.webChannelTransport) conectar();
    else document.addEventListener('DOMContentLoaded', conectar);
  });
  const llamar = (metodo, ...args) => listo.then((p) => new Promise((ok) => p[metodo](...args, (r) => ok(JSON.parse(r)))));
  window.raphiEscritorio = {
    elegirArchivos: (filtro) => llamar('elegirArchivos', filtro || ''),
    elegirCarpeta: () => llamar('elegirCarpeta'),
    abrirCarpeta: (ruta) => llamar('abrirCarpeta', ruta),
    abrirArchivo: (ruta) => llamar('abrirArchivo', ruta),
    copiarA: (rutas, carpeta) => llamar('copiarA', JSON.stringify(rutas), carpeta),
    vigilar: (carpeta, receta) => llamar('vigilar', carpeta, receta),
    dejarDeVigilar: (carpeta) => llamar('dejarDeVigilar', carpeta),
    vigiladas: () => llamar('vigiladas'),
    menusDolphin: (si) => llamar('menusDolphin', Boolean(si)),
    hayMenusDolphin: () => llamar('hayMenusDolphin'),
    notificar: (t, x) => llamar('notificar', t, x),
  };
})();
"""
