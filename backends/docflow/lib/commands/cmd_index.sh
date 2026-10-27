#!/usr/bin/env bash
# lib/commands/cmd_index.sh — Comando index: índice global de documentos.
# Genera <dir>/index.md con todos los Markdown del árbol (título extraído
# del frontmatter o del primer encabezado) más un árbol del directorio.

cmd_index() {
    local dir="${1:-.}"
    validate_input_path "$dir" || exit "$EXIT_BAD_INPUT"
    [[ -d "$dir" ]] || { log_error "index requiere un directorio."; exit "$EXIT_USAGE"; }

    local out="${dir%/}/index.md"
    log_header "Generando índice de ${dir}"

    if [[ "${DOCFLOW_DRY_RUN:-false}" == "true" ]]; then
        log_info "[dry-run] escribiría ${out}"
        exit 0
    fi

    DOCFLOW_INDEX_EXCLUDES="${DOCFLOW_EXCLUDES:-}" \
    python3 - "$dir" "$out" <<'PYEOF'
import os, re, sys
from datetime import datetime
from pathlib import Path

root = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2])
excludes = set((os.environ.get("DOCFLOW_INDEX_EXCLUDES") or "").split())

def title_of(md: Path) -> str:
    try:
        text = md.read_text(encoding="utf-8", errors="replace")[:4000]
    except OSError:
        return md.stem
    m = re.search(r"\A---\n.*?^title:\s*(.+?)\s*$.*?\n---", text, re.S | re.M)
    if m:
        return m.group(1).strip('"\'')
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else md.stem

entries = []
tree_lines = []

def walk(path: Path, depth: int):
    children = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    for child in children:
        if child.name.startswith(".") or child.name in excludes:
            continue
        if child.is_dir():
            tree_lines.append(f"{'  ' * depth}- 📁 {child.name}/")
            walk(child, depth + 1)
        elif child.suffix.lower() == ".md" and child.resolve() != out.resolve():
            rel = child.relative_to(root)
            entries.append((str(rel), title_of(child)))
            tree_lines.append(f"{'  ' * depth}- 📄 [{child.name}]({rel})")

walk(root, 0)

lines = [
    f"# Índice de documentos — {root.name}", "",
    f"> Generado por docflow el {datetime.now().strftime('%Y-%m-%d %H:%M')} · {len(entries)} documentos", "",
    "## Documentos", "",
]
for rel, title in sorted(entries, key=lambda e: e[0].lower()):
    lines.append(f"- [{title}]({rel})")
lines += ["", "## Árbol del directorio", ""] + tree_lines + [""]
out.write_text("\n".join(lines), encoding="utf-8")
print(len(entries))
PYEOF
    local estado=$?
    (( estado == 0 )) || { log_error "no se pudo generar ${out}."; exit "$EXIT_ERROR"; }
    log_ok "índice generado: ${out}"
    exit 0
}

cli_help_index() {
    cat >&2 <<EOF
${C_BOLD}docflow index${C_RESET} — Índice global + árbol de documentos Markdown.

USO: docflow index [directorio]

Genera <directorio>/index.md con enlaces a todos los .md (título real
extraído del frontmatter o del primer encabezado) y un árbol navegable.
EOF
}
