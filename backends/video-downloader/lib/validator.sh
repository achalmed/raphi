#!/usr/bin/env bash
# =============================================================================
#  lib/validator.sh — Validación de dependencias, entorno y entradas
# =============================================================================
#
#  Centraliza todas las verificaciones previas a la descarga. Falla rápido y
#  con un mensaje accionable si falta algo obligatorio; degrada con una
#  advertencia si falta algo opcional (aria2c, AtomicParsley).
#
#  Todas las funciones retornan 0 en éxito o llaman a exit con el código
#  apropiado del proyecto (5 = dependencia, 2 = argumentos, etc.).
# =============================================================================

# ── _detect_install_hint() ───────────────────────────────────────────────────
# Detecta el gestor de paquetes para sugerir el comando de instalación correcto.
# Outputs (stdout): el prefijo de instalación, ej. "sudo pacman -S".
_detect_install_hint() {
    if command -v pacman &>/dev/null; then
        echo "sudo pacman -S"
    elif command -v apt &>/dev/null; then
        echo "sudo apt install"
    elif command -v dnf &>/dev/null; then
        echo "sudo dnf install"
    else
        echo "tu gestor de paquetes"
    fi
}

# ── validate_dependencies() ──────────────────────────────────────────────────
# yt-dlp es obligatorio. ffmpeg es prácticamente obligatorio (fusión de
# video+audio y extracción de audio lo requieren). aria2c y AtomicParsley son
# opcionales: si faltan, se avisa y se continúa sin ellos.
#
# Arguments:
#   $1 - use_aria2 (true/false): si true, aria2c pasa a ser obligatorio
# Returns:
#   0 si las dependencias obligatorias están; exit 5 si falta alguna
validate_dependencies() {
    local use_aria2="${1:-false}"
    log_title "Verificando dependencias del sistema..."
    log_separator

    local hint failures=0
    hint=$(_detect_install_hint)

    # ── yt-dlp: OBLIGATORIO (el motor de descarga) ────────────────────────────
    if command -v yt-dlp &>/dev/null; then
        log_ok "yt-dlp encontrado: v$(yt-dlp --version 2>/dev/null || echo '?')"
    else
        log_error "yt-dlp no encontrado — es obligatorio."
        log_error "Instalar con: ${hint} yt-dlp   (o: pipx install yt-dlp)"
        # No usar ((failures++)): con valor 0 devuelve estado 1 y set -e abortaría
        failures=$((failures + 1))
    fi

    # ── ffmpeg/ffprobe: necesarios para fusionar y convertir ──────────────────
    if command -v ffmpeg &>/dev/null && command -v ffprobe &>/dev/null; then
        log_ok "ffmpeg y ffprobe encontrados (fusión y conversión disponibles)"
    else
        log_error "ffmpeg/ffprobe no encontrados — obligatorios para fusionar"
        log_error "video+audio y para extraer audio. Instalar: ${hint} ffmpeg"
        failures=$((failures + 1))
    fi

    # ── aria2c: opcional salvo que se pida --aria2 ────────────────────────────
    if command -v aria2c &>/dev/null; then
        log_ok "aria2c encontrado (descargador externo acelerado disponible)"
    elif [ "${use_aria2}" = true ]; then
        log_error "--aria2 solicitado pero aria2c no está instalado."
        log_error "Instalar con: ${hint} aria2"
        failures=$((failures + 1))
    else
        log_debug "aria2c no encontrado (opcional; se usa el descargador nativo)"
    fi

    # ── AtomicParsley: opcional (miniatura incrustada en mp4) ──────────────────
    if command -v AtomicParsley &>/dev/null || command -v atomicparsley &>/dev/null; then
        log_ok "AtomicParsley encontrado (miniatura incrustable en mp4)"
    else
        log_debug "AtomicParsley no encontrado (opcional; mkv no lo necesita)"
    fi

    # ── jq: opcional (formatea el modo info) ──────────────────────────────────
    command -v jq &>/dev/null || log_debug "jq no encontrado (opcional; modo info usará JSON crudo)"

    if [ "${failures}" -gt 0 ]; then
        log_error "Faltan dependencias obligatorias. Abortando."
        exit 5
    fi
    echo ""
}

# ── validate_output_dir() ────────────────────────────────────────────────────
# Verifica que la carpeta de destino exista y sea escribible; la crea si falta.
#
# Arguments:
#   $1 - Ruta de la carpeta de destino
#   $2 - Modo simulación (true/false): si true, no crea nada
# Returns:
#   0 si la carpeta está lista; exit 4 si no es escribible; exit 1 si no se crea
validate_output_dir() {
    local dir="$1"
    local simulate="${2:-false}"

    if [ -d "${dir}" ]; then
        if [ ! -w "${dir}" ]; then
            log_error "Sin permisos de escritura en: ${dir}"
            exit 4
        fi
        log_debug "Carpeta de destino lista: ${dir}"
        return 0
    fi

    if [ "${simulate}" = true ]; then
        log_info "[SIMULACIÓN] Se crearía la carpeta de destino: ${dir}"
        return 0
    fi

    log_info "Creando carpeta de destino: ${dir}"
    if ! mkdir -p "${dir}"; then
        log_error "No se pudo crear la carpeta: ${dir}"
        exit 1
    fi
    log_ok "Carpeta creada: ${dir}"
}

# ── validate_cookies() ───────────────────────────────────────────────────────
# Si se indicó un archivo de cookies, verifica que exista y sea legible.
# El navegador (--cookies-from-browser) no se valida aquí: yt-dlp lo resuelve.
#
# Arguments:
#   $1 - Ruta al archivo de cookies (puede ir vacía)
# Returns:
#   0 si es válido o no se usó; exit 3 si se indicó pero no existe
validate_cookies() {
    local cookies_file="$1"
    [ -z "${cookies_file}" ] && return 0
    if [ ! -f "${cookies_file}" ]; then
        log_error "Archivo de cookies no encontrado: ${cookies_file}"
        exit 3
    fi
    if [ ! -r "${cookies_file}" ]; then
        log_error "Sin permisos para leer el archivo de cookies: ${cookies_file}"
        exit 4
    fi
    log_debug "Cookies válidas: ${cookies_file}"
}

# ── validate_quality() ───────────────────────────────────────────────────────
# La calidad debe ser 'best', 'worst' o un número entero (altura en px).
#
# Arguments:
#   $1 - Valor de calidad a validar
# Returns:
#   0 si es válido; exit 2 si no lo es
validate_quality() {
    local quality="$1"
    case "${quality}" in
        best|worst) return 0 ;;
        ''|*[!0-9]*)
            log_error "Calidad inválida: '${quality}'. Usa best, worst o un número (ej. 1080)."
            exit 2 ;;
        *) return 0 ;;
    esac
}

# ── validate_targets() ───────────────────────────────────────────────────────
# Verifica que haya al menos una URL/objetivo para descargar.
#
# Arguments:
#   $1 - Nombre (nameref) del array de objetivos
# Returns:
#   0 si hay al menos un objetivo; exit 2 si está vacío
validate_targets() {
    local -n targets_ref="$1"
    if [ "${#targets_ref[@]}" -eq 0 ]; then
        log_error "No se indicó ninguna URL ni archivo de lotes (--batch)."
        log_error "Usa --help para ver ejemplos de uso."
        exit 2
    fi
    log_debug "Objetivos a procesar: ${#targets_ref[@]}"
}

# ── warn_if_not_url() ────────────────────────────────────────────────────────
# Aviso suave: yt-dlp acepta URLs http(s) y prefijos de búsqueda (ytsearch:).
# No abortamos porque hay entradas válidas que no empiezan por http.
#
# Arguments:
#   $1 - Cadena del objetivo
warn_if_not_url() {
    local target="$1"
    if [[ ! "${target}" =~ ^https?:// ]] && [[ ! "${target}" =~ ^[a-z0-9]+: ]]; then
        log_warn "Esto no parece una URL ni una búsqueda: '${target}' (se intentará igual)"
    fi
}
