---
tipo: estado
estado: activo
actualizado: 2026-11-19
---
# estado.md — raphi (repo `achalmed/raphi`, antes DocFlow Studio)

Lo primero que se lee y lo último que se escribe en cada sesión (regla 10 de la guía raíz). Lo decidido vive en
`docs/decisiones.md`; lo pendiente, aquí, en §Por hacer, con fecha y dueño. Hasta el 2026-11-02 los pendientes
vivían en `docs/decisiones.md` §Pendientes por una regla propia del repo; desde el 2026-11-03 viven aquí (RQ-DOC-02;
`docs/decisiones.md`, entrada del 2026-11-03).

**Repositorio público** (AGPL-3.0): nada del despacho ni de nadie; `python3 scripts/escanear.py` antes de cada envío.

## Hecho

| fecha | qué | dónde se ve |
|---|---|---|
| 2026-11-19 | **Descarga guiada sin terminal** (web, Qillqa y Raphi Studio): el enlace muestra qué video es y si está en vivo con su ventana; el tramo con barra y horas (en vivo, por la hora y con atajos); calidad y formato según lo que se baje; «Más opciones» plegadas; botón «Descargar»; avance por partes. Genérico en la ficha (`si`, `grupo`, vistas «enlace» y «tramo», `accion`). Probado en el navegador contra `raphi.sola` (el reel de Facebook, tramo 2:00–3:30, 720×1280 y 90 s exactos) y en Raphi Studio por captura (el reel y el Pleno en vivo); la calidad cuenta el lado corto. **Dentro de Qillqa de prueba** (web construida y servida en 5198, API 8010): el Pleno en vivo, tramo @12:21:00–@12:22:00 por la ventana, avance por partes, «1 archivo listo», 1080p y 60 s exactos. La web de Qillqa en modo dev (`npm run dev`) no arranca hoy («createTheme_default is not a function» de Vite con MUI): se prueba construida | `docs/arquitectura.md` §El motor, `tests/test_audio_video_fotos.py` |
| 2026-11-19 | **Tramos de directos**: `descargar` recorta una transmisión en vivo de YouTube (HLS) desde el comienzo, desde el vivo (`-16:30--14:08`) o por la hora (`@11:20-@11:22:35`), bajando solo sus segmentos y renovando la lista ante el 403 de YouTube; el tramo va suelto tras el enlace; títulos de Facebook sin vistas ni reacciones. Probado en vivo con el Pleno del Congreso (3 min 40 s de 1080p en ~4 min) y con un reel de Facebook | `backends/video-downloader/README.md`, `tests/test_backends_medios.py` |
| 2026-11-18 | **Raphi Studio, un taller** (rediseño visual aprobado, R14): arriba la zona para soltar con lo que entró, la paleta de herramientas por familia (PDF, imágenes, audio y video, documentos…) y a la derecha la cola con su barra de avance; cero colores propios; los avisos, a las notificaciones de KDE; el cambio de claro a oscuro en vivo probado aislado. Sobre la muestra: `tests/run.sh` 35 pasan | `docs/decisiones.md` R14, `escritorio/studio/README.md`, `docs/figuras/raphi-studio-*.png` |
| 2026-11-11 | **Probado con uso real** (desde Muyu): `descargar` de YouTube a MP3 con el avance real de yt-dlp, `transcribir` lo bajado con Whisper (SRT y su versión de líneas cortas), `quitar_metadatos_archivo` con mat2 sobre una foto con GPS, autor y número de serie (quedan solo los campos del formato) | `tests/test_archivos_multimedia.py` |
| 2026-11-11 | **La rueda ampliada**, tras probarla el autor en la sesión: vista previa de PDF con el visor de gui-comun (zoom, desplazar, seleccionar, buscar), imagen ampliable, texto; «Ver el original»; panel acotado con Ampliar (F11) y el cerrar de la decoración de KWin; informes de las herramientas de información; enlaces (descargas con avance real, cookies del navegador, listas, subtítulos, SponsorBlock); Okular (D-Bus), macro de LibreOffice, correo y copiar el archivo. En el motor, 13 operaciones nuevas (metadatos, sumas, comprimidos, información de medios, subtítulos, volumen, rotar, unir, carátula, dividir, foto de documento) e ICO y medidas listas; limpieza con mat2 y su comprobación; valores actuales. Okular probado por D-Bus sin pantalla; la macro de LibreOffice, no dentro de LibreOffice | `raphi/motor/archivos.py`, `raphi/motor/multimedia.py`, `tests/test_archivos_multimedia.py`, `docs/decisiones.md` R13 (adenda) |
| 2026-11-11 | **La rueda de soltar** (R13; ese mismo día se mudó a Muyu, repo `muyu`, su M1): el círculo de formatos (interior) y herramientas (exterior) que sale de `formatos_de`/`opciones_para`, con vista previa en vivo, editor del recorte, encadenar, arrastrar el resultado fuera, deshacer a la papelera y teclado; desde el menú de Dolphin y Krusader, el atajo Meta+Ctrl+R o la franja del borde (`--residente`), con layer-shell en Wayland. En el motor: «Poner fondo» (`fondo_imagen`), `opciones_para`, la pista `vista` de un parámetro y el recorte por rectángulo. Probado sin pantalla y en un KWin anidado (`kwin_wayland --virtual`): no en la sesión real | el repo `muyu`; aquí, `tests/test_rueda.py` y `docs/arquitectura.md` §El corredor como API de Muyu |
| 2026-11-08 | **Auditoría de las 62 operaciones en las tres caras**: cada una simulada y aplicada sobre un corpus de 34 archivos (318 corridas), la CLI con sus órdenes y errores de uso, la web en el navegador contra `raphi.sola` (subir, simular, aplicar, descargar, «Seguir con…», mesa de trabajo, recetas, sistema) y Raphi Studio sin pantalla sobre la muestra (catálogo, foliar aplicada, la cola con audio). Corregidos: la CLI con Python 3.14 (`%` en la ayuda), `numerar` simulado y los mensajes de página inexistente, `tachar` con celulares con espacios, `quitar_metadatos_archivo` con documentos de oficina y PDF, `auditar_fechas_fotos` que escribía en la carpeta, Ghostscript que dejaba PDF a medias, «Seguir con…» en la web, `web/dist` desfasado, README con 48 operaciones | `CHANGELOG.md` §Sin publicar, las pruebas nuevas en `tests/` |
| 2026-11-03 | **gui-comun 3.2 adoptado**: la vista previa de PDF es `VistaPdf` de la base sobre `gui_comun.visor_pdf.VisorPdf` (QtPdf o `pdftoppm`, zoom, miniaturas, selección, enlaces y búsqueda); retirado el renderizado propio (`controladores/vista.py`, `servicios/vista_previa.py`) | `escritorio/studio/README.md` |
| 2026-11-03 | **Alertas de Dependabot** (87 abiertas, todas de pip): yt-dlp a 2026.10.26 en `backends/whisper-transcriber/requirements.txt` (cierra las cinco; las opciones que pasan los backends existen en esa versión). Las 82 de Pillow piden 13.0.0, un cambio de mayor: anotado abajo con la prueba hecha. npm: `npm audit` sin vulnerabilidades | `docs/decisiones.md`, entrada del 2026-11-03 |
| 2026-11-03 | `install.sh` instala `gui-comun` 3.0.0 (la etiqueta `v3.0.0` ya está en su remoto) cuando el repo de al lado no está; antes, la 1.0.0 | `install.sh` |
| 2026-11-03 | `estado.md` adoptado (RQ-DOC-02): los pendientes salen de `docs/decisiones.md` §Pendientes | este archivo |
| 2026-11-02 | Reingeniería de Raphi Studio (R1–R12) fusionada en `main` en local por el director | `docs/reingenieria.md` |

## En curso

nada en curso

## Por hacer

- 2026-11-19 · dueño: director · en una ventana angosta (~420 px) la página de una herramienta mide 860 px de ancho;
  no se halló aún qué lo fuerza (no son los componentes nuevos: ocultarlos no lo cambia). Revisar el `Marco` de Tiqsi y
  la página `Herramienta`.


- 2026-11-18 · dueño: **el autor** · ver el taller en la sesión real: soltar desde Dolphin sobre la zona (se marca con
  el resaltado) y sobre la paleta, la cola de la derecha con un trabajo largo (transcribir: la barra va indeterminada
  hasta que el motor avisa) y el cambio de claro a oscuro con `plasma-apply-colorscheme` (aquí solo se probó aislado).
- 2026-11-18 · dueño: director · la paleta se recorre con Tab y Espacio; la cuadrícula anterior tenía flechas e Intro.
  Si hace falta, un `GridView` por familia con `keyNavigationEnabled`, o un componente común de «paleta por grupos» en
  gui-comun (propuesta; gui-comun no se tocó).
- 2026-11-18 · dueño: director · las secciones de la cola (aquí y en la vista Cola) pueden repetirse («Hechos», «Con
  error», «Hechos») porque los terminados se ordenan por fecha y no por sección; ordenar por sección o quitar los
  encabezados de terminados.
- 2026-11-11 · dueño: director · `PaginaFormulario` de gui-comun avisa en la consola al cambiar de campos
  («Kirigami FormLayout: Cannot read property 'isSection' of null»; lo ven la rueda y, al cambiar de herramienta, Raphi
  Studio): sin efecto visible; llevarlo a gui-comun.
- 2026-11-11 · dueño: director · la web puede adoptar la pista `vista="caja"` (el editor del recorte) y «Poner fondo» con
  vista previa; hoy los muestra con sus controles de siempre.
- 2026-11-03 · dueño: **el autor** · **Pillow 13** (82 alertas de Dependabot, varias críticas y altas, todas con arreglo
  solo en 13.0.0): `requirements.txt` y `backends/photo-metadata/requirements.txt` fijan 12.3.0, la versión de Qillqa
  (Raphi corre en su mismo proceso dentro de la plataforma). Probado el 2026-11-03 sin tocar el `.venv`: la suite del
  motor con Pillow 13.0.0 antepuesto da el mismo resultado que con 12.3.0 (`docs/decisiones.md`, entrada del
  2026-11-03). **Recomendación**: subir Pillow a 13.0.0 a la vez en Qillqa y en Raphi (los dos `requirements.txt` y el
  `.venv`), con las pruebas de los dos.
- 2026-11-03 · dueño: **el autor** · el `yt-dlp` que usa la máquina es el del sistema (`/usr/bin/yt-dlp`, paquete de la
  distribución, 2026.03.17), que también cae bajo esos avisos: actualizarlo (`sudo apt upgrade yt-dlp` o el de pip en el
  `.venv` con `pip install -r backends/whisper-transcriber/requirements.txt`).
- 2026-11-02 · dueño: **el autor** · usar Raphi Studio 3.0 en la sesión real (Lliphi, Wayland): soltar archivos desde
  Dolphin sobre el catálogo y sobre una herramienta, la vista previa de un vídeo propio, procesar y repetir, un trabajo
  largo (transcribir) con su progreso y Esc.
- 2026-11-02 · dueño: director · la prueba `test_servidor_con_ficha` (`tests/test_escritorio.py`) necesita `web/dist`
  construido (`npm run web:construir`): en un worktree recién creado falla hasta construirlo o enlazarlo.
- 2026-11-02 · dueño: director · la bandeja del sistema con su zona para soltar quedó solo en la ventana web
  (QtWidgets); si se quiere en el studio, `org.kde.notification` o un `QSystemTrayIcon` fuera del proceso QML.
- 2026-11-02 · dueño: director · el progreso de un trabajo depende de que la operación llame a `ctx.avisar`; las que
  no lo hacen muestran solo «en curso» hasta terminar.
- 2026-11-08 · dueño: director · la simulación de `reparar`, `info` y `leer_comprobante` no abre el archivo: con un
  PDF roto o sin texto dice que lo haría; decidir si vale abrirlo al simular (como ya hacen `descifrar` y `miniatura`).
- 2026-11-08 · dueño: director · el validador avisa de `CHANGELOG.md` fuera de Keep a Changelog (sin `## [Unreleased]`,
  títulos por herramienta) y de `docs/*.md` sin `genero:`: es la forma elegida del repo (decisiones); revisar si se
  alinea con RQ-DOC-09 y RQ-DOC-10 o se documenta la excepción.

## Futuro

- Pillow 13 con Qillqa (arriba) y, después, revisar las alertas de Dependabot en cada envío.
