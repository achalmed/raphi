"""studio — Raphi escritorio (antes DocFlow Studio), aplicación PySide6.

Frontend gráfico sobre los backends existentes del proyecto
raphi (repo scripts_for_libreoffice):

- backends/docflow      → conversión documental (CLI Bash, se invoca por QProcess)
- backends/pdf-suite    → manipulación PDF (CLI Bash, se invoca por QProcess)
- backends/page-counter → conteo de páginas Quarto (Python, se importa directo)

La app está organizada por dominios funcionales (Conversión, PDF, Metadatos,
Reportes, Vigilancia, Sistema), no por scripts de origen.
"""

APP_NAME = "Raphi"
APP_ID = "raphi"
# Nombre anterior (hasta 2026-10-27): sus ajustes y su registro se migran solos al arrancar.
APP_ID_ANTERIOR = "docflow-studio"
APP_VERSION = "1.0.0"
APP_ORG = "achalma"
