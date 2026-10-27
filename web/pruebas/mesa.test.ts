// La lógica de la mesa de trabajo (node --test --experimental-strip-types).
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { aplicar, deshacer, inicialDe, type Mesa } from '../src/lib/mesa.ts'

const vacia: Mesa = { hojas: [], historia: [] }
const orden = (m: Mesa) => m.hojas.map((h) => (h.blanca ? 'b' : `${h.archivo}${h.pagina}`)).join(' ')

test('los archivos suman sus páginas y los quitados se las llevan', () => {
  let m = inicialDe([{ id: 'a', paginas: 2 }, { id: 'b', paginas: 1 }], vacia)
  assert.equal(orden(m), 'a1 a2 b1')
  m = inicialDe([{ id: 'b', paginas: 1 }], m)
  assert.equal(orden(m), 'b1')
})

test('mover, girar, duplicar, blanca, quitar e invertir, con deshacer', () => {
  let m = inicialDe([{ id: 'a', paginas: 3 }], vacia)
  m = aplicar(m, { tipo: 'mover', desde: 2, hasta: 0 })
  assert.equal(orden(m), 'a3 a1 a2')
  m = aplicar(m, { tipo: 'rotar', claves: [m.hojas[0].clave], grados: -90 })
  assert.equal(m.hojas[0].rotar, 270)
  m = aplicar(m, { tipo: 'duplicar', claves: [m.hojas[1].clave] })
  assert.equal(orden(m), 'a3 a1 a1 a2')
  m = aplicar(m, { tipo: 'blanca', despues: m.hojas[0].clave })
  assert.equal(orden(m), 'a3 b a1 a1 a2')
  m = aplicar(m, { tipo: 'quitar', claves: [m.hojas[1].clave] })
  m = aplicar(m, { tipo: 'invertir' })
  assert.equal(orden(m), 'a2 a1 a1 a3')
  m = deshacer(deshacer(m))
  assert.equal(orden(m), 'a3 b a1 a1 a2')
})
