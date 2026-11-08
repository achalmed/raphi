---
tipo: estado
estado: activo
actualizado: 2026-11-08
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
| 2026-11-08 | **Auditoría de las 62 operaciones en las tres caras**: cada una simulada y aplicada sobre un corpus de 34 archivos (318 corridas), la CLI con sus órdenes y errores de uso, la web en el navegador contra `raphi.sola` (subir, simular, aplicar, descargar, «Seguir con…», mesa de trabajo, recetas, sistema) y Raphi Studio sin pantalla sobre la muestra (catálogo, foliar aplicada, la cola con audio). Corregidos: la CLI con Python 3.14 (`%` en la ayuda), `numerar` simulado y los mensajes de página inexistente, `tachar` con celulares con espacios, `quitar_metadatos_archivo` con documentos de oficina y PDF, `auditar_fechas_fotos` que escribía en la carpeta, Ghostscript que dejaba PDF a medias, «Seguir con…» en la web, `web/dist` desfasado, README con 48 operaciones | `CHANGELOG.md` §Sin publicar, las pruebas nuevas en `tests/` |
| 2026-11-03 | **gui-comun 3.2 adoptado**: la vista previa de PDF es `VistaPdf` de la base sobre `gui_comun.visor_pdf.VisorPdf` (QtPdf o `pdftoppm`, zoom, miniaturas, selección, enlaces y búsqueda); retirado el renderizado propio (`controladores/vista.py`, `servicios/vista_previa.py`) | `escritorio/studio/README.md` |
| 2026-11-03 | **Alertas de Dependabot** (87 abiertas, todas de pip): yt-dlp a 2026.10.26 en `backends/whisper-transcriber/requirements.txt` (cierra las cinco; las opciones que pasan los backends existen en esa versión). Las 82 de Pillow piden 13.0.0, un cambio de mayor: anotado abajo con la prueba hecha. npm: `npm audit` sin vulnerabilidades | `docs/decisiones.md`, entrada del 2026-11-03 |
| 2026-11-03 | `install.sh` instala `gui-comun` 3.0.0 (la etiqueta `v3.0.0` ya está en su remoto) cuando el repo de al lado no está; antes, la 1.0.0 | `install.sh` |
| 2026-11-03 | `estado.md` adoptado (RQ-DOC-02): los pendientes salen de `docs/decisiones.md` §Pendientes | este archivo |
| 2026-11-02 | Reingeniería de Raphi Studio (R1–R12) fusionada en `main` en local por el director | `docs/reingenieria.md` |

## En curso

nada en curso

## Por hacer

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
- 2026-11-08 · dueño: **el autor** · lo que la auditoría no pudo probar sin red ni horas: `descargar` de verdad (yt-dlp
  contra un enlace real) y `transcribir` con Whisper (solo simuladas; el backend de Whisper sí corre en las pruebas
  de `ajustar_subtitulos`). Probarlas una vez a mano desde Raphi Studio.
- 2026-11-08 · dueño: director · la simulación de `reparar`, `info` y `leer_comprobante` no abre el archivo: con un
  PDF roto o sin texto dice que lo haría; decidir si vale abrirlo al simular (como ya hacen `descifrar` y `miniatura`).
- 2026-11-08 · dueño: director · el validador avisa de `CHANGELOG.md` fuera de Keep a Changelog (sin `## [Unreleased]`,
  títulos por herramienta) y de `docs/*.md` sin `genero:`: es la forma elegida del repo (decisiones); revisar si se
  alinea con RQ-DOC-09 y RQ-DOC-10 o se documenta la excepción.

## Futuro

- Pillow 13 con Qillqa (arriba) y, después, revisar las alertas de Dependabot en cada envío.
