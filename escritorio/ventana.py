"""La ventana de Raphi escritorio: QtWebEngine con la web de Raphi, su sesión, el puente, lo soltado y la bandeja.

- **La sesión**: antes de que la página cargue, un guion pone la ficha del servidor donde la cáscara mínima de Tiqsi
  guarda la suya (`tiqsi_token`), así que no hay pantalla de inicio de sesión.
- **Lo soltado**: un archivo arrastrado desde Dolphin a la ventana llega a la web como su RUTA (evento `raphi:rutas`),
  no como una copia subida; así una operación puede escribir junto al original. Sin tecla, lo toma la zona para soltar
  de la pantalla abierta (y, si esa pantalla no tiene, se abren Herramientas); con **Shift**, la Mesa de trabajo; con
  **Alt**, Herramientas y su menú «a qué se puede convertir» (`destino_de`).
- **La bandeja del sistema**: el ícono abre la ventana y su menú muestra la **zona para soltar**, una ventanita que
  queda encima de todo: lo que se suelta en ella abre Raphi con esos archivos (el gesto de Tangerine en Plasma).
- **Una sola instancia**: si Raphi ya está abierto, `raphi escritorio archivo.pdf` (el menú de Dolphin) le manda los
  archivos por un socket local en vez de abrir otra ventana.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtCore import QEvent, QFile, QIODevice, QObject, QSettings, QSize, Qt, QUrl
from PySide6.QtGui import QAction, QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineScript
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QMenu, QSystemTrayIcon, QVBoxLayout, QWidget

from escritorio import puente as modulo_puente
from escritorio.servidor import Servidor
from escritorio.vigilancia import Vigilancia

NOMBRE_SOCKET = "raphi-escritorio"
ICONO = "document-edit"


def _rutas(evento) -> list[str]:
    datos = evento.mimeData()
    return [u.toLocalFile() for u in datos.urls() if u.isLocalFile()] if datos and datos.hasUrls() else []


def destino_de(teclas) -> str | None:
    """A qué pantalla van los archivos soltados según la tecla apretada: Shift, la Mesa de trabajo; Alt, Herramientas;
    sin tecla, None (la pantalla abierta)."""
    if teclas & Qt.KeyboardModifier.ShiftModifier:
        return "/raphi/mesa"
    if teclas & Qt.KeyboardModifier.AltModifier:
        return "/raphi"
    return None


# Lo que la web declara de cada tarjeta de herramienta (Herramientas.tsx): qué pantalla abre y qué extensiones acepta.
# MARCAR resalta la que queda bajo el puntero mientras se arrastra; TARJETA dice cuál quedó bajo el punto al soltar.
MARCAR = ("(() => { const p = %s; document.querySelectorAll('[data-raphi-encima]').forEach((e) => e.removeAttribute('data-raphi-encima'));"
          " if (!p) return; const t = document.elementFromPoint(p[0], p[1])?.closest('[data-raphi-ruta]');"
          " if (t && !t.disabled) t.setAttribute('data-raphi-encima', '') })()")
TARJETA = ("(() => { const p = %s; const t = document.elementFromPoint(p[0], p[1])?.closest('[data-raphi-ruta]');"
           " return JSON.stringify(t && !t.disabled ? {ruta: t.dataset.raphiRuta, ext: t.dataset.raphiExt || '',"
           " titulo: t.dataset.raphiTitulo || ''} : null) })()")


class FiltroSoltar(QObject):
    """Recibe lo soltado sobre la vista web: si son archivos del disco, entrega sus rutas a la web (y el punto donde cayeron,
    para la tarjeta de herramienta que haya debajo)."""

    def __init__(self, ventana: "Ventana") -> None:
        super().__init__(ventana)
        self.ventana = ventana

    def eventFilter(self, _objeto, evento) -> bool:
        if evento.type() in (QEvent.Type.DragEnter, QEvent.Type.DragMove) and _rutas(evento):
            evento.acceptProposedAction()
            self.ventana.marcar(self.ventana.punto(evento.position()))
            return True
        if evento.type() == QEvent.Type.DragLeave:
            self.ventana.marcar(None)
            return False
        if evento.type() == QEvent.Type.Drop and (rutas := _rutas(evento)):
            evento.acceptProposedAction()
            self.ventana.marcar(None)
            self.ventana.entregar(rutas, destino_de(evento.modifiers()), self.ventana.punto(evento.position()))
            return True
        return False


class ZonaSoltar(QWidget):
    """La ventanita para soltar: siempre encima, sin marco; lo soltado abre Raphi con esos archivos."""

    def __init__(self, ventana: "Ventana") -> None:
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.ventana = ventana
        self.setAcceptDrops(True)
        self.setFixedSize(QSize(150, 110))
        self.setWindowTitle("Raphi: soltar aquí")
        caja = QVBoxLayout(self)
        etiqueta = QLabel("Soltar aquí\npara Raphi")
        etiqueta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caja.addWidget(etiqueta)
        self.setStyleSheet("QWidget{background:#1f3a93;color:white;border-radius:14px;font-weight:600}")
        self._arrastre = None

    def dragEnterEvent(self, e):
        if _rutas(e):
            e.acceptProposedAction()

    def dropEvent(self, e):
        if rutas := _rutas(e):
            e.acceptProposedAction()
            self.ventana.entregar(rutas, destino_de(e.modifiers()))

    def mousePressEvent(self, e):
        self._arrastre = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._arrastre is not None:
            self.move(e.globalPosition().toPoint() - self._arrastre)

    def mouseReleaseEvent(self, _e):
        self._arrastre = None


class Ventana(QMainWindow):
    def __init__(self, servidor: Servidor, ajustes: QSettings) -> None:
        super().__init__()
        self.servidor, self.ajustes = servidor, ajustes
        self.setWindowTitle("Raphi")
        self.setWindowIcon(QIcon.fromTheme(ICONO))
        self.resize(1280, 860)
        self.pendientes: list[tuple[list[str], str | None]] = []
        self.cargada = False

        # Perfil propio y persistente. Su padre es la aplicación, no la ventana: la página debe destruirse antes que él.
        perfil = QWebEngineProfile("raphi", QApplication.instance())
        sesion = QWebEngineScript()
        sesion.setName("raphi-sesion")
        sesion.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        sesion.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        sesion.setSourceCode("localStorage.setItem('tiqsi_token', %s);localStorage.setItem('tiqsi_rol','administrador');"
                             "localStorage.setItem('tiqsi_nombre', %s);" % (json.dumps(servidor.ficha), json.dumps("Raphi")))
        canal_js = QFile(":/qtwebchannel/qwebchannel.js")
        canal_js.open(QIODevice.OpenModeFlag.ReadOnly)
        canal = QWebEngineScript()
        canal.setName("raphi-puente")
        canal.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        canal.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        canal.setSourceCode(bytes(canal_js.readAll()).decode() + modulo_puente.GUION)
        perfil.scripts().insert(sesion)
        perfil.scripts().insert(canal)

        self.vista = QWebEngineView(self)
        self.vista.setPage(QWebEnginePage(perfil, self.vista))
        self.vigilancia = Vigilancia(servidor, ajustes, self.avisar)
        self.puente = modulo_puente.Puente(self, self.vigilancia, self.avisar)
        self.canal = QWebChannel(self.vista.page())
        self.canal.registerObject("puente", self.puente)
        self.vista.page().setWebChannel(self.canal)
        self.vista.loadFinished.connect(self._cargada)
        self.setCentralWidget(self.vista)
        self.vista.setAcceptDrops(True)
        self._filtro = FiltroSoltar(self)
        self.vista.installEventFilter(self._filtro)
        if self.vista.focusProxy():
            self.vista.focusProxy().installEventFilter(self._filtro)
        self.vista.load(QUrl(f"{servidor.url}/raphi"))

        self.zona = ZonaSoltar(self)
        self.bandeja = QSystemTrayIcon(QIcon.fromTheme(ICONO), self)
        menu = QMenu()
        for texto, hacer in (("Abrir Raphi", self.mostrar), ("Zona para soltar", self.alternar_zona),
                             ("Salir", QApplication.instance().quit)):
            accion = QAction(texto, menu)
            accion.triggered.connect(hacer)
            menu.addAction(accion)
        self.bandeja.setContextMenu(menu)
        self.bandeja.activated.connect(lambda r: self.mostrar() if r == QSystemTrayIcon.ActivationReason.Trigger else None)
        self.bandeja.setToolTip("Raphi")
        self.bandeja.show()
        if self.ajustes.value("geometria"):
            self.restoreGeometry(self.ajustes.value("geometria"))

    def _cargada(self, ok: bool) -> None:
        self.cargada = ok
        if ok and self.pendientes:
            pendientes, self.pendientes = self.pendientes, []
            for rutas, destino in pendientes:
                self.entregar(rutas, destino)

    def punto(self, posicion) -> list[float]:
        """Un punto de la vista en píxeles de la página (la vista los da con su zoom)."""
        z = self.vista.zoomFactor() or 1
        return [posicion.x() / z, posicion.y() / z]

    def marcar(self, punto: list[float] | None) -> None:
        if self.cargada:
            self.vista.page().runJavaScript(MARCAR % json.dumps(punto))

    def entregar(self, rutas: list[str], destino: str | None = None, punto: list[float] | None = None) -> None:
        """Las rutas van a la web: a `destino` (una pantalla de Raphi, por la tecla); si no, a la tarjeta de herramienta
        que quedó bajo `punto`; si no, a la pantalla abierta, cuya zona para soltar marca el evento como atendido; y si
        nadie lo atiende (Trabajos, Recetas, Sistema), se abren Herramientas. Sin la página cargada, esperan a que cargue."""
        self.mostrar()
        if not self.cargada:
            self.pendientes.append((rutas, destino))
            return
        if destino:
            self._abrir(destino, rutas)
            return
        if punto is not None:
            self.vista.page().runJavaScript(TARJETA % json.dumps(punto), 0,
                                            lambda t: self._a_tarjeta(json.loads(t), rutas) if t and t != "null" else self._a_pantalla(rutas))
            return
        self._a_pantalla(rutas)

    def _a_tarjeta(self, tarjeta: dict, rutas: list[str]) -> None:
        """Lo soltado sobre una herramienta la abre con los archivos que acepta. (La página la devuelve como texto JSON:
        un objeto de JavaScript no siempre llega entero a Python.)"""
        extensiones = [e for e in tarjeta.get("ext", "").split(",") if e]
        sirven = [r for r in rutas if not extensiones or Path(r).suffix.lower() in extensiones]
        if not sirven:
            self.avisar("Raphi", f"«{tarjeta.get('titulo') or 'Esa herramienta'}» no acepta esos archivos.")
            return
        self._abrir(tarjeta["ruta"], sirven)

    def _a_pantalla(self, rutas: list[str]) -> None:
        self.vista.page().runJavaScript(
            "window.dispatchEvent(new CustomEvent('raphi:rutas', {detail: %s, cancelable: true}))" % json.dumps(rutas),
            0, lambda libre: self._abrir("/raphi", rutas) if libre else None)

    def _abrir(self, pantalla: str, rutas: list[str]) -> None:
        """Registra las rutas en el servidor (sin copiarlas) y abre esa pantalla con ellas (`?archivos=`)."""
        try:
            ids = ",".join(a["id"] for a in self.servidor.pedir("/api/raphi/locales", {"rutas": rutas}))
        except Exception as e:  # noqa: BLE001 — se avisa y la ventana sigue
            self.avisar("Raphi", f"No se pudieron abrir los archivos: {e}")
            return
        if ids:
            self.vista.page().runJavaScript("location.assign(%s)" % json.dumps(f"{pantalla}?archivos={ids}"))

    def mostrar(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def alternar_zona(self) -> None:
        self.zona.setVisible(not self.zona.isVisible())

    def avisar(self, titulo: str, texto: str) -> None:
        self.bandeja.showMessage(titulo, texto, QIcon.fromTheme(ICONO), 6000)

    def closeEvent(self, e) -> None:
        self.ajustes.setValue("geometria", self.saveGeometry())
        super().closeEvent(e)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    rutas = [str(Path(a).resolve()) for a in argv if not a.startswith("-")]
    # ¿Ya hay un Raphi abierto? Se le mandan los archivos y se termina.
    otro = QLocalSocket()
    otro.connectToServer(NOMBRE_SOCKET)
    if otro.waitForConnected(300):
        otro.write(json.dumps(rutas).encode())
        otro.waitForBytesWritten(1000)
        otro.disconnectFromServer()
        return 0

    QApplication.setApplicationName("Raphi")
    QApplication.setOrganizationName("achalma")
    QApplication.setDesktopFileName("raphi")
    app = QApplication([sys.argv[0], *argv])
    app.setQuitOnLastWindowClosed(True)
    ajustes = QSettings("achalma", "raphi")
    servidor = Servidor()
    try:
        servidor.arrancar()
    except RuntimeError as e:
        print(f"raphi: {e}", file=sys.stderr)
        return 1
    ventana = Ventana(servidor, ajustes)
    QLocalServer.removeServer(NOMBRE_SOCKET)
    escucha = QLocalServer()
    escucha.listen(NOMBRE_SOCKET)

    def recibir():
        conexion = escucha.nextPendingConnection()
        conexion.waitForReadyRead(1000)
        try:
            ventana.entregar(json.loads(bytes(conexion.readAll()).decode() or "[]"))
        except ValueError:
            ventana.mostrar()

    escucha.newConnection.connect(recibir)
    ventana.show()
    if rutas:
        ventana.entregar(rutas)
    app.aboutToQuit.connect(servidor.detener)
    try:
        return app.exec()
    finally:
        servidor.detener()
