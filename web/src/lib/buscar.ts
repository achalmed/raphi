/**
 * El buscador de herramientas: «juntar» encuentra «Unir PDF», «heic» encuentra «Convertir imagen», sin tildes ni
 * mayúsculas. Lógica pura (sin React): la prueban web/pruebas/buscar.test.ts.
 */
export interface Buscable {
  id: string
  titulo: string
  descripcion: string
  categoria: string
  palabras: string[]
}

export const normalizar = (t: string): string =>
  t.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim()

/** La puntuación de una herramienta para una consulta: 0 si no casa; más alto, más arriba. */
export function puntuar(h: Buscable, consulta: string): number {
  const q = normalizar(consulta)
  if (!q) return 1
  const titulo = normalizar(h.titulo)
  const palabras = h.palabras.map(normalizar)
  const todo = [titulo, normalizar(h.descripcion), normalizar(h.categoria), h.id, ...palabras].join(' · ')
  const terminos = q.split(/\s+/).filter(Boolean)
  if (!terminos.every((t) => todo.includes(t))) return 0
  let p = 1
  if (titulo === q) p += 100
  if (titulo.startsWith(q)) p += 40
  if (palabras.some((w) => w === q)) p += 30
  if (titulo.includes(q)) p += 20
  if (palabras.some((w) => w.includes(q))) p += 10
  return p
}

export function buscar<T extends Buscable>(lista: T[], consulta: string): T[] {
  return lista
    .map((h, i) => ({ h, p: puntuar(h, consulta), i }))
    .filter((x) => x.p > 0)
    .sort((a, b) => b.p - a.p || a.i - b.i)
    .map((x) => x.h)
}
