---
tipo: readme
estado: activo
---
# pdf-suite/ — manipulación de PDF: comprimir, unir, dividir, rotar, OCR, cifrar, marca de agua, reparar, metadatos

<!-- suite:inicio -->
**Suite `pdf_suite`** · objetivo *documentos* · estado *activo* · bash · interfaz cli

Manipulación de PDF: comprimir, unir, dividir, rotar, convertir, metadatos, OCR, proteger, reparar.

- Escribe en: archivos · simula por defecto: no
- Depende de: gs, qpdf, pdfinfo
- Nota: gs, qpdf y pdfinfo son obligatorios (lib/validator.sh); pdftk, ocrmypdf, tesseract, exiftool, img2pdf y otros se exigen solo en la operación que los usa.

Comandos:

```bash
main.sh                      # menú
main.sh compress <pdf>
main.sh ocr <pdf>
main.sh merge a.pdf b.pdf
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-04); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

La CLI que comprime, une, divide, extrae, rota, reordena y elimina páginas, convierte (PDF ↔ imagen,
texto, HTML), aplica OCR, lee y escribe metadatos (DocInfo y XMP), cifra, pone marca de agua o numeración,
repara y valida PDF, en archivos sueltos o en carpetas enteras, con un menú interactivo si se llama sin
argumentos. En Raphi escritorio es el motor de **toda** operación PDF salvo PDF/A, que hace docflow
(`docs/decisiones.md`).

| operación | qué hace | motor |
|---|---|---|
| `compress` · `test` | comprimir con cinco niveles; comparar métodos sobre un archivo | Ghostscript, ocrmypdf |
| `merge` · `split` · `extract` · `rotate` · `reorder` · `delete` | operaciones estructurales sobre páginas | qpdf (`delete` con python3) |
| `convert` | PDF → png/jpg/txt/html, imágenes → PDF, extraer imágenes | poppler, img2pdf |
| `ocr` | capa de texto en escaneados; `--scan` lista los que la necesitan | ocrmypdf, tesseract |
| `info` · `metadata` | información, metadatos, título desde el nombre en lote, auditoría de faltantes | poppler, exiftool |
| `encrypt` · `decrypt` · `protect` · `watermark` | cifrado AES-256, sellos, marca de agua, numeración | qpdf, pdftk, cpdf |
| `repair` · `validate` · `optimize` | reparar (tres estrategias), validar, linealizar | qpdf, mutool, Ghostscript |
| `deps` | qué dependencias faltan | — |

## Uso

```bash
backends/pdf-suite/main.sh                              # menú interactivo
backends/pdf-suite/main.sh deps                         # dependencias obligatorias y opcionales
backends/pdf-suite/main.sh -n compress -m ebook doc.pdf # simular (-n) antes de escribir
backends/pdf-suite/main.sh compress -m ebook -r carpeta/
backends/pdf-suite/main.sh merge a.pdf b.pdf -o unido.pdf
backends/pdf-suite/main.sh ocr -l spa+eng escaneo.pdf
backends/pdf-suite/main.sh --help                       # ayuda completa
```

Las dependencias obligatorias son `gs`, `qpdf` y `pdfinfo`; las opcionales activan operaciones concretas
(lista en `docs/referencia-pdf-suite.md`). `backends/pdf-suite/install.sh` ofrece instalarlas con apt o
pacman, **pero además copia el código a una ruta fija ajena al repo y crea con `sudo` un lanzador
`/usr/local/bin/pdf-suite` que apunta a esa copia** (pendiente de corregir en `docs/decisiones.md`): hasta
entonces, instala las dependencias con el gestor de paquetes y llama a `main.sh` desde el repo. Sin
salida explícita (`-o`), cada resultado se escribe junto al original con el sufijo `_out`.

## Estructura

| archivo | qué es |
|---|---|
| `main.sh` | carga los módulos, limpia temporales al salir y despacha la operación |
| `config.sh` | versión, valores por defecto, rutas sugeridas del menú, directorio de logs |
| `lib/cli.sh` | opciones globales, ayuda, menú interactivo y preguntas |
| `lib/validator.sh` | dependencias, PDF válidos, rangos de página, rutas de salida |
| `lib/logger.sh` | mensajes con niveles y log opcional en archivo |
| `lib/compress.sh` · `lib/manipulate.sh` · `lib/convert.sh` · `lib/ocr.sh` · `lib/metadata.sh` · `lib/protect.sh` · `lib/repair.sh` | un módulo por familia de operaciones |
| `install.sh` · `suite.yml` | instalador (ver Uso); manifiesto de la suite |

## Documentación

| documento | para qué |
|---|---|
| `docs/referencia-pdf-suite.md` | dependencias, opciones globales, cada operación con sus flags y ejemplos, problemas frecuentes |
| `docs/arquitectura.md` §Cómo extender | añadir una operación |
| `CHANGELOG.md` | versiones de pdf-suite |

## Límite honesto

- **No simula por defecto**: `-n`/`--dry-run` no escribe salidas, pero sí crea temporales en
  `/tmp/pdfsuite_*` (se limpian al salir).
- **El sufijo (`_out`) es también la marca de «ya procesado»**: cambiarlo con `-s` entre llamadas del mismo
  lote rompe la prevención de bucles y reprocesa lo que ya estaba.
- **Marca de agua y numeración dependen de `cpdf`** (gratuito solo para uso no comercial), que el
  instalador no trae; `delete` necesita `python3`.
- **No implementa PDF/A**: eso queda en docflow.
- **El instalador no sigue al repo** (ver Uso); las rutas sugeridas del menú (`PDF_SEARCH_PATHS` en
  `config.sh`) incluyen carpetas que ya no existen y no afectan a la CLI.
- Sin pruebas automáticas: se comprueba con `bash -n`, `-n` y sobre un PDF de prueba.
