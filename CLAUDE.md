---
tipo: guia_ia
estado: activo
---
# CLAUDE.md — raphi (repo `achalmed/raphi`, suite `raphi`; antes DocFlow Studio)

Guía para el asistente. En español, como todo el ecosistema. `AGENTS.md` es un enlace a este archivo.
Léase antes: `README.md` (qué es, uso, deduplicación), `docs/README.md` (índice), `docs/arquitectura.md`
(los principios), `suite.yml` (raíz y uno por backend), `studio/README.md` (la GUI) y el README del backend
que se toque.

## Reglas que no se negocian

- **Raphi, escritorio y web, es una sola aplicación** (decisión del 2026-10-27, `docs/decisiones.md`; plan en
  el repo de Qillqa, `docs/plataforma/propuesta-raphi.md`): la interfaz que viene es la web, y el escritorio la
  mostrará en PySide6 con un puente nativo; ninguna pantalla nueva se escribe solo para el escritorio. Hasta la
  fase R4, la GUI de `studio/` sigue siendo Raphi escritorio y sus reglas, las de abajo.
- **El repo es público**: nada del despacho ni de nadie; `python3 scripts/escanear.py` (o la guarda pre-push
  que instala con `--instalar-guarda`) escanea cada commit antes de que salga. Licencia AGPL-3.0.
- **Una GUI que orquesta tres backends intactos.** `docflow` y `pdf-suite` se invocan como procesos
  (`QProcess`, línea de comandos construida en `studio/services/`); `page-counter` se importa como módulo
  (`studio/services/pagecounter.py`). Los backends siguen siendo CLIs completas desde la terminal: sus
  instaladores, tests y CI no dependen de la GUI. La GUI no importa código Bash ni reescribe backends.
- **Los ejecutables de backend se resuelven en un solo sitio**, `studio/core/paths.py` (con override del
  usuario en QSettings). Si un backend se mueve, se toca solo ese archivo.
- **Las páginas no conocen los CLIs**: construyen parámetros y llaman a `studio/services/`, que devuelve el
  comando. Un cambio de flags de un backend se corrige en un archivo. Toda operación es una `Task`
  (`studio/core/tasks.py`) y hereda consola, panel, log y cancelación.
- **Deduplicación deliberada** (README §Deduplicación): en la app toda operación PDF pasa por `pdf-suite`;
  `docflow` es solo conversión documental más **PDF/A**. Ninguna operación aparece en dos módulos: añadir
  una operación PDF es una entrada en `OPERACIONES` de `studio/ui/pages/pdf.py` y una función de una línea
  en `studio/services/pdfsuite.py`; añadir un dominio es una página en `studio/ui/pages/` registrada en
  `PAGINAS` de `studio/ui/main_window.py`.
- **Errores por archivo, nunca por lote** (`docs/arquitectura.md` §Principios): docflow no usa `set -e`;
  el fallo de un documento se registra y el lote sigue; el código de salida final lo refleja (6). Un
  original solo se respalda o elimina si la conversión fue exitosa **y** verificada.
- **Bash orquesta, Python stdlib parsea.** Bash coordina procesos y archivos; todo parsing estructurado
  (OOXML, TOML, Markdown, JSON) vive en `backends/docflow/lib/helpers/*.py` sin dependencias externas. El
  núcleo de docflow no conoce formatos: se declaran en `backends/docflow/lib/formats/` con `registry_add`.
- **Instalación en dos niveles**: `install.sh` crea `.venv/` con `requirements.txt` (PySide6, pypdf,
  openpyxl) y el lanzador `raphi`; las dependencias del sistema (pandoc, LibreOffice, qpdf, gs,
  ocrmypdf, exiftool…) las instalan `backends/docflow/install.sh` y `backends/pdf-suite/install.sh`.
  `run.sh` usa `.venv/` si existe y el `python3` del sistema si no. Un solo camino documentado.
- **Simular antes de aplicar**: `-n`/`--dry-run` en docflow y pdf-suite; la GUI no simula por sí misma.
- **Lo generado no se edita**: los bloques `<!-- suite:inicio -->` y `<!-- suites:inicio -->` de los README
  salen de los `suite.yml` con `core/suites.py generar --aplicar`; `docs/README.md`, con
  `core/docs.py indice`. `studio/README.md` no lleva bloque: la suite `raphi` se declara en el
  `suite.yml` de la raíz.
- **Raíz y logger de `core/`**: ninguna ruta de máquina en código. Excepciones declaradas: docflow tiene
  logger propio (nota en su `suite.yml`); `page-counter` resuelve `~/Documents` con `Path.home()` en su
  `config.py` (pendiente en `docs/decisiones.md`).
- **Español con tildes** en código, mensajes, comentarios y docs; nada del despacho en este repo.

### Dónde va cada cosa nueva

Raíz admitida: `README.md`, `CLAUDE.md`, `AGENTS.md`, `suite.yml`, `LICENSE`, `CHANGELOG.md` (y los no
documentales `main.py`, `run.sh`, `install.sh`, `requirements.txt`). Ningún otro `.md` en la raíz ni en un
backend fuera de su `README.md`.

| lo que apareció | va a | nunca a |
|---|---|---|
| cómo se instala o se usa una herramienta | su `README.md` §Uso; una opción o una operación, `docs/referencia-docflow.md` o `docs/referencia-pdf-suite.md` | un `GUIA.md` o `ejemplos.md` |
| cómo funciona por dentro o cómo se extiende | `docs/arquitectura.md`; la GUI, `studio/README.md` | un segundo documento de arquitectura |
| por qué se decidió algo · un pendiente | `docs/decisiones.md` (entrada fechada · §Pendientes con fecha y dueño) | un `TODO.md`, el README |
| qué cambió en una versión | `CHANGELOG.md`, bajo la herramienta y su «Sin publicar» | el README de la herramienta |
| un comando de un `suite.yml` | el `suite.yml`, y se regenera el bloque | el bloque generado a mano |

Lo que hiciste en esta sesión va al mensaje de commit, no a un archivo. Si nada encaja, pregunta antes de
crear un documento.

## Cómo se verifica un cambio

```bash
python3 core/archivos.py validar scripts_document_studio     # A01–A14 y D01–D12, desde ~/Documents
python3 core/suites.py validar                                # los 4 suite.yml contra el esquema
python3 core/suites.py generar                                # ¿bloques de README desfasados? (simula)
python3 core/docs.py verificar scripts_document_studio        # índice de docs/ al día
cd scripts_document_studio
bash -n backends/docflow/bin/docflow backends/pdf-suite/main.sh
python3 scripts/escanear.py --trabajo                         # la guarda del repo público (escáner de Tiqsi)
shellcheck -x -S warning backends/docflow/bin/docflow backends/docflow/lib/*/*.sh  # lo del CI
bats backends/docflow/tests/                                  # pruebas en sandbox (pandoc, soffice, qpdf)
python3 -m py_compile main.py studio/**/*.py backends/page-counter/*.py backends/page-counter/lib/*.py
backends/docflow/bin/docflow to-md -n -v ruta/                # simular
backends/pdf-suite/main.sh -n compress documento.pdf           # simular
./run.sh                                                      # abrir la GUI y mirar la consola integrada
meta/doctor/main.sh --breve                                   # desde ~/Documents
```

Solo docflow tiene pruebas automáticas; un cambio en la GUI se prueba abriéndola y leyendo la consola
integrada (comando exacto, stdout, stderr, código de salida y duración) y el log en
`~/.local/state/raphi/studio.log`.

## Detalles que cuesta redescubrir

- **El CI se dispara solo con cambios en `backends/docflow/`** (`.github/workflows/ci.yml`, `paths`): si se
  mueve una carpeta, sus rutas y las de `.gitignore` se mueven con ella, o el CI deja de correr sin avisar.
- **`page-counter` localiza la raíz y el hub por `core/env.py` y los blogs por el registro `<hub>/_pubs/pubs.yml`** (`core/py-common/pubs.py`, ola 6, 6f): nada se lista a mano ni se descubre por el prefijo de carpeta.
- **soffice devuelve 0 aunque no convierta** (documentos protegidos) y corrompe su perfil si corre en
  paralelo: docflow aísla cada invocación en un perfil temporal, le pone `timeout` (300 s,
  `DOCFLOW_SOFFICE_TIMEOUT`) y comprueba que el archivo esperado exista (`backends/docflow/lib/core/soffice.sh`).
- **Paralelización sin `export -f`**: cada worker re-invoca `docflow __worker <tarea> <archivo>`; la
  configuración viaja en variables `DOCFLOW_*` y los resultados convergen en el `results.tsv` de la sesión
  (`~/.local/state/docflow/sessions/<ts>/`; se conservan 50).
- **La caché de docflow** (~/.cache/docflow/) se indexa por `sha256(contenido) + tarea + opciones`;
  `docflow cache prune` la compacta. `--resume` reanuda un lote interrumpido (código 130).
- **pdf-suite usa el sufijo (`_out`) para no reprocesar lo ya procesado**: cambiarlo entre llamadas del
  mismo lote rompe esa prevención de bucles. `delete` necesita `python3`; `watermark`/numeración
  necesitan `cpdf` (AGPL, se instala aparte); `--dry-run` sí crea temporales en `/tmp/pdfsuite_*`.
- **El shell de la GUI es un `.ui`** cargado con `QUiLoader`: los cambios de Qt Designer se ven al
  reiniciar sin recompilar. Ajustes en QSettings (~/.config/achalma/raphi.conf; migra los de `docflow-studio`).

## Dónde está cada cosa

| pregunta | documento |
|---|---|
| principios comunes, registry, motores, sesiones, caché, extender docflow | `docs/arquitectura.md` |
| dominios de la GUI, capas, cómo añadir una operación o un dominio, Qt Designer | `studio/README.md` |
| uso esencial y límites de docflow | `backends/docflow/README.md` |
| todas las opciones de docflow; el frontmatter que emite y quién lo consume | `docs/referencia-docflow.md` |
| operaciones, flags y dependencias de pdf-suite | `docs/referencia-pdf-suite.md`; su puerta, `backends/pdf-suite/README.md` |
| opciones, blogs y advertencias del contador de páginas | `backends/page-counter/README.md` |
| por qué el repo es así; pendientes (instaladores, manifiestos, `core/env.py`) | `docs/decisiones.md` |
| versiones de cada herramienta | `CHANGELOG.md` |
| el contrato de suite y los bloques generados | `core/suite.schema.yml`, `core/README.md` |
| normativa de archivos, fechas, cabeceras y documentación | `meta/docs/historial/NORMATIVA_ARCHIVOS.md` |
