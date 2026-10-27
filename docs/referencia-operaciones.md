---
tipo: doc
titulo: Referencia de las operaciones de Raphi
estado: activo
genero: referencia
---
# Referencia de las operaciones de Raphi

GENERADO por `python -m raphi referencia --aplicar` desde el registro del motor (`raphi/motor/`); no editar.
Cada operación se usa igual desde la CLI (`raphi <id> archivos --opción valor`, `-n` simula), la API
(`POST /api/raphi/trabajos` con `operacion` y `params`) y la web, que arma su formulario con esta misma ficha.

## Organizar

### `unir` — Unir PDF

Junta varios PDF en uno, en el orden dado.

Entrada: pdfs (todas juntas) · .pdf · necesita: nada aparte.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--nombre` | Nombre del archivo (sin «.pdf») | texto | `unido` |
| `--marcadores` | Un marcador por archivo | casilla | `True` |

### `dividir` — Dividir PDF

Parte un PDF por rangos o cada N páginas.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: nada aparte.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--cada` | Páginas por parte (0 = una por página) | entero | `0` |
| `--rangos` | O por rangos (separados por «;») («1-3; 4-10; 11-z»: un PDF por rango) | texto |  |

### `extraer` — Extraer páginas

Saca las páginas elegidas a un PDF nuevo.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: nada aparte.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--paginas` | Páginas (1-5 · 1,3,10-12 · 10-z · -3 (las tres últimas)) | paginas | `1` |

### `rotar` — Rotar páginas

Gira las páginas elegidas (o todas).

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: nada aparte.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--angulo` | Ángulo | opcion: 90 · 180 · 270 | `90` |
| `--paginas` | Páginas (vacío = todas) | paginas |  |

### `reordenar` — Reordenar páginas

Pone las páginas en el orden escrito (vacío = invertir).

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: nada aparte.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--orden` | Nuevo orden (3,1,2,4-z · vacío invierte el documento) | paginas |  |

### `eliminar` — Eliminar páginas

Quita las páginas elegidas.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: nada aparte.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--paginas` | Páginas a quitar | paginas |  |

### `componer` — Componer (mesa de trabajo)

Arma un PDF con páginas de varios archivos, en cualquier orden, rotadas o en blanco.

Entrada: pdfs (todas juntas) · .pdf · necesita: nada aparte.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--plan` | Plan de páginas ([{"archivo": 0, "pagina": 3, "rotar": 90}, {"blanca": true}, …]) | json |  |
| `--nombre` | Nombre del archivo | texto | `compuesto` |

## Optimizar

### `comprimir` — Comprimir PDF

Reduce el peso. Con un tope («10 MB»), prueba del más fiel al más agresivo y se queda con el primero que entra.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: gs.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--perfil` | Nivel | opcion: ebook · screen · printer · prepress | `ebook` |
| `--hasta` | Que pese menos de (MB, 0 = sin tope) (p. ej. 10 para una mesa de partes virtual) | tamano | `0` |
| `--umbral` | Ganancia mínima (%) (si reduce menos, se conserva el original) | entero | `5` |

### `comparar_compresion` — Comparar niveles de compresión

Prueba los cuatro niveles y dice cuánto pesaría cada uno, sin guardar nada.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: gs.

### `linearizar` — Optimizar para la web

Lineariza el PDF: la primera página se ve antes de que termine de descargarse.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: nada aparte.

### `reparar` — Reparar PDF

Reconstruye un PDF dañado (qpdf y, si no basta, Ghostscript).

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: nada aparte.

### `validar` — Validar estructura

Revisa la estructura interna (qpdf --check) sin escribir nada.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: nada aparte.

### `pdfa` — Convertir a PDF/A (archivo)

PDF/A-2b, el formato de conservación a largo plazo de los archivos públicos.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: gs.

## Convertir

### `a_pdf` — Documento a PDF

Word, Excel, PowerPoint, LibreOffice, RTF, texto o HTML a PDF.

Entrada: documentos (cada archivo por su lado) · .doc .docx .dotx .odt .rtf .txt .xls .xlsx .ods .csv .ppt .pptx .odp .html .htm .epub · necesita: soffice.

### `ofimatica` — Entre formatos de oficina

Office ↔ LibreOffice (docx ↔ odt, xlsx ↔ ods, pptx ↔ odp) y más.

Entrada: documentos (cada archivo por su lado) · .doc .docx .dotx .odt .rtf .txt .xls .xlsx .ods .csv .ppt .pptx .odp .html .htm .epub · necesita: soffice.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--formato` | A | opcion: docx · odt · xlsx · ods · pptx · odp · rtf · txt · html | `odt` |

### `imagenes_a_pdf` — Imágenes a PDF

Junta fotos o escaneos (también HEIC del celular) en un PDF, una por página, en el orden dado.

Entrada: imagenes (todas juntas) · .jpg .jpeg .png .webp .heic .heif .avif .tif .tiff .bmp .gif · necesita: PIL.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--nombre` | Nombre del archivo | texto | `imagenes` |
| `--papel` | Página | opcion: imagen · A4 · carta | `imagen` |
| `--ppp` | Resolución (ppp) | entero | `150` |
| `--calidad` | Calidad JPG | entero | `85` |

### `a_markdown` — Documento a Markdown

Word, PowerPoint, Excel, PDF y más a Markdown con su frontmatter (con docflow, que lee pptx y xlsx).

Entrada: documentos (cada archivo por su lado) · .doc .docx .dotx .odt .rtf .txt .xls .xlsx .ods .csv .ppt .pptx .odp .html .htm .epub .pdf .md .tex · necesita: pandoc.

### `tablas_a_excel` — Tablas a Excel

Encuentra las tablas del PDF y deja cada una en una hoja de Excel.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: pymupdf, openpyxl.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--paginas` | Páginas (vacío = todas) | paginas |  |

### `pdf_a_imagen` — PDF a imagen

Cada página como imagen (PNG, JPG o TIFF).

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: pdftocairo.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--formato` | Formato | opcion: png · jpg · tiff | `png` |
| `--ppp` | Resolución (ppp) | entero | `150` |
| `--paginas` | Páginas (vacío = todas) | paginas |  |

### `pdf_a_texto` — PDF a texto

Extrae el texto (conservando la disposición, si se pide).

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: pdftotext.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--disposicion` | Conservar la disposición | casilla | `True` |

### `pdf_a_html` — PDF a HTML

Una página web con el texto y las imágenes de cada página.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: pymupdf.

### `pdf_a_word` — PDF a Word (básico)

Lo abre LibreOffice y lo guarda como .docx: sirve para recuperar el texto; el diseño puede variar.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: soffice.

### `extraer_imagenes` — Extraer imágenes

Saca las imágenes incrustadas tal como están en el PDF.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: pdfimages.

### `ocr` — OCR (texto buscable)

Reconoce el texto de un escaneo y le agrega una capa que se puede buscar y copiar.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: ocrmypdf.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--idioma` | Idioma | opcion: spa · eng · spa+eng | `spa` |
| `--enderezar` | Enderezar páginas torcidas | casilla | `True` |
| `--rotar` | Girar páginas de costado | casilla | `True` |
| `--forzar` | Rehacer aunque ya tenga texto | casilla | `False` |
| `--optimizar` | Optimización (0–3) | entero | `1` |

### `miniatura` — Miniatura de una página

Una imagen pequeña de una página (para vistas previas).

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: pymupdf.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--pagina` | Página | entero | `1` |
| `--ancho` | Ancho (px) | entero | `240` |
| `--formato` | Formato | opcion: png · jpg · webp | `png` |

## Editar

### `marca_agua` — Marca de agua

Escribe un texto en diagonal (o recto) sobre las páginas.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: pymupdf.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--texto` | Texto | texto | `BORRADOR` |
| `--tamano` | Tamaño (pt) | entero | `60` |
| `--opacidad` | Opacidad (0–1) | decimal | `0.18` |
| `--angulo` | Ángulo | entero | `45` |
| `--color` | Color | color | `#C0392B` |
| `--paginas` | Páginas (vacío = todas) | paginas |  |

### `numerar` — Numerar páginas

Pone el número de página («Página 3 de 10» o como se quiera).

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: pymupdf.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--formato` | Formato ({n} número · {total} total · «Página {n} de {total}») | texto | `{n}` |
| `--posicion` | Posición | opcion: arriba-izquierda · arriba-centro · arriba-derecha · abajo-izquierda · abajo-centro · abajo-derecha · centro | `abajo-centro` |
| `--inicio` | Primer número | entero | `1` |
| `--desde` | Desde la página (p. ej. 2 para no numerar la carátula) | entero | `1` |
| `--tamano` | Tamaño (pt) | entero | `10` |
| `--color` | Color | color | `#000000` |

### `foliar` — Foliar expediente

Numera los folios en el ángulo superior derecho, correlativos o de atrás hacia adelante, siguiendo una cuenta anterior si la hay.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: pymupdf.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--inicio` | Primer folio (para continuar un expediente ya foliado) | entero | `1` |
| `--orden` | Orden | opcion: ascendente · inverso | `ascendente` |
| `--formato` | Formato ({n} · «Folio {n}» · «{n:04d}») | texto | `{n}` |
| `--posicion` | Posición | opcion: arriba-izquierda · arriba-centro · arriba-derecha · abajo-izquierda · abajo-centro · abajo-derecha · centro | `arriba-derecha` |
| `--recuadro` | Con recuadro | casilla | `True` |
| `--tamano` | Tamaño (pt) | entero | `11` |
| `--color` | Color | color | `#1F3A93` |

### `sello` — Sello de recepción

Estampa el sello «RECIBIDO» con la fecha y la hora, los folios y lo que se escriba.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: pymupdf.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--titulo` | Título | texto | `RECIBIDO` |
| `--entidad` | Oficina o entidad | texto |  |
| `--fecha` | Fecha y hora (vacío = ahora) | texto |  |
| `--folios` | Contar los folios | casilla | `True` |
| `--nota` | Más líneas (registro, firma…) | multilinea |  |
| `--posicion` | Posición | opcion: arriba-izquierda · arriba-centro · arriba-derecha · abajo-izquierda · abajo-centro · abajo-derecha · centro | `arriba-derecha` |
| `--pagina` | Página | entero | `1` |
| `--color` | Color | color | `#1F3A93` |

### `metadatos` — Editar metadatos

Título, autor, asunto y palabras clave (DocInfo y XMP); o el título tomado del nombre del archivo.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: nada aparte.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--titulo` | Título | texto |  |
| `--autor` | Autor | texto |  |
| `--asunto` | Asunto | texto |  |
| `--palabras` | Palabras clave | texto |  |
| `--titulo-del-nombre` | Título desde el nombre del archivo | casilla | `False` |

### `resaltar` — Resaltar términos

Marca con resaltador cada aparición de los términos (anotaciones que se pueden quitar).

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: pymupdf.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--terminos` | Términos (uno por línea) | multilinea |  |
| `--color` | Color | color | `#FFE14D` |
| `--paginas` | Páginas (vacío = todas) | paginas |  |

### `nota` — Nota en una página

Un cuadro de texto visible (o una nota adhesiva) en la página y posición elegidas.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: pymupdf.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--texto` | Texto | multilinea |  |
| `--pagina` | Página | entero | `1` |
| `--posicion` | Posición | opcion: arriba-izquierda · arriba-centro · arriba-derecha · abajo-izquierda · abajo-centro · abajo-derecha · centro | `arriba-derecha` |
| `--tipo` | Tipo | opcion: cuadro · adhesiva | `cuadro` |
| `--autor` | Autor | texto |  |

### `estampar_imagen` — Estampar firma o sello (imagen)

Pone una imagen (la firma escaneada, un sello, un logo) en la página y posición elegidas. Es una firma visible, no una firma digital.

Entrada: archivos (todas juntas) · .pdf .png .jpg .jpeg .webp · necesita: pymupdf.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--paginas` | Páginas (z = la última; vacío = todas) | paginas | `z` |
| `--posicion` | Posición | opcion: arriba-izquierda · arriba-centro · arriba-derecha · abajo-izquierda · abajo-centro · abajo-derecha · centro | `abajo-derecha` |
| `--ancho` | Ancho (mm) | decimal | `40` |
| `--margen` | Margen (mm) | decimal | `15` |

### `formulario` — Rellenar formulario

Lista los campos de un formulario PDF y, si se dan valores, los rellena (y aplana, si se pide).

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: pymupdf.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--valores` | Valores (JSON: {"campo": "valor"}) (vacío = solo listar los campos) | multilinea |  |
| `--aplanar` | Aplanar (ya no se puede editar) | casilla | `False` |

### `aplanar` — Aplanar anotaciones y formularios

Convierte anotaciones, resaltados y campos en parte de la página: se ven igual en cualquier lector y ya no se editan.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: pymupdf.

## Seguridad

### `quitar_metadatos` — Quitar metadatos

Borra autor, programa, fechas y el XMP del PDF antes de compartirlo.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: nada aparte.

### `tachar` — Tachar (redactar de verdad)

Borra del archivo los términos o datos elegidos (DNI, RUC, correos, celulares) y los cubre; luego comprueba que ya no se puedan copiar.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: pymupdf.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--terminos` | Términos a tachar (uno por línea) | multilinea |  |
| `--dni` | Todos los DNI | casilla | `False` |
| `--ruc` | Todos los RUC | casilla | `False` |
| `--correo` | Todos los correos | casilla | `False` |
| `--celular` | Todos los celulares | casilla | `False` |
| `--paginas` | Páginas (vacío = todas) | paginas |  |
| `--color` | Color del tachado | color | `#000000` |

### `firmas` — Verificar firmas digitales

Quién firmó, cuándo, si el documento cambió después de firmarse y, con raíces de confianza (RAPHI_RAICES), si la cadena es válida.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: pyhanko.

### `cifrar` — Proteger con contraseña

Cifra el PDF con AES-256 y, si se quiere, limita imprimir o copiar.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: nada aparte.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--clave` | Contraseña para abrirlo | clave |  |
| `--propietario` | Contraseña de permisos (vacío = la misma) | clave |  |
| `--imprimir` | Permitir imprimir | casilla | `True` |
| `--copiar` | Permitir copiar texto | casilla | `True` |
| `--modificar` | Permitir modificar | casilla | `False` |

### `descifrar` — Quitar contraseña

Abre un PDF protegido con su contraseña y lo guarda sin ella.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: nada aparte.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--clave` | Contraseña | clave |  |

## Información

### `comparar` — Comparar dos PDF

Dice qué cambió entre dos versiones, página por página, con un informe HTML que marca lo quitado y lo añadido.

Entrada: pdfs (todas juntas) · .pdf · necesita: pymupdf.

### `leer_comprobante` — Leer comprobante

Saca RUC, serie y número, fecha y total de boletas y facturas (si es una foto o un escaneo, pase antes por OCR).

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: pymupdf.

### `detectar_ocr` — ¿Necesita OCR?

Dice, página por página, si el PDF tiene texto o es solo imagen.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: pymupdf.

### `info` — Información del PDF

Páginas, tamaño del papel, versión, cifrado, firmas, PDF/A, texto y metadatos.

Entrada: pdf (cada archivo por su lado) · .pdf · necesita: nada aparte.

### `inventario_paginas` — Inventario de páginas

Cuenta las páginas de muchos PDF (archivos, carpetas o una fuente como «blogs del hub») y lo deja en un Excel con subtotales por grupo.

Entrada: archivos (todas juntas) · necesita: openpyxl.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--fuente` | Fuente | opcion: archivos · hub | `archivos` |
| `--solo-index` | Solo los index.pdf (como page-counter: un PDF por publicación) | casilla | `False` |
| `--blogs` | Blogs (vacío = todos) (solo con la fuente «hub») | texto |  |
| `--nombre` | Nombre del Excel | texto |  |

## Medios

### `convertir_imagen` — Convertir imagen

JPG, PNG, WebP, AVIF, HEIC, TIFF, BMP, GIF o PDF; también desde SVG.

Entrada: medios (cada archivo por su lado) · .jpg .jpeg .png .webp .heic .heif .avif .tif .tiff .bmp .gif .svg · necesita: PIL.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--formato` | A | opcion: jpg · png · webp · avif · heic · tiff · bmp · gif · pdf | `jpg` |
| `--calidad` | Calidad | entero | `85` |
| `--metadatos` | Conservar EXIF | casilla | `False` |

### `redimensionar_imagen` — Redimensionar imagen

Cambia el tamaño por ancho, alto o porcentaje, sin deformar.

Entrada: medios (cada archivo por su lado) · .jpg .jpeg .png .webp .heic .heif .avif .tif .tiff .bmp .gif .svg · necesita: PIL.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--ancho` | Ancho máximo (px, 0 = libre) | entero | `1600` |
| `--alto` | Alto máximo (px, 0 = libre) | entero | `0` |
| `--porcentaje` | O porcentaje (0 = no) | entero | `0` |
| `--formato` | Formato (vacío = el mismo) | texto |  |
| `--calidad` | Calidad | entero | `85` |

### `recortar_imagen` — Recortar imagen

Recorta un rectángulo o a una proporción (1:1, 4:5, 9:16, 16:9…), centrado.

Entrada: medios (cada archivo por su lado) · .jpg .jpeg .png .webp .heic .heif .avif .tif .tiff .bmp .gif .svg · necesita: PIL.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--proporcion` | Proporción | opcion: 1:1 · 4:5 · 9:16 · 16:9 · 3:2 · 2:3 · 4:3 · libre | `1:1` |
| `--caja` | Rectángulo (x,y,ancho,alto; con «libre») | texto |  |
| `--calidad` | Calidad | entero | `90` |

### `comprimir_imagen` — Comprimir imagen

Baja el peso: con pérdida (calidad) o sin ella (PNG optimizado).

Entrada: medios (cada archivo por su lado) · .jpg .jpeg .png .webp .heic .heif .avif .tif .tiff .bmp .gif .svg · necesita: PIL.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--modo` | Modo | opcion: con_perdida · sin_perdida | `con_perdida` |
| `--calidad` | Calidad | entero | `75` |
| `--ancho` | Ancho máximo (px, 0 = igual) | entero | `0` |

### `convertir_audio` — Convertir audio

MP3, M4A, FLAC, Opus, OGG o WAV.

Entrada: medios (cada archivo por su lado) · .mp3 .m4a .aac .flac .opus .ogg .wav .mp4 .mov .mkv .webm .avi .m4v .gif · necesita: ffmpeg, ffprobe.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--formato` | A | opcion: mp3 · m4a · flac · opus · ogg · wav | `mp3` |

### `convertir_video` — Convertir video

MP4, MOV, MKV, WebM o GIF (o solo su audio en MP3/M4A).

Entrada: medios (cada archivo por su lado) · .mp4 .mov .mkv .webm .avi .m4v .gif · necesita: ffmpeg, ffprobe.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--formato` | A | opcion: mp4 · mov · mkv · webm · gif · mp3 · m4a | `mp4` |
| `--ancho` | Ancho máximo (px, 0 = igual) | entero | `0` |

### `recortar_medio` — Recortar audio o video

Deja solo el tramo entre dos tiempos (sin recodificar si se puede).

Entrada: medios (cada archivo por su lado) · .mp3 .m4a .aac .flac .opus .ogg .wav .mp4 .mov .mkv .webm .avi .m4v .gif · necesita: ffmpeg, ffprobe.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--desde` | Desde (s o mm:ss) | texto | `0` |
| `--hasta` | Hasta (vacío = el final) | texto |  |
| `--exacto` | Corte exacto (recodifica) | casilla | `False` |

### `comprimir_video` — Comprimir video

Baja el peso (H.264) a una calidad o hasta un tamaño, para enviarlo por chat o subirlo.

Entrada: medios (cada archivo por su lado) · .mp4 .mov .mkv .webm .avi .m4v .gif · necesita: ffmpeg, ffprobe.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--calidad` | Calidad (CRF: 18 alta · 28 baja) | entero | `26` |
| `--hasta` | O que pese menos de (MB, 0 = sin tope) | tamano | `0` |
| `--ancho` | Ancho máximo (px, 0 = igual) | entero | `1280` |

### `convertir_subtitulos` — Convertir subtítulos

SRT ↔ VTT.

Entrada: medios (cada archivo por su lado) · .srt .vtt · necesita: nada aparte.

## Archivos

### `comprimir_archivos` — Comprimir en un archivo

ZIP, TAR.GZ o 7Z con lo elegido (archivos y carpetas).

Entrada: archivos (todas juntas) · necesita: nada aparte.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--formato` | Formato | opcion: zip · tar.gz · 7z | `zip` |
| `--nombre` | Nombre | texto | `archivo` |
| `--clave` | Contraseña (zip y 7z; vacío = sin) | clave |  |

### `extraer_archivo` — Extraer archivo comprimido

ZIP, TAR, TAR.GZ, 7Z o RAR a una carpeta.

Entrada: archivos (cada archivo por su lado) · .zip .tar .gz .tgz .7z .rar .xz .bz2 · necesita: nada aparte.

| opción | qué es | tipo | por omisión |
|---|---|---|---|
| `--clave` | Contraseña (si la tiene) | clave |  |

### `quitar_metadatos_archivo` — Quitar metadatos (cualquier archivo)

Borra EXIF, GPS, autor y programa de fotos, videos y documentos antes de compartirlos.

Entrada: archivos (cada archivo por su lado) · necesita: exiftool.
