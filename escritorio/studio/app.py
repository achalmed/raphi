"""Arranque de Raphi Studio: una sola instancia (los archivos que llegan van a la ventana abierta) y su QApplication.

Comparte el nombre del socket con la ventana web: Dolphin y la CLI (`raphi escritorio archivo`) no necesitan saber
cuál de las dos está abierta.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtNetwork import QLocalServer, QLocalSocket

NOMBRE_SOCKET = "raphi-escritorio"


def datos_lanzador() -> dict:
    """El acceso directo de Raphi Studio en el menú de aplicaciones (gui_comun.lanzador)."""
    from escritorio.studio.ventana import ACENTO, LOGO
    raiz = Path(__file__).resolve().parents[2]
    return dict(app_id="raphi", nombre="Raphi Studio", comentario="Documentos, PDF, imágenes, audio y video",
                orden=[str(raiz / "run.sh")], logo_svg=LOGO, acento=ACENTO, categorias="Office;Graphics;AudioVideo;Utility;",
                palabras="pdf;convertir;comprimir;ocr;audio;video;transcribir;whisper;imagen;fotos;", archivos=True)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--instalar-lanzador" in argv or "--quitar-lanzador" in argv:
        from escritorio.studio import hay_gui_comun
        if not hay_gui_comun():
            print("raphi: falta gui-comun para el acceso directo de Raphi Studio", file=sys.stderr)
            return 1
        from gui_comun import lanzador
        return lanzador.desde_main(argv, **datos_lanzador())
    smoke = "--smoke" in argv
    rutas = [str(Path(a).resolve()) for a in argv if not a.startswith("-")]
    otro = QLocalSocket()
    otro.connectToServer(NOMBRE_SOCKET)
    if not smoke and otro.waitForConnected(300):
        otro.write(json.dumps(rutas).encode())
        otro.waitForBytesWritten(1000)
        otro.disconnectFromServer()
        return 0

    from gui_comun.diseno import preparar_plataforma
    preparar_plataforma()
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication
    QApplication.setApplicationName("Raphi Studio")
    QApplication.setOrganizationName("achalma")
    QApplication.setDesktopFileName("raphi")
    app = QApplication([sys.argv[0], *argv])
    from escritorio.studio.ventana import Ventana
    ventana = Ventana()
    escucha = None
    if not smoke:
        QLocalServer.removeServer(NOMBRE_SOCKET)
        escucha = QLocalServer()
        escucha.listen(NOMBRE_SOCKET)

        def recibir():
            conexion = escucha.nextPendingConnection()
            conexion.waitForReadyRead(1000)
            try:
                ventana.entregar(json.loads(bytes(conexion.readAll()).decode() or "[]"))
            except ValueError:
                ventana.entregar([])

        escucha.newConnection.connect(recibir)
    ventana.show()
    if rutas:
        ventana.entregar(rutas)
    if smoke:
        QTimer.singleShot(0, app.quit)
    return app.exec()
