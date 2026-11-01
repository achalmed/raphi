"""El formulario de una operación, generado de su ficha (`parametros` del motor), como el de la web.

Ninguna operación tiene un formulario escrito a mano: cada `tipo` de parámetro tiene su control, y lo que la persona
escribe vuelve como texto o número para que `Parametro.convertir` del motor lo valide (el mismo camino que la CLI).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QCheckBox, QColorDialog, QComboBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPlainTextEdit, QPushButton, QSpinBox, QWidget)

from gui_comun.diseno import clase


class Formulario(QWidget):
    def __init__(self, parametros: list[dict]):
        super().__init__()
        self.parametros = parametros
        self._controles: dict[str, tuple[str, QWidget]] = {}
        forma = QFormLayout(self)
        forma.setContentsMargins(0, 0, 0, 0)
        forma.setHorizontalSpacing(14)
        forma.setVerticalSpacing(10)
        forma.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        forma.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        for p in parametros:
            control = self._control(p)
            self._controles[p["clave"]] = (p["tipo"], control)
            etiqueta = QLabel(p["etiqueta"] + (" *" if p.get("obligatorio") else ""))
            etiqueta.setWordWrap(True)
            if p.get("ayuda"):
                etiqueta.setToolTip(p["ayuda"])
                control.setToolTip(p["ayuda"])
            forma.addRow(etiqueta, control)
            if p.get("ayuda") and p["tipo"] not in ("casilla",):
                forma.addRow("", clase(QLabel(p["ayuda"]), "tenue"))
        if not parametros:
            forma.addRow(clase(QLabel("Esta herramienta no tiene opciones."), "tenue"))

    def _control(self, p: dict) -> QWidget:
        tipo, defecto = p["tipo"], p.get("defecto")
        if tipo == "opcion":
            c = QComboBox()
            for valor, nombre in p["opciones"]:
                c.addItem(str(nombre), valor)
            i = c.findData(defecto)
            c.setCurrentIndex(max(0, i))
            return c
        if tipo == "casilla":
            c = QCheckBox()
            c.setChecked(bool(defecto))
            return c
        if tipo == "entero":
            c = QSpinBox()
            c.setRange(int(p["minimo"]) if p.get("minimo") is not None else -1_000_000,
                       int(p["maximo"]) if p.get("maximo") is not None else 1_000_000)
            c.setValue(int(defecto or 0))
            return c
        if tipo == "decimal":
            c = QDoubleSpinBox()
            c.setDecimals(2)
            c.setRange(float(p["minimo"]) if p.get("minimo") is not None else -1e9,
                       float(p["maximo"]) if p.get("maximo") is not None else 1e9)
            c.setValue(float(defecto or 0))
            return c
        if tipo in ("multilinea", "json"):
            c = QPlainTextEdit(str(defecto or ""))
            c.setMinimumHeight(80)
            c.setMaximumHeight(140)
            return c
        if tipo == "color":
            return _Color(str(defecto or "#000000"))
        c = QLineEdit("" if defecto is None else str(defecto))
        if tipo == "clave":
            c.setEchoMode(QLineEdit.Password)
        if tipo == "paginas":
            c.setPlaceholderText("todas · 1-3,5 · último")
        if tipo == "tamano":
            c.setPlaceholderText("p. ej. 10 MB")
        return c

    def valores(self) -> dict:
        """Lo escrito, como la CLI lo pasaría al motor (sin los vacíos: el motor pone el valor por omisión)."""
        datos = {}
        for clave, (tipo, c) in self._controles.items():
            if isinstance(c, QComboBox):
                v = c.currentData()
            elif isinstance(c, QCheckBox):
                v = c.isChecked()
            elif isinstance(c, (QSpinBox, QDoubleSpinBox)):
                v = c.value()
            elif isinstance(c, QPlainTextEdit):
                v = c.toPlainText().strip()
            elif isinstance(c, _Color):
                v = c.valor
            else:
                v = c.text().strip()
            if v != "" and v is not None:
                datos[clave] = v
        return datos


class _Color(QWidget):
    def __init__(self, valor: str):
        super().__init__()
        self.valor = valor
        fila = QHBoxLayout(self)
        fila.setContentsMargins(0, 0, 0, 0)
        self.muestra = QPushButton()
        self.muestra.setFixedSize(36, 28)
        self.muestra.clicked.connect(self._elegir)
        self.texto = QLabel(valor)
        fila.addWidget(self.muestra)
        fila.addWidget(self.texto, 1)
        self._pintar()

    def _elegir(self) -> None:
        color = QColorDialog.getColor(QColor(self.valor), self, "Color")
        if color.isValid():
            self.valor = color.name()
            self._pintar()

    def _pintar(self) -> None:
        self.muestra.setStyleSheet(f"background: {self.valor}; border-radius: 6px;")
        self.texto.setText(self.valor)
