"""Las páginas de la barra lateral de Raphi Studio: Inicio, una por familia, Recetas y Sistema.

Todas se arman de lo que el motor declara (fichas de operaciones, recetas, requisitos): ninguna lista una herramienta
a mano. La de una familia es una rejilla de mosaicos con un buscador; la de «para estos archivos» es la misma rejilla
con las herramientas que sirven para lo que se soltó.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QComboBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QPushButton, QVBoxLayout, QWidget)

from gui_comun.diseno import clase, icono_trazo, variante
from gui_comun.widgets.tarjetas import (Cifra, ListaConVacio, Mosaico, Tarjeta, encabezado, pagina_desplazable,
                                        rejilla_pareja, seccion)

from escritorio.studio.familias import FAMILIAS, acepta, familia_de, icono_de


class PaginaRejilla(QWidget):
    """Mosaicos de herramientas con un buscador; `abrir(ficha)` al elegir una."""

    abrir = Signal(dict)

    def __init__(self, titulo: str, subtitulo: str, fichas: list[dict], columnas: int = 3):
        super().__init__()
        self.columnas = columnas
        contenido = QWidget()
        self.raiz = QVBoxLayout(contenido)
        self.raiz.setSpacing(14)
        cabeza = QHBoxLayout()
        self.encabezado = encabezado(titulo, subtitulo)
        cabeza.addWidget(self.encabezado, 1)
        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("Filtrar…")
        self.buscador.setClearButtonEnabled(True)
        self.buscador.setFixedWidth(240)
        clase(self.buscador, "busqueda")
        self.buscador.textChanged.connect(self._filtrar)
        cabeza.addWidget(self.buscador, 0, Qt.AlignTop)
        self.raiz.addLayout(cabeza)
        self.rejilla_caja = QWidget()
        self.rejilla = rejilla_pareja(columnas)
        self.rejilla.setContentsMargins(0, 0, 0, 0)
        self.rejilla_caja.setLayout(self.rejilla)
        self.raiz.addWidget(self.rejilla_caja)
        self.vacio = clase(QLabel("Ninguna herramienta coincide."), "vacio")
        self.raiz.addWidget(self.vacio)
        self.raiz.addStretch(1)
        self._mosaicos: list[tuple[dict, Mosaico]] = []
        self.poner(fichas)
        fuera = QVBoxLayout(self)
        fuera.setContentsMargins(0, 0, 0, 0)
        fuera.addWidget(pagina_desplazable(contenido))

    def poner(self, fichas: list[dict]) -> None:
        for _f, m in self._mosaicos:
            self.rejilla.removeWidget(m)
            m.deleteLater()
        self._mosaicos = []
        for ficha in fichas:
            extra = " · falta " + ", ".join(ficha["faltan"]) if ficha.get("faltan") else ""
            m = Mosaico(icono_trazo(icono_de(ficha)), ficha["titulo"], ficha["descripcion"] + extra,
                        lambda f=ficha: self.abrir.emit(f))
            if ficha.get("faltan"):
                m.setEnabled(True)
                m.setToolTip(f"Falta {', '.join(ficha['faltan'])} en esta máquina")
            self._mosaicos.append((ficha, m))
        self._filtrar(self.buscador.text())

    def _filtrar(self, texto: str) -> None:
        texto = texto.strip().lower()
        visibles = [(f, m) for f, m in self._mosaicos
                    if not texto or texto in f"{f['titulo']} {f['descripcion']} {' '.join(f.get('palabras', []))}".lower()]
        for _f, m in self._mosaicos:
            self.rejilla.removeWidget(m)
            m.hide()
        for i, (_f, m) in enumerate(visibles):
            self.rejilla.addWidget(m, i // self.columnas, i % self.columnas)
            m.show()
        self.vacio.setVisible(not visibles)


class PaginaFamilia(PaginaRejilla):
    def __init__(self, familia: str, nombre: str, para_que: str, fichas: list[dict]):
        super().__init__(nombre, para_que, [f for f in fichas if familia_de(f) == familia])


class PaginaParaArchivos(PaginaRejilla):
    """Lo soltado sobre la ventana: las herramientas que sirven para esos archivos."""

    def __init__(self, fichas: list[dict]):
        self.todas = fichas
        self.rutas: list[str] = []
        super().__init__("¿Qué hacemos con esto?", "Herramientas para lo que soltaste", [])

    def para(self, rutas: list[str]) -> None:
        self.rutas = rutas
        nombres = ", ".join(Path(r).name for r in rutas[:3]) + (f" y {len(rutas) - 3} más" if len(rutas) > 3 else "")
        self.encabezado.findChild(QLabel, "subtituloPagina").setText(f"Herramientas para {nombres}")
        self.poner([f for f in self.todas if acepta(f, rutas)])


class PaginaInicio(QWidget):
    ir_a = Signal(str)

    def __init__(self, fichas: list[dict], recetas: int, vigiladas: int):
        super().__init__()
        contenido = QWidget()
        raiz = QVBoxLayout(contenido)
        raiz.setSpacing(14)
        raiz.addWidget(encabezado("Inicio", "Documentos, PDF, imágenes, audio y video en tu máquina: el original "
                                            "nunca se toca. Suelta archivos en cualquier parte de la ventana."))
        cifras = rejilla_pareja(4)
        disponibles = sum(not f.get("faltan") for f in fichas)
        for i, c in enumerate((Cifra("Herramientas", str(len(fichas)), f"{disponibles} listas en esta máquina"),
                               Cifra("Familias", str(len(FAMILIAS)), "Por el tipo de archivo"),
                               Cifra("Recetas", str(recetas), "Varios pasos de una vez"),
                               Cifra("Carpetas vigiladas", str(vigiladas), "Procesan lo que llega"))):
            cifras.addWidget(c, 0, i)
        raiz.addLayout(cifras)
        raiz.addSpacing(4)
        raiz.addWidget(seccion("Familias"))
        rejilla = rejilla_pareja(3)
        for i, (id_, nombre, para_que, icono) in enumerate(FAMILIAS):
            n = sum(familia_de(f) == id_ for f in fichas)
            rejilla.addWidget(Mosaico(icono_trazo(icono), f"{nombre} · {n}", para_que, lambda p=id_: self.ir_a.emit(p)),
                              i // 3, i % 3)
        rejilla.addWidget(Mosaico(icono_trazo("receta"), "Recetas", "Cadenas de herramientas guardadas: para archivo, "
                                  "para enviar, escaneos…", lambda: self.ir_a.emit("recetas")), 1, 2)
        raiz.addLayout(rejilla)
        soltar = Tarjeta()
        soltar.setMinimumHeight(130)
        texto = clase(QLabel("Suelta aquí archivos o carpetas desde Dolphin\nRaphi te muestra lo que puede hacer con "
                             "ellos (Ctrl+K busca cualquier herramienta)"), "vacio")
        texto.setAlignment(Qt.AlignCenter)
        soltar.cuerpo.addWidget(texto)
        raiz.addWidget(soltar, 1)
        fuera = QVBoxLayout(self)
        fuera.setContentsMargins(0, 0, 0, 0)
        fuera.addWidget(pagina_desplazable(contenido))


class PaginaRecetas(QWidget):
    abrir = Signal(dict)

    def __init__(self, recetas: list):
        super().__init__()
        contenido = QWidget()
        raiz = QVBoxLayout(contenido)
        raiz.setSpacing(14)
        raiz.addWidget(encabezado("Recetas", "Varias herramientas, una tras otra, con sus opciones guardadas. Las tuyas "
                                             "viven en ~/.config/raphi/recetas/ (YAML)."))
        rejilla = rejilla_pareja(2)
        from raphi.motor import obtener
        for i, r in enumerate(recetas):
            pasos = " → ".join(obtener(p.operacion).titulo for p in r.pasos)
            rejilla.addWidget(Mosaico(icono_trazo("receta"), r.nombre, f"{r.descripcion}\n{pasos}".strip(),
                                      lambda r=r: self.abrir.emit(_ficha_de_receta(r))), i // 2, i % 2)
        raiz.addLayout(rejilla)
        if not recetas:
            raiz.addWidget(clase(QLabel("No hay recetas."), "vacio"))
        raiz.addStretch(1)
        fuera = QVBoxLayout(self)
        fuera.setContentsMargins(0, 0, 0, 0)
        fuera.addWidget(pagina_desplazable(contenido))


def _ficha_de_receta(r) -> dict:
    from raphi.motor import obtener
    primero = obtener(r.pasos[0].operacion)
    return {"id": r.id, "titulo": r.nombre, "descripcion": r.descripcion or "Receta", "parametros": [],
            "extensiones": list(primero.extensiones), "entrada": "ninguna" if r.sin_entradas else primero.entrada,
            "minimo_entradas": 0 if r.sin_entradas else 1, "faltan": sorted({x for p in r.pasos
                                                                               for x in obtener(p.operacion).faltan()})}


class PaginaSistema(QWidget):
    """Lo que esta máquina tiene, los menús de Dolphin, las carpetas vigiladas y la versión web."""

    def __init__(self, ventana, fichas: list[dict], recetas: list):
        super().__init__()
        self.ventana = ventana
        contenido = QWidget()
        raiz = QVBoxLayout(contenido)
        raiz.setSpacing(14)
        from raphi import VERSION
        raiz.addWidget(encabezado("Sistema", f"Raphi {VERSION} · el motor corre en esta máquina; nada sale de ella."))

        fila = QHBoxLayout()
        fila.setSpacing(14)
        faltan = sorted({x for f in fichas for x in f.get("faltan", [])})
        req = Tarjeta("Programas que faltan")
        lista_req = ListaConVacio("Están todos: cada herramienta puede correr.")
        for programa in faltan:
            usan = [f["titulo"] for f in fichas if programa in f.get("faltan", [])]
            item = QListWidgetItem(icono_trazo("quitar"), f"{programa.removeprefix('py:')}\nlo usan: {', '.join(usan[:4])}")
            lista_req.lista.addItem(item)
        lista_req.actualizar()
        req.cuerpo.addWidget(lista_req, 1)
        req.setMinimumHeight(220)
        fila.addWidget(req, 1)

        dol = Tarjeta("Menús de Dolphin")
        from escritorio import dolphin
        self.lbl_dolphin = clase(QLabel(), "suave")
        self.lbl_dolphin.setWordWrap(True)
        self.b_dolphin = QPushButton()
        self.b_dolphin.clicked.connect(self._alternar_dolphin)
        dol.cuerpo.addWidget(clase(QLabel("Clic derecho sobre un archivo → Raphi → la herramienta, sin abrir la "
                                          "ventana."), "tenue"))
        dol.cuerpo.addWidget(self.lbl_dolphin)
        dol.cuerpo.addWidget(self.b_dolphin)
        dol.cuerpo.addStretch(1)
        web = variante(QPushButton(icono_trazo("abrir"), " Abrir la versión web (navegador)"), "fantasma")
        web.clicked.connect(lambda: subprocess.Popen([sys.executable, "-m", "raphi.sola"],
                                                     cwd=str(Path(__file__).resolve().parents[2])))
        dol.cuerpo.addWidget(web)
        fila.addWidget(dol, 1)
        raiz.addLayout(fila)
        self._dolphin = dolphin
        self._pintar_dolphin()

        vig = Tarjeta("Carpetas vigiladas: lo que llegue pasa por una receta y queda en su subcarpeta «raphi»")
        self.lista_vig = ListaConVacio("Ninguna carpeta vigilada.")
        vig.cuerpo.addWidget(self.lista_vig, 1)
        fila_vig = QHBoxLayout()
        self.combo_receta = QComboBox()
        for r in recetas:
            if not r.sin_entradas:
                self.combo_receta.addItem(r.nombre, r.id)
        b_vigilar = variante(QPushButton(icono_trazo("mas"), " Vigilar una carpeta"), "primario")
        b_vigilar.clicked.connect(self._vigilar)
        b_dejar = variante(QPushButton("Dejar de vigilar"), "peligro")
        b_dejar.clicked.connect(self._dejar)
        fila_vig.addWidget(QLabel("Receta:"))
        fila_vig.addWidget(self.combo_receta, 1)
        fila_vig.addWidget(b_vigilar)
        fila_vig.addWidget(b_dejar)
        vig.cuerpo.addLayout(fila_vig)
        vig.setMinimumHeight(220)
        raiz.addWidget(vig, 1)
        self._pintar_vigiladas()
        fuera = QVBoxLayout(self)
        fuera.setContentsMargins(0, 0, 0, 0)
        fuera.addWidget(pagina_desplazable(contenido))

    def _pintar_dolphin(self) -> None:
        hay = bool(self._dolphin.instalados())
        self.lbl_dolphin.setText("Instalados." if hay else "No están instalados.")
        self.b_dolphin.setText("Quitar los menús" if hay else "Instalar los menús")
        variante(self.b_dolphin, "peligro" if hay else "primario")

    def _alternar_dolphin(self) -> None:
        hay = bool(self._dolphin.instalados())
        self._dolphin.instalar(not hay)
        self._pintar_dolphin()
        self.ventana.marco.avisar("Menús de Dolphin " + ("quitados" if hay else "instalados"), "", "ok")

    def _pintar_vigiladas(self) -> None:
        self.lista_vig.lista.clear()
        for v in self.ventana.vigilancia.lista():
            item = QListWidgetItem(icono_trazo("carpeta"), f"{v['carpeta']}\nreceta: {v['receta']}")
            item.setData(Qt.UserRole, v["carpeta"])
            self.lista_vig.lista.addItem(item)
        self.lista_vig.actualizar()

    def _vigilar(self) -> None:
        carpeta = QFileDialog.getExistingDirectory(self, "Carpeta que vigilar", str(Path.home()))
        if carpeta and self.combo_receta.currentData():
            self.ventana.vigilancia.vigilar(carpeta, self.combo_receta.currentData())
            self._pintar_vigiladas()
            self.ventana.marco.avisar("Carpeta vigilada", carpeta, "ok")

    def _dejar(self) -> None:
        item = self.lista_vig.lista.currentItem()
        if item:
            self.ventana.vigilancia.dejar(item.data(Qt.UserRole))
            self._pintar_vigiladas()
