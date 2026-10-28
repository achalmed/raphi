---
tipo: guia_ia
estado: activo
---
# CLAUDE.md — raphi (repo `achalmed/raphi`, suite `raphi`; antes DocFlow Studio)

Guía para el asistente. En español, como todo el ecosistema. `AGENTS.md` es un enlace a este archivo. Léase antes:
`README.md` (qué es y uso), `docs/arquitectura.md` (principios, motor, API, web, escritorio), `suite.yml` y el README
del backend que se toque. El plan por fases vive en el repo de Qillqa: `qillqa/docs/plataforma/propuesta-raphi.md`.

## Reglas que no se negocian

- **Escritorio y web son una sola aplicación** (decisión del 2026-10-27, `docs/decisiones.md`): la única interfaz es
  `web/`; `escritorio/` es una ventana que la muestra más un puente nativo. Ninguna pantalla se escribe solo para el
  escritorio (lo vigila `tests/test_escritorio.py`); lo propio del escritorio se ofrece en la web con `hayEscritorio()`.
- **Una operación existe en un solo lugar**: su función con `@operacion(...)` en `raphi/motor/`. De su ficha salen la
  CLI, la API, el formulario de la web y el menú de formatos. Nada de formularios escritos a mano.
- **Los tres principios viven en el núcleo** (`raphi/motor/base.py`): error por archivo, nunca por lote; la salida
  nunca pisa una entrada ni otra salida y se verifica antes de darla por buena; `simular=True` no escribe nada.
- **Fronteras** (`tests/test_fronteras.py`, `tests/test_escritorio.py`): el motor no importa FastAPI, SQLAlchemy, Qt
  ni Tiqsi; `raphi/` no importa PySide6 ni `escritorio`; nadie importa a otro proyecto de la plataforma. Lo que se
  pida de otro módulo, por una capacidad de Tiqsi que se APROVECHA.
- **El repo es público**: nada del despacho ni de nadie; `python3 scripts/escanear.py` (y la guarda pre-push que
  instala `--instalar-guarda`) escanea cada envío. Licencia AGPL-3.0.
- **docflow sigue siendo una CLI completa** (`backends/docflow`, con sus tests Bats y su CI): el motor lo usa solo para
  «a Markdown» (sus parsers de pptx y xlsx). pdf-suite y page-counter se retiraron en R8: sus operaciones están en el motor.
- **El entorno es el Python del sistema**, no el de conda: el de Anaconda trae una libbrotli vieja y QtWebEngine no
  abre (`install.sh` lo elige y rehace un `.venv` de conda).
- **Lo generado no se edita**: los bloques `<!-- suite:inicio -->` y `<!-- suites:inicio -->` salen de los `suite.yml`
  con `core/suites.py generar --aplicar`; `docs/README.md`, con `core/docs.py indice`; `web/dist`, de `npm run web:construir`.
- **Español con tildes** en código, mensajes, comentarios y docs.

### Dónde va cada cosa nueva

Raíz admitida: `README.md`, `CLAUDE.md`, `AGENTS.md`, `suite.yml`, `LICENSE`, `CHANGELOG.md` y los no documentales
`main.py`, `run.sh`, `install.sh`, `requirements.txt`, `pyproject.toml`, `package.json`, `package-lock.json`.

| lo que apareció | va a | nunca a |
|---|---|---|
| una operación | `raphi/motor/<familia>.py` con su prueba en `tests/` | la web o el escritorio |
| una pantalla | `web/src/paginas/` y su ruta en `web/src/modulo.ts` | `escritorio/` |
| algo que solo el escritorio puede hacer | un `@Slot` en `escritorio/puente.py` y su firma en `web/src/lib/escritorio.ts` | una ventana nueva |
| cómo se usa | `README.md` §Uso; una opción de un backend, `docs/referencia-*.md` | un `GUIA.md` |
| cómo funciona por dentro | `docs/arquitectura.md` | un segundo documento de arquitectura |
| por qué se decidió algo · un pendiente | `docs/decisiones.md` (entrada fechada · §Pendientes con fecha y dueño) | un `TODO.md` |
| qué cambió | `CHANGELOG.md`, bajo la herramienta y su «Sin publicar» | el README |

Lo que hiciste en esta sesión va al mensaje de commit, no a un archivo. Si nada encaja, pregunta antes.

## Cómo se verifica un cambio

```bash
.venv/bin/python -m pytest -q tests                           # motor, recetas, CLI, API, escritorio (corpus generado)
npm run web:pruebas && npx tsc -p web && npm run web:construir  # la web: su lógica, sus tipos y su construcción
python3 scripts/escanear.py --trabajo                         # la guarda del repo público
bats backends/docflow/tests/ && shellcheck -x -S warning backends/docflow/bin/docflow   # lo del CI de docflow
raphi doctor · raphi lista · raphi <operación> archivo -n     # el motor desde la terminal
raphi                                                         # la ventana; la web sola: raphi.sola (README §Uso)
python3 core/archivos.py validar raphi && python3 core/suites.py validar   # desde ~/Documents
meta/doctor/main.sh --breve                                   # desde ~/Documents
```

Un cambio de la web se prueba en el navegador contra `raphi.sola` (o en la ventana) y mirando su consola; el del
escritorio, abriendo `raphi` y soltando archivos desde Dolphin.

## Detalles que cuesta redescubrir

- **La ficha del escritorio**: `escritorio/servidor.py` arranca `raphi.escritorio` con `RAPHI_FICHA`; la ventana la
  pone en `localStorage.tiqsi_token` antes de cargar la página. Sin ella la API responde 401.
- **Lo soltado sobre la ventana llega como ruta** (evento `raphi:rutas`), no como subida: así se puede escribir junto
  al original. En el navegador llega como `File` y se sube.
- **Menús de Dolphin**: un archivo por familia de tipos (`raphi-<familia>.desktop`, ejecutables, bajo el submenú
  «Raphi»); KDE no restringe tipos por acción. Las acciones rápidas son `raphi accion <operación>`.
- **QtWebEngine fuera de pantalla** (pruebas con `QT_QPA_PLATFORM=offscreen`) necesita `QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`.
- **soffice devuelve 0 aunque no convierta** y corrompe su perfil en paralelo: la función `soffice` de `raphi/motor/utiles.py` usa un
  perfil por llamada, tope de tiempo y comprueba el archivo esperado (lo mismo hace docflow).
- **El CI se dispara solo con cambios en `backends/docflow/`** (`.github/workflows/ci.yml`).
- **El `qpdf` de Ubuntu no abre archivos bajo una carpeta oculta del inicio** (su perfil de AppArmor, `/etc/apparmor.d/qpdf`):
  `docflow` falla su verificación ahí («Permission denied»); en `/tmp` o en `~/Documents` funciona. El motor no lo sufre: usa pikepdf.
- **Estado fuera del repo**: `RAPHI_DIR` (por omisión ~/.local/share/raphi: subidos, trabajos, base SQLite), las
  recetas propias en ~/.config/raphi/recetas/, los ajustes de la ventana en ~/.config/achalma/raphi.conf.
