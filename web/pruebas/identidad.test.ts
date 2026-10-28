// La identidad de las herramientas: colores, tintes y qué acepta cada una (node --test --experimental-strip-types).
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { COLOR_CATEGORIA, RESUMEN_CATEGORIA, aclarar, acepta, colorDe, tinte, tonoDe } from '../src/lib/identidad.ts'

test('cada categoría tiene su color y su resumen; una desconocida, el neutro', () => {
  assert.deepEqual(Object.keys(COLOR_CATEGORIA).sort(), Object.keys(RESUMEN_CATEGORIA).sort())
  assert.equal(new Set(Object.values(COLOR_CATEGORIA)).size, Object.keys(COLOR_CATEGORIA).length)
  assert.equal(colorDe('Otra'), '#56708F')
})

test('el tinte añade el alfa en hexadecimal', () => {
  assert.equal(tinte('#2F6FDB', 1), '#2F6FDBff')
  assert.equal(tinte('#2F6FDB', 0.1), '#2F6FDB1a')
  assert.equal(tinte('#2F6FDB', 7), '#2F6FDBff')
})

test('qué acepta, dicho para quien la usa', () => {
  assert.equal(acepta({ entrada: 'pdf', extensiones: ['.pdf'], minimo_entradas: 1 }), 'PDF')
  assert.equal(acepta({ entrada: 'pdfs', extensiones: ['.pdf'], minimo_entradas: 2 }), 'Dos o más PDF')
  assert.equal(acepta({ entrada: 'imagenes', extensiones: ['.jpg', '.jpeg', '.png'], minimo_entradas: 1 }), 'JPG, PNG')
  assert.equal(acepta({ entrada: 'documentos', extensiones: ['.doc', '.docx', '.odt', '.rtf', '.txt', '.html', '.htm'], minimo_entradas: 1 }),
    'DOC, DOCX, ODT y 3 más')
  assert.equal(acepta({ entrada: 'archivos', extensiones: [], minimo_entradas: 1 }), 'Cualquier archivo')
  assert.equal(acepta({ entrada: 'ninguna', extensiones: [], minimo_entradas: 0 }), 'Sin archivo: trabaja con una fuente')
})

test('en oscuro, el mismo tono subido de luz', () => {
  assert.equal(aclarar('#000000', 0.5), '#808080')
  assert.equal(aclarar('#2F6FDB', 0), '#2F6FDB')
  assert.equal(tonoDe('Organizar', false), '#2F6FDB')
  assert.notEqual(tonoDe('Organizar', true), '#2F6FDB')
})
