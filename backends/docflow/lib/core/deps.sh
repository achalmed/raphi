#!/usr/bin/env bash
# lib/core/deps.sh — Detección de dependencias y sugerencias de instalación.
# docflow nunca asume que una herramienta existe: cada motor consulta aquí
# y se degrada con elegancia (o falla con instrucciones claras).

# Nombre de paquete por distro: "arch:apt:dnf:zypper"
declare -gA _DEP_PACKAGES=(
    [pandoc]="pandoc:pandoc:pandoc:pandoc"
    [soffice]="libreoffice-still:libreoffice:libreoffice:libreoffice"
    [python3]="python:python3:python3:python3"
    [magick]="imagemagick:imagemagick:ImageMagick:ImageMagick"
    [qpdf]="qpdf:qpdf:qpdf:qpdf"
    [gs]="ghostscript:ghostscript:ghostscript:ghostscript"
    [pdftotext]="poppler:poppler-utils:poppler-utils:poppler-tools"
    [tesseract]="tesseract:tesseract-ocr:tesseract:tesseract-ocr"
    [ocrmypdf]="ocrmypdf:ocrmypdf:ocrmypdf:python3-ocrmypdf"
    [inotifywait]="inotify-tools:inotify-tools:inotify-tools:inotify-tools"
    [wkhtmltopdf]="wkhtmltopdf:wkhtmltopdf:wkhtmltopdf:wkhtmltopdf"
    [weasyprint]="python-weasyprint:weasyprint:weasyprint:python3-weasyprint"
    [exiftool]="perl-image-exiftool:libimage-exiftool-perl:perl-Image-ExifTool:exiftool"
    [lualatex]="texlive-luatex:texlive-luatex:texlive-luatex:texlive-luatex"
    [cwebp]="libwebp:webp:libwebp-tools:libwebp-tools"
)

declare -gA _DEP_ROLES=(
    [pandoc]="Conversión a Markdown y PDF de documentos de texto"
    [soffice]="Conversión ODF↔Office, presentaciones y hojas de cálculo"
    [python3]="Parsers OOXML, limpieza de Markdown, config TOML"
    [magick]="Optimización, conversión y redimensionado de imágenes"
    [qpdf]="Operaciones PDF: unir, dividir, rotar, cifrar"
    [gs]="Compresión de PDF y PDF/A"
    [pdftotext]="Extracción de texto de PDF (poppler)"
    [tesseract]="Motor OCR"
    [ocrmypdf]="OCR sobre PDFs escaneados"
    [inotifywait]="Modo watch eficiente por eventos del kernel"
    [wkhtmltopdf]="Motor alternativo HTML → PDF"
    [weasyprint]="Motor alternativo HTML/CSS → PDF"
    [exiftool]="Lectura/escritura avanzada de metadatos"
    [lualatex]="Motor LaTeX (LuaLaTeX, el del ecosistema) para pandoc → PDF de alta calidad"
    [cwebp]="Conversión de imágenes a WebP sin ImageMagick"
)

# deps_pkg_manager → pacman | apt | dnf | zypper | "" (desconocido)
deps_pkg_manager() {
    if   command -v pacman  &>/dev/null; then echo "pacman"
    elif command -v apt-get &>/dev/null; then echo "apt"
    elif command -v dnf     &>/dev/null; then echo "dnf"
    elif command -v zypper  &>/dev/null; then echo "zypper"
    else echo ""; fi
}

# deps_install_hint <herramienta> → comando de instalación para esta distro
deps_install_hint() {
    local tool="$1" pkgs="${_DEP_PACKAGES[$1]:-$1}"
    local arch apt dnf zyp
    IFS=':' read -r arch apt dnf zyp <<< "$pkgs"
    case "$(deps_pkg_manager)" in
        pacman) echo "sudo pacman -S ${arch}" ;;
        apt)    echo "sudo apt install ${apt}" ;;
        dnf)    echo "sudo dnf install ${dnf}" ;;
        zypper) echo "sudo zypper install ${zyp}" ;;
        *)      echo "instala '${tool}' con el gestor de paquetes de tu distro" ;;
    esac
}

# deps_has <herramienta> → 0 si está disponible (con caché por proceso)
declare -gA _DEP_CACHE=()
deps_has() {
    local tool="$1"
    if [[ -z "${_DEP_CACHE[$tool]:-}" ]]; then
        command -v "$tool" &>/dev/null && _DEP_CACHE[$tool]=1 || _DEP_CACHE[$tool]=0
    fi
    [[ "${_DEP_CACHE[$tool]}" == "1" ]]
}

# deps_require <herramienta>... → aborta con EXIT_MISSING_DEPS si falta alguna
deps_require() {
    local tool missing=()
    for tool in "$@"; do
        deps_has "$tool" || missing+=("$tool")
    done
    [[ ${#missing[@]} -eq 0 ]] && return 0
    for tool in "${missing[@]}"; do
        log_error "Dependencia requerida no encontrada: ${tool}"
        log_plain "  ${_DEP_ROLES[$tool]:-}"
        log_plain "  Instálala con: $(deps_install_hint "$tool")"
    done
    exit "$EXIT_MISSING_DEPS"
}

# deps_version <herramienta> → primera línea de versión ("?" si no se conoce)
deps_version() {
    local tool="$1" v=""
    case "$tool" in
        soffice)  v="$(soffice --version 2>/dev/null | head -1)" ;;
        lualatex) v="$(lualatex --version 2>/dev/null | head -1)" ;;
        gs)       v="gs $(gs --version 2>/dev/null)" ;;
        *)        v="$("$tool" --version 2>/dev/null | head -1)" ;;
    esac
    printf '%s' "${v:-?}"
}
