// La lógica pura del buscador de herramientas (node --test --experimental-strip-types).
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { buscar, normalizar, puntuar } from '../src/lib/buscar.ts'

const H = [
  { id: 'unir', titulo: 'Unir PDF', descripcion: 'Junta varios PDF en uno.', categoria: 'Organizar', palabras: ['juntar', 'combinar'] },
  { id: 'convertir_imagen', titulo: 'Convertir imagen', descripcion: 'JPG, PNG, HEIC…', categoria: 'Medios', palabras: ['heic a jpg', 'foto'] },
  { id: 'foliar', titulo: 'Foliar expediente', descripcion: 'Numera los folios.', categoria: 'Editar', palabras: ['folios', 'foliación'] },
]

test('normaliza tildes y mayúsculas', () => {
  assert.equal(normalizar('  Foliación  '), 'foliacion')
})

test('una palabra clave encuentra su herramienta', () => {
  assert.equal(buscar(H, 'juntar')[0].id, 'unir')
  assert.equal(buscar(H, 'HEIC')[0].id, 'convertir_imagen')
  assert.equal(buscar(H, 'foliacion')[0].id, 'foliar')
})

test('el título exacto va primero y lo que no casa no sale', () => {
  assert.ok(puntuar(H[0], 'unir pdf') > puntuar(H[0], 'pdf'))
  assert.deepEqual(buscar(H, 'zzz'), [])
  assert.equal(buscar(H, '').length, 3)
})
