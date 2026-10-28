---
tipo: readme
estado: activo
---
# docflow/ — conversión documental masiva por motores: → Markdown, → PDF, Office ↔ ODF

<!-- suite:inicio -->
**Suite `docflow`** · objetivo *documentos* · estado *activo* · bash · interfaz cli

Flujos de conversión y ofimática (LibreOffice, pandoc) para documentos de trabajo; herramienta en bin/ con instalador.

- Escribe en: archivos · simula por defecto: no
- Nota: config en config/defaults.conf y lib/core/config.sh; logger propio con niveles y modo quiet (excepción documentada a core/shell-lib)

Comandos:

```bash
main.sh --help
main.sh to-pdf <archivo>
bin/docflow …           # mismo programa
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-04); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

La CLI que convierte en lote documentos de Microsoft Office, OpenDocument, PDF, EPUB, HTML y LaTeX hacia
**Markdown**, hacia **PDF** y entre **Office y ODF** (en los dos sentidos, plantillas incluidas), con
verificación de cada salida, caché, paralelización, vigilancia de carpetas y reportes. Resuelve lo que
`pandoc` y `soffice` en un bucle no resuelven: pandoc no lee pptx ni xlsx (docflow trae parsers OOXML
propios que conservan notas del presentador, tablas e imágenes) y LibreOffice corrompe su perfil si corre
en paralelo (docflow lo aísla en un perfil temporal por invocación, con tiempo límite).

En Raphi escritorio es el motor de conversión y de PDF/A; el resto de operaciones PDF de la app las hace
pdf-suite (`docs/decisiones.md`). Desde la terminal sigue siendo una CLI completa.

## Uso

```bash
backends/docflow/install.sh                  # dependencias por distro, enlace docflow en el PATH, autocompletado
docflow doctor                               # qué falta y el comando exacto para instalarlo
docflow to-md -n -v tesis/                   # simular antes de un lote
docflow to-md tesis/                         # carpeta completa → Markdown (imágenes en <base>_files/images/)
docflow to-pdf informe.docx                  # el mejor motor disponible según el documento
docflow to-odf legacy/                       # docx→odt, xlsx→ods, pptx→odp
docflow to-md datos/ -j 8 --report html      # en paralelo, con reporte de sesión
docflow pdf pdfa articulo.pdf                # PDF/A-2b
docflow <comando> --help                     # ayuda contextual
bats backends/docflow/tests/                 # pruebas en sandbox (desde la raíz del repo)
```

Sin instalar, `backends/docflow/bin/docflow` (o `backends/docflow/main.sh`) es el mismo programa. Por
defecto la salida queda junto al original y no sobrescribe nada. Todas las opciones, formatos y códigos de
salida: `docs/referencia-docflow.md`.

## Estructura

| carpeta o archivo | qué es |
|---|---|
| `bin/docflow` · `main.sh` | entrada: carga `lib/core/bootstrap.sh` y despacha el comando |
| `config/defaults.conf` | valores por defecto (los sobrescribe `~/.config/docflow/config.toml` y la CLI) |
| `lib/core/` | infraestructura: registro de formatos, despacho, LibreOffice aislado, caché, paralelización, sesiones, logger |
| `lib/engines/` | motores de conversión (Markdown, PDF, ODF, Office, imágenes, metadatos, validación, reportes, vigilancia) |
| `lib/formats/` | un archivo por familia de formatos, que se registra solo |
| `lib/commands/` | un archivo por subcomando |
| `lib/helpers/` | Python stdlib: parsers OOXML, limpieza de Markdown, metadatos, reportes |
| `tests/` · `completions/` | pruebas Bats; autocompletado bash y fish |
| `install.sh` · `suite.yml` · `LICENSE` | instalador multi-distro; manifiesto de la suite; licencia AGPL-3.0 |

## Documentación

| documento | para qué |
|---|---|
| `docs/referencia-docflow.md` | comandos, opciones, formatos, originales, caché, reportes, hooks, configuración, códigos de salida, problemas frecuentes y el frontmatter que emite |
| `docs/arquitectura.md` | principios, registro, contrato de los motores, paralelización, caché y cómo extender |
| `CHANGELOG.md` | versiones de docflow |

## Límite honesto

- **No usa `set -e`**: el fallo de un documento se registra y el lote continúa; el código de salida final
  lo refleja (6 si alguna conversión falló, 7 si falló la verificación). Un lote «verde» hay que leerlo en
  el reporte de sesión.
- **Un original solo se toca si su conversión fue exitosa y verificada** (`--backup`, `--delete`); los
  archivos con error, protegidos o sin convertir jamás se mueven ni eliminan.
- **Los parsers OOXML** cubren texto, tablas, imágenes y notas del presentador, no animaciones ni macros;
  `soffice` devuelve 0 aunque no convierta (protegidos), por eso se comprueba que la salida exista, con
  300 s de tiempo límite por archivo (`DOCFLOW_SOFFICE_TIMEOUT`).
- **Markdown y LaTeX → PDF usan LuaLaTeX**, el motor del ecosistema, si está instalado (después wkhtmltopdf,
  weasyprint o LibreOffice).
- **Logger propio** con niveles y `--quiet`, excepción declarada al logger de `core/shell-lib` en
  `suite.yml`; la salida al usuario va a stderr y stdout queda para datos (`--json`).
- **En Raphi escritorio solo se usa su PDF/A**; las demás operaciones de `docflow pdf` existen en la CLI
  pero la app las hace con pdf-suite.
- **El bloque generado de arriba cita `main.sh convert`**, que no existe: el manifiesto está pendiente de
  corregir (`docs/decisiones.md` §Pendientes); el comando es `to-pdf`.
- Estado fuera del repo: `~/.config/docflow/config.toml`, sesiones en `~/.local/state/docflow/sessions/`
  (se conservan 50) y caché en ~/.cache/docflow/.

Licencia AGPL-3.0 (`LICENSE` de esta carpeta, igual que la del repo; MIT hasta el 2026-10-27).
