---
tipo: readme
estado: activo
---
# raphi/ — Raphi: PDF, ofimática y conversión de archivos (antes DocFlow Studio)

<!-- suite:inicio -->
**Suite `raphi`** · objetivo *documentos* · estado *activo* · python · interfaz gui

Raphi escritorio (PySide6; antes DocFlow Studio) sobre docflow, pdf-suite y page-counter.

- Escribe en: archivos · simula por defecto: no
- Depende de: PySide6
- Nota: config en studio/core/settings.py (QSettings); backends docflow, pdf-suite y page-counter en backends/

Comandos:

```bash
main.py
./run.sh                 # usa el .venv si existe
python3 -m studio
raphi
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

Una aplicación de escritorio (Raphi escritorio, PySide6; hasta el 2026-10-27, «DocFlow Studio») y los tres motores de línea de comandos que
envuelve, para convertir y gestionar documentos de oficina y PDF en Linux: `docflow` (Bash; conversión
documental masiva → Markdown, → PDF, Office ↔ ODF, con caché, paralelización, vigilancia de carpetas y
reportes), `pdf-suite` (Bash; comprimir, unir, dividir, rotar, OCR, cifrar, marca de agua, reparar,
metadatos) y `page-counter` (Python; cuenta las páginas de los `index.pdf` renderizados por la familia de
blogs Quarto y produce un Excel). Resuelven lo que `pandoc` y `soffice` en un bucle no resuelven: pptx y
xlsx que pandoc no lee, LibreOffice que corrompe su perfil al correr en paralelo, y lotes de miles de
archivos en los que el fallo de uno no debe detener el resto.

Un solo nombre desde el 2026-10-27: la carpeta, el repositorio de GitHub (`achalmed/raphi`, antes
`scripts_for_libreoffice`), la suite raíz y la aplicación se llaman **Raphi** («hoja» en quechua).

**Hacia dónde va** (plan en `qillqa/docs/plataforma/propuesta-raphi.md`): un módulo más de la plataforma
Qillqa, que funciona solo o dentro de ella, con un motor Python que reúne pdf-suite, docflow, page-counter y la
conversión de medios, y **una sola interfaz, la web**, que el escritorio mostrará en PySide6.

**No es** una biblioteca y no reescribe los backends: cada motor sigue siendo una CLI independiente, con
su `suite.yml`, su README y su instalador (docflow, además, con tests Bats y CI); la GUI los invoca como
procesos o, en el caso de `page-counter`, importa sus módulos tal cual. Depende de `core/` (contrato de
suites) y de PySide6 en un `.venv/` local; no tiene `verdad` propia en `meta/workspace.yml` y no escribe
fuera de la carpeta que se le pasa y de los directorios XDG de cada backend.

## Uso

```bash
./install.sh                                          # una vez: .venv con PySide6, lanzador ~/.local/bin/raphi y entrada de escritorio
raphi                                                 # o ./run.sh (usa .venv si existe), python3 main.py, python3 -m studio
backends/docflow/install.sh                           # dependencias del sistema de docflow (pandoc, LibreOffice, qpdf, gs, ocrmypdf…)
backends/pdf-suite/main.sh deps                       # dependencias de pdf-suite (su install.sh no sigue al repo: ver su README)
backends/docflow/bin/docflow doctor                   # qué falta y el comando exacto para tu distro
backends/docflow/bin/docflow to-md -n -v ruta/        # simular (-n) una conversión a Markdown antes de aplicarla
backends/docflow/bin/docflow to-md ruta/ --jobs 4 --report html   # lote en paralelo con reporte de sesión
backends/pdf-suite/main.sh                            # menú interactivo; con operación: compress, merge, split, ocr, metadata…
backends/pdf-suite/main.sh -n compress documento.pdf  # -n simula sin escribir
python3 backends/page-counter/main.py --listar        # conteo de páginas de los blogs (escribe solo su excel_databases/)
bats backends/docflow/tests/                          # pruebas de docflow en sandbox aislado
pyside6-designer studio/resources/ui/main_window.ui   # editar el shell de la GUI; se carga en tiempo de ejecución
```

Regla de oro: `-n`/`--dry-run` antes de un lote en `docflow` y `pdf-suite`, que escriben de verdad salvo
que se les pida lo contrario. `page-counter` no simula: siempre escribe su Excel, pero solo dentro de su
carpeta. La app muestra las dependencias que faltan en Sistema → Diagnóstico.

## Deduplicación

`docflow pdf` y `pdf-suite` implementaban las mismas operaciones (merge, split, rotate, extract,
compress, encrypt, watermark, ocr, info). En la app **toda la manipulación PDF pasa por pdf-suite** —que
es superconjunto— y docflow queda como motor de *conversión documental*; la única operación PDF que
conserva es **PDF/A**, que pdf-suite no implementa. Ninguna operación aparece en dos módulos. La
duplicación de código sigue existiendo en los backends (ambos son CLIs completas); lo que no se duplica
es la puerta de entrada.

## Estructura

| carpeta | qué es | dueño / generador |
|---|---|---|
| `main.py` · `run.sh` · `install.sh` | entrada de la GUI (equivale a `python3 -m studio`); lanzador que usa `.venv/` si existe; instalador del frontend (venv, ~/.local/bin/raphi, `.desktop`; retira los del nombre anterior) | a mano |
| `studio/` | la aplicación PySide6: `app.py`, `core/` (rutas, QSettings, tareas), `services/` (GUI → línea de comandos exacta), `ui/` (ventana, páginas por dominio, widgets), `studio/resources/ui/main_window.ui` | a mano; `studio/README.md` |
| `backends/docflow/` | CLI Bash de conversión documental: `bin/docflow`, `lib/{core,engines,formats,commands,helpers}`, `tests/` Bats, `completions/`, `install.sh`, `LICENSE` | a mano; `backends/docflow/README.md` |
| `backends/pdf-suite/` | CLI Bash de manipulación PDF: `main.sh` + `config.sh` + `lib/` (un módulo por familia de operaciones), `install.sh` | a mano; `backends/pdf-suite/README.md` |
| `backends/page-counter/` | Python: `main.py` + `config.py` + `lib/`; escribe Excel en su `excel_databases/` (ignorado) | a mano; `backends/page-counter/README.md` |
| `suite.yml` (raíz y uno por backend) | manifiesto de cada suite (`core/suite.schema.yml`) | a mano; los bloques de README los genera `core/suites.py generar --aplicar` |
| `docs/` | documentación permanente: arquitectura, referencia de docflow y de pdf-suite, decisiones | a mano; el índice `docs/README.md` lo genera `core/docs.py indice` |
| `requirements.txt` | PySide6, pypdf, openpyxl (frontend y page-counter); las dependencias del sistema las instalan los backends | a mano |
| `.github/workflows/ci.yml` | ShellCheck + Bats de docflow en Ubuntu y Arch (se dispara solo con cambios en `backends/docflow/`) | a mano |
| `scripts/escanear.py` · `demo/demo.conf` | la guarda del repositorio público: el escáner de Tiqsi sobre cada commit que se envía (pre-push) y lo que acepta | a mano |
| `CHANGELOG.md` · `LICENSE` | versiones con fecha ISO de las cuatro suites; AGPL-3.0 | a mano |
| `.venv/` | entorno del frontend creado por `install.sh` (ignorado) | `install.sh` |

## Documentación

| documento | para qué leerlo |
|---|---|
| `CLAUDE.md` | reglas para el asistente: invariantes de diseño, cómo verificar, trampas |
| `docs/README.md` | índice de `docs/` |
| `docs/arquitectura.md` | los principios comunes (errores por archivo, Bash orquesta y Python parsea…), el diseño de docflow y cómo extender las tres CLIs |
| `docs/referencia-docflow.md` · `docs/referencia-pdf-suite.md` | todas las opciones, operaciones y códigos de salida de cada CLI |
| `docs/decisiones.md` | por qué el repo es como es, y sus pendientes |
| `studio/README.md` | la GUI: dominios, arquitectura por capas, reglas para añadir operaciones y dominios, Qt Designer |
| `backends/docflow/README.md` · `backends/pdf-suite/README.md` · `backends/page-counter/README.md` | la puerta de cada herramienta: qué es, uso, estructura y límites |
| `CHANGELOG.md` | versiones de cada herramienta |
| `meta/INDICE_SCRIPTS.md` | las 4 suites entre las del workspace (generado) |

## Límite honesto

- **Solo docflow tiene pruebas** (Bats, ShellCheck y CI); `pdf-suite`, `page-counter` y la GUI se
  comprueban a mano: `bash -n`, `py_compile`, `--dry-run` y abrir la app.
- **La GUI no simula**: ejecuta la línea de comandos exacta que muestra en la consola; la simulación es la
  de cada backend (`-n`). Una operación a la vez por tarea; las tareas corren en `QProcess`/`QThread` y se
  pueden cancelar.
- **Los originales solo los toca docflow y solo si la conversión fue exitosa y verificada** (`--backup`,
  `--delete`); los archivos con error o protegidos por contraseña jamás se mueven ni eliminan.
- **PDF/A vive en docflow; todo lo demás del PDF, en pdf-suite**: no hay una sola CLI para todo, y
  `pdf-suite` sigue implementando lo que `docflow pdf` también implementa.
- **docflow tiene logger propio** (niveles y modo `--quiet`), excepción documentada al logger de
  `core/shell-lib` en su `suite.yml`; `page-counter` resuelve la raíz de los blogs con `Path.home()` en su
  `config.py`, no con `core/env.py`. Esto y los defectos conocidos de los instaladores y de los manifiestos
  de los backends están en `docs/decisiones.md` §Pendientes.
- **Estado fuera del repo**: config TOML de docflow en `~/.config/docflow/`, sesiones y caché en
  ~/.local/state/docflow/ y ~/.cache/docflow/ (se conservan 50 sesiones), log de la GUI en
  ~/.local/state/raphi/studio.log, ajustes en QSettings (~/.config/achalma/raphi.conf; los del nombre anterior se
  migran solos la primera vez).
- **Lo que no hace**: no edita documentos (convierte, manipula, cuenta), no sincroniza con Calibre ni
  Zotero (eso es `scripts-biblioteca`), no compila LaTeX (`scripts-latex`).
- Licencia **AGPL-3.0** desde el 2026-10-27 (`LICENSE` y `backends/docflow/LICENSE`); las versiones publicadas
  antes siguen siendo MIT. El repositorio es público: `python3 scripts/escanear.py --instalar-guarda` instala la
  guarda que escanea cada envío (necesita Tiqsi en el espacio de trabajo).
