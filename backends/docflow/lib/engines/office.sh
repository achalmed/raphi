#!/usr/bin/env bash
# lib/engines/office.sh — Office Engine: OpenDocument/otros → MS Office.
# Dirección inversa del ODF Engine: odt→docx, ods→xlsx, odp→pptx y
# plantillas ott→dotx, ots→xltx, otp→potx. Markdown→docx usa pandoc
# (produce Word semántico mucho mejor que LibreOffice desde texto plano).

engine_office_output_ext() {
    printf '%s' "${REG_MS_TARGET[$1]:-}"
}

engine_office_convert() {
    local input="$1" output="$2"
    local in_ext
    in_ext="$(util_ext "$input")"

    # Markdown → docx: pandoc genera estructura semántica (estilos reales)
    if [[ "$in_ext" == "md" || "$in_ext" == "qmd" ]] && deps_has pandoc; then
        local -a cmd=(pandoc "$input" -o "$output")
        # shellcheck disable=SC2206  # los argumentos extra se parten a propósito
        [[ -n "${DOCFLOW_PANDOC_ARGS:-}" ]] && cmd+=(${DOCFLOW_PANDOC_ARGS})
        "${cmd[@]}" >/dev/null 2>&1 && [[ -s "$output" ]] && return 0
    fi

    deps_require soffice
    local out_dir produced
    out_dir="$(dirname -- "$output")"
    soffice_convert "$input" "$(util_ext "$output")" "$out_dir" || return 1
    produced="${out_dir}/$(util_basename_noext "$input").$(util_ext "$output")"
    [[ "$produced" != "$output" && -f "$produced" ]] && mv -- "$produced" "$output"
    [[ -s "$output" ]]
}
