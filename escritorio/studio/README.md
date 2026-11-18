---
tipo: readme
estado: activo
---
# escritorio/studio/ — Raphi Studio, el estudio multimedia (QML + Kirigami sobre gui-comun 3.0)

## Qué es

Un estudio de documentos, PDF, imágenes, audio y vídeo, no un explorador de archivos (`../../docs/reingenieria.md`,
decisión R12). Desde el 2026-11-18 tiene la forma de un **taller** (decisión R14, el rediseño visual aprobado): arriba,
la barra del estudio (volver, buscar, las áreas, Simular, Procesar, la cola) y, debajo, la **zona para soltar**
archivos y carpetas con lo que ya entró (miniatura o icono, tipo, tamaño, quitar; añadir, «Solo las que sirven» y
vaciar); en el centro, una de tres vistas; a la derecha, salvo en la Cola, la **cola** entera con su barra de avance
(indeterminada si el motor no dice cuánto lleva), Detener y el estado de cada trabajo en color de estado.

| vista | qué se ve |
|---|---|
| **Catálogo** (Ctrl+1) | la paleta de herramientas: las herramientas del motor y las recetas agrupadas por familia, en el orden del taller: PDF, Imágenes, Audio y video, Documentos, Archivos y Recetas; cada una con su icono, qué hace, los formatos que acepta y si está lista en esta máquina (o qué le falta). Filtran las áreas de la barra (Documentos y PDF, Imágenes, Audio, Vídeo, Transcripción, Conversión, Procesamiento por lotes, Automatización y recetas), la búsqueda (sin distinguir tildes) y «Solo las que sirven»; con entradas, lo que no sirve para ellas queda tenue |
| **Herramienta** (Ctrl+2) | su espacio de trabajo, al estilo de HandBrake: el **monitor** con la vista previa de la entrada elegida arriba o del resultado (imagen; PDF con el visor de gui-comun; audio y vídeo con QtMultimedia; texto), las **opciones** generadas de su ficha (`PaginaFormulario`) y dónde dejar la salida; el avance, en la cola de la derecha |
| **Cola** (Ctrl+3) | los trabajos por sección (en curso con su barra, en cola, hechos, con error), filtrables; el elegido con sus entradas, opciones y salida, el resultado (el plan si fue simulado), las salidas con vista previa y el registro del motor; Detener, Quitar, **Repetir** e Ir a su herramienta |

**Color y avisos.** Todo color sale del esquema activo de KDE (`Kirigami.Theme`; hoy Lliphi Claro u Oscuro) y cambia
con la ventana abierta; el violeta de Raphi es solo marca (lanzador y «Acerca de»). Un aviso sin decisión («Rotar
páginas: 2 correctos», «Menús de Dolphin instalados») va a las notificaciones de KDE, también con la ventana sin foco;
en la ventana queda solo lo que es estado de la herramienta (lo que le falta).

**F5 simula y Ctrl+Intro procesa.** Simular es el `simular=True` del motor como trabajo en la cola: su plan dice qué
se producirá y dónde. Procesar es una «escritura» de `gui-comun` 3.0: su confirmación dice la herramienta, las
entradas, las opciones y la salida; el trabajo va a la cola de verdad, uno a la vez, con su progreso en la barra de
estado y Esc para detenerlo. El original nunca se toca; ninguna pantalla se escribe a mano por herramienta (el studio
no nombra operaciones salvo en `familias.py`, que también calcula las áreas de cada ficha).

Atajos: Ctrl+Intro procesar · F5 simular · Esc detener · Ctrl+F buscar · Ctrl+O añadir archivos · Ctrl+Mayús+O añadir
una carpeta · Ctrl+1/2/3 catálogo, herramienta, cola · Alt+← volver al catálogo · Ctrl+0 todas las áreas · F6 releer
las fichas · F4 la salida del motor · Ctrl+K la paleta.

## Cómo corre

La ventana corre con el **Python del sistema** (`/usr/bin/python3`: su PySide6 y su Kirigami); el motor corre como
**proceso con el `.venv` del repo** (`corredor.py`: pikepdf, PyMuPDF, Pillow…), que `install.sh` crea. `raphi`
(run.sh) y `python -m escritorio` arrancan en el `.venv` y relanzan al Python del sistema diciéndole dónde está el
motor (`RAPHI_MOTOR_PYTHON`) y dónde está `gui_comun` (`GUI_COMUN_DIR`, o instalado). Sin PySide6 con QML en el
sistema, `raphi` abre la ventana web de siempre (`raphi --web`).

```bash
cd ~/Documents/raphi
raphi                                      # Raphi Studio (o, si ya está abierto, le manda los archivos)
raphi escritorio a.pdf b.pdf               # con archivos; raphi --web, la ventana web
/usr/bin/python3 -m escritorio.studio --smoke       # con PYTHONPATH=. y GUI_COMUN_DIR: construye la interfaz y sale
tests/run.sh                               # las pruebas del studio sobre los archivos de muestra
/usr/bin/python3 escritorio/studio/capturar.py salida.png --esquema ~/Documents/lliphi/generado/esquema/LliphiOscuro.colors --vista herramienta --herramienta rotar --aplicar
```

## Estructura

```
escritorio/studio/
├── __main__.py             sin lógica: arranca aplicacion.main
├── aplicacion.py           construir(): controladores y Acciones (menú, paleta, atajos, estados de operación); instancia única; Main.qml
├── corredor.py             el motor como proceso (con el .venv): fichas · doctor · ejecutar <trabajo.json>
├── familias.py             familia y áreas de cada operación, leídas de su ficha (el único archivo que nombra operaciones)
├── servicios/              sin Qt: rutas, fichas (caché), archivos, trabajos (cola persistida), operaciones, vista_previa (qué se muestra)
├── controladores/          espacio (vistas, áreas, búsqueda), archivos, herramientas (catálogo), trabajos (cola, repetir), operaciones, vista, ajustes
├── qml/                    Main.qml sobre GuiComun.VentanaBase y componentes/ (BarraEstudio, ZonaSoltar, PaginaCatalogo (la
│                           paleta), EspacioHerramienta, VistaPrevia, ReproductorMedios, Opciones, PanelCola, PaginaCola, diálogos)
└── muestra.py · capturar.py   los archivos de muestra (PDF, PNG, SRT, Markdown, WAV) y las capturas sobre ellos
```

Las fichas en caché, los trabajos y el plan de cada orden viven en la caché del studio (`$XDG_CACHE_HOME/raphi/`);
las opciones por herramienta y las carpetas vigiladas, en la configuración (`QSettings`); nada entra en el repo.

## Límite honesto

- **La vista previa de audio y vídeo** usa el módulo QML `QtMultimedia` del sistema (con su plugin de ffmpeg); si
  faltara, la vista previa lo dice y el archivo se abre con su aplicación. **La de PDF** es `VistaPdf` de `gui-comun` 3.2: con
  `QtQuick.Pdf`, páginas de Qt con selección de texto, enlaces y búsqueda; sin él, imágenes de `pdftoppm`.
- **La Mesa de trabajo sigue solo en la web**; **la bandeja del sistema** con su zona para soltar la conserva la
  ventana web (`QSystemTrayIcon` es de QtWidgets).
- **Las recetas no se editan aquí**: son YAML en `~/.config/raphi/recetas/`.
- **El progreso lo da el motor** (`ctx.avisar`): una operación que no avisa muestra solo «en curso» hasta terminar.
