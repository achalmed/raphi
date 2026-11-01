"""La ventana de Raphi Studio: el marco común de los studios (gui_comun) con las páginas que arma el motor.

Barra lateral: Inicio · Documentos · PDF · Imágenes · Audio y video · Archivos · Recetas · Sistema. La paleta (Ctrl+K)
encuentra cualquiera de las herramientas por su nombre o sus palabras. Lo que se suelta sobre la ventana abre «¿qué
hacemos con esto?» con las herramientas que sirven para esos archivos; si solo una sirve, se abre directamente.
"""
from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtCore import QSettings, QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QListWidget, QListWidgetItem, QMainWindow, QMenu,
                               QMessageBox, QStackedWidget, QSystemTrayIcon, QWidget)

from gui_comun.diseno import icono_trazo, logo
from gui_comun.theming import aplicar_tema, disenador_de
from gui_comun.widgets.console_dock import ConsoleDock
from gui_comun.widgets.marco import montar_studio
from gui_comun.widgets.paleta import Comando

from raphi import VERSION, motor, recetas

from escritorio.studio.familias import FAMILIAS, familia_de, icono_de
from escritorio.studio.herramienta import PaginaHerramienta
from escritorio.studio.motor_local import MotorLocal
from escritorio.studio.paginas import (PaginaFamilia, PaginaInicio, PaginaParaArchivos, PaginaRecetas,
                                       PaginaSistema)

ACENTO = "violeta"
LOGO = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#888888" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 '
        '2-2V8z"/><path d="M14 3v5h5"/><path d="M8 13l2.5 2.5L16 10"/></svg>')


class Ajustes:
    """Lo que el marco espera de los ajustes de un studio (el tema), sobre los de la ventana de Raphi."""

    def __init__(self) -> None:
        self.q = QSettings("achalma", "raphi")

    def theme(self) -> str:
        return str(self.q.value("studio/tema", "sistema"))

    def set_theme(self, tema: str) -> None:
        self.q.setValue("studio/tema", tema)


class Ventana:
    """Envoltorio de la QMainWindow, con la forma que `gui_comun.widgets.marco.montar_studio` espera."""

    def __init__(self) -> None:
        app = QApplication.instance()
        self.settings = Ajustes()
        disenador = disenador_de(app) or aplicar_tema(app, self.settings.theme(), acento=ACENTO)
        self.ui = QMainWindow()
        self.ui.setWindowTitle(f"Raphi Studio {VERSION}")
        self.ui.setAcceptDrops(True)
        central = QWidget()
        fila = QHBoxLayout(central)
        self.ui.sidebar = QListWidget()
        self.ui.stack = QStackedWidget()
        fila.addWidget(self.ui.sidebar)
        fila.addWidget(self.ui.stack, 1)
        self.ui.setCentralWidget(central)
        self.ui.statusbar = self.ui.statusBar()
        self.console = ConsoleDock(self.ui)
        self.ui.addDockWidget(Qt.BottomDockWidgetArea, self.console)
        self._workers: list = []

        # --- Vigilancia: la misma de la ventana web, con el motor de este proceso ---------------------------------
        from escritorio.vigilancia import Vigilancia
        self.vigilancia = Vigilancia(MotorLocal(self), self.settings.q, self._avisar_bandeja)

        # --- páginas -----------------------------------------------------------------------------------------
        self.fichas = motor.operaciones()
        self.recetas = recetas.todas()
        self.controllers: dict[str, SimpleNamespace] = {}
        self._page_order: list[str] = []
        inicio = PaginaInicio(self.fichas, len(self.recetas), len(self.vigilancia.lista()))
        inicio.ir_a.connect(self.navigate)
        self._pagina("dashboard", "Inicio", "inicio", inicio)
        for id_, nombre, para_que, icono in FAMILIAS:
            pagina = PaginaFamilia(id_, nombre, para_que, self.fichas)
            pagina.abrir.connect(self.abrir_herramienta)
            self._pagina(id_, nombre, icono, pagina)
        pag_recetas = PaginaRecetas(self.recetas)
        pag_recetas.abrir.connect(lambda f: self.abrir_herramienta(f, receta=True))
        self._pagina("recetas", "Recetas", "receta", pag_recetas)
        self._pagina("sistema", "Sistema", "sistema", PaginaSistema(self, self.fichas, self.recetas))
        self.para_archivos = PaginaParaArchivos(self.fichas)
        self.para_archivos.abrir.connect(lambda f: self.abrir_herramienta(f, rutas=self.para_archivos.rutas))
        self.ui.stack.addWidget(self.para_archivos)
        self._herramientas: dict[str, PaginaHerramienta] = {}
        self.ui.sidebar.currentRowChanged.connect(lambda fila: self.ui.stack.setCurrentIndex(fila))
        self.ui.sidebar.setCurrentRow(0)

        # --- el marco común ------------------------------------------------------------------------------------
        self.marco = montar_studio(self, nombre="Raphi Studio", subtitulo="Documentos y medios", logo_svg=LOGO,
                                   disenador=disenador)
        for ficha in self.fichas:
            self.marco.comandos_extra.append(
                Comando(ficha["titulo"], lambda f=ficha: self.abrir_herramienta(f), grupo=ficha["categoria"],
                        icono=icono_trazo(icono_de(ficha)), palabras=" ".join(ficha.get("palabras", []))))
        for r in self.recetas:
            from escritorio.studio.paginas import _ficha_de_receta
            self.marco.comandos_extra.append(
                Comando(f"Receta: {r.nombre}", lambda r=r: self.abrir_herramienta(_ficha_de_receta(r), receta=True),
                        grupo="Recetas", icono=icono_trazo("receta")))
        self._bandeja()
        self.ui.dragEnterEvent = self._arrastre
        self.ui.dragMoveEvent = self._arrastre
        self.ui.dropEvent = self._soltar

    # ------------------------------------------------------------------------------------------------------- API
    def show(self) -> None:
        self.ui.show()

    def navigate(self, page_id: str) -> None:
        if page_id in self._page_order:
            fila = self._page_order.index(page_id)
            self.ui.sidebar.setCurrentRow(fila)
            self.ui.stack.setCurrentIndex(fila)

    def abrir_herramienta(self, ficha: dict, rutas: list[str] | None = None, receta: bool = False) -> None:
        clave = ("receta:" if receta else "") + ficha["id"]
        pagina = self._herramientas.get(clave)
        if pagina is None:
            pagina = PaginaHerramienta(self, ficha, "receta" if receta else icono_de(ficha), receta=receta)
            pagina.volver.connect(lambda: self.ui.stack.setCurrentIndex(max(0, self.ui.sidebar.currentRow())))
            self.ui.stack.addWidget(pagina)
            self._herramientas[clave] = pagina
        if rutas:
            pagina.cargar(rutas)
        familia = "recetas" if receta else familia_de(ficha)
        if familia in self._page_order:                      # la barra marca la familia de la herramienta abierta
            self.ui.sidebar.blockSignals(True)
            self.ui.sidebar.setCurrentRow(self._page_order.index(familia))
            self.ui.sidebar.blockSignals(False)
        self.ui.stack.setCurrentWidget(pagina)

    def entregar(self, rutas: list[str]) -> None:
        """Archivos que llegan (soltados, desde Dolphin o desde otra instancia): las herramientas que sirven."""
        self.ui.show()
        self.ui.raise_()
        self.ui.activateWindow()
        if not rutas:
            return
        self.para_archivos.para(rutas)
        utiles = self.para_archivos._mosaicos
        if len(utiles) == 1:
            self.abrir_herramienta(utiles[0][0], rutas=rutas)
        else:
            self.ui.stack.setCurrentWidget(self.para_archivos)
            if not utiles:
                self.marco.avisar("Ninguna herramienta los acepta", "Prueba con otro tipo de archivo.", "aviso")

    def run_function_worker(self, worker, nombre: str) -> None:
        self.console.attach_function_worker(worker, nombre)
        self._workers.append(worker)
        worker.finished.connect(lambda: worker in self._workers and self._workers.remove(worker))
        worker.start()

    # ------------------------------------------------------------------------------------------------ privado
    def _pagina(self, id_: str, nombre: str, icono: str, widget) -> None:
        self.controllers[id_] = SimpleNamespace(widget=widget)
        self._page_order.append(id_)
        self.ui.stack.addWidget(widget)
        item = QListWidgetItem(icono_trazo(icono), nombre)
        self.ui.sidebar.addItem(item)

    def _open_preferences(self) -> None:
        self.navigate("sistema")

    def _about(self) -> None:
        QMessageBox.about(self.ui, "Acerca de Raphi Studio",
                          f"<b>Raphi Studio</b> {VERSION}<br><br>Documentos, PDF, imágenes, audio y video, en tu "
                          "máquina: el original nunca se toca.<br><br>Cada herramienta es una operación del motor "
                          "de Raphi; la misma está en la CLI (<code>raphi</code>), en la web y en Qillqa.<br><br>"
                          "AGPL-3.0 · Edison Achalma")

    def _bandeja(self) -> None:
        self.bandeja = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        from PySide6.QtGui import QIcon
        self.bandeja = QSystemTrayIcon(QIcon(logo(LOGO, 64)), self.ui)
        menu = QMenu()
        mostrar = QAction("Mostrar Raphi Studio", menu, triggered=lambda: self.entregar([]))
        salir = QAction("Salir", menu, triggered=QApplication.instance().quit)
        menu.addAction(mostrar)
        menu.addAction(salir)
        self.bandeja.setContextMenu(menu)
        self.bandeja.activated.connect(lambda _r: self.entregar([]))
        self.bandeja.show()

    def _avisar_bandeja(self, titulo: str, texto: str) -> None:
        if getattr(self, "marco", None):
            self.marco.avisar(titulo, texto, "info")
        if getattr(self, "bandeja", None) and not self.ui.isActiveWindow():
            self.bandeja.showMessage(titulo, texto, QSystemTrayIcon.Information, 6000)

    def _arrastre(self, e) -> None:
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def _soltar(self, e) -> None:
        self.entregar([u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()])
        e.acceptProposedAction()
