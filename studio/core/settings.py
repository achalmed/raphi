"""Configuración persistente de la aplicación (QSettings).

Envoltorio fino: agrupa las claves usadas por la app para que ninguna
página invente claves sueltas. El almacenamiento real es el estándar de
Qt (~/.config/achalma/raphi.conf en Linux). La primera vez copia los de
~/.config/achalma/docflow-studio.conf, el nombre anterior de la app.
"""

from __future__ import annotations

from PySide6.QtCore import QSettings

from studio import APP_ID, APP_ID_ANTERIOR, APP_ORG


def app_settings() -> QSettings:
    ajustes = QSettings(APP_ORG, APP_ID)
    if not ajustes.allKeys():
        anteriores = QSettings(APP_ORG, APP_ID_ANTERIOR)
        for clave in anteriores.allKeys():
            ajustes.setValue(clave, anteriores.value(clave))
        ajustes.sync()
    return ajustes


def last_dir(settings: QSettings, contexto: str) -> str:
    """Último directorio usado en un diálogo de archivos, por contexto."""
    return str(settings.value(f"lastdir/{contexto}", str(settings.value("lastdir/global", ""))))


def set_last_dir(settings: QSettings, contexto: str, ruta: str) -> None:
    settings.setValue(f"lastdir/{contexto}", ruta)
    settings.setValue("lastdir/global", ruta)
