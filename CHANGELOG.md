---
tipo: changelog
estado: activo
---
# CHANGELOG — raphi (antes DocFlow Studio; repo `achalmed/raphi`, antes `scripts_for_libreoffice`)

Versiones de las cuatro herramientas del repo, cada una con su número, según
[Keep a Changelog 1.1.0](https://keepachangelog.com/es-ES/1.1.0/) y [SemVer 2.0.0](https://semver.org/lang/es/).
La versión vigente se declara en el código: `DOCFLOW_VERSION` (`backends/docflow/lib/core/constants.sh`),
`PDF_SUITE_VERSION` (`backends/pdf-suite/config.sh`), `SCRIPT_VERSION` (`backends/page-counter/config.py`)
y `APP_VERSION` (`studio/__init__.py`). Sin etiquetas git: por qué se lleva igualmente, en
`docs/decisiones.md`.

<!-- Mantén «Sin publicar» arriba en cada herramienta; al subir su versión en el código, sus entradas pasan a la versión nueva con fecha ISO. -->

## Raphi escritorio (GUI; antes DocFlow Studio)

### Sin publicar

#### Cambiado

- La aplicación se llama **Raphi** (ventana, lanzador `raphi`, entrada de escritorio `raphi.desktop`); el
  instalador retira el lanzador y la entrada de `docflow-studio`.
- Los ajustes pasan a `~/.config/achalma/raphi.conf` y el registro a `~/.local/state/raphi/`; los del nombre
  anterior se migran solos la primera vez.
- Licencia AGPL-3.0 (antes MIT) en todo el repositorio, docflow incluido.

#### Añadido

- `scripts/escanear.py`: la guarda pre-push del repositorio público, con el escáner de Tiqsi.

### [1.0.0] - 2026-07-13

#### Añadido

- Aplicación de escritorio PySide6 que orquesta docflow, pdf-suite y page-counter sin reescribirlos, por
  dominios: Conversión, PDF, Metadatos, Reportes, Vigilancia y Sistema.
- Explorador acoplable, consola en vivo con el comando exacto, panel de tareas cancelables, visor de
  logs y ajustes persistentes.
- `install.sh` (entorno `.venv`, lanzador `docflow-studio` y entrada de escritorio) y `run.sh`.
- Toda operación PDF pasa por pdf-suite; de docflow solo se usa PDF/A.

## docflow

### Sin publicar

#### Cambiado

- El frontmatter que escribe `to-md` usa las claves en español del ecosistema (`tipo: original`,
  `titulo`, `origen`, `convertidor`, `convertido`…) en lugar de `source`, `converter` y `converted`
  (2026-09-15).

#### Corregido

- El CI (ShellCheck y Bats en Ubuntu y Arch) vuelve a dispararse: sus rutas apuntaban a una carpeta que
  ya no existía (2026-09-20).

### [3.0.0] - 2026-07-10

Reescritura completa: de suite de scripts (`script_doc_suite`, v2) a herramienta CLI.

#### Añadido

- Arquitectura por motores (Markdown, PDF, ODF, Office, Media, Metadata, OCR, Validation, Reporting,
  Watch) sobre un registro de formatos: añadir un formato o un comando no toca el núcleo.
- Parsers OOXML propios para pptx (notas del presentador, tablas, imágenes, orden real de las
  diapositivas) y xlsx (todas las hojas, fechas y números con formato), que pandoc no lee.
- Operaciones PDF: unir, dividir, rotar, extraer, comprimir, PDF/A, cifrar y descifrar (AES-256), marca
  de agua, OCR e información.
- Caché SHA-256 para pasadas incrementales sobre colecciones grandes; `--resume`.
- Verificación posterior a la conversión como requisito para tocar originales; detección de documentos
  protegidos con estado propio.
- Reportes HTML, CSV, JSON y Markdown con estadísticas por formato; salida `--json` y modo `--quiet`.
- Frontmatter YAML con los metadatos reales del documento.
- Conversión, redimensionado y optimización de imágenes.
- Configuración TOML, códigos de salida documentados, hooks antes y después, barra de progreso,
  autocompletado bash y fish, pruebas Bats e instalador para varias distribuciones.

#### Corregido

- pptx → Markdown funciona (v2 intentaba pandoc sobre odp, que no tiene lector).
- LibreOffice en paralelo ya no corrompe el perfil de usuario (perfil aislado por invocación) ni puede
  colgar el lote (tiempo límite).
- Un fallo de conversión ya no deja salidas parciales que bloqueen el reintento.
- soffice devolviendo 0 sin convertir (documentos protegidos) ya no cuenta como éxito.

### [2.0.0] - 2026-06-22

- `script_doc_suite`: los scripts de conversión se consolidan en una suite modular (`to-odf`, `to-pdf`,
  `to-md`).

### [1.0.0] - 2026-06-18

- `convert_ms_to_odf.sh`: un script único MS Office → ODF.

## pdf-suite

### [3.0.0] - 2026-06

Une tres scripts previos: `compress_pdf.sh` 2.0 (hoy `lib/compress.sh`),
`arch_pdf_metadata_commands.sh` (hoy `lib/metadata.sh`) y `test_compression.sh` (hoy la operación `test`).

#### Añadido

- Arquitectura modular en `lib/`; operaciones merge, split, extract, rotate, reorder, delete, convert,
  ocr, protect, watermark, repair, validate y optimize.
- Menú interactivo, `--dry-run` global, registro con niveles e instalador para apt y pacman.

#### Corregido

- Los errores de Ghostscript y ocrmypdf ya no se descartan (`2>/dev/null` silenciaba la causa).
- Las estadísticas del lote ya no se pierden en subshells.
- `qpdf --show-object`, que no existe, sustituido por opciones reales.
- Metadatos: se distinguen DocInfo y XMP (`mutool show trailer/Info` no leía XMP).
- Los bucles sobre `find` usan `IFS= read -r` y admiten nombres con espacios.

### [2.0.0] - 2026-01

#### Corregido

- La compresión reduce el tamaño (en 1.0.0 lo aumentaba); modo recursivo, estadísticas y umbral
  configurable.

### [1.0.0] - 2026-01

- Primera versión: compresión y metadatos.

## page-counter

### Sin publicar

#### Cambiado

- Los blogs se localizan en `04 index/_pubs/pub_*` (submódulos del hub) y las secciones `blog` y
  `teching` en el `_site/` del hub (`DIR_HUB`, `SUBDIR_PUBS` en `config.py`) (2026-09-06).

### [2.0.0] - 2026-07-13

#### Cambiado

- Arquitectura `main.py` + `config.py` + `lib/`; lectura con `pypdf` (PyPDF2 queda como alternativa);
  `--verbose` y `--version`.

#### Corregido

- La ruta base apuntaba a una carpeta que ya no existía: la herramienta no funcionaba.
- La causa de un PDF ilegible ya no se descarta: `--verbose` la muestra.
- Códigos de salida: 0 éxito, 1 error (incluye PDF ilegibles), 2 uso, 3 ruta o blog no encontrados,
  5 dependencia ausente (antes terminaba siempre en 0).
- Un nombre de blog desconocido aborta con error y sugiere `--listar` (antes se ignoraba en silencio).
- Los PDF de 0 páginas (`VACÍO`) ya no cuentan como éxito en el resumen.
- `--listar` y `--help` funcionan sin la biblioteca PDF instalada (importación diferida).
- Un fallo al guardar el Excel (sin permisos, archivo abierto) da un mensaje claro y salida 1.
