---
tipo: doc
titulo: Arquitectura de docflow y principios comunes a las cuatro suites
estado: activo
---
# Arquitectura de docflow y principios comunes a las cuatro suites

Este documento explica las decisiones de diseño de docflow v3 y cómo extender el sistema. Léelo antes
de modificar el núcleo. Sus **Principios** son los de las dos suites del repo (`raphi` y
`docflow`; pdf-suite y page-counter se retiraron en R8); lo de docflow tiene sus rutas relativas a
`backends/docflow/`. El motor, la API, la web y el escritorio de Raphi tienen sus secciones más abajo.

## Principios

1. **Responsabilidad única por módulo.** Ningún archivo mezcla parsing de CLI
   con lógica de conversión, ni logging con estado de sesión.
2. **El núcleo no conoce formatos.** Los formatos se declaran en
   `backends/docflow/lib/formats/` y los motores los consultan a través del registry.
   Añadir un formato jamás toca `backends/docflow/lib/core/`.
3. **Errores por archivo, nunca por lote.** No se usa `set -e`: el fallo de
   un documento se registra y el lote continúa. El código de salida final
   refleja si hubo fallos (6) o no (0).
4. **Nada destructivo sin verificación.** Un original solo se respalda o
   elimina si su conversión fue exitosa **y** pasó la verificación del
   Validation Engine.
5. **Bash para orquestar, Python (stdlib) para parsear.** Bash coordina
   procesos y archivos; todo lo que requiere parsing estructurado (XML OOXML,
   TOML, Markdown, JSON) vive en `backends/docflow/lib/helpers/*.py` sin dependencias externas.

## Capas

```
bin/docflow
  └─ lib/core/bootstrap.sh        carga módulos, resuelve el comando
       ├─ lib/core/*              infraestructura transversal
       ├─ lib/engines/*           motores de conversión
       ├─ lib/formats/*           declaraciones de formatos (registry)
       └─ lib/commands/cmd_*.sh   un archivo por subcomando
```

### El registry (`backends/docflow/lib/core/registry.sh`)

Cada formato declara una línea:

```bash
registry_add docx "document" "Word (OOXML)" pandoc soffice odt ""
#            ext   categoría  descripción    md     pdf     odf ms
```

Los campos `md`/`pdf` son **estrategias** que el motor correspondiente sabe
ejecutar; `odf`/`ms` son extensiones destino para los motores bidireccionales.
El descubrimiento de archivos (`finder`), la tabla `docflow formats`, y los
cuatro comandos de conversión derivan todo de aquí.

### El contrato de los motores

Cada tarea de conversión (`md`, `pdf`, `odf`, `office`) expone dos funciones:

```bash
engine_<tarea>_output_ext <ext_entrada>   # → extensión salida ('' = n/a)
engine_<tarea>_convert <entrada> <salida> # → 0 éxito / ≠0 error
```

`dispatch.sh` es el único llamador y aporta todo lo transversal:
descubrimiento, rutas de salida, overwrite/resume, caché, detección de
protegidos, dry-run, hooks, cronometraje, verificación, registro en sesión
y gestión de originales. Un motor nuevo (p. ej. `epub`) solo implementa el
contrato y gana todas esas capacidades gratis.

### Estrategias del Markdown Engine

| Estrategia | Formatos | Ruta |
|---|---|---|
| `pandoc` | docx, odt, rtf, epub, html, tex | pandoc directo con `--extract-media` |
| `via_docx` | doc, dot, dotx, fodt, ott | soffice → docx → pandoc |
| `pptx_parser` | pptx, pptm, ppsx, potx | `backends/docflow/lib/helpers/pptx_to_md.py` (OOXML directo) |
| `via_pptx` | ppt, pps, pot, odp, fodp, otp | soffice → pptx → parser |
| `xlsx_parser` | xlsx, xlsm, xltx | `backends/docflow/lib/helpers/xlsx_to_md.py` (OOXML directo) |
| `via_xlsx` | xls, ods, fods, ots | soffice → xlsx → parser |
| `csv_parser` | csv, tsv | `backends/docflow/lib/helpers/xlsx_to_md.py --csv` |
| `pdf_text` | pdf | (ocrmypdf →) pdftotext |

**Por qué parsers propios:** pandoc no tiene lectores para pptx/xlsx. La
alternativa clásica (soffice → html → pandoc) pierde notas del presentador,
el orden de las diapositivas y produce HTML sucio. Los contenedores OOXML son
zip+XML documentado: parsearlos con `xml.etree` es más fiel y sin dependencias.

**Post-proceso común** (`_md_postprocess`): consolidación de imágenes en
`<base>_files/images/figure-NNN.*` con reescritura de enlaces relativos
(`mdtools.py fix-media`), procesamiento de imágenes (Media Engine), limpieza
conservadora (`mdtools.py clean`) y frontmatter YAML (Metadata Engine).

### LibreOffice headless (`backends/docflow/lib/core/soffice.sh`)

Dos problemas conocidos de `soffice --convert-to` en automatización:

1. **Perfil compartido:** dos instancias simultáneas corrompen el perfil de
   usuario. Solución: `-env:UserInstallation=file:///tmp/...` único por
   invocación (es lo que permite `--jobs N` con seguridad).
2. **Cuelgues:** documentos rotos pueden bloquear soffice indefinidamente.
   Solución: `timeout` (300 s por defecto) + verificación de que el archivo
   esperado realmente existe (soffice devuelve 0 aunque no convierta, p. ej.
   con documentos protegidos).

### Paralelización (`backends/docflow/lib/core/parallel.sh`)

En lugar del frágil `export -f` de funciones a subshells, cada worker
re-invoca `docflow __worker <tarea> <archivo>`: un subcomando interno que
re-carga el entorno completo. La configuración viaja por variables
`DOCFLOW_*` exportadas; los resultados convergen en el `results.tsv` de la
sesión (append atómico: líneas < PIPE_BUF). El proceso padre dibuja la barra
de progreso monitorizando ese archivo.

### Sesiones y estado

- `~/.local/state/docflow/sessions/<ts>/results.tsv` — una línea por archivo:
  `status task input output ms bytes_in bytes_out mensaje`.
- Estados: `ok | skip | cached | fail | protected | dry-run`.
- `report.py` genera HTML/CSV/JSON/MD desde ese TSV; `--json` lo emite crudo.
- Se conservan las últimas 50 sesiones.

### Caché (`backends/docflow/lib/core/cache.sh`)

Clave = `sha256(contenido) + tarea + opciones relevantes` (flavor, formato de
imagen, motor PDF). Valor = ruta de salida. Hit solo si la salida registrada
coincide con la esperada y aún existe. El índice es append-only (la última
entrada gana); `docflow cache prune` lo compacta.

## El motor de Raphi (`raphi/`)

Desde el 2026-10-27 (R1 de `qillqa/docs/plataforma/propuesta-raphi.md`) las operaciones viven en un motor Python
que reúne las de pdf-suite, el PDF/A y la conversión de docflow, el conteo de page-counter y la conversión de medios.
Lo usan la CLI (`raphi <operación>`), la API y la web que vienen (R2–R3) y, al final, el escritorio (R4).

- **Una operación, una declaración**: `@operacion(id, categoría, título, descripción, entrada=, lote=, parametros=,
  requiere=)` en el módulo de su familia (`raphi/motor/pdf_*.py`, `documentos.py`, `medios.py`). La ficha
  (`Operacion.ficha()`) es lo que leen la CLI y los formularios; `requiere` dice qué programa o módulo necesita y, si
  falta, la operación se ofrece como no disponible en vez de fallar a mitad.
- **Los tres principios, en `raphi/motor/base.py` y no en cada operación**: `ejecutar` corre una operación de lote una vez
  por entrada y anota el error de cada una sin detener el resto; `Contexto.salida` nunca devuelve la ruta de una
  entrada ni una que exista («-2», «-3»…); `verificar_salida` comprueba toda salida (existe, no está vacía; un PDF abre
  y tiene páginas) antes de darla por buena. Con `simular=True` cada función devuelve su `plan` sin escribir.
- **Recetas** (`raphi/recetas.py`): pasos encadenados en una carpeta temporal; lo que sale de un paso entra al
  siguiente, un paso sin cambio deja pasar lo que recibió y solo el resultado final se copia al destino.
- **Fuentes** (`raphi/fuentes/`): de dónde sale un inventario de páginas; «hub» es el caso de page-counter y solo
  existe dentro del espacio de trabajo.
- **Fronteras** (`tests/test_fronteras.py`): el motor no importa FastAPI, SQLAlchemy, Qt ni Tiqsi; nada en `raphi/`
  importa a otro proyecto de la plataforma.

## La API y el módulo de Tiqsi (`raphi/api/`, `raphi/manifiesto.py`)

La misma API (`/api/raphi/…`) sirve a la web, al escritorio y a otros sistemas: operaciones y formatos; archivos
subidos (con miniaturas WebP en caché) o, solo en el escritorio, del disco por su ruta (`/locales`, nunca se copian
ni se borran); trabajos; recetas. Toda ruta pide la identidad del anfitrión (`tiqsi.puertos.usuario_actual`) y una
cuenta solo ve lo suyo.

- **La cola** (`raphi/trabajos.py`): un trabajo se guarda «pendiente»; el repartidor (tarea del anfitrión) corre
  `RAPHI_CONCURRENCIA` a la vez en un hilo, con el avance en memoria guardado cada segundo y la cancelación mirada
  entre página y página. Al arrancar, lo que quedó «en_curso» vuelve a la cola. Al terminar anota
  «raphi.trabajo.terminado» en su bandeja y, si tardó más de 30 s, «aviso.nuevo» (la campana, como Minka y Punku).
  La purga borra a las `RAPHI_RETENCION_HORAS` lo subido y las salidas, nunca los archivos locales.
- **La base propia** (`raphi/db.py`): tablas `raphi_*` sin claves foráneas hacia nadie, con el mismo código en
  SQLite (escritorio, sola) y en PostgreSQL (Qillqa).
- **Tres modos** (`RAPHI_MODO`): `modulo` (lo monta un anfitrión por `MANIFIESTO`), `sola` (`raphi.sola`, el
  anfitrión mínimo de Tiqsi con cuentas) y `escritorio` (`raphi.escritorio`, una persona en 127.0.0.1 con una ficha
  de un solo uso que la ventana pone donde la cáscara web guarda la sesión).
- **Lo que ofrece a los demás** (`raphi/contrato.py`): «pdf.v1» (ejecutar una operación o receta, miniatura, texto,
  info, firmas) y «conversion.v1» (formatos de un archivo, convertir). Los demás la aprovechan, nunca la necesitan.

## La web (`web/`): la única interfaz

`web/` es el módulo web de Tiqsi (`@qillqa/raphi`, `web/src/modulo.ts`): Qillqa lo monta en su menú, `raphi.sola` y
`raphi.escritorio` lo sirven construido (`web/dist`) con la cáscara mínima de Tiqsi. Sus pantallas: Herramientas
(cuadrícula con buscador y la zona para soltar un archivo y ver a qué se convierte), cada herramienta
(`/raphi/h/:id`, también `receta:<id>`), la Mesa de trabajo (miniaturas de varios PDF que se ordenan, giran, duplican
o quitan, con deshacer; guarda con «componer»), Trabajos, Recetas y Sistema.

- **Ningún formulario escrito a mano**: `web/src/componentes/Formulario.tsx` sale de la ficha de cada operación.
- **Lógica pura aparte** (`web/src/lib/buscar.ts`, `web/src/lib/mesa.ts`), probada con `npm run web:pruebas`.
- **Lo del escritorio, solo si está** (`web/src/lib/escritorio.ts`): `hayEscritorio()` ofrece archivos del disco, «Mostrar» en
  la carpeta, dónde guardar, menús de Dolphin y carpetas vigiladas; en el navegador esas opciones no aparecen.
- Las miniaturas se piden con la sesión (`descargarBlob`) y el servidor las guarda en WebP junto al archivo.
- **La identidad de las herramientas** (`web/src/lib/identidad.ts`, `web/src/componentes/Icono.tsx`): el marco es del
  anfitrión y es neutro; el color vive solo en el ícono de cada herramienta (un tono por categoría) y en lo que pasa al
  tocarla o al soltarle un archivo. Una operación nueva elige su ícono en `ICONOS`; sin él, lleva el genérico.
- **La pieza para los demás módulos** (`@qillqa/raphi/publico`, `web/src/componentes/Acciones.tsx`): el anfitrión la
  registra como «raphi.Acciones» y un módulo la pinta junto a un archivo suyo con `<Pieza pieza="raphi.Acciones" />`.
  Recibe cómo traer el archivo (`archivo`) y, si el módulo quiere, cómo guardar el resultado (`guardar`, por su
  API): Raphi nunca escribe en la carpeta ni en la base de otro. Sin Raphi montada, la pieza no existe.

## Cómo extender

### Raphi

Una operación nueva es una función en el módulo de su familia con `@operacion(...)`: recibe un `Contexto` (sus
entradas, `ctx.p(clave)`, `ctx.salida()`, `ctx.temporal()`, `ctx.avisar(fracción, mensaje)`, `ctx.simular`) y devuelve
un `Resultado` (archivos, datos, mensajes, plan o `sin_cambio`). Un fallo explicable es `ErrorOperacion`. Su prueba va
en `tests/` con el corpus de `tests/conftest.py`, generado en cada corrida.

### docflow

**Formato nuevo:** un archivo en `backends/docflow/lib/formats/` con `registry_add`. Si
necesita una estrategia nueva, añádela al `case` del motor correspondiente
y documenta aquí.

**Comando nuevo:** `backends/docflow/lib/commands/cmd_<nombre>.sh` con una función
`cmd_<nombre>()` (y opcionalmente `cli_help_<nombre>()`). El bootstrap lo
descubre por convención de nombres; no hay lista central que mantener.

**Motor nuevo:** implementa el contrato de dos funciones y añade la tarea a
`_dispatch_exts_for_task`. Todo lo transversal es gratis.

**Opción de configuración nueva (docflow):** valor por defecto en
`backends/docflow/config/defaults.conf`, mapeo TOML en `KEYMAP` de `backends/docflow/lib/core/config.sh`,
flag en `backends/docflow/lib/core/cli.sh` y plantilla en `config_write_template`.

## Convenciones de docflow

- `bash -n` limpio y ShellCheck (nivel warning) en CI.
- Funciones privadas de módulo con prefijo `_`.
- Toda salida al usuario pasa por `logger.sh` y va a **stderr**; stdout queda
  reservado para datos (`--json`, `config path`).
- Rutas siempre entrecomilladas; iteración de archivos con NUL
  (`find -print0` / `read -d ''`).
- Mensajes de cara al usuario en español; identificadores en inglés técnico.
