#!/usr/bin/env bash
# lib/core/constants.sh — Metadatos, códigos de salida y colores.
# Única fuente de verdad para valores inmutables de todo el proyecto.
# shellcheck disable=SC2034  # las constantes las leen los demás archivos de lib/

readonly DOCFLOW_NAME="docflow"
readonly DOCFLOW_VERSION="3.0.0"
readonly DOCFLOW_AUTHOR="Edison Achalma"
readonly DOCFLOW_URL="https://github.com/achalmed/docflow"

# ---------------------------------------------------------------------------
# Códigos de salida bien definidos (integración con scripts y CI/CD).
# Documentados en README.md → sección "Códigos de salida".
# ---------------------------------------------------------------------------
readonly EXIT_OK=0            # Todo correcto
readonly EXIT_ERROR=1         # Error general no clasificado
readonly EXIT_USAGE=2         # Uso incorrecto de la CLI
readonly EXIT_BAD_INPUT=3     # Ruta de entrada inválida o ilegible
readonly EXIT_NO_FILES=4      # No se encontraron archivos que procesar
readonly EXIT_MISSING_DEPS=5  # Falta una dependencia requerida
readonly EXIT_CONVERT_FAIL=6  # Al menos una conversión falló
readonly EXIT_VERIFY_FAIL=7   # La verificación post-conversión falló
readonly EXIT_BAD_CONFIG=8    # Archivo de configuración inválido
readonly EXIT_INTERRUPTED=130 # Interrumpido por el usuario (SIGINT)

# ---------------------------------------------------------------------------
# Rutas XDG (respetan las variables de entorno del usuario).
# ---------------------------------------------------------------------------
readonly DOCFLOW_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/docflow"
readonly DOCFLOW_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/docflow"
readonly DOCFLOW_STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/docflow"
readonly DOCFLOW_CONFIG_FILE_DEFAULT="${DOCFLOW_CONFIG_DIR}/config.toml"

# ---------------------------------------------------------------------------
# Colores — desactivados si stdout no es TTY o si NO_COLOR está definido.
# ---------------------------------------------------------------------------
if [[ -t 2 && -z "${NO_COLOR:-}" ]]; then
    readonly C_BOLD=$'\033[1m'  C_DIM=$'\033[2m'
    readonly C_GREEN=$'\033[0;32m' C_YELLOW=$'\033[1;33m'
    readonly C_RED=$'\033[0;31m'   C_BLUE=$'\033[0;34m'
    readonly C_CYAN=$'\033[0;36m'  C_RESET=$'\033[0m'
else
    readonly C_BOLD='' C_DIM='' C_GREEN='' C_YELLOW=''
    readonly C_RED='' C_BLUE='' C_CYAN='' C_RESET=''
fi
