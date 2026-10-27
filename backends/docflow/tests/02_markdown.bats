#!/usr/bin/env bats
# tests/02_markdown.bats — Markdown Engine: conversión, metadatos, imágenes,
# caché, overwrite y limpieza.

load test_helper

setup() {
    setup_sandbox
    have pandoc || skip "pandoc no disponible"
}
teardown() { teardown_sandbox; }

@test "docx → md con frontmatter y contenido" {
    make_docx informe.docx
    run "$DOCFLOW_BIN" to-md informe.docx
    [ "$status" -eq 0 ]
    [ -f informe.md ]
    grep -q '^titulo:' informe.md
    grep -q '# Título de prueba' informe.md
    grep -q '| A' informe.md
}

@test "sin --overwrite no sobreescribe salidas existentes" {
    make_docx informe.docx
    echo "contenido previo" > informe.md
    run "$DOCFLOW_BIN" to-md informe.docx
    [ "$status" -eq 0 ]
    [ "$(cat informe.md)" = "contenido previo" ]
}

@test "con --overwrite sí sobreescribe" {
    make_docx informe.docx
    echo "contenido previo" > informe.md
    run "$DOCFLOW_BIN" to-md informe.docx -w
    [ "$status" -eq 0 ]
    grep -q '# Título de prueba' informe.md
}

@test "caché: la segunda pasada con -w no reconvierte" {
    make_docx informe.docx
    "$DOCFLOW_BIN" to-md informe.docx
    run "$DOCFLOW_BIN" to-md informe.docx -w --json
    [ "$status" -eq 0 ]
    [[ "$output" == *'"cached": 1'* ]]
}

@test "--no-metadata omite el frontmatter" {
    make_docx informe.docx
    run "$DOCFLOW_BIN" to-md informe.docx --no-metadata
    [ "$status" -eq 0 ]
    [ "$(head -c 3 informe.md)" != "---" ]
}

@test "dry-run no escribe nada" {
    make_docx informe.docx
    run "$DOCFLOW_BIN" to-md informe.docx -n
    [ "$status" -eq 0 ]
    [ ! -f informe.md ]
}

@test "procesa directorios recursivamente respetando exclusiones" {
    mkdir -p docs/sub docs/node_modules
    make_docx docs/a.docx
    make_docx docs/sub/b.docx
    make_docx docs/node_modules/c.docx
    run "$DOCFLOW_BIN" to-md docs/
    [ "$status" -eq 0 ]
    [ -f docs/a.md ]
    [ -f docs/sub/b.md ]
    [ ! -f docs/node_modules/c.md ]
}

@test "nombres con espacios y acentos funcionan" {
    make_docx "Investigación Económica 2024.docx"
    run "$DOCFLOW_BIN" to-md "Investigación Económica 2024.docx"
    [ "$status" -eq 0 ]
    [ -f "Investigación Económica 2024.md" ]
}

@test "-o preserva la estructura relativa" {
    mkdir -p src/cap1
    make_docx src/cap1/tesis.docx
    run "$DOCFLOW_BIN" to-md src/ -o salida/
    [ "$status" -eq 0 ]
    [ -f salida/cap1/tesis.md ]
}

@test "csv → tabla markdown" {
    printf 'a,b\n1,2\n' > datos.csv
    run "$DOCFLOW_BIN" to-md datos.csv
    [ "$status" -eq 0 ]
    grep -q '| a | b |' datos.md
}
