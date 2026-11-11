---
tipo: readme
estado: activo
---
# raphi/ — Raphi: PDF, ofimática y conversión de archivos (antes DocFlow Studio)

<!-- suite:inicio -->
**Suite `raphi`** · objetivo *documentos* · estado *activo* · python · interfaz gui

PDF, ofimática y conversión de archivos (motor, CLI, web y escritorio; antes DocFlow Studio).

- Escribe en: archivos · simula por defecto: no
- Depende de: {'PySide6 (el del sistema para Raphi Studio': 'python3-pyside6.* con Kirigami y QtMultimedia de QML, y gui-comun 3.0; el del .venv para la ventana web)'}, pikepdf, PyMuPDF
- Nota: motor y CLI en raphi/ (python -m raphi); la web en web/ y la ventana en escritorio/ (la misma interfaz); docflow, en backends/docflow (pdf-suite y page-counter se retiraron en R8)

Comandos:

```bash
main.py
raphi lista
raphi doctor
raphi comprimir a.pdf --hasta 10 -n   # una operación (simulada)
raphi receta para-enviar a.pdf
python3 -m pytest -q tests
tests/run.sh
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-11-08); no se edita a mano.</sub>
<!-- suite:fin -->

<!-- suites:inicio -->
Suites de esta carpeta (5); índice global en `meta/INDICE_SCRIPTS.md`. Patrón: M main · C config · L lib.

| Suite | Carpeta | Objetivo | Escribe en | Simula | Timer | Estado | Patrón |
|---|---|---|---|---|---|---|---|
| `docflow` | [raphi/backends/docflow](backends/docflow/) | documentos | archivos | no |  | activo | `MCL` |
| `photo_metadata_suite` | [raphi/backends/photo-metadata](backends/photo-metadata/) | multimedia | archivos | sí |  | activo | `MCL` |
| `video_downloader` | [raphi/backends/video-downloader](backends/video-downloader/) | multimedia | archivos | no |  | activo | `MCL` |
| `whisper_transcriber` | [raphi/backends/whisper-transcriber](backends/whisper-transcriber/) | multimedia | archivos | no |  | activo | `MCL` |
| `raphi` | [raphi](./) | documentos | archivos | no |  | activo | `MCL` |

<sub>Bloque generado desde los `suite.yml` por `core/suites.py generar` (2026-11-08); no se edita a mano.</sub>
<!-- suites:fin -->

## Qué es

**Raphi** («hoja» en quechua; hasta el 2026-10-27, «DocFlow Studio») es una sola aplicación para PDF, ofimática y
conversión de archivos, con tres caras sobre el mismo motor: la **ventana de escritorio** (`raphi`), la **web** (sola,
con cuentas, o como módulo de la plataforma Qillqa) y la **CLI** (`raphi <operación>`). Es local: ningún archivo sale a
un servicio ajeno.

- **62 operaciones** en un solo registro (`raphi/motor/`): unir, dividir, extraer, rotar, reordenar, componer páginas
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

docflow sigue como CLI completa (`backends/docflow`: conversión documental masiva, con caché, paralelización y tests
Bats); pdf-suite y page-counter se retiraron en R8 porque el motor hace todo lo suyo. El plan por fases
vive en el repo de Qillqa: `qillqa/docs/plataforma/propuesta-raphi.md`.

## Uso

```bash
./install.sh                                          # una vez: .venv (Python del sistema), Tiqsi, lanzador raphi y entrada de escritorio
npm install && npm run web:construir                  # la web (web/dist), que usan la ventana y raphi.sola
raphi                                                 # Raphi Studio (QML + Kirigami; raphi --web: la ventana web); raphi escritorio a.pdf abre con archivos
raphi ver_metadatos foto.jpg · raphi suma_verificacion iso.img --algoritmo todas   # lo de Metadata Cleaner y KDE-Services, en la CLI
tests/run.sh                                          # las pruebas de Raphi Studio sobre archivos de muestra (escritorio/studio/README.md)
raphi lista · raphi doctor                            # las operaciones y lo que falta en esta máquina
raphi comprimir *.pdf --hasta 10 -n                   # cualquier operación: -n simula, -o carpeta de salida, --json
raphi receta escaneo-mesa-de-partes recibido.pdf      # una cadena guardada (raphi recetas); raphi formatos foto.heic
raphi transcribir entrevista.mp3 --idioma es          # Whisper local; raphi descargar --url URL --modo audio
raphi convertir_audio notas/ -r --tasa 192k           # una carpeta entera (-r con subcarpetas); las etiquetas se conservan
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
| `escritorio/studio/` | Raphi Studio: la ventana de trabajo de la familia de los studios (QML + Kirigami sobre `gui-comun`), con las opciones de cada herramienta generadas de su ficha; el motor corre como proceso con el `.venv` (`corredor.py`) |
| `escritorio/` | la ventana que muestra la web (`raphi --web`): servidor local, puente QWebChannel; y lo que comparten las dos: carpetas vigiladas, menús de Dolphin |
| `backends/docflow/` | docflow, la CLI de conversión documental, con su `suite.yml`, su README, sus tests y su CI |
| `backends/video-downloader/` · `whisper-transcriber/` · `photo-metadata/` | las CLI de medios llegadas de scripts-linux el 2026-10-31 (yt-dlp, Whisper, fechas de fotos), cada una con su README y su `suite.yml` |
| `tests/` | pruebas del motor, la CLI, la API y el escritorio, con su corpus generado |
| `scripts/escanear.py` · `demo/demo.conf` | la guarda del repositorio público (escáner de Tiqsi en cada envío) |
| `docs/` | arquitectura, el rediseño de Raphi Studio, referencia de las operaciones (generada) y de docflow, decisiones (índice por `core/docs.py indice`) |
| `suite.yml` · `pyproject.toml` · `package.json` · `requirements.txt` | manifiestos y dependencias |
| `CHANGELOG.md` · `LICENSE` | versiones por herramienta; AGPL-3.0 |

## Límite honesto

- **Editar el texto existente de un PDF** no está (sí tachar, sellar, foliar y numerar encima); la firma digital se
  verifica, no se hace (R7).
- **La configuración y la caché de docflow** (`docflow config`, `docflow cache`) se ven desde su CLI: la web no las muestra.
- **La rueda de soltar es Muyu** (repo privado `muyu`, desde el 2026-11-11): usa el corredor de Raphi (`escritorio/studio/corredor.py`: `rueda`, `ejecutar`, `vista`, `actuales`) como su API; Raphi no sabe de ella.
- **El OCR es pesado**: la cola corre `RAPHI_CONCURRENCIA` trabajos a la vez (1 por omisión).
- **Estado fuera del repo**: `RAPHI_DIR` (~/.local/share/raphi: subidos y trabajos, borrados a las 24 h; base
  SQLite), recetas propias en ~/.config/raphi/recetas/, ajustes de la ventana en ~/.config/achalma/raphi.conf;
  docflow guarda lo suyo en ~/.config/docflow/, ~/.local/state/docflow/ y ~/.cache/docflow/.
- Licencia **AGPL-3.0** desde el 2026-10-27 (lo publicado antes sigue siendo MIT). El repositorio es público:
  `python3 scripts/escanear.py --instalar-guarda` instala la guarda que escanea cada envío.
