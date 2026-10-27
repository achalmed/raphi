// Cada pantalla de Raphi le dice al anfitrión qué módulo es (`<Marco modulo="raphi">`): Qillqa busca con eso su entrada
// del menú y su icono, y sin él la página no abre (R6, 2026-10-27).
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readdirSync, readFileSync } from 'node:fs'

const PAGINAS = new URL('../src/paginas/', import.meta.url)

test('todas las pantallas pasan modulo="raphi" al Marco', () => {
  const sin = readdirSync(PAGINAS).filter((f) => f.endsWith('.tsx')).flatMap((f) =>
    [...readFileSync(new URL(f, PAGINAS), 'utf8').matchAll(/<Marco\b[^>]*>/g)].filter((m) => !m[0].includes('modulo="raphi"')).map(() => f))
  assert.deepEqual(sin, [])
})
