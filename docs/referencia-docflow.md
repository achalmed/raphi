---
tipo: doc
titulo: Referencia de docflow, la CLI de conversión documental
estado: activo
---
# Referencia de docflow

Comandos, opciones, formatos, estado y códigos de salida de `backends/docflow/bin/docflow` (también
`backends/docflow/main.sh`). Para instalarlo y empezar, `backends/docflow/README.md`; para su diseño y cómo
extenderlo, `docs/arquitectura.md`. La ayuda de la propia CLI (`docflow --help`, `docflow <comando> --help`)
manda sobre este documento si discrepan.

## Dependencias

`docflow doctor` dice qué falta y el comando exacto para la distro; `backends/docflow/install.sh` ofrece
instalarlas, enlaza `docflow` en `~/.local/bin` (o `/usr/local/bin` si es escribible) e instala el
autocompletado de bash y fish.

| Dependencia         | Rol                                          |               |
| ------------------- | -------------------------------------------- | ------------- |
| pandoc              | Markdown y documentos de texto               | **requerida** |
| python3 (≥3.11)     | parsers OOXML, limpieza, config TOML         | **requerida** |
| libreoffice         | Office↔ODF, presentaciones, hojas de cálculo | **requerida** |
| qpdf, ghostscript   | operaciones PDF, compresión, PDF/A           | opcional      |
| poppler (pdftotext) | PDF → Markdown                               | opcional      |
| imagemagick         | conversión/optimización de imágenes          | opcional      |
| ocrmypdf, tesseract | OCR de PDFs escaneados                       | opcional      |
| inotify-tools       | modo watch instantáneo                       | opcional      |
| texlive-xetex       | pandoc → PDF de alta calidad                 | opcional      |

## Comandos

| Comando     | Función                                                                               |
| ----------- | ------------------------------------------------------------------------------------- |
| `to-md`     | Office/ODF/PDF/EPUB/HTML → Markdown                                                   |
| `to-pdf`    | Office/ODF/Markdown/HTML/LaTeX → PDF                                                  |
| `to-odf`    | MS Office → OpenDocument                                                              |
| `to-office` | OpenDocument (y Markdown) → MS Office                                                 |
| `pdf <op>`  | merge, split, rotate, extract, compress, pdfa, encrypt, decrypt, watermark, ocr, info |
| `watch`     | vigilar directorio y convertir al vuelo                                               |
| `report`    | reporte de la última sesión (html/csv/json/md)                                        |
| `index`     | índice global + árbol de documentos Markdown                                          |
| `doctor`    | diagnóstico de dependencias con instrucciones por distro                              |
| `formats`   | tabla de formatos soportados                                                          |
| `cache`     | stats / clear / prune del caché de conversiones                                       |
| `config`    | init / show / path de la configuración                                                |

Ayuda contextual: `docflow <comando> --help`.

## Opciones comunes

Valen para los comandos de conversión (`backends/docflow/lib/core/cli.sh`); `docflow <comando> --help`
añade las propias de cada uno.

| opción | efecto |
|---|---|
| `-i, --input <ruta>` | ruta de entrada (equivale a pasarla como argumento) |
| `-o, --output <dir>` (`--output-dir`) | directorio de salida; por defecto, junto al original |
| `-f, --formats <lista>` · `--include <glob>` · `-e, --exclude <patrón>` · `--exclude-regex <re>` · `--no-default-excludes` | selección de archivos (§Selección de archivos) |
| `-w, --overwrite` · `--resume` | sobrescribir salidas; reanudar sin tocar salidas válidas |
| `-n, --dry-run` | simular sin escribir |
| `-j, --jobs <n>` | workers en paralelo (por defecto, `nproc`) |
| `--no-cache` · `--no-verify` | ignorar la caché; omitir la verificación posterior (los originales no se tocan sin ella) |
| `--backup` · `--delete` · `--force` | gestión de originales (§Seguridad de los originales); `--backup` prevalece sobre `--delete` |
| `-v, --verbose` · `--trace` · `-q, --quiet` · `--log-level <nivel>` · `-l, --log <archivo>` · `--json` | registro; `--json` emite los resultados por stdout |
| `--flavor` · `--no-metadata` · `--no-clean` · `--no-notes` · `--slide-separator <s>` · `--pandoc-args "<args>"` | Markdown (§Conversión a Markdown) |
| `--img-format` · `--img-quality` · `--img-max-width` · `--img-optimize` | imágenes extraídas |
| `--pdf-engine <motor>` · `--pdfa` · `--compress` | PDF |
| `--ocr` · `--ocr-lang <langs>` | OCR antes de extraer texto de un PDF |
| `--report <fmts>` · `--report-out <ruta>` | reporte al terminar el lote |
| `--pre-hook <cmd>` · `--post-hook <cmd>` | hooks (§Hooks) |
| `--interval <s>` | polling de `watch` |
| `--config <archivo>` | cargar otro `config.toml` |

## Formatos soportados

`docflow formats` imprime la tabla completa. Resumen:

- **Documentos:** docx, docm, doc, dot, dotx, rtf, odt, fodt, ott
- **Presentaciones:** pptx, pptm, ppsx, potx, ppt, pps, pot, odp, fodp, otp
- **Hojas de cálculo:** xlsx, xlsm, xltx, xls, ods, fods, ots, csv, tsv
- **Otros:** pdf, epub, html, txt, tex, md

Añadir un formato nuevo = crear un archivo de ~3 líneas en `backends/docflow/lib/formats/`
(`docs/arquitectura.md` §Cómo extender); el núcleo no se toca.

## Conversión a Markdown en detalle

```bash
docflow to-md documento.docx
```

produce:

```
documento.docx        ← original intacto
documento.md          ← Markdown con frontmatter YAML
documento_files/
    images/
        figure-001.png
        figure-002.png
```

- **Metadatos**: título, autor, fechas, idioma, palabras clave, empresa…
  extraídos del XML del documento e inyectados como frontmatter
  (desactivable con `--no-metadata`).
- **Imágenes**: extraídas, renombradas secuencialmente y enlazadas con rutas
  relativas. `--img-format webp --img-quality 85` las convierte;
  `--img-max-width 1200` las redimensiona; `--img-optimize` las comprime.
- **Presentaciones**: una sección `#` por diapositiva separada con `---`,
  con listas anidadas, tablas y notas del presentador como cita
  (`--no-notes` para omitirlas).
- **Hojas de cálculo**: una sección `##` por hoja, como tabla Markdown.
- **PDF**: texto extraído con poppler; `--ocr` aplica OCR antes
  (PDFs escaneados) con `--ocr-lang spa+eng`.
- **Limpieza** (`--no-clean` para desactivar): HTML residual, atributos de
  pandoc, líneas en blanco duplicadas, normalización UTF-8 (NFC).
- **Destino** con `--flavor`: `gfm` (defecto), `obsidian`, `logseq`,
  `mkdocs`, `hugo`, `quarto`.
- **Verificación automática**: el `.md` existe, tiene contenido y todas las
  imágenes enlazadas existen; si algo falla, se marca como error y el
  original queda a salvo.

## Operaciones PDF

```bash
docflow pdf merge tesis.pdf cap1.pdf cap2.pdf cap3.pdf
docflow pdf split escaneo.pdf 10                # trozos de 10 páginas
docflow pdf extract libro.pdf --pages 5-20 -o capitulo.pdf
docflow pdf rotate apaisado.pdf --degrees 90 --pages 2-4
docflow pdf compress pesado.pdf -o ligero.pdf   # solo si realmente reduce
docflow pdf pdfa articulo.pdf                   # PDF/A-2b para archivado
docflow pdf encrypt privado.pdf --password clave
docflow pdf decrypt privado.pdf --password clave
docflow pdf watermark borrador.pdf --text "BORRADOR"
docflow pdf ocr escaneado.pdf -o buscable.pdf
docflow pdf info documento.pdf
```

En `to-pdf`, `--pdfa` y `--compress` aplican el post-proceso a cada PDF
generado; `--pdf-engine` fuerza un motor concreto.

## Selección de archivos

```bash
-f docx,odt             # solo estas extensiones
--include "*.final.*"   # solo archivos que casen con el glob
-e node_modules -e .git # excluir directorios por nombre (repetible)
-e "*.tmp"              # excluir por patrón
--exclude-regex 'borrador|v[0-9]+' # excluir rutas por regex
--no-default-excludes   # no aplicar la lista por defecto
```

Exclusiones por defecto: `.git node_modules __pycache__ _backup _site
_freeze .quarto .obsidian` y similares. Los archivos de bloqueo de Office
(`~$doc.docx`, `.~lock.*`) se ignoran siempre.

## Seguridad de los originales

Invariante del proyecto: **un original solo se toca si su conversión fue
exitosa Y verificada.**

```bash
--backup     # mueve originales exitosos a _backup/ (nunca pregunta)
--delete     # elimina originales exitosos (pide confirmación)
--force      # suprime la confirmación (automatización/cron)
```

Los archivos con error, protegidos por contraseña o sin convertir **jamás**
se mueven ni eliminan. Los documentos protegidos se detectan antes de
convertir y se reportan con estado propio (`protected`).

## Caché y reanudación

docflow guarda un índice SHA-256 de cada conversión exitosa
(~/.cache/docflow/). Un archivo sin cambios con las mismas opciones no se
reconvierte, lo que hace las pasadas incrementales sobre colecciones grandes
casi instantáneas.

```bash
docflow to-md /mnt/Datos --resume   # reanudar un lote interrumpido
docflow to-md tesis/ --no-cache -w  # forzar reconversión
docflow cache stats|prune|clear
```

## Reportes

```bash
docflow to-md tesis/ --report html,json   # al terminar el lote
docflow report md                         # de la última sesión
```

Incluyen: archivos convertidos, errores con causa, protegidos, tiempo total
y promedio, tamaños de entrada/salida, porcentaje de éxito y desglose por
formato. Para integración con scripts: `--json` emite los resultados de la
sesión por stdout y `-q` silencia el resto.

## Modo watch

```bash
docflow watch ~/Descargas                    # → PDF al detectar archivos
docflow watch --to md -f docx ~/notas/
docflow watch ~/buzon --post-hook 'notify-send docflow "$DOCFLOW_OUTPUT"'
```

Usa inotify si está instalado (detección instantánea, CPU cero); si no,
polling cada `--interval` segundos.

## Hooks

```bash
--pre-hook  'echo "convirtiendo $DOCFLOW_INPUT"'
--post-hook 'git -C $(dirname "$DOCFLOW_OUTPUT") add "$DOCFLOW_OUTPUT"'
```

El comando recibe `DOCFLOW_INPUT`, `DOCFLOW_OUTPUT`, `DOCFLOW_STATUS`
(solo post: `ok`/`fail`) y `DOCFLOW_TASK` como variables de entorno.

## Configuración

```bash
docflow config init    # crea ~/.config/docflow/config.toml comentado
```

Todas las opciones de la CLI tienen su equivalente permanente en TOML
(secciones `[general]`, `[markdown]`, `[images]`, `[pdf]`, `[ocr]`,
`[watch]`, `[reports]`, `[hooks]`, `[originals]`).
Precedencia: **CLI > config.toml > defaults**.

## Códigos de salida

| Código | Significado                             |
| ------ | --------------------------------------- |
| 0      | éxito                                   |
| 1      | error general                           |
| 2      | uso incorrecto de la CLI                |
| 3      | ruta de entrada inválida                |
| 4      | no se encontraron archivos que procesar |
| 5      | dependencia requerida ausente           |
| 6      | al menos una conversión falló           |
| 7      | verificación post-conversión fallida    |
| 8      | configuración inválida                  |

## Problemas frecuentes

**«protegido por contraseña o corrupto»** — el documento está cifrado
(o truncado). Para PDF: `docflow pdf decrypt archivo.pdf --password …`.

**LibreOffice tarda o se cuelga con un documento** — hay un timeout de 300 s
por archivo (`DOCFLOW_SOFFICE_TIMEOUT` para ajustarlo); el archivo se marca
como fallo y el lote continúa.

**El PDF no tiene las fuentes correctas** — instala las fuentes del documento
(`fc-list | grep Fuente`); LibreOffice sustituye las que faltan.

**Las imágenes no se convierten a WebP** — requiere ImageMagick
(`docflow doctor` te da el comando exacto para tu distro).

**Quiero ver qué haría sin tocar nada** — `docflow to-md -n -v ruta/`.

## Consumidores

`docflow to-md` escribe, salvo `--no-metadata`, un frontmatter YAML con las claves de
`meta/docs/historial/NORMATIVA_ARCHIVOS.md` §6.2 (`backends/docflow/lib/helpers/office_meta.py`), en este orden: `id`,
`tipo: original`, `titulo` (o el nombre del archivo), `estado: activo`; si el documento los trae, `creado`
(fecha), `autor`, `asunto`, `descripcion`, `palabras_clave`, `categoria`, `idioma`, `modificado`,
`modificado_por`, `organizacion`, `paginas`, `palabras` y `laminas`; y siempre `origen` (nombre del archivo
convertido), `convertidor: docflow`, `convertido` (instante) y `tags: [original]`. Las imágenes van a `<base>_files/images/figure-NNN.*`.

Dependen de esa forma el vault (`notas`, notas `tipo: original`), la estructura de proyecto de
`escritura` (`escritura/proyecto/esquema.py` y `escritura/proyecto/lib/normalizar.py` ubican las imágenes de una conversión en
`originales/`) y `meta/vault-os/organization/normalizar_notas.py`. Un cambio en las claves o en la carpeta de
imágenes se anuncia en `docs/decisiones.md` y se avisa a esos tres.
