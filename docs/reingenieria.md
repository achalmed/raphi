---
tipo: doc
estado: activo
forma: explicacion
titulo: "Reingeniería de Raphi Studio (2026-11-02): de una tabla de herramientas a un estudio multimedia"
creado: 2026-11-02
---
# Reingeniería de Raphi Studio: diagnóstico, distribución y decisiones

Encargo del autor del 2026-11-02 (§3.9 de la instrucción maestra de la reingeniería de los diez studios, con §4–§6):
Raphi Studio no debe parecerse a Dolphin ni a un administrador de archivos; es un estudio de procesamiento de medios
con más de sesenta herramientas. Este documento es el diagnóstico de la ventana 2.0 (la de la fase 5,
`docs/rediseno.md`), la nueva distribución y sus decisiones (X1–X12). Lo construido y lo que quedó fuera, en §5 y §6.

## 1. Diagnóstico de la ventana 2.0 (leído en el código, `respaldo/antes-reingenieria-2026-11-02`)

Capturas de antes: `docs/figuras/antes/raphi-studio-{oscuro,claro,paleta}.png`.

### 1.1 Qué hace cada pieza hoy

| pieza | dónde | qué hace de verdad |
|---|---|---|
| fichas | `servicios/fichas.py`, `corredor.py fichas` | las 62 operaciones del motor y las recetas, con lo que falta en la máquina (calculado con el intérprete del motor); en caché y releídas en segundo plano. **Correcto** |
| familias | `familias.py` | cada operación en una de seis familias (Documentos, PDF, Imágenes, Audio y video, Archivos, Recetas) leída de su ficha. Correcto, pero no son las áreas que pide el encargo (no hay Transcripción, Conversión ni Lotes; Audio y Vídeo van juntos) |
| tabla de herramientas | `controladores/herramientas.py`, `Main.qml` | una `TablaDatos` de 66 filas (Herramienta · Estado): la vista principal es una tabla |
| archivos | `controladores/archivos.py` | una lista única de entradas (soltar, diálogo, Dolphin, otra instancia); filtra la tabla a lo que los acepta. Correcto |
| opciones | `componentes/Opciones.qml` | `PaginaFormulario` desde la ficha, valores recordados por herramienta, destino. **Correcto** (R4/R9 se cumplen) |
| simular y aplicar | `controladores/operaciones.py` | F5 encola el trabajo simulado; Ctrl+Intro, tras un diálogo propio, el real. Correcto |
| cola | `controladores/trabajos.py`, `servicios/trabajos.py` | cola persistida (200), uno a la vez con `gui_comun.tareas`, progreso `## progreso`, informe del corredor, cancelar. **Correcto**; falta **repetir** un trabajo |
| vista previa | `servicios/archivos.py` | solo imagen o texto, y solo de una salida; nada de PDF, audio ni vídeo, nada de las entradas |
| Whisper, descarga | `raphi/motor/medios.py` (`transcribir`, `descargar`) | existen y corren como cualquier herramienta. Correcto; no se simula nada |

### 1.2 Lo incompleto y lo que no se comporta

- **La distribución es la de Dolphin**: navegación por familias · tabla · panel de detalles con cinco pestañas · consola ·
  barra de estado. Con el nombre oculto, se reconoce un gestor de archivos.
- **No hay catálogo visual**: ni icono grande, ni descripción, ni formatos, ni disponibilidad a la vista; buscar es
  filtrar una tabla.
- **No hay espacio de trabajo por herramienta**: la herramienta elegida se reparte en pestañas de un panel lateral; las
  entradas, las opciones y el resultado no se ven a la vez.
- **Vista previa pobre**: sin PDF, audio ni vídeo; sin la entrada antes de procesarla.
- **La cola está escondida** en una vista de tabla más; no se puede repetir un trabajo.
- **Datos ficticios**: ninguno. **Botones sin comportamiento**: ninguno.

### 1.3 Problemas de KDE

- `FileDialog`/`FolderDialog` con la `QGuiApplication` de 2.7: el diálogo «extraño» de Qt Quick. Con `gui-comun` 3.0
  (`QApplication`, `ElegirArchivos`, `ElegirCarpeta`) es el de KDE.
- «Mostrar en la carpeta» y «Abrir» son de `controladores/espacio.py` (`xdg-open`): con 3.0, las funciones de
  `escritorio` de la base (`dolphin --select`).

### 1.4 Riesgos

| riesgo | mitigación |
|---|---|
| tocar archivos del usuario | el motor nunca pisa una entrada (principio del núcleo); aplicar confirma con herramienta, archivos, opciones y salida (operación «escritura» de la base) |
| red o transcripciones en las pruebas | las pruebas usan los archivos de muestra (`muestra.py`, ahora con un WAV); nunca `descargar` ni `transcribir` de verdad |
| prometer vista previa de audio y vídeo | comprobado antes: el módulo QML `QtMultimedia` del sistema está (con el plugin de ffmpeg); el binding de Python no lo trae, y no hace falta |
| el lanzador (`run.sh escritorio %F`) | no cambia: `escritorio/__main__.py` sigue relanzando al Python del sistema |
| la regla R4/R9 (ninguna pantalla a mano) | las áreas y los formatos se leen de la ficha en `familias.py`, el único archivo que nombra operaciones |

## 2. Referencias y distribución

| referencia | qué se toma |
|---|---|
| **HandBrake** | el flujo «fuente → preajuste → destino → cola»: las entradas a la izquierda, la vista previa en el centro, las opciones a la derecha, «Añadir a la cola» y «Procesar»; la cola como ventana propia con su estado y repetir |
| **Kdenlive** | el monitor de vista previa con reproducción de audio y vídeo; el «bin» de entradas con miniaturas |
| **OBS Studio** | la barra de estado viva con el trabajo en curso y su progreso |
| **GIMP** | la caja de herramientas por áreas con iconos reconocibles |

```
┌ [‹] [buscar herramientas…] [Todas][Documentos y PDF][Imágenes][Audio][Vídeo][Transcripción][Conversión][Lotes][Recetas] [Cola 3] ┐
│ Catálogo: cuadrícula de tarjetas — icono, nombre, descripción, área, formatos, disponible / falta X                          │
│   (con archivos soltados: «para estos 3 archivos» arriba y solo las que los aceptan)                                         │
├──────────────────────────────── al elegir una ───────────────────────────────────────────────────────────────────────────┤
│ Entradas (miniaturas, +, soltar) │ Vista previa: entrada | resultado (imagen, PDF, audio, vídeo, texto) │ Opciones de la ficha │
│                                   │                                                                    │ Salida · Simular · Procesar │
└ barra de estado: trabajo en curso · progreso · cola ─────────────────────────────────────────────────────────────────────┘
Cola: en curso (progreso) · en cola · hechos · fallidos; cada trabajo con sus archivos, salidas, registro, repetir.
```

## 3. Decisiones

- **X1. Áreas del encargo** (Documentos y PDF, Imágenes, Audio, Vídeo, Transcripción, Conversión, Procesamiento por
  lotes, Automatización y recetas), calculadas de la ficha en `familias.py`: una herramienta puede estar en varias
  (convertir vídeo: Vídeo y Conversión). «Lotes» son las que trabajan con carpetas o reúnen muchos archivos en uno
  (todas aceptan varios archivos). Las familias de antes siguen para el icono y para la CLI de Dolphin.
- **X2. Catálogo en cuadrícula** (`GridView` de tarjetas) con búsqueda rápida (título, descripción, palabras de la
  ficha, formatos) y filtros por área; la disponibilidad es la real (`faltan` de la ficha, calculada con el motor).
- **X3. Espacio de trabajo por herramienta**: entradas · vista previa · opciones, a la vez. Las opciones siguen siendo
  `PaginaFormulario` desde la ficha (R4/R9).
- **X4. Vista previa** de entradas y salidas: imagen (`Image`), PDF (páginas con `pdftoppm` por demanda, en la caché),
  audio y vídeo (`QtMultimedia` de QML, si el módulo carga; si no, el aviso), texto (`VistaTexto`).
- **X5. La cola es una vista propia** (Ctrl+3) con en curso, en cola, hechos y fallidos; cada trabajo con su
  progreso, registro, salidas (abrir con su aplicación, mostrar en Dolphin) y **repetir** (el mismo trabajo, con sus
  archivos y opciones, otra vez a la cola).
- **X6. `VentanaBase` de `gui-comun` 3.0**, no `VentanaStudio`: sin navegación lateral, tabla ni panel de detalles
  impuestos. La salida del motor sigue en el registro de cada trabajo y en la consola (Herramientas › Salida).
- **X7. Procesar** (Ctrl+Intro) es una «escritura» de la base con sus consecuencias redactadas (herramienta, archivos,
  opciones, salida): la confirmación es la común. **Simular** (F5) no escribe.
- **X8. KDE**: `ElegirArchivos`/`ElegirCarpeta` para las entradas, la carpeta de salida y las vigiladas; abrir y mostrar
  en Dolphin con `escritorio` de la base; soltar desde Dolphin donde sea.
- **X9. Atajos**: Ctrl+Intro procesar, F5 simular, Ctrl+F buscar herramientas, Ctrl+1/2/3 catálogo, herramienta y
  cola, Ctrl+O añadir archivos, Ctrl+K paleta, Alt+← volver al catálogo.
- **X10. Whisper y descargas tal como existen**: herramientas del motor, sin nada simulado; en el catálogo dicen si
  faltan `whisper` o `yt-dlp`.
- **X11. Pruebas sin red ni transcripción**: la muestra gana un WAV escrito con `wave` (sin ffmpeg); un vídeo de
  prueba solo si ffmpeg está, generado en un temporal.
- **X12. Repo público**: capturas con `HOME` y caché temporales; `scripts/escanear.py --trabajo` antes de cada commit.
