---
tipo: readme
estado: activo
---
# raphi/ — Raphi: PDF, ofimática y conversión de archivos (antes DocFlow Studio)

<!-- suite:inicio -->
**Suite `raphi`** · objetivo *documentos* · estado *activo* · python · interfaz gui

Raphi escritorio (PySide6; antes DocFlow Studio) sobre docflow, pdf-suite y page-counter.

- Escribe en: archivos · simula por defecto: no
- Depende de: PySide6, pikepdf, PyMuPDF
- Nota: motor y CLI en raphi/ (python -m raphi); la web en web/ y la ventana en escritorio/ (la misma interfaz); backends docflow, pdf-suite y page-counter en backends/

Comandos:

```bash
main.py
raphi lista
raphi doctor
raphi comprimir a.pdf --hasta 10 -n   # una operación (simulada)
raphi receta para-enviar a.pdf
python3 -m pytest -q tests
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-27); no se edita a mano.</sub>
<!-- suite:fin -->

<!-- suites:inicio -->
Suites de esta carpeta (4); índice global en `meta/INDICE_SCRIPTS.md`. Patrón: M main · C config · L lib.

| Suite | Carpeta | Objetivo | Escribe en | Simula | Timer | Estado | Patrón |
|---|---|---|---|---|---|---|---|
| `docflow` | [raphi/backends/docflow](backends/docflow/) | documentos | archivos | no |  | activo | `MCL` |
| `page_counter` | [raphi/backends/page-counter](backends/page-counter/) | documentos | archivos | no |  | activo | `MCL` |
| `pdf_suite` | [raphi/backends/pdf-suite](backends/pdf-suite/) | documentos | archivos | no |  | activo | `MCL` |
| `raphi` | [raphi](./) | documentos | archivos | no |  | activo | `MCL` |

<sub>Bloque generado desde los `suite.yml` por `core/suites.py generar` (2026-10-27); no se edita a mano.</sub>
<!-- suites:fin -->

## Qué es

**Raphi** («hoja» en quechua; hasta el 2026-10-27, «DocFlow Studio») es una sola aplicación para PDF, ofimática y
conversión de archivos, con tres caras sobre el mismo motor: la **ventana de escritorio** (`raphi`), la **web** (sola,
con cuentas, o como módulo de la plataforma Qillqa) y la **CLI** (`raphi <operación>`). Es local: ningún archivo sale a
un servicio ajeno.

- **48 operaciones** en un solo registro (`raphi/motor/`): unir, dividir, extraer, rotar, reordenar, componer páginas
  de varios PDF; comprimir (también «hasta 10 MB»), linearizar, reparar, validar, PDF/A; OCR; foliar expedientes,
  sello de recepción, numerar, marca de agua, metadatos; cifrar, ver firmas; PDF a imagen, texto, HTML y Word;
  documentos a PDF, entre formatos de oficina y a Markdown; imágenes (con HEIC y AVIF), audio, video, subtítulos y
  archivos comprimidos; inventario de páginas en Excel (lo que hacía `page-counter`).
- **Recetas**: cadenas de pasos guardadas (escaneo de mesa de partes, para enviar, para archivo…), aplicables a un
  lote o a una carpeta vigilada.
- **Una sola interfaz, la web**: la ventana la muestra en PySide6 y le suma lo que un navegador no puede (archivos del
  disco sin copiarlos, «Mostrar» en la carpeta, carpetas vigiladas, menús de Dolphin, la bandeja con su zona para
  soltar). Toda mejora de la web aparece en el escritorio.
- **Dentro de Qillqa** es un módulo de Tiqsi que ofrece «pdf.v1» y «conversion.v1» a los demás.

Los motores de antes siguen como CLIs completas hasta su retiro (R8): `backends/docflow` (conversión documental
masiva, con caché, paralelización y tests Bats), `backends/pdf-suite` y `backends/page-counter`. El plan por fases
vive en el repo de Qillqa: `qillqa/docs/plataforma/propuesta-raphi.md`.

## Uso

```bash
./install.sh                                          # una vez: .venv (Python del sistema), Tiqsi, lanzador raphi y entrada de escritorio
npm install && npm run web:construir                  # la web (web/dist), que usan la ventana y raphi.sola
raphi                                                 # la ventana (o python3 main.py); raphi escritorio a.pdf abre con archivos
raphi lista · raphi doctor                            # las operaciones y lo que falta en esta máquina
raphi comprimir *.pdf --hasta 10 -n                   # cualquier operación: -n simula, -o carpeta de salida, --json
raphi receta escaneo-mesa-de-partes recibido.pdf      # una cadena guardada (raphi recetas); raphi formatos foto.heic
JWT_SECRET=… .venv/bin/uvicorn raphi.sola:app --port 8040   # la web sola (cuentas: python -m tiqsi.minimo cuenta …)
.venv/bin/python -m pytest -q tests · npm run web:pruebas   # las pruebas (corpus generado en cada corrida)
backends/docflow/bin/docflow to-md ruta/ --jobs 4 -n  # docflow sigue como CLI (y bats backends/docflow/tests/)
```

Regla de oro: `-n` antes de un lote. Ninguna operación toca el original: la salida va junto a él con un sufijo, a la
carpeta de trabajos de Raphi o a la que se elija.

## Estructura

| carpeta | qué es |
|---|---|
| `raphi/motor/` | las operaciones (Python puro): `base.py` (registro, principios), `pdf_*.py`, `documentos.py`, `medios.py` |
| `raphi/` | la CLI (`__main__.py`), las recetas (`recetas.py`, `recetas/`), las fuentes, la API (`api/`), la cola (`trabajos.py`), la base (`db.py`), el módulo de Tiqsi (`manifiesto.py`, `contrato.py`) y sus modos (`sola.py`, `escritorio.py`) |
| `web/` | la única interfaz: el módulo web de Tiqsi `@qillqa/raphi` (pantallas, componentes, lógica pura con sus pruebas) |
| `escritorio/` | la ventana PySide6: servidor local, puente QWebChannel, carpetas vigiladas, menús de Dolphin |
| `backends/` | docflow, pdf-suite y page-counter, CLIs completas con su `suite.yml` y su README |
| `tests/` | pruebas del motor, la CLI, la API y el escritorio, con su corpus generado |
| `scripts/escanear.py` · `demo/demo.conf` | la guarda del repositorio público (escáner de Tiqsi en cada envío) |
| `docs/` | arquitectura, referencias de docflow y pdf-suite, decisiones (índice generado por `core/docs.py indice`) |
| `suite.yml` · `pyproject.toml` · `package.json` · `requirements.txt` | manifiestos y dependencias |
| `CHANGELOG.md` · `LICENSE` | versiones por herramienta; AGPL-3.0 |

## Límite honesto

- **Editar el texto existente de un PDF** no está (sí tachar, sellar, foliar y numerar encima); la firma digital se
  verifica, no se hace (R7).
- **La configuración y la caché de docflow** (`docflow config`, `docflow cache`) se ven desde su CLI: la web no las muestra.
- **El OCR es pesado**: la cola corre `RAPHI_CONCURRENCIA` trabajos a la vez (1 por omisión).
- **Estado fuera del repo**: `RAPHI_DIR` (~/.local/share/raphi: subidos y trabajos, borrados a las 24 h; base
  SQLite), recetas propias en ~/.config/raphi/recetas/, ajustes de la ventana en ~/.config/achalma/raphi.conf;
  docflow guarda lo suyo en ~/.config/docflow/, ~/.local/state/docflow/ y ~/.cache/docflow/.
- Licencia **AGPL-3.0** desde el 2026-10-27 (lo publicado antes sigue siendo MIT). El repositorio es público:
  `python3 scripts/escanear.py --instalar-guarda` instala la guarda que escanea cada envío.
