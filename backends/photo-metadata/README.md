---
tipo: readme
estado: activo
---
# scripts_photo_metadata_suite/ — fechas y nombres de fotos y videos: renombrado por la marca de tiempo impresa, auditoría, EXIF y digiKam
<!-- suite:inicio -->
**Suite `photo_metadata_suite`** · objetivo *multimedia* · estado *activo* · python · interfaz cli

Renombra e incrusta fechas en fotos de cámaras (Tapo y similares) a partir de la marca de tiempo; audita y sincroniza con digiKam.

- Escribe en: archivos · simula por defecto: sí
- Depende de: exiftool, python3

Comandos:

```bash
main.py analyze <carpeta>
main.py apply <carpeta> --execute
main.py verify <carpeta>
main.py undo <carpeta> --execute
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-09-20); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

Una CLI con siete subcomandos sobre **una carpeta** de fotos y videos (sin recorrer subcarpetas). Dos familias:

- **Renombrado por la marca de tiempo impresa** (cámaras que imprimen `AAAA-MM-DD HH:MM:SS` en una esquina):
  `analyze` lee la marca con OCR (`tesseract`; en los videos, sobre un fotograma extraído con `ffmpeg`) y
  arma el plan `AAAAMMDD_HHMMSS.ext`; `verify` genera montajes PNG de las lecturas dudosas y las colisiones;
  `apply` renombra según el plan; `undo` revierte el último `apply`.
- **Fechas y nombres de una colección**: `audit-dates` compara la fecha del nombre con la de los metadatos;
  `embed-date` escribe en EXIF/QuickTime/XMP la fecha que trae el nombre; `fix-names` corrige extensiones que
  no corresponden al formato real y lleva a `AAAAMMDD_HHMMSS` los nombres con fecha decodificable (WhatsApp,
  Facebook, capturas, epoch…) o los que no traen fecha pero sí EXIF; `sync-digikam` escribe en el EXIF las
  fechas corregidas dentro de digiKam.

Qué escribe, siempre dentro de la carpeta objetivo:

| subcomando | sin `--execute` | con `--execute` |
|---|---|---|
| `analyze` | `rename_plan.csv` y `analysis.json` (no acepta `--execute`) | — |
| `verify` | `verify_review_N.png` y, si no se da `--from-plan`, `analysis.json` | — |
| `apply` | si no se da `--from-plan`, reanaliza y **reescribe `rename_plan.csv`** y `analysis.json` | renombra en dos fases y deja `_rename_log.csv` y `_undo_rename.sh` |
| `undo` | nada | revierte con `_rename_log.csv` y lo borra |
| `audit-dates` | `date_audit.csv` (no acepta `--execute`) | — |
| `embed-date` | nada | metadatos de los archivos, en el sitio, y su fecha de modificación |
| `fix-names` | nada | renombra y añade filas a `_fix_log.csv` |
| `sync-digikam` | nada | metadatos de los archivos, en el sitio, y su fecha de modificación |

Simula por defecto en los cinco subcomandos que aceptan `--execute`. `sync-digikam` lee `digikam4.db` de la
carpeta padre (o de la propia carpeta) **en una copia temporal**; la base original no se toca. Los mensajes van
a la terminal y, con `--log-file`, también a ese archivo.

## Uso

```bash
python3 main.py analyze "<carpeta>"                         # plan y JSON, sin renombrar
python3 main.py verify "<carpeta>"                          # montajes de revisión
python3 main.py apply "<carpeta>" --from-plan "<carpeta>/rename_plan.csv"             # simula el plan revisado
python3 main.py apply "<carpeta>" --from-plan "<carpeta>/rename_plan.csv" --execute   # lo aplica
python3 main.py undo "<carpeta>" --execute                  # revierte el último apply
python3 main.py audit-dates "<carpeta>" --year 2026         # nombre frente a EXIF, a CSV
python3 main.py fix-names "<carpeta>"                       # simula; --execute renombra
python3 main.py embed-date "<carpeta>" --only images        # simula; --execute escribe
python3 main.py sync-digikam "<carpeta>"                    # simula; --execute escribe
python3 main.py analyze "<carpeta>" --crop-left 0 --crop-width 1 --crop-height 0.10   # marca en otra franja
```

| opción | subcomandos | qué hace | por defecto |
|---|---|---|---|
| `--execute` | `apply`, `undo`, `embed-date`, `fix-names`, `sync-digikam` | aplica de verdad | simula |
| `--from-plan CSV` | `apply`, `verify` | usa un plan editado a mano en vez de reanalizar | reanaliza |
| `--workers N` | `analyze`, `apply`, `verify` | procesos de OCR en paralelo; `0` = todos los núcleos | `0` |
| `--limit N` | `analyze`, `apply`, `verify` | solo los N primeros archivos | `0` (sin límite) |
| `--only all\|images\|videos` | `analyze`, `apply`, `verify`, `embed-date` | qué medios procesar | `all` |
| `--crop-left`, `--crop-top` | `analyze`, `apply`, `verify` | esquina del recorte donde se lee la marca, en fracción 0–1 | `0`, `0` |
| `--crop-width`, `--crop-height` | `analyze`, `apply`, `verify` | tamaño del recorte, en fracción 0–1 | `0.40`, `0.075` |
| `--trust-name` | `embed-date` | el nombre manda sobre cualquier EXIF (fotos escaneadas) | no |
| `--year N` | `audit-dates` | año esperado, para señalar intrusos | el nombre de la carpeta, si es un año |
| `-v`, `--verbose` | todos | salida detallada | no |
| `--log-file RUTA` | todos | copia los mensajes a ese archivo | no |
| `--version` | — | la imprime | — |

El resto de valores (umbrales del OCR, regex de la marca, rango de años 2015–2035, extensiones, etiquetas de
fecha que se escriben, nombres de los archivos de salida, tolerancia de la auditoría) vive en `config.py`.
Códigos de salida: `0` bien, `1` error de E/S, `2` uso o plan inválido, `3` no encontrado, `4` sin permisos,
`5` falta una dependencia.

Requisitos: Python 3 con Pillow y numpy (`requirements.txt`; los cargan todos los subcomandos); `tesseract`
para `analyze`, `apply` y `verify`; `ffmpeg` solo si la carpeta tiene videos; `exiftool` para `audit-dates`,
`embed-date`, `fix-names` y `sync-digikam`; el logger común del workspace (`core/py-common/logger.py`, en su
raíz), que `lib/logger.py` busca subiendo carpetas.

## Estructura

| archivo | qué hace |
|---|---|
| `main.py` | parsea, despacha el subcomando y traduce las excepciones a códigos de salida |
| `config.py` | `Settings` con todos los valores ajustables y los códigos de salida |
| `requirements.txt` | dependencias de Python |
| `lib/cli.py` | subcomandos y opciones; fusiona las opciones con `config.py` |
| `lib/commands.py` | implementación de cada subcomando |
| `lib/validator.py` | comprueba `tesseract`, `ffmpeg`, `exiftool`, la carpeta y el recorte |
| `lib/scanner.py` | lista los medios de la carpeta y los analiza en paralelo |
| `lib/ocr.py` | recorte, binarización con varios umbrales, `tesseract` y votación de la lectura |
| `lib/video.py` | extrae un fotograma de un video con `ffmpeg` |
| `lib/media.py` | lleva fotos y videos al mismo OCR |
| `lib/planner.py` | plan de renombrado, sufijos `_2`, `_3`… ante colisiones, lectura y escritura del CSV |
| `lib/renamer.py` | renombrado en dos fases, registro y script de deshacer |
| `lib/montage.py` | montajes PNG de revisión |
| `lib/audit.py` | lectura de fechas con `exiftool`, clasificación nombre frente a metadatos y CSV de auditoría |
| `lib/metadata.py` | escritura de fechas con `exiftool` (pase estándar, pase especial y fecha de archivo) |
| `lib/fixer.py` | correcciones de extensión y de nombre, y su registro |
| `lib/digikam.py` | lee las fechas de digiKam en copia y las escribe con `exiftool` |
| `lib/errors.py` | excepciones propias |
| `lib/logger.py` | envoltorio del logger común |
| `suite.yml` | manifiesto de la suite (genera el bloque de arriba) |

## Límite honesto

- **No todo se deshace.** Solo `apply` tiene `undo`. `embed-date` y `sync-digikam` escriben con
  `-overwrite_original`: sin copia de respaldo ni registro de los valores anteriores. `fix-names` anota lo que
  renombra en `_fix_log.csv`, pero no hay subcomando que lo revierta (ver `docs/decisiones.md` §Pendientes).
- **`apply` sin `--from-plan` reanaliza y reescribe `rename_plan.csv`**, también al simular: las correcciones
  hechas a mano en el plan se pierden si no se pasa `--from-plan`.
- **`undo` solo revierte el último `apply`**: cada `apply --execute` sobrescribe `_rename_log.csv` y
  `_undo_rename.sh`. `undo --execute` borra el registro y deja el script.
- **`embed-date` escribe por defecto solo donde falta la fecha** (o donde el EXIF es posterior al día del nombre
  y no trae cámara); `--trust-name` la pisa siempre. La fecha de modificación del archivo la fija en todos los
  que tienen nombre `AAAAMMDD_HHMMSS`, haya o no EXIF; en formatos sin metadatos escribibles es lo único que
  queda.
- **`fix-names` también renombra desde el EXIF** cuando el nombre no trae fecha o el EXIF es anterior; no toca
  mayúsculas y minúsculas.
- **Un solo formato de marca** (`AAAA-MM-DD HH:MM:SS`) y años entre 2015 y 2035; otro formato exige cambiar
  `timestamp_regex` en `config.py`. Lo que no tiene marca legible queda `SKIP` y no se toca.
- **Una carpeta cada vez**: ningún subcomando recorre subcarpetas.
- **Solo se usa en Linux**; otras plataformas no están probadas.
