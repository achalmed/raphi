---
tipo: doc
estado: hecho
forma: explicacion
titulo: "Rediseño de Raphi Studio como espacio de trabajo: auditoría de la GUI de Widgets, arquitectura de información, distribución de la ventana, componentes y decisiones"
creado: 2026-11-02
---
# Rediseño de Raphi Studio: las herramientas del motor, los archivos y los trabajos en una ventana de trabajo

Fase 5 de la modernización de la familia de studios (`gui-comun/docs/arquitectura-qml-kirigami.md` §8): Raphi Studio
es el octavo que sigue al piloto Git Studio, cuyo lenguaje visual y arquitectura de información
(`git-studio/docs/reingenieria.md` §2, §4, §6, §8) el autor aprobó el 2026-11-01 «para todos los programas de la
familia». Biblioteca, Quarto y Simuladores Studio mostraron cómo se aplica a un studio que orquesta un motor con datos
propios: la tabla de lo que se maneja, una operación actual, F5 simula y Ctrl+Intro aplica tras confirmar. Este
documento aplica ese diseño al escritorio nativo de Raphi: la auditoría de lo que hay (§1), las ocho preguntas de
producto (§2), la arquitectura de información (§3), la ventana (§4), lo construido (§5), los componentes (§6), lo
que el marco necesitó (§7) y las decisiones (§8). **Está construido** (rama `wip/2026-11-02-qml`, 2026-11-02): las
capturas de §5 son reales; pasa a `hecho` cuando el autor lo valide en la sesión real (`estado.md` §Por hacer).

Tres reglas condicionan todo lo demás. **Ninguna pantalla se escribe a mano por herramienta** (R4/R9 de
`decisiones.md`): el formulario de cada operación sale de su ficha (`raphi/motor/base.py`: `Operacion.ficha()` y
`Parametro.ficha()`), y el código del studio no nombra operaciones salvo en el mapa de familias. **La interfaz web se
queda como está** (D7 de la arquitectura QML): solo migra la ventana de escritorio; `raphi --web` sigue siendo la
ventana que muestra la web. **El motor pesado no entra en el proceso de la ventana** (§8, S1): la ventana corre con
el Python del sistema (PySide6 6.10 y Kirigami) y el motor corre como proceso con el `.venv` del repo, que ya tiene
pikepdf, PyMuPDF, Pillow y lo demás; no se crea otro entorno.

## 1. Auditoría de la GUI actual (Widgets, `gui-comun` 1.1)

Ocho páginas en una barra lateral con la marca «Raphi Studio · Documentos y medios» (retirada en esta fase), con
`gui_comun.widgets` y `QtWidgets`: Inicio (cuatro cifras y los mosaicos de las familias), una página por familia
(mosaicos con buscador), Recetas, Sistema (programas que faltan, menús de Dolphin, carpetas vigiladas, la versión
web) y, al elegir una herramienta, su página (archivos, el formulario generado de la ficha, dónde dejar la salida,
«solo simular», Ejecutar y el resultado). Lo que esta fase conserva como servicios: `familias.py` (cada operación
cae en una familia por su ficha; sin Qt) y la idea de `motor_local.py` (el motor sin servidor) y de `formulario.py`
(un control por tipo de parámetro), que pasa al marco como `PaginaFormulario`.

| página | qué hace hoy | entidades y operaciones | lógica separada | mezclado en la ventana |
|---|---|---|---|---|
| Inicio | cifras (herramientas, familias, recetas, carpetas vigiladas) y mosaicos | familia | `familias` | las cifras pintadas a mano; es un panel de control |
| Familia | los mosaicos de sus herramientas con un buscador; «¿qué hacemos con esto?» al soltar archivos | herramienta | `familias.acepta` | la rejilla construida a mano; nada dice qué herramientas corren en esta máquina de un vistazo |
| Herramienta | archivos (soltar, elegir, quitar), opciones generadas, salida, simular, Ejecutar, resultado | archivo, opciones, trabajo, salida | `motor_local`, `Formulario` | el trabajo corre en un hilo del proceso de la ventana (con el `.venv` de PySide6 6.12, que no carga Kirigami); el resultado se pierde al cambiar de página; nada lista los trabajos hechos |
| Recetas · Sistema | mosaicos de recetas; programas que faltan, Dolphin, carpetas vigiladas, abrir la web | receta, requisito, carpeta vigilada | `dolphin`, `vigilancia` | las carpetas vigiladas pintadas a mano |

Lo que falta hoy: la ventana **no tiene una lista de trabajos** (qué corrió, con qué archivos, qué produjo y dónde,
qué falló); el progreso de lo largo (descargar, transcribir, OCR) solo se ve en la consola; no hay plan antes de
escribir (el usuario marca «solo simular» o no); los archivos de entrada viven en la página de cada herramienta y se
pierden al cambiar; el lanzador instalado apunta al `.venv` con PySide6 6.12, que no carga Kirigami.

## 2. Las ocho preguntas de producto

1. **Tarea principal**: con unos archivos (soltados desde Dolphin o elegidos), aplicarles una herramienta del motor
   con sus opciones: ver primero qué produciría y dónde (F5), y aplicarlo (Ctrl+Intro); seguir el trabajo mientras
   corre; abrir lo producido. La herramienta y los archivos son el sujeto; simular y aplicar, los verbos.
2. **Información constante**: cuántas herramientas hay y cuántas corren en esta máquina; cuántos trabajos hay en
   cola, en curso, hechos y con error; qué herramienta está elegida y con cuántos archivos; si hay un trabajo en
   marcha (barra de estado).
3. **Flujo de trabajo**: elegir la familia (o soltar archivos: la tabla queda con lo que sirve para ellos) → elegir
   la herramienta → Archivos → Opciones → F5 (el plan) → Ctrl+Intro (confirmar) → el trabajo en la cola, su progreso,
   su resultado (abrir, mostrar en la carpeta) y su registro.
4. **Qué se edita y qué se lee**: se leen las fichas, los requisitos, las recetas, los trabajos y sus salidas; se
   editan los archivos de entrada y las opciones (en memoria; las opciones se recuerdan por herramienta). La
   ventana nunca edita una operación ni una receta de serie.
5. **Lo irreversible**: nada toca el original (principio del motor), pero aplicar escribe archivos nuevos junto al
   original o en la carpeta elegida; descargar trae de la red; transcribir ocupa la máquina minutos. Siempre tras
   confirmar con el plan de F5; los largos con progreso y cancelación (Esc).
6. **Qué comparte con la familia**: menú, barra, navegación, tabla, detalles, panel inferior, barra de estado,
   paleta, ajustes, mensajes, `VistaTexto`, `CampoRuta` (`gui-comun` 2.x); y pidió el formulario generado (§7).
7. **Dependencias**: la ventana, el PySide6 y el Kirigami del sistema; el motor, el `.venv` del repo (`install.sh`
   lo crea: pikepdf, PyMuPDF, Pillow, pyhanko…) y los programas del sistema (gs, qpdf, ocrmypdf, soffice, ffmpeg,
   yt-dlp, whisper). Decisión S1.
8. **Qué queda fuera**: la Mesa de trabajo (solo en la web), la bandeja del sistema con su zona para soltar
   (`QSystemTrayIcon` es de QtWidgets; la ventana web la conserva), la edición de recetas (son YAML en
   la carpeta de recetas del usuario: el editor).

## 3. Arquitectura de información

### 3.1 Dos tablas, una herramienta actual, un trabajo actual, una ventana

- **Navegación** (`PanelNavegacion`): *Herramientas* (Todas y una fila por familia: Documentos, PDF, Imágenes,
  Audio y video, Archivos, con contador; Recetas) y *Trabajos* (Todos, En cola, En curso, Hechos, Con error, con
  contador). Elegir una fila de Herramientas muestra la tabla de herramientas filtrada; una de Trabajos, la de trabajos.
- **Centro**: la tabla de **herramientas** (Herramienta, Familia, Categoría, Acepta, Entradas, Opciones, Estado:
  lista · falta <programa>) o la de **trabajos** (Trabajo, Herramienta, Archivos, Estado, Progreso, Inicio, Duración,
  Salidas). Filtro Ctrl+F. Soltar archivos sobre la ventana los pone en Archivos y deja la tabla de herramientas con
  las que los aceptan.
- **Detalles** (`PanelDetalles`): de la herramienta: Resumen · Archivos · Opciones · Resultado · Registro; del
  trabajo: Resumen · Resultado · Registro.
- **Panel inferior** (`PanelInferior`): la salida del motor (lo que el proceso del `.venv` escribe: cada archivo con
  su resultado o su error, el progreso) y la barra de la tarea.
- **Barra de estado**: «62 herramientas · 62 listas · N trabajos: n en cola · n en curso · n hechos · n con error» y,
  a la derecha, la herramienta actual con sus archivos y el trabajo en marcha.

### 3.2 Entidades y dónde vive cada dato

| entidad | de dónde sale | qué muestra la ventana |
|---|---|---|
| herramienta | la ficha de la operación (`motor.operaciones()` por el corredor del `.venv`: id, categoría, título, descripción, entrada, lote, parámetros, requiere, faltan, extensiones, mínimo de entradas, palabras) y su familia (`familias.py`) | la fila; Resumen; el formulario de Opciones |
| receta | `recetas.todas()` por el corredor (id, nombre, descripción, pasos, origen) | una fila como herramienta de la familia Recetas (sin opciones; el plan dice sus pasos) |
| archivo de entrada | lo soltado, elegido o recibido de Dolphin y de otra instancia (socket local); la lista actual vive en memoria | la pestaña Archivos (nombre, tipo, tamaño, carpeta; quitar) |
| opciones | el formulario generado de `parametros`; los valores se recuerdan por herramienta en QSettings; la salida (junto a cada original · en una carpeta) | Opciones |
| trabajo | la cola del studio (`trabajos.json` de la caché): id, herramienta, archivos, opciones, destino, simulado, estado (en_cola · en_curso · hecho · parcial · fallido · cancelado), progreso y mensaje, informe (el JSON del motor), salidas, registro, inicio y fin | la fila; Resumen; Resultado (plan, archivos, mensajes, errores por archivo); Registro |
| salida | los archivos del informe (`Informe.archivos`) | Resultado: abrir, mostrar en la carpeta; vista previa si es imagen o texto |
| requisito | `faltan` de cada ficha (programas del sistema o módulos de Python del `.venv`) | la columna Estado y el Resumen; Herramientas › Lo que falta en esta máquina |
| carpeta vigilada | `escritorio/vigilancia.py` (QSettings) | Herramientas › Carpetas vigiladas… (vigilar, dejar) |

### 3.3 Dónde vive cada operación

Cada operación existe una sola vez en `Acciones` (`escritorio/studio/aplicacion.py`) y su catálogo es
`escritorio/studio/servicios/operaciones.py`: lo que lee (F5) y lo que escribe (Ctrl+Intro tras confirmar).

| F5 simula o lee | Ctrl+Intro aplica tras confirmar |
|---|---|
| **Simular la herramienta** sobre los archivos con las opciones: el plan del motor (`simular=True`: qué se producirá, dónde, con qué backend), como trabajo simulado en la cola | **Aplicar la herramienta**: el mismo trabajo de verdad, en la cola; progreso y cancelación por `gui_comun.tareas` |
| Doctor (`raphi doctor`: qué falta en esta máquina) · Lista (`raphi lista`) · Formatos de un archivo (`raphi formatos`) · Releer las fichas (F6) | — |
| — | Instalar o quitar los menús de Dolphin · Vigilar una carpeta con una receta · Dejar de vigilarla |

## 4. Distribución de la ventana (1280 × 800)

Menú (Archivo · Editar · Ver · Herramienta · Trabajos · Herramientas · Ajustes · Ayuda), barra corta (Simular F5 ·
Aplicar Ctrl+Intro · | · Añadir archivos · Añadir carpeta · el filtro), navegación compacta a la izquierda, la tabla
de herramientas o de trabajos en el centro, los detalles a la derecha (Resumen, Archivos, Opciones, Resultado,
Registro), el panel inferior con la salida del motor y la barra de estado con los contadores. Ningún nombre ni
logotipo dentro de la ventana; ningún color ni fuente propios. Soltar archivos en cualquier parte los añade.

## 5. Lo construido

| captura | qué muestra |
|---|---|
| `figuras/antes/raphi-studio-oscuro.png` | Lliphi Oscuro: la tabla de herramientas de la familia PDF, una herramienta elegida con sus archivos de muestra y la pestaña Opciones generada de su ficha |
| `figuras/antes/raphi-studio-claro.png` | Lliphi Claro: la tabla de trabajos con un trabajo hecho y su Resultado (el plan y las salidas) |
| `figuras/antes/raphi-studio-paleta.png` | la paleta de órdenes (Ctrl+K) buscando una herramienta |

Las capturas se toman sobre los archivos de muestra (`escritorio/studio/muestra.py`), con HOME, configuración y
caché temporales (ninguna ruta de la máquina en pantalla), con `escritorio/studio/capturar.py`.

## 6. Componentes

`VentanaStudio`, `PanelNavegacion`, `TablaDatos` (dos tablas en un `StackLayout`), `PanelDetalles`, `PanelInferior`,
`VistaTexto` (el registro, la vista previa de texto), `CampoRuta` (la carpeta de salida), `PaginaFormulario` (§7),
`MenuAcciones`, `BotonAccion`, `DialogoAjustes`, `PaletaOrdenes`, `Mensajes`; `DropArea` de Qt Quick para soltar;
`Kirigami.PromptDialog` para confirmar; `Image` para la vista previa de una imagen.

## 7. Lo que el marco necesitó (`gui-comun` 2.7.0)

- **`PaginaFormulario`**: un `Kirigami.FormLayout` generado desde una lista de campos (`{clave, etiqueta, tipo,
  defecto, opciones, minimo, maximo, ayuda, obligatorio, marcador}`) con un control por tipo (texto, multilínea,
  entero, decimal, opción, casilla, clave, color, ruta, carpeta); `valores` (lo escrito, sin los vacíos), la señal
  `cambiado(clave, valor)`, `poner(valores)` y `restablecer()`. Lo que la ventana 1.x hacía a mano con QtWidgets y
  lo que pedirá cualquier studio que arme pantallas desde fichas. Página en la galería y pruebas.

## 8. Decisiones

- **S1 · La ventana corre con el Python del sistema y el motor corre como proceso con el `.venv` del repo.** El
  `.venv` (1 GB, sobre `/usr/bin/python3` 3.14) trae su propio PySide6 6.12 con QtWebEngine para la ventana web, y
  ese PySide6 no carga Kirigami (es de otro Qt); el del sistema (6.10, `python3-pyside6.*`) sí. Dar al `.venv`
  `include-system-site-packages` no sirve: su PySide6 taparía al del sistema. Así que `escritorio/studio` se abre
  con `/usr/bin/python3` (lo hace `escritorio/__main__.py` desde el `.venv`, pasando dónde está el `.venv` y
  `gui_comun`), y cada trabajo es `.venv/bin/python escritorio/studio/corredor.py …` por `gui_comun.tareas.proceso`:
  el corredor importa el motor, corre la operación o la receta con el progreso en líneas `## progreso` y escribe el
  informe en JSON al final. Sin el `.venv`, la ventana enseña las fichas que el Python del sistema puede leer y dice
  qué crear (`install.sh`). No se crea otro entorno ni se duplica nada.
- **S2 · Las fichas también vienen del corredor** (`corredor.py fichas`): `faltan` se calcula en el intérprete que
  va a correr (los módulos `py:` viven en el `.venv`). Se guardan en la caché del studio para abrir al instante y se
  releen en segundo plano al arrancar y con F6.
- **S3 · El studio tiene su propia cola de trabajos**, no la de la API (`raphi/trabajos.py` es de la web y de Qillqa,
  con base y cuentas): uno a la vez, por `gui_comun.tareas`; lo que llega mientras uno corre espera «en cola»; la
  lista se guarda en `trabajos.json` de la caché del studio (los últimos 200) y sobrevive a cerrar la ventana; las
  salidas no se borran (son del usuario, junto a su original o en su carpeta).
- **S4 · F5 simula y Ctrl+Intro aplica.** Simular es el `simular=True` del motor como trabajo (su plan dice qué se
  produciría y dónde, y el corredor dice con qué programa); aplicar pide confirmación con la herramienta, los
  archivos, el destino y, en descargar y transcribir, que tardará. Doctor, lista y formatos son la CLI de solo lectura.
- **S5 · Los archivos de entrada son del espacio, no de la herramienta.** Lo soltado, elegido o recibido de Dolphin
  va a una sola lista; al cambiar de herramienta sigue ahí; la tabla de herramientas puede quedarse con las que los
  aceptan (`familias.acepta`). Las opciones se recuerdan por herramienta.
- **S6 · La familia Recetas es una fila más**: una receta se simula y se aplica como una herramienta sin opciones;
  su plan enumera los pasos. Editarlas sigue siendo del editor (YAML).
- **S7 · La vista previa es la del escritorio**: una salida que es imagen se muestra con `Image`; una que es texto
  (txt, md, srt, vtt, csv, json, html) con `VistaTexto`; lo demás se abre con el sistema. Una transcripción se lee ahí.
- **S8 · Sigue en `escritorio/studio/`**, donde el repo lo declara (`CLAUDE.md`, `README.md`, `run.sh`,
  `install.sh`, `tests/`); la estructura de la familia va dentro (`__main__.py` sin lógica, `aplicacion.py`,
  `servicios/`, `controladores/`, `qml/`). La ventana 1.x (`app.py`, `ventana.py`, `paginas.py`, `herramienta.py`,
  `formulario.py`, `motor_local.py`) se retira; se lee en la historia de git.
- **S9 · `gui_comun` se localiza instalado o por `GUI_COMUN_DIR`**, nunca subiendo carpetas: Raphi corre fuera del
  espacio de trabajo. `escritorio/__main__.py` (en el `.venv`, donde `gui-comun` está instalado) le pasa la carpeta
  al Python del sistema; `run.sh` también la pone si el repo `gui-comun` está al lado.
- **S10 · Los archivos de muestra** (`escritorio/studio/muestra.py`): un PDF y un PNG escritos a mano (sin PyMuPDF
  ni Pillow: la muestra se crea con el Python del sistema), un SRT, un Markdown y una carpeta; las pruebas corren un
  trabajo real ligero (convertir subtítulos: sin programas) por el corredor si el `.venv` está, y nunca descargan ni
  transcriben.
- **S11 · Rutas por `core/env.py` cuando `core/` está**; sin él, `RAPHI_DIR` y los XDG como ya hace el repo. La
  caché del studio es la de Qt (`QStandardPaths`); nada de rutas de la máquina en el código ni en pantalla.
