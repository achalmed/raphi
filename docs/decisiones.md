---
tipo: decision
titulo: Decisiones de raphi y sus pendientes
estado: activo
---
# Decisiones

Registro acumulativo, por tema, de lo que se decidió en este repo y por qué. Cada entrada lleva su fecha;
lo revocado se marca «Superada por …» y no se borra. Los pendientes, con fecha y dueño, al final.

## Producto

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
`studio/services/pdfsuite.py`, nunca en `docflow pdf`.

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
`docs/referencia-pdf-suite.md`, el «cómo extender» a `docs/arquitectura.md`, y la historia de versiones y
correcciones a `CHANGELOG.md`. page-counter cabe en su README y no tiene referencia aparte.

### 2026-10-04 · CHANGELOG.md se conserva aunque la versión viva en el código

Desviación del perfil del ecosistema (NORMATIVA §15.11 pide un manifiesto que declare versión y alguien
que la consuma): aquí ningún `suite.yml` declara versión y no hay etiquetas. Se conserva porque las
cuatro herramientas muestran su versión al usuario (`--version` y la ventana de la app) y el repo es
público. La versión se declara en `backends/docflow/lib/core/constants.sh`, `backends/pdf-suite/config.sh`,
`backends/page-counter/config.py` y `studio/__init__.py`; `CHANGELOG.md` la sigue por herramienta y no
registra fases internas del ecosistema, que quedan en el `git log`.

### 2026-10-04 · La visión de producto sale del repo

La visión de producto (docs/vision.md, llegada del vault el 2026-09-20 como plan cumplido) era la
transcripción de una conversación con un asistente. Contra la regla de que un documento `hecho` no se
edita, manda la de no dejar rastro de conversaciones con asistentes en un repo público: se eliminó y git
conserva el original. Lo que tenía de decisión está en la primera entrada de este registro.

## Pendientes

| fecha | pendiente | dueño |
|---|---|---|
| 2026-10-27 | Este repo se convierte en **Raphi** (escritorio y web con una sola interfaz; módulo de la plataforma Qillqa): carpeta y GitHub `raphi`, `page-counter` como «Inventario de páginas», `pdf-suite` y `studio/` se retiran al quedar cubiertos; propuesta en `qillqa/docs/plataforma/propuesta-raphi.md`. Supera el plan de `gui-suites` de absorber el studio | Edison |
| 2026-10-31 | `backends/page-counter/config.py` resuelve `~/Documents` con `Path.home()`: pasar a `core/env.py` | autor |
| 2026-10-31 | `backends/pdf-suite/install.sh` instala en una ruta fija de otro repo (`scripts-linux/pdf-suite`) y crea con `sudo` un lanzador en `/usr/local/bin` que apunta a esa copia: debe usar la carpeta del propio backend | autor |
| 2026-10-31 | `backends/pdf-suite/config.sh`: las rutas sugeridas del menú (`PDF_SEARCH_PATHS`) incluyen carpetas que ya no existen en el espacio de trabajo | autor |
| 2026-10-31 | `backends/page-counter/install.sh` crea un entorno conda propio: tercer camino de instalación frente al `.venv` del repo | autor |
| 2026-10-31 | `backends/docflow/suite.yml` y `backends/page-counter/suite.yml` citan comandos que no existen (`main.sh convert … --to pdf`, `main.py --hub`); el bloque generado de sus README los repite hasta que se corrija el manifiesto y se regenere | orquestador del ecosistema |
| 2026-10-31 | `backends/page-counter/suite.yml` declara `escribe_en: ninguno` y `simula_por_defecto: true`, pero la herramienta escribe su Excel en `excel_databases/` sin pedir ningún flag; `backends/pdf-suite/suite.yml` da como dependencias `ocrmypdf` y `exiftool`, que son opcionales (las obligatorias son `gs`, `qpdf` y `pdfinfo`) | orquestador del ecosistema |
| 2026-10-31 | docflow convierte Markdown y LaTeX a PDF con XeLaTeX; el ecosistema usa LuaLaTeX en sus frameworks: decidir si docflow lo sigue | autor |
