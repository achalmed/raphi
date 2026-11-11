---
tipo: changelog
estado: activo
---
# CHANGELOG — raphi (antes DocFlow Studio; repo `achalmed/raphi`, antes `scripts_for_libreoffice`)

Versiones de las herramientas del repo, cada una con su número, según
[Keep a Changelog 1.1.0](https://keepachangelog.com/es-ES/1.1.0/) y [SemVer 2.0.0](https://semver.org/lang/es/).
La versión vigente se declara en el código: `version` de `pyproject.toml` (Raphi: motor, CLI, API, web y
escritorio) y `DOCFLOW_VERSION` (`backends/docflow/lib/core/constants.sh`). pdf-suite y page-counter se
retiraron el 2026-10-27; su historia queda abajo. Sin etiquetas de versión: por qué se lleva igualmente, en
`docs/decisiones.md`.

<!-- Mantén «Sin publicar» arriba en cada herramienta; al subir su versión en el código, sus entradas pasan a la versión nueva con fecha ISO. -->

## Raphi (motor, CLI y recetas)

### Sin publicar

#### Añadido (2026-11-11, la rueda de soltar)

- **`fondo_imagen` («Poner fondo»)**: la imagen sobre un fondo de color o degradado diagonal, con margen, esquinas
  redondeadas, sombra y la proporción del lienzo (1:1, 4:5, 9:16, 16:9, 4:3, 3:2); los tamaños son porcentajes del lado
  menor, así que el mismo ajuste sirve para una captura y para una foto grande. Está en el menú de formatos de toda imagen.
- **`motor.medios.opciones_para(rutas)`**: lo que se ofrece para varios archivos juntos (lo común de `formatos_de`
  más unir y comparar PDF), con `junta` en cada opción (una salida con todos o una por archivo).
- **La pista de edición `vista` de un parámetro** (`Parametro(..., vista="caja")`, `base.VISTAS`): la interfaz que la
  conoce pone un editor a la vista (la rueda, el rectángulo de recorte sobre la imagen); las demás, el control de su tipo.

#### Añadido (2026-11-11, la rueda ampliada: KDE-Services, Metadata Cleaner y Video Downloader dentro del motor)

- **Archivos** (`raphi/motor/archivos.py`): `ver_metadatos` (todo lo que exiftool lee, por grupo, con «lo que te
  delata» aparte y lo que mat2 quitaría), `suma_verificacion` (MD5, SHA-1, SHA-256, SHA-512 o todas, y el `.sha256` al
  lado), `verificar_suma` (archivos de sha256sum o del estilo BSD) y `verificar_comprimido` (`7z t`).
- **Audio y vídeo** (`raphi/motor/multimedia.py`): `info_medio` (ffprobe: contenedor, duración, pistas, etiquetas),
  `extraer_subtitulos`, `incrustar_subtitulos` (como pista o quemados), `normalizar_audio` (loudnorm: podcast,
  plataformas, EBU R128), `rotar_video` (90°, 180°, 270°, espejo), `unir_medios` (sin recodificar si se puede),
  `portada_audio` (carátula de MP3, M4A o FLAC) y `dividir_medio` (partes de N minutos).
- **Imágenes**: `foto_documento` (pasaporte o visa 35×45 mm, visa de EE. UU. 2×2 pulgadas, carnés, a 300 ppp), ICO con
  todos sus tamaños en `convertir_imagen`, y medidas listas en `redimensionar_imagen` (iconos, VGA a 8K, Instagram,
  historias, enlaces).
- **`descargar`**: avance real de yt-dlp (porcentaje, velocidad, lo que falta, elemento n de N), cookies del navegador
  para lo privado o con sesión, solo el vídeo o la lista entera, qué elementos de la lista, subtítulos automáticos,
  carátula y SponsorBlock; `opciones_para_enlaces` (lo que la rueda ofrece para un enlace) y `utiles.correr_en_vivo`.
- **Valores actuales** (`Operacion.actuales`, `base.actuales`, `corredor.py actuales`): lo que un archivo ya tiene en
  los parámetros de una operación; «Editar metadatos» llega con el título y el autor del PDF.
- `formatos_de` y `opciones_para` ofrecen todo lo anterior (transcribir a SRT o TXT desde el audio y el vídeo; vídeo +
  SRT para incrustar; audios + una imagen para la carátula; varios audios o vídeos para unir).

#### Cambiado (2026-11-11)

- `quitar_metadatos_archivo`: con mat2 si está (más a fondo que exiftool; `--lightweight` a pedido), sobre una copia,
  y comprueba después cuántos campos quedan (antes y después, y cuáles). Los PDF siguen sin rasterizarse.
- `recortar_imagen`: el rectángulo (`caja`) manda sobre la proporción si se da (antes solo contaba con «libre»).
- `formatos_de`: las herramientas de un PDF en el orden de uso (comprimir, OCR, tachar, nota, marca de agua…) y con
  nota, marca de agua, metadatos y resaltar; las de una imagen, con «Poner fondo».

- **Nada de nubes de pastillas** (web, 2026-11-08, Edison; `../qillqa/docs/decisiones.md` §Nada de nubes de pastillas): las recetas de Herramientas son una lista con su descripción (`ListaCatalogo` de Tiqsi web).

#### Corregido (auditoría de las 62 operaciones, 2026-11-08)

- La CLI con Python 3.14: `raphi comprimir …`, `raphi ayuda comprimir` y `raphi accion comprimir` (los menús de
  Dolphin) reventaban por el «%» de «Ganancia mínima (%)» en la ayuda de argparse; la ayuda escapa el «%».
- `numerar` simulado reventaba («document closed»); `numerar`, `sello` y `nota` con una página que no existe
  decían «document closed» en vez de «El documento tiene N páginas».
- `tachar` no encontraba un celular escrito con espacios («987 654 321») ni un dato pegado a una coma: los patrones
  se buscan sobre el texto corrido de la página y cada hallazgo se localiza con `search_for`.
- `quitar_metadatos_archivo` fallaba con docx, xlsx, pptx, odt, ods y odp («exiftool: Can't write DOCX files»): se
  reescribe el ZIP con las propiedades vacías y sin la miniatura; un PDF va por `quitar_metadatos` (exiftool deja lo
  viejo recuperable dentro del PDF).
- `auditar_fechas_fotos` decía «solo lee» pero el backend dejaba `date_audit.csv` dentro de la carpeta auditada y
  la operación no mostraba nada (el backend escribe en stderr): el CSV sale como salida junto a la carpeta (o al
  destino) y el resumen se ve; `ordenar_fotos_por_fecha` muestra los renombrados.
- `reparar` y `pdfa` dejaban un PDF a medias cuando Ghostscript fallaba; ya no.
- `descifrar` simulado decía que descifraría aunque la clave fuera otra; comprueba la clave también al simular.
  `miniatura` simulada con una página inexistente ya avisa. `info` de un PDF cifrado decía «None páginas · PDF ?».
  `comparar_compresion` mostraba la ganancia con «+».
- Web: «Seguir con…» dejaba en la herramienta nueva los paneles de trabajos de la anterior.
- README: son 62 operaciones, no 48; `web/dist` reconstruido (estaba desfasado del 31 de octubre).

#### Añadido

- 2026-10-31: `descargar` (yt-dlp), `transcribir` (Whisper local), `ajustar_subtitulos`, `auditar_fechas_fotos` y
  `ordenar_fotos_por_fecha`, sobre los backends de medios llegados de scripts-linux con su historia.
- 2026-10-31: `convertir_audio` con `tasa` fija y las etiquetas del original; la CLI acepta carpetas (`-r`).

- El motor `raphi/motor/`: 48 operaciones en un solo registro (organizar, optimizar, convertir, editar, seguridad,
  información, medios y archivos), con simular, verificar la salida y el error por archivo en el núcleo.
- Lo nuevo frente a pdf-suite y docflow: comprimir hasta un tamaño, componer páginas de varios PDF, foliar
  expedientes (correlativo o de atrás hacia adelante), sello de recepción, ver firmas digitales, ¿necesita OCR?,
  PDF a HTML y a Word, imágenes (también HEIC) a PDF, conversión de imágenes, audio, video y subtítulos, archivos
  comprimidos y quitar metadatos de cualquier archivo; el menú «a qué se puede convertir» (`raphi formatos`).
- «Inventario de páginas» con el Excel de page-counter y la fuente «blogs del hub» (solo en el espacio de trabajo).
- Recetas (`raphi recetas`, `raphi receta`): cuatro de serie y las del usuario en `~/.config/raphi/recetas/`.
- La CLI `raphi <operación>` (`-n`, `-o`, `--json`; salida 0 · 1 · 2 · 130) y `raphi doctor`.
- 37 pruebas con un corpus generado en cada corrida y la prueba de fronteras del motor.
- La API `/api/raphi` (operaciones, formatos, archivos con miniaturas, trabajos, recetas), la cola de trabajos con
  avance, cancelación, reanudación y purga, la base propia (SQLite o PostgreSQL) y el módulo de Tiqsi (`MANIFIESTO`,
  «pdf.v1», «conversion.v1»); los modos `sola` y `escritorio` (servidor local con ficha de un solo uso).
- Lo avanzado (R7, `raphi/motor/pdf_avanzado.py`): tachar de verdad (términos, DNI, RUC, correos, celulares; se
  comprueba que no quede nada legible), resaltar, notas, estampar una firma o un sello en imagen, rellenar y listar
  formularios, aplanar, comparar dos PDF con un informe HTML, verificar firmas digitales con pyHanko (integridad,
  firmante, fecha y la cadena si hay raíces en `RAPHI_RAICES`), tablas a Excel y leer comprobantes (RUC, serie,
  número, fecha, total).
- La web (`web/`, `@qillqa/raphi`): Herramientas con buscador y «soltar y convertir», cada herramienta con su formulario
  generado de la ficha, simular y aplicar, «Seguir con…» para encadenar; la Mesa de trabajo (miniaturas de varios PDF,
  ordenar, girar, duplicar, página en blanco, deshacer); Trabajos, Recetas (con su editor) y Sistema.
- La pieza «raphi.Acciones» (`@qillqa/raphi/publico`): «Raphi ▸» junto a un archivo de otro módulo, con sus
  sugeridas, «Convertir a», las herramientas y «Guardar aquí» de vuelta por la API de ese módulo.
- Herramientas con otra cara: cada herramienta con su ícono y el tono de su categoría, qué acepta («PDF», «Dos o
  más PDF», «JPG, PNG y 5 más») y **soltarle un archivo encima la abre con él**; categorías con su resumen, filtros con
  su color (en el celular, una fila que se desliza), la zona para soltar en franja y las recetas con su título. El
  mismo ícono en la cabecera de cada herramienta y en Trabajos (`web/src/lib/identidad.ts`, `componentes/Icono.tsx`).
  En el tema oscuro, cada tono sube de luz para que su ícono se lea (`tonoDe`).
- Sistema muestra docflow: su versión, dónde está su configuración y su caché, que un administrador compacta o vacía
  (`POST /api/raphi/sistema/docflow/cache`); antes solo con `docflow cache` en la terminal.

## Raphi escritorio (GUI; antes DocFlow Studio)

### Sin publicar

#### Añadido (2026-11-11)

- **La rueda de soltar** (decisión R13; **desde el 2026-11-11 es Muyu**, repo `muyu`: lo de abajo vive allí y aquí queda el corredor como su API): un círculo que aparece bajo el puntero
  con lo soltado en el centro, el anillo interior «Convertir a» (los destinos de `formatos_de`, los más pedidos
  primero) y el exterior «Herramientas»; «Más» abre el resto en el mismo anillo (también pasando encima con un
  arrastre). Clic o soltar encima corre; clic derecho, o una herramienta que pide algo (un texto, una clave, un color),
  abre el panel de opciones generado de la ficha con la **vista previa en vivo** (la operación de verdad sobre una
  copia reducida en la caché: imágenes, y PDF en Editar, Seguridad y Organizar) o, con la pista `caja`, el **editor
  del recorte** sobre la imagen. El resultado queda en el centro: **se arrastra fuera** (a Dolphin, al escritorio, a
  otra aplicación) o **sigue** con los anillos ya rehechos para su tipo; Deshacer lo manda a la papelera y Volver
  regresa al archivo anterior. Varios archivos a la vez (lo común a todos, y lo que los junta). Teclado completo.
  Aparece desde el menú «Raphi ▸ Rueda de Raphi…» de **Dolphin y Krusader** (Krusader lee los menús de servicio de KDE),
  con el **atajo global Meta+Ctrl+R** en medio de un arrastre o, `--residente`, con una franja en el borde de la
  pantalla que la abre al llegar un arrastre. En Wayland es una capa de superposición de layer-shell (org.kde.layershell);
  sin él, una ventana sin marco a pantalla completa. Instancia única: las llamadas siguientes le pasan los archivos.
  `raphi rueda --instalar [--residente] [-n]` pone el acceso, el atajo y el inicio con la sesión (simula con `-n`).
- El corredor del motor (`escritorio/studio/corredor.py`) responde `rueda <archivos o enlaces…>`, `vista <trabajo.json>`
  (deja la salida misma: un PDF entero, una imagen, un texto) y `actuales <operación> <archivo>`.
- 2026-11-11, tras probarla en la sesión: la **vista previa** de un PDF es el visor de gui-comun (desplazar, zoom,
  miniaturas, seleccionar y copiar texto, buscar), una imagen se amplía y se arrastra, un texto se lee; «Ver el
  original» compara; si a la operación le falta algo, se ve el original con un aviso (no un recuadro vacío en rojo).
  El panel de opciones tiene tamaño acotado, los botones siempre a la vista, las opciones con desplazamiento y
  **Ampliar** (F11): casi toda la pantalla, con la vista a la izquierda. El **cerrar** de los paneles es el de las
  ventanas de la sesión: un punto rojo en el lado que dice la decoración de KWin (`ButtonsOnLeft`).
- **Enlaces**: soltados desde el navegador o pegados con Ctrl+V, abren la rueda de descargas (Mejor, 4K, 1080p, 720p,
  480p, MP3, M4A, Opus, FLAC; con subtítulos, sin patrocinios, solo este vídeo, un tramo, con tu sesión, todas las
  opciones), con el avance real; el resultado sigue en la rueda (transcribirlo, convertirlo, recortarlo).
- **Informes**: lo que dice una herramienta de información (metadatos, información de un PDF o un vídeo, sumas) se ve
  en un panel con buscador y «Copiar todo».
- **Okular**: la rueda vacía ofrece lo que Okular está mostrando; lo que trabaja en una página (sello, nota) llega con
  la página que se está leyendo; un PDF se abre en Okular con un botón. **LibreOffice**: la macro «Rueda de Raphi»
  (`raphi rueda --instalar`) manda el documento abierto a la rueda. **Correo** (xdg-email) y **copiar el archivo** al
  portapapeles, desde la tarjeta del resultado.
- Iconos propios para las herramientas más usadas en `familias.py` (también en el catálogo de Raphi Studio).

#### Cambiado

- 2026-11-02: **reingeniería** (`docs/reingenieria.md`, decisión R12): Raphi Studio deja la distribución de Dolphin por
  un estudio multimedia sobre `VentanaBase` de `gui-comun` 3.0 — catálogo de herramientas en cuadrícula por áreas
  (Documentos y PDF, Imágenes, Audio, Vídeo, Transcripción, Conversión, Procesamiento por lotes, Automatización y
  recetas) con búsqueda sin tildes y disponibilidad real; espacio de trabajo por herramienta con entradas, vista previa
  (imagen, PDF, audio y vídeo con QtMultimedia, texto) y opciones de la ficha; la cola como vista propia con repetir;
  Procesar con la confirmación de la base; el diálogo de archivos de KDE; abrir y mostrar en Dolphin de la base.
- 2026-11-02: Raphi Studio pasa a QML + Kirigami sobre `gui-comun` 2.7 (`docs/rediseno.md`): espacio de trabajo con la
  tabla de herramientas por familia o la de trabajos por estado, los archivos de entrada en una sola lista, las
  opciones generadas de la ficha con `PaginaFormulario`, el resultado con vista previa y el registro; F5 simula y
  Ctrl+Intro aplica tras confirmar; la ventana corre con el Python del sistema y el motor como proceso con el `.venv`
  (`escritorio/studio/corredor.py`); `escritorio/__main__.py` relanza al Python del sistema; pruebas `tests/run.sh`.
  Se retira la ventana de Widgets (`app.py`, `ventana.py`, `paginas.py`, `herramienta.py`, `formulario.py`,
  `motor_local.py`). Fuera: la bandeja del sistema (sigue en la ventana web).

#### Añadido

- 2026-10-31: **Raphi Studio** (`escritorio/studio/`), el escritorio nativo de la familia de los studios: barra lateral
  por familias, páginas armadas de las fichas del motor, paleta Ctrl+K, avisos, soltar archivos, carpetas vigiladas y
  menús de Dolphin. `raphi` lo abre; la ventana web, con `raphi --web` (decisiones R9).

#### Cambiado

- **La ventana es nueva** (`escritorio/`, R4): PySide6 con QtWebEngine que muestra la web de Raphi, servida en
  127.0.0.1 con una ficha de un solo uso; puente nativo (archivos del disco por su ruta, «Mostrar» en la carpeta,
  guardar donde se elija, carpetas vigiladas, menús de Dolphin), lo soltado desde Dolphin llega como ruta, bandeja
  del sistema con su zona para soltar y una sola instancia. `raphi` sin argumentos la abre; con argumentos es la CLI.
- `install.sh` crea el entorno con el Python del sistema (el de conda carga una libbrotli que rompe QtWebEngine) y
  rehace un `.venv` de conda.

#### Retirado

- `studio/`, la GUI nativa con sus seis páginas: las cubre la web (etiqueta `antes-retirar-studio-2026-10-27`).

#### Añadido

- `raphi accion <operación>`: la usan los menús de Dolphin; escribe junto al original y avisa al terminar.
- Soltar con teclas: **Shift** abre la Mesa de trabajo con los archivos y **Alt**, Herramientas con su menú «a qué se
  puede convertir»; sin tecla los toma la pantalla abierta y, si no tiene zona para soltar (Trabajos, Recetas,
  Sistema), se abren Herramientas en vez de perderlos. Herramientas acepta `?archivos=`.
- Soltar sobre una herramienta también en la ventana: la tarjeta bajo el puntero se resalta mientras se arrastra y, al
  soltar, abre esa herramienta con los archivos que acepta (o avisa que no los acepta).


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
- Markdown y LaTeX → PDF con **LuaLaTeX**, el motor del ecosistema (antes XeLaTeX); `doctor` y el instalador
  piden `texlive-luatex` (2026-10-27).

#### Corregido

- El CI (ShellCheck y Bats en Ubuntu y Arch) vuelve a dispararse: sus rutas apuntaban a una carpeta que
  ya no existía (2026-09-20).
- `index` informaba «índice generado» y salía con 0 aunque el script de Python fallara; ahora sale con 1.
- El CI pasa de nuevo: ShellCheck ya no avisa de las variables que comparten los archivos de `lib/` (se
  declara en cada uno por qué), la prueba de `to-md` busca `titulo:` y no `title:`, y en Arch el paquete se
  llama `bats` (2026-10-27).

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

### Retirado - 2026-10-27

- La herramienta se retira (R8 de Raphi): todo lo que hacía está en el motor de Raphi (`raphi lista`); etiqueta
  `antes-retirar-backends-2026-10-27`.

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

### Retirado - 2026-10-27

- La herramienta se retira (R8 de Raphi): todo lo que hacía está en el motor de Raphi (`raphi lista`); etiqueta
  `antes-retirar-backends-2026-10-27`.

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
