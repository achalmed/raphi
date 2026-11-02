---
tipo: readme
estado: activo
---
# escritorio/studio/ — Raphi Studio, la ventana de trabajo (QML + Kirigami sobre gui-comun 2.7)

## Qué es

El escritorio nativo de Raphi, al estilo Dolphin/Kate (`../../docs/rediseno.md`): la tabla de **herramientas** (las
operaciones del motor y las recetas) por familia (Documentos, PDF, Imágenes, Audio y video, Archivos, Recetas) con lo
que les falta en esta máquina, o la tabla de **trabajos** por estado (en cola, en curso, hechos, con error); los
**archivos** que sueltas en la ventana, eliges o mandas desde Dolphin, en una sola lista; la herramienta elegida en el
panel de detalles con su **Resumen** (la ficha), los **Archivos**, sus **Opciones** (el formulario generado de su ficha:
`PaginaFormulario` del marco), su **Resultado** (el plan o las salidas, con vista previa de una imagen o un texto) y su
**Registro**; el panel inferior con la salida del motor; la paleta (Ctrl+K) encuentra cualquier herramienta o trabajo.

**F5 simula y Ctrl+Intro aplica tras confirmar.** Simular es el `simular=True` del motor como trabajo en la cola: su
plan dice qué se producirá y dónde. Aplicar pide confirmación (herramienta, archivos, opciones, salida) y encola el
trabajo de verdad; uno corre a la vez, con su progreso en la barra de estado y Esc para cancelar. El original nunca se
toca; ninguna pantalla se escribe a mano por herramienta (el studio no nombra operaciones salvo en `familias.py`).

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
/usr/bin/python3 escritorio/studio/capturar.py salida.png --esquema ~/Documents/lliphi/generado/esquema/LliphiOscuro.colors --pestana 2
```

## Estructura

```
escritorio/studio/
├── __main__.py             sin lógica: arranca aplicacion.main
├── aplicacion.py           construir(): controladores y Acciones (menú, barra, paleta, atajos); instancia única; Main.qml
├── corredor.py             el motor como proceso (con el .venv): fichas · doctor · ejecutar <trabajo.json>
├── familias.py             cada operación en su familia, leída de su ficha (el único archivo que nombra operaciones)
├── servicios/              sin Qt: rutas, fichas (caché), archivos, trabajos (cola persistida), operaciones
├── controladores/          espacio, archivos, herramientas, trabajos, operaciones, ajustes
├── qml/                    Main.qml sobre GuiComun.VentanaStudio y componentes/ (Resumen, Archivos, Opciones, Resultado, Registro, diálogos)
└── muestra.py · capturar.py   los archivos de muestra (PDF y PNG escritos a mano) y las capturas sobre ellos
```

Las fichas en caché, los trabajos y el plan de cada orden viven en la caché del studio (`$XDG_CACHE_HOME/raphi/`);
las opciones por herramienta y las carpetas vigiladas, en la configuración (`QSettings`); nada entra en el repo.

## Límite honesto

- **La Mesa de trabajo sigue solo en la web**; **la bandeja del sistema** con su zona para soltar la conserva la
  ventana web (`QSystemTrayIcon` es de QtWidgets).
- **Las recetas no se editan aquí**: son YAML en `~/.config/raphi/recetas/`.
- **El progreso lo da el motor** (`ctx.avisar`): una operación que no avisa muestra solo «en curso» hasta terminar.
