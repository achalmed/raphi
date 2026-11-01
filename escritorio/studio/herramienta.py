"""La página de una herramienta (o de una receta): archivos, opciones, salida, simular y ejecutar.

Es la misma página para las 60 operaciones: cabecera, lista de archivos que acepta lo soltado desde Dolphin, el
formulario de su ficha, dónde dejar la salida, «solo simular» y el resultado con cada archivo (abrir, abrir su
carpeta) y cada error por su nombre. Corre en un `FunctionWorker` de gui_comun: la consola y los avisos del marco
dicen cuándo terminó.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QPushButton, QRadioButton, QScrollArea, QFrame,
                               QVBoxLayout, QWidget)

from gui_comun.diseno import clase, icono_trazo, variante
from gui_comun.widgets.tarjetas import ListaConVacio, Tarjeta
from gui_comun.workers.function_worker import FunctionWorker

from escritorio.studio import motor_local
from escritorio.studio.formulario import Formulario


class ListaArchivos(QListWidget):
    """Archivos de entrada: se sueltan desde Dolphin, se añaden con el diálogo o se quitan con Supr."""

    cambiada = Signal()

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DropOnly)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("QListWidget { background: transparent; border: none; }")
        self.setIconSize(QSize(18, 18))

    def agregar(self, rutas: list[str]) -> None:
        actuales = set(self.rutas())
        for r in rutas:
            if r and r not in actuales:
                item = QListWidgetItem(icono_trazo("carpeta" if Path(r).is_dir() else "documento"), Path(r).name)
                item.setToolTip(r)
                item.setData(Qt.UserRole, r)
                self.addItem(item)
        self.cambiada.emit()

    def rutas(self) -> list[str]:
        return [self.item(i).data(Qt.UserRole) for i in range(self.count())]

    def quitar_seleccion(self) -> None:
        for item in self.selectedItems():
            self.takeItem(self.row(item))
        self.cambiada.emit()

    def dragEnterEvent(self, e) -> None:
        e.acceptProposedAction() if e.mimeData().hasUrls() else super().dragEnterEvent(e)

    dragMoveEvent = dragEnterEvent

    def dropEvent(self, e) -> None:
        self.agregar([u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()])
        e.acceptProposedAction()

    def keyPressEvent(self, e) -> None:
        if e.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.quitar_seleccion()
            return
        super().keyPressEvent(e)


class PaginaHerramienta(QWidget):
    """`ficha`: la de una operación del motor, o la de una receta (con `receta=True`)."""

    volver = Signal()

    def __init__(self, ventana, ficha: dict, icono: str, receta: bool = False):
        super().__init__()
        self.ventana, self.ficha, self.es_receta = ventana, ficha, receta
        self._informe = None
        contenido = QWidget()
        raiz = QVBoxLayout(contenido)
        raiz.setContentsMargins(28, 18, 28, 24)
        raiz.setSpacing(14)

        # --- cabecera -----------------------------------------------------------------------------------------
        cabeza = QHBoxLayout()
        atras = variante(QPushButton(icono_trazo("volver"), " Volver"), "fantasma")
        atras.clicked.connect(self.volver.emit)
        cabeza.addWidget(atras, 0, Qt.AlignTop)
        ic = QLabel()
        ic.setObjectName("mosaicoIcono")
        ic.setFixedSize(46, 46)
        ic.setAlignment(Qt.AlignCenter)
        ic.setPixmap(icono_trazo(icono).pixmap(QSize(26, 26), QIcon.Selected))   # el color del acento
        cabeza.addWidget(ic, 0, Qt.AlignTop)
        textos = QVBoxLayout()
        textos.setSpacing(2)
        titulo = QLabel(ficha["titulo"])
        titulo.setObjectName("tituloPagina")
        desc = QLabel(ficha["descripcion"])
        desc.setObjectName("subtituloPagina")
        desc.setWordWrap(True)
        textos.addWidget(titulo)
        textos.addWidget(desc)
        cabeza.addLayout(textos, 1)
        raiz.addLayout(cabeza)
        if ficha.get("faltan"):
            aviso = clase(QLabel(f"Falta en esta máquina: {', '.join(ficha['faltan'])}. Instálalo para usar esta "
                                 "herramienta."), "suave")
            aviso.setWordWrap(True)
            aviso.setStyleSheet("padding: 10px 12px; border-radius: 8px; background: rgba(217,119,6,0.14);")
            raiz.addWidget(aviso)

        # --- archivos y opciones ------------------------------------------------------------------------------
        fila = QHBoxLayout()
        fila.setSpacing(14)
        self.sin_archivos = ficha.get("minimo_entradas", 1) == 0 or ficha.get("entrada") == "ninguna"
        self.archivos = ListaArchivos()
        if not self.sin_archivos:
            botones = QHBoxLayout()
            b_mas = variante(QPushButton(icono_trazo("mas"), " Archivos"), "fantasma")
            b_mas.clicked.connect(self._elegir_archivos)
            b_carpeta = variante(QPushButton(icono_trazo("carpeta"), " Carpeta"), "fantasma")
            b_carpeta.clicked.connect(self._elegir_carpeta)
            b_quitar = variante(QPushButton(icono_trazo("quitar"), ""), "fantasma")
            b_quitar.setToolTip("Quitar lo seleccionado (Supr)")
            b_quitar.clicked.connect(self.archivos.quitar_seleccion)
            for b in (b_mas, b_carpeta, b_quitar):
                botones.addWidget(b)
            botones.addStretch(1)
            acepta = ", ".join(e.lstrip(".").upper() for e in ficha.get("extensiones", [])[:8]) or "carpetas o archivos"
            self.envoltura = ListaConVacio(f"Suelta aquí los archivos\n{acepta}")
            self.envoltura.pila.removeWidget(self.envoltura.lista)
            self.envoltura.lista.deleteLater()
            self.envoltura.lista = self.archivos
            self.envoltura.pila.insertWidget(0, self.archivos)
            self.envoltura.vacio.setAcceptDrops(False)
            self.archivos.cambiada.connect(self.envoltura.actualizar)
            self.envoltura.actualizar()
            self.setAcceptDrops(True)
            caja = Tarjeta("Archivos")
            caja.cuerpo.addWidget(self.envoltura, 1)
            caja.cuerpo.addLayout(botones)
            caja.setMinimumHeight(260)
            fila.addWidget(caja, 1)

        opciones = Tarjeta("Opciones")
        self.formulario = Formulario(ficha.get("parametros", []))
        opciones.cuerpo.addWidget(self.formulario)
        opciones.cuerpo.addSpacing(6)
        opciones.cuerpo.addWidget(clase(QLabel("Dónde dejar el resultado"), "suave"))
        self.junto = QRadioButton("Junto a cada original" if not self.sin_archivos else "En Descargas")
        self.en_carpeta = QRadioButton("En otra carpeta:")
        self.junto.setChecked(True)
        self.carpeta = QLineEdit()
        self.carpeta.setPlaceholderText("elige una carpeta…")
        b_carpeta_salida = variante(QPushButton("…"), "fantasma")
        b_carpeta_salida.setFixedWidth(40)
        b_carpeta_salida.clicked.connect(self._elegir_salida)
        destino = QHBoxLayout()
        destino.addWidget(self.en_carpeta)
        destino.addWidget(self.carpeta, 1)
        destino.addWidget(b_carpeta_salida)
        opciones.cuerpo.addWidget(self.junto)
        opciones.cuerpo.addLayout(destino)
        opciones.cuerpo.addStretch(1)
        fila.addWidget(opciones, 1)
        raiz.addLayout(fila)

        # --- ejecutar -----------------------------------------------------------------------------------------
        accion = QHBoxLayout()
        self.simular = QCheckBox("Solo simular (dice qué haría, no escribe nada)")
        accion.addWidget(self.simular)
        accion.addStretch(1)
        self.b_ejecutar = variante(QPushButton("Ejecutar"), "primario")
        self.b_ejecutar.setMinimumWidth(150)
        self.b_ejecutar.setShortcut("Ctrl+Return")
        self.b_ejecutar.setToolTip("Ctrl+Intro")
        self.b_ejecutar.clicked.connect(self.ejecutar)
        self.b_ejecutar.setEnabled(not ficha.get("faltan"))
        accion.addWidget(self.b_ejecutar)
        raiz.addLayout(accion)

        # --- resultado ----------------------------------------------------------------------------------------
        self.resultado = Tarjeta("Resultado")
        self.lista_resultado = QListWidget()
        self.lista_resultado.setFrameShape(QFrame.NoFrame)
        self.lista_resultado.setStyleSheet("QListWidget { background: transparent; border: none; }")
        self.lista_resultado.setWordWrap(True)
        self.lista_resultado.itemDoubleClicked.connect(self._abrir_item)
        self.resultado.cuerpo.addWidget(self.lista_resultado)
        botones_res = QHBoxLayout()
        self.b_abrir_carpeta = variante(QPushButton(icono_trazo("abrir"), " Abrir la carpeta"), "fantasma")
        self.b_abrir_carpeta.clicked.connect(self._abrir_carpeta)
        botones_res.addStretch(1)
        botones_res.addWidget(self.b_abrir_carpeta)
        self.resultado.cuerpo.addLayout(botones_res)
        self.resultado.setMinimumHeight(170)
        self.resultado.hide()
        raiz.addWidget(self.resultado, 1)
        raiz.addStretch(0)

        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        area.setWidget(contenido)
        fuera = QVBoxLayout(self)
        fuera.setContentsMargins(0, 0, 0, 0)
        fuera.addWidget(area)

    # ------------------------------------------------------------------------------------------------------ API
    def cargar(self, rutas: list[str]) -> None:
        if not self.sin_archivos:
            self.archivos.agregar(rutas)

    def ejecutar(self) -> None:
        entradas = [] if self.sin_archivos else self.archivos.rutas()
        if not self.sin_archivos and not entradas:
            self.ventana.marco.avisar("Faltan archivos", "Suelta o añade al menos uno.", "aviso")
            return
        destino = self.carpeta.text().strip() if self.en_carpeta.isChecked() else None
        if self.en_carpeta.isChecked() and not destino:
            self.ventana.marco.avisar("Falta la carpeta de salida", "Elige una o marca «Junto a cada original».",
                                      "aviso")
            return
        simular = self.simular.isChecked()
        if self.es_receta:
            worker = FunctionWorker(motor_local.ejecutar_receta, self.ficha["id"], entradas, destino, simular,
                                    description=self.ficha["titulo"])
        else:
            worker = FunctionWorker(motor_local.ejecutar_operacion, self.ficha["id"], entradas,
                                    self.formulario.valores(), destino, simular, description=self.ficha["titulo"])
        worker.result_ready.connect(self._mostrar)
        worker.failed.connect(lambda error: self._mostrar_error(error))
        worker.finished.connect(lambda: self.b_ejecutar.setEnabled(True))
        self.b_ejecutar.setEnabled(False)
        self.ventana.run_function_worker(worker, self.ficha["titulo"] + (" (simulación)" if simular else ""))

    # ------------------------------------------------------------------------------------------------- privado
    def _mostrar(self, informe) -> None:
        self._informe = informe
        self.lista_resultado.clear()
        for e in informe.elementos:
            r = e.resultado
            if not e.ok:
                item = QListWidgetItem(icono_trazo("quitar"), f"{Path(e.entrada).name}: {e.error}")
                self.lista_resultado.addItem(item)
                continue
            for linea in (r.plan if r else []):
                self.lista_resultado.addItem(QListWidgetItem(icono_trazo("receta"), linea))
            for archivo in (r.archivos if r else []):
                item = QListWidgetItem(icono_trazo("carpeta" if Path(archivo).is_dir() else "documento"),
                                       f"{Path(archivo).name}\n{Path(archivo).parent}")
                item.setData(Qt.UserRole, str(archivo))
                item.setToolTip("Doble clic para abrir")
                self.lista_resultado.addItem(item)
            for linea in (r.mensajes if r else [])[:12]:
                self.lista_resultado.addItem(QListWidgetItem(linea))
        self.resultado.show()
        self.b_abrir_carpeta.setVisible(bool(informe.archivos))
        fallidos = sum(not e.ok for e in informe.elementos)
        if fallidos:
            self.ventana.marco.avisar(f"{fallidos} de {len(informe.elementos)} con error",
                                      "Cada error está en el resultado, con el nombre de su archivo.", "error")

    def _mostrar_error(self, error: str) -> None:
        self.lista_resultado.clear()
        self.lista_resultado.addItem(QListWidgetItem(icono_trazo("quitar"), error))
        self.resultado.show()
        self.b_abrir_carpeta.hide()

    def _abrir_item(self, item: QListWidgetItem) -> None:
        ruta = item.data(Qt.UserRole)
        if ruta:
            QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))

    def _abrir_carpeta(self) -> None:
        if self._informe and self._informe.archivos:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(self._informe.archivos[0]).parent)))

    def _elegir_archivos(self) -> None:
        ext = " ".join(f"*{e}" for e in self.ficha.get("extensiones", []))
        filtro = f"Archivos que acepta ({ext})" if ext else "Todos los archivos (*)"
        rutas, _ = QFileDialog.getOpenFileNames(self, self.ficha["titulo"], str(Path.home()), filtro)
        self.archivos.agregar(rutas)

    def _elegir_carpeta(self) -> None:
        ruta = QFileDialog.getExistingDirectory(self, "Elegir una carpeta", str(Path.home()))
        if ruta:
            self.archivos.agregar([ruta])

    def _elegir_salida(self) -> None:
        ruta = QFileDialog.getExistingDirectory(self, "Carpeta de salida", self.carpeta.text() or str(Path.home()))
        if ruta:
            self.carpeta.setText(ruta)
            self.en_carpeta.setChecked(True)

    def dragEnterEvent(self, e) -> None:
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e) -> None:
        self.cargar([u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()])
        e.acceptProposedAction()
