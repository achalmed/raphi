#!/usr/bin/env bash
# =============================================================================
# install.sh — Instalador de pdf-suite v3.0
# =============================================================================
# Soporta: Kubuntu, Ubuntu, Debian (apt) y Arch Linux (pacman)
# =============================================================================

set -euo pipefail

# Colores básicos (sin depender de config.sh)
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

# Ruta del script (relativa al instalador, no al CWD)
INSTALLER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ruta de instalación fija del usuario
INSTALL_DIR="${HOME}/Documents/scripts-linux/pdf-suite"

# Wrapper global
WRAPPER_PATH="/usr/local/bin/pdf-suite"

# ---------------------------------------------------------------------------
# detect_package_manager()
# Detecta el gestor de paquetes del sistema.
# ---------------------------------------------------------------------------
detect_package_manager() {
    if command -v apt &>/dev/null; then
        echo "apt"
    elif command -v pacman &>/dev/null; then
        echo "pacman"
    elif command -v dnf &>/dev/null; then
        echo "dnf"
    else
        echo "unknown"
    fi
}

# install_package()
# Instala un paquete usando el gestor detectado.
#
# Arguments:
#   $1 - nombre del paquete
install_package() {
    local pkg="$1"
    local pm
    pm="$(detect_package_manager)"
    case "$pm" in
        apt)    sudo apt install -y "$pkg" ;;
        pacman) sudo pacman -S --noconfirm "$pkg" ;;
        dnf)    sudo dnf install -y "$pkg" ;;
        *)
            echo -e "${YELLOW}Instala manualmente: ${pkg}${NC}"
            return 1
            ;;
    esac
}

# check_and_offer_install()
# Verifica si un comando está disponible y ofrece instalarlo si no.
#
# Arguments:
#   $1 - comando   $2 - paquete   $3 - "required" | "optional"
check_and_offer_install() {
    local cmd="$1"
    local pkg="$2"
    local kind="${3:-optional}"

    if command -v "$cmd" &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} ${cmd}"
        return 0
    fi

    if [[ "$kind" == "required" ]]; then
        echo -e "  ${RED}✗${NC} ${cmd} — ${RED}OBLIGATORIO${NC}"
        read -rp "    ¿Instalar ${pkg} ahora? (s/n): " ans
        [[ "${ans,,}" == "s" ]] && install_package "$pkg" && return 0
        echo -e "${RED}Error: ${cmd} es obligatorio. Instalación cancelada.${NC}"
        exit 5
    else
        echo -e "  ${YELLOW}–${NC} ${cmd} (opcional; activa operaciones adicionales)"
        read -rp "    ¿Instalar ${pkg} ahora? (s/n) [n]: " ans
        [[ "${ans,,}" == "s" ]] && install_package "$pkg"
    fi
}

# create_wrapper()
# Crea el script wrapper en /usr/local/bin/pdf-suite.
# El wrapper simplemente delega a main.sh en la ubicación fija.
create_wrapper() {
    sudo tee "$WRAPPER_PATH" > /dev/null << EOF
#!/usr/bin/env bash
# pdf-suite wrapper — generado por install.sh
exec "${INSTALL_DIR}/main.sh" "\$@"
EOF
    sudo chmod +x "$WRAPPER_PATH"
}

# ---------------------------------------------------------------------------
# INICIO DEL INSTALADOR
# ---------------------------------------------------------------------------

echo -e "\n${BOLD}${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}  pdf-suite v3.0 — Instalador${NC}"
echo -e "${BOLD}${BLUE}══════════════════════════════════════════════════════════════${NC}\n"

# Verificar que estamos en el directorio correcto
if [[ ! -f "${INSTALLER_DIR}/main.sh" ]]; then
    echo -e "${RED}Error: ejecuta el instalador desde el directorio pdf-suite/${NC}"
    exit 1
fi

# ---------------------------------------------------------------------------
# 1. VERIFICAR / INSTALAR DEPENDENCIAS
# ---------------------------------------------------------------------------
echo -e "${BOLD}Verificando dependencias...${NC}\n"

check_and_offer_install "gs"         "ghostscript"              "required"
check_and_offer_install "qpdf"       "qpdf"                     "required"
check_and_offer_install "pdfinfo"    "poppler-utils"            "required"
echo ""
check_and_offer_install "pdftk"      "pdftk"                    "optional"
check_and_offer_install "mutool"     "mupdf-tools"              "optional"
check_and_offer_install "ocrmypdf"   "ocrmypdf"                 "optional"
check_and_offer_install "tesseract"  "tesseract-ocr"            "optional"
check_and_offer_install "exiftool"   "libimage-exiftool-perl"   "optional"
check_and_offer_install "img2pdf"    "img2pdf"                  "optional"
check_and_offer_install "pdfjam"     "texlive-extra-utils"      "optional"

# ---------------------------------------------------------------------------
# 2. CREAR DIRECTORIO DE INSTALACIÓN
# ---------------------------------------------------------------------------
echo -e "\n${BOLD}Instalando en: ${CYAN}${INSTALL_DIR}${NC}\n"

if [[ "$INSTALLER_DIR" != "$INSTALL_DIR" ]]; then
    mkdir -p "$INSTALL_DIR/lib"
    cp "${INSTALLER_DIR}/main.sh"   "${INSTALL_DIR}/"
    cp "${INSTALLER_DIR}/config.sh" "${INSTALL_DIR}/"
    cp "${INSTALLER_DIR}/README.md" "${INSTALL_DIR}/" 2>/dev/null || true
    cp "${INSTALLER_DIR}/lib/"*.sh  "${INSTALL_DIR}/lib/"
    echo -e "  ${GREEN}✓${NC} Archivos copiados a ${INSTALL_DIR}"
else
    echo -e "  ${YELLOW}–${NC} Ya estás en el directorio de instalación"
fi

# ---------------------------------------------------------------------------
# 3. PERMISOS DE EJECUCIÓN
# ---------------------------------------------------------------------------
chmod +x "${INSTALL_DIR}/main.sh"
chmod +x "${INSTALL_DIR}/lib/"*.sh
echo -e "  ${GREEN}✓${NC} Permisos de ejecución establecidos"

# ---------------------------------------------------------------------------
# 4. INSTALAR WRAPPER GLOBAL
# ---------------------------------------------------------------------------
echo -e "\n${BOLD}Instalando wrapper global en ${WRAPPER_PATH}...${NC}"
if create_wrapper; then
    echo -e "  ${GREEN}✓${NC} Wrapper instalado: ${WRAPPER_PATH}"
else
    echo -e "  ${YELLOW}⚠${NC} No se pudo instalar el wrapper global."
    echo -e "     Ejecuta manualmente: ${CYAN}${INSTALL_DIR}/main.sh${NC}"
fi

# ---------------------------------------------------------------------------
# 5. VERIFICACIÓN FINAL
# ---------------------------------------------------------------------------
echo -e "\n${BOLD}${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}  ¡Instalación completada!${NC}"
echo -e "${BOLD}${BLUE}══════════════════════════════════════════════════════════════${NC}\n"

echo -e "${BOLD}Ejemplos de uso rápido:${NC}\n"
echo -e "  ${CYAN}pdf-suite${NC}                                  # Menú interactivo"
echo -e "  ${CYAN}pdf-suite info documento.pdf${NC}               # Información del PDF"
echo -e "  ${CYAN}pdf-suite compress -m ebook libro.pdf${NC}      # Comprimir"
echo -e "  ${CYAN}pdf-suite merge a.pdf b.pdf -o unido.pdf${NC}   # Unir"
echo -e "  ${CYAN}pdf-suite split --pages 10 libro.pdf${NC}       # Dividir"
echo -e "  ${CYAN}pdf-suite ocr -l spa escaneo.pdf${NC}           # OCR"
echo -e "  ${CYAN}pdf-suite deps${NC}                             # Ver dependencias"
echo -e "  ${CYAN}pdf-suite --help${NC}                           # Ayuda completa\n"

echo -e "${BOLD}Ruta de instalación:${NC}  ${INSTALL_DIR}"
echo -e "${BOLD}Comando global:${NC}       pdf-suite\n"
