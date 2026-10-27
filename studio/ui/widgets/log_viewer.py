"""Visor del log persistente de la aplicación (~/.local/state/raphi).

La consola muestra la sesión en vivo; este visor muestra el histórico en
disco, con filtro de texto y nivel.
"""

from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLineEdit, QPlainTextEdit, QPushButton,
    QVBoxLayout, QWidget,
)

from studio.core import paths

NIVELES = ("Todos", "INFO", "WARNING", "ERROR")
MAX_LINEAS = 5000


class LogViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filtro = QLineEdit()
        self._filtro.setPlaceholderText("Filtrar texto…")
        self._filtro.textChanged.connect(self.refrescar)

        self._nivel = QComboBox()
        self._nivel.addItems(NIVELES)
        self._nivel.currentTextChanged.connect(self.refrescar)

        recargar = QPushButton("Recargar")
        recargar.clicked.connect(self.refrescar)

        barra = QHBoxLayout()
        barra.addWidget(self._filtro, 1)
        barra.addWidget(self._nivel)
        barra.addWidget(recargar)

        self._texto = QPlainTextEdit(readOnly=True)
        fuente = QFont("Monospace")
        fuente.setStyleHint(QFont.TypeWriter)
        self._texto.setFont(fuente)

        cuerpo = QVBoxLayout(self)
        cuerpo.setContentsMargins(4, 4, 4, 4)
        cuerpo.addLayout(barra)
        cuerpo.addWidget(self._texto)

    def refrescar(self) -> None:
        try:
            lineas = paths.LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            self._texto.setPlainText("(sin log todavía)")
            return
        lineas = lineas[-MAX_LINEAS:]
        nivel = self._nivel.currentText()
        if nivel != "Todos":
            lineas = [ln for ln in lineas if nivel in ln]
        patron = self._filtro.text().lower()
        if patron:
            lineas = [ln for ln in lineas if patron in ln.lower()]
        self._texto.setPlainText("\n".join(lineas))
        barra = self._texto.verticalScrollBar()
        barra.setValue(barra.maximum())

    def showEvent(self, event) -> None:  # noqa: N802 — API Qt
        super().showEvent(event)
        self.refrescar()
