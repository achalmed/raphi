---
tipo: decision
titulo: Decisiones de raphi y sus pendientes
estado: activo
---
# Decisiones

Registro acumulativo, por tema, de lo que se decidió en este repo y por qué. Cada entrada lleva su fecha;
lo revocado se marca «Superada por …» y no se borra. Los pendientes, con fecha y dueño, al final.

## Producto

### 2026-10-27 · R8: se retiran pdf-suite y page-counter

El motor de Raphi hace todo lo que hacían (las 22 operaciones de pdf-suite, con las mismas opciones de compresión, y
el Excel de page-counter con su fuente «blogs del hub» y la receta `paginas-de-los-blogs`), con pruebas que ellos no
tenían. Se retiran con la etiqueta `antes-retirar-backends-2026-10-27`; su referencia pasa a
`docs/referencia-operaciones.md`, que genera `python -m raphi referencia --aplicar` desde el registro. docflow se
queda entero: es el motor de «a Markdown» y tiene sus tests y su CI; su `docflow pdf` sigue en su CLI, duplicado
con el motor, y no se usa desde Raphi. Los pendientes de los dos backends retirados quedan resueltos por el retiro.

### 2026-10-27 · R4: la ventana nueva y el retiro de la GUI nativa

La GUI PySide6 nativa (`studio/`) se retira: sus seis páginas las cubre la web (Conversión y PDF por las
herramientas, Metadatos por «editar» y «quitar metadatos», Reportes por «Inventario de páginas» y Trabajos,
Vigilancia por las carpetas vigiladas del escritorio, Sistema por su pantalla). Lo único que no pasa a la web son
la configuración y la caché de docflow, que siguen en su CLI. La versión de la aplicación vive ahora en
`raphi/__init__.py` (`VERSION`). El entorno se crea con el Python del sistema: el de Anaconda carga su libbrotli
1.0.x y QtWebEngine no abre. Se conserva todo en la etiqueta `antes-retirar-studio-2026-10-27`.

### 2026-10-27 · DocFlow Studio se convierte en Raphi, escritorio y web con una sola interfaz

Edison decide que el repo no se separa: la carpeta y el repositorio de GitHub pasan a llamarse `raphi`, la
aplicación también, y Raphi será a la vez la aplicación de escritorio y un módulo de la plataforma Qillqa
(contrato Tiqsi) que funciona solo. Escritorio y web son la misma aplicación: hay una sola interfaz, la
web, y el escritorio la muestra en PySide6 con QtWebEngine más un puente nativo (archivos del disco,
bandeja del sistema, menús de Dolphin, carpetas vigiladas). `page-counter` no se pierde: pasa al motor como
«Inventario de páginas» y la lista de los blogs, como una fuente que solo existe en el espacio de trabajo.
La licencia pasa a AGPL-3.0 (Edison es el único autor; lo publicado antes sigue siendo MIT) y el repo sigue
público, con la guarda del escáner de Tiqsi en cada envío (`scripts/escanear.py`). Supera a la entrada
del 2026-07-13 en lo que dice de la plataforma («no una plataforma») y al plan de `gui-suites` de absorber
el studio. La propuesta completa, con sus fases R0–R8, vive en el repo de Qillqa
(`qillqa/docs/plataforma/propuesta-raphi.md`); R0 es este renombre.

### 2026-07-13 · Una GUI sobre tres backends intactos, no una plataforma

Superada en parte por «2026-10-27 · DocFlow Studio se convierte en Raphi»: Raphi será también un módulo de
plataforma con su web; lo de no adoptar el núcleo propio de la visión de producto sigue en pie.

DocFlow Studio se construye como una aplicación PySide6 que **orquesta** `docflow`, `pdf-suite` y
`page-counter` sin reescribirlos: los dos primeros se invocan como procesos y `page-counter` se importa
como módulo. Cada backend sigue siendo una CLI completa con su instalador, y docflow con sus tests y CI.

La visión de producto escrita ese día proponía otra cosa y **no se adoptó**: un núcleo propio con
`Workspace`, `Document Model`, gestor de plugins y buses de eventos y de comandos, explorador por
consultas, panel de métricas, búsqueda por campos, etiquetas, varios motores de OCR comparables, análisis
con IA, compilación LaTeX desde la GUI, plantillas y una suite común con Quarto Studio sobre un mismo
núcleo. Si alguna vuelve, se decide aquí como entrada nueva.

### 2026-07-13 · Deduplicación: el PDF pasa por pdf-suite; docflow conserva solo PDF/A

`docflow pdf` y `pdf-suite` implementan las mismas operaciones (unir, dividir, rotar, extraer, comprimir,
cifrar, marca de agua, OCR, información). En la app toda operación PDF pasa por pdf-suite, que es
superconjunto; docflow queda como motor de conversión documental y conserva **PDF/A**, que pdf-suite no
implementa. El código sigue duplicado en los backends (ambos son CLIs completas); lo que no se duplica es
la puerta de entrada. Consecuencia: una operación PDF nueva se añade en pdf-suite y en
studio/services/pdfsuite.py (retirado el 2026-10-27), nunca en `docflow pdf`.

### 2026-07-10 · docflow sustituye a script_doc_suite

docflow v3 reemplaza a `script_doc_suite` (v2) y a los scripts sueltos anteriores. Pandoc no lee pptx ni
xlsx: docflow trae parsers OOXML propios en Python stdlib, y aísla LibreOffice en un perfil temporal por
invocación para poder paralelizar.

## Estructura del repo

### 2026-09-07 · Contrato de suites del ecosistema

Cuatro `suite.yml` (`document_studio` en la raíz, uno por backend) con bloques de README generados por
`core/suites.py`; patrón `main` + `config` + `lib` en cada suite; núcleo compartido de `core/`. Dos
excepciones declaradas: docflow conserva su logger propio (niveles, `--quiet`, stdout reservado para
datos) y `page-counter` resuelve la raíz de los blogs con `Path.home()` (ver Pendientes).

### 2026-09-20 · La arquitectura vive en `docs/`, no en el backend

Los principios de diseño de docflow (errores por archivo, Bash orquesta y Python parsea, nada destructivo
sin verificación) valen para las cuatro suites: el documento de arquitectura sube a `docs/arquitectura.md`
y el README de docflow lo enlaza. El CI se dispara solo con cambios en `backends/docflow/`.

### 2026-10-04 · Las puertas de backend son breves; la referencia de cada CLI va a `docs/`

Los README de docflow y pdf-suite habían crecido hasta ser manuales de cientos de líneas con instalación,
referencia, changelog y bitácora de bugs mezclados. Cada backend conserva una puerta corta (qué es, uso,
estructura, límite honesto); la referencia completa va a `docs/referencia-docflow.md` y
docs/referencia-pdf-suite.md (retirado el 2026-10-27), el «cómo extender» a `docs/arquitectura.md`, y la historia de versiones y
correcciones a `CHANGELOG.md`. page-counter cabe en su README y no tiene referencia aparte.

### 2026-10-04 · CHANGELOG.md se conserva aunque la versión viva en el código

Desviación del perfil del ecosistema (NORMATIVA §15.11 pide un manifiesto que declare versión y alguien
que la consuma): aquí ningún `suite.yml` declara versión y no hay etiquetas. Se conserva porque las
cuatro herramientas muestran su versión al usuario (`--version` y la ventana de la app) y el repo es
público. La versión se declara en `backends/docflow/lib/core/constants.sh`, backends/pdf-suite/config.sh (retirado el 2026-10-27),
backends/page-counter/config.py (retirado el 2026-10-27) y studio/__init__.py (hoy `raphi/__init__.py`); `CHANGELOG.md` la sigue por herramienta y no
registra fases internas del ecosistema, que quedan en el `git log`.

### 2026-10-04 · La visión de producto sale del repo

La visión de producto (docs/vision.md, llegada del vault el 2026-09-20 como plan cumplido) era la
transcripción de una conversación con un asistente. Contra la regla de que un documento `hecho` no se
edita, manda la de no dejar rastro de conversaciones con asistentes en un repo público: se eliminó y git
conserva el original. Lo que tenía de decisión está en la primera entrada de este registro.

## Pendientes

| fecha | pendiente | dueño |
|---|---|---|
| 2026-10-27 | Raphi R6 (`qillqa/docs/plataforma/propuesta-raphi.md` §8): montar Raphi en Qillqa y poner sus piezas en Punku, Qillqasqa, Yupay, Rimay y Rikchay; toca la carpeta de producción y los módulos instalados en ella, así que espera el visto bueno de Edison y su procedimiento de publicación | Edison |
| 2026-10-31 | `backends/docflow/suite.yml` cita un comando que no existe (`main.sh convert … --to pdf`); el bloque generado de su README lo repite hasta que se corrija el manifiesto y se regenere | orquestador del ecosistema |
| 2026-10-31 | docflow convierte Markdown y LaTeX a PDF con XeLaTeX; el ecosistema usa LuaLaTeX en sus frameworks: decidir si docflow lo sigue | autor |
