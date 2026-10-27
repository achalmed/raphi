"""Dominio: Sistema.

Diagnóstico unificado de dependencias (docflow doctor + pdf-suite deps),
gestión del caché de conversiones, configuración TOML de docflow y ajustes
propios de la aplicación (rutas de backends).
"""

from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QLabel, QMessageBox, QPushButton,
)

from studio.core import paths
from studio.services import docflow, pdfsuite
from studio.ui.pages.base import BasePage, SelectorRuta


class SystemPage(BasePage):
    titulo = "Sistema"
    descripcion = ("Diagnóstico de dependencias, caché de conversiones, "
                   "configuración de docflow y ajustes de la aplicación.")

    def __init__(self, task_manager, settings, parent=None):
        super().__init__(task_manager, settings, parent)
        lay = self.layout_contenido()

        # --- diagnóstico -------------------------------------------------------
        caja_diag = QGroupBox("Diagnóstico de dependencias")
        fila_diag = QHBoxLayout(caja_diag)
        doctor = QPushButton("docflow doctor")
        doctor.clicked.connect(lambda: self.ejecutar("Diagnóstico docflow",
                                                     docflow.doctor(self.settings)))
        deps = QPushButton("pdf-suite deps")
        deps.clicked.connect(lambda: self.ejecutar("Diagnóstico pdf-suite",
                                                   pdfsuite.deps(settings=self.settings)))
        formatos = QPushButton("Formatos soportados")
        formatos.clicked.connect(lambda: self.ejecutar("Tabla de formatos",
                                                       docflow.formats_table(self.settings)))
        fila_diag.addWidget(doctor)
        fila_diag.addWidget(deps)
        fila_diag.addWidget(formatos)
        fila_diag.addStretch(1)
        lay.addWidget(caja_diag)

        # --- caché ------------------------------------------------------------------
        caja_cache = QGroupBox("Caché de conversiones (docflow)")
        fila_cache = QHBoxLayout(caja_cache)
        for accion, etiqueta in (("stats", "Estadísticas"), ("prune", "Depurar"), ("clear", "Vaciar")):
            boton = QPushButton(etiqueta)
            boton.clicked.connect(lambda _=False, a=accion: self._cache(a))
            fila_cache.addWidget(boton)
        fila_cache.addStretch(1)
        lay.addWidget(caja_cache)

        # --- configuración docflow ------------------------------------------------------
        caja_conf = QGroupBox("Configuración de docflow (config.toml)")
        fila_conf = QHBoxLayout(caja_conf)
        for accion, etiqueta in (("init", "Crear config"), ("show", "Mostrar"), ("path", "Ruta")):
            boton = QPushButton(etiqueta)
            boton.clicked.connect(lambda _=False, a=accion: self.ejecutar(
                f"docflow config {a}", docflow.config(a, self.settings)))
            fila_conf.addWidget(boton)
        abrir_toml = QPushButton("Abrir en el editor")
        abrir_toml.clicked.connect(self._abrir_toml)
        fila_conf.addWidget(abrir_toml)
        fila_conf.addStretch(1)
        lay.addWidget(caja_conf)

        # --- ajustes de la app -------------------------------------------------------------
        caja_app = QGroupBox("Ajustes de Raphi (rutas de backends)")
        form = QFormLayout(caja_app)
        self._selectores = {}
        for clave, etiqueta, defecto in (
            ("backends/docflow", "Ejecutable docflow:", str(paths.DOCFLOW_BIN)),
            ("backends/pdfsuite", "Script pdf-suite:", str(paths.PDFSUITE_MAIN)),
            ("backends/pagecounter", "Carpeta page-counter:", str(paths.PAGECOUNTER_DIR)),
        ):
            selector = SelectorRuta("system", settings, carpeta=clave.endswith("pagecounter"))
            selector.campo.setPlaceholderText(defecto)
            selector.set_ruta(str(settings.value(clave, "")))
            self._selectores[clave] = selector
            form.addRow(etiqueta, selector)
        nota = QLabel("Vacío = usar el backend incluido en backends/ de Raphi. "
                      "Los cambios aplican a las próximas tareas.")
        nota.setWordWrap(True)
        form.addRow(nota)
        guardar = QPushButton("Guardar ajustes")
        guardar.clicked.connect(self._guardar_ajustes)
        form.addRow("", guardar)
        lay.addWidget(caja_app)
        lay.addStretch(1)

    def _cache(self, accion: str) -> None:
        if accion == "clear":
            respuesta = QMessageBox.question(
                self, "Vaciar caché",
                "¿Vaciar todo el caché de conversiones? Las próximas pasadas "
                "reconvertirán todos los archivos.")
            if respuesta != QMessageBox.Yes:
                return
        self.ejecutar(f"Caché · {accion}", docflow.cache(accion, self.settings))

    def _abrir_toml(self) -> None:
        if paths.DOCFLOW_CONFIG_TOML.is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(paths.DOCFLOW_CONFIG_TOML)))
        else:
            self.aviso("Aún no existe; usa «Crear config» primero.")

    def _guardar_ajustes(self) -> None:
        for clave, selector in self._selectores.items():
            self.settings.setValue(clave, selector.ruta())
        self.settings.sync()
