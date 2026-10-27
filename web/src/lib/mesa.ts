/**
 * La lógica de la mesa de trabajo, sin React: las hojas (una página de un archivo, girada o no, o una en blanco) y las
 * acciones sobre ellas, con su deshacer. La prueban web/pruebas/mesa.test.ts.
 */
export interface Hoja {
  clave: string
  archivo?: string
  pagina?: number
  rotar: number
  blanca?: boolean
}

export interface Mesa {
  hojas: Hoja[]
  historia: Hoja[][]
}

export type Accion =
  | { tipo: 'mover'; desde: number; hasta: number }
  | { tipo: 'rotar'; claves: string[]; grados: number }
  | { tipo: 'quitar'; claves: string[] }
  | { tipo: 'duplicar'; claves: string[] }
  | { tipo: 'blanca'; despues: string }
  | { tipo: 'invertir' }

let contador = 0
const nueva = () => `h${++contador}`

/** Las hojas de los archivos que hay: conserva el orden y los cambios de los que ya estaban; suma al final las
 *  páginas de los nuevos; quita las de los que se fueron. */
export function inicialDe(archivos: { id: string; paginas?: number | null }[], m: Mesa): Mesa {
  const ids = new Set(archivos.map((a) => a.id))
  const quedan = m.hojas.filter((h) => h.blanca || ids.has(h.archivo!))
  const ya = new Set(quedan.map((h) => h.archivo))
  const nuevas: Hoja[] = []
  for (const a of archivos) {
    if (ya.has(a.id)) continue
    for (let p = 1; p <= (a.paginas ?? 0); p++) nuevas.push({ clave: nueva(), archivo: a.id, pagina: p, rotar: 0 })
  }
  if (!nuevas.length && quedan.length === m.hojas.length) return m
  return { hojas: [...quedan, ...nuevas], historia: m.historia }
}

export function aplicar(m: Mesa, a: Accion): Mesa {
  const h = [...m.hojas]
  const en = (claves: string[]) => new Set(claves)
  switch (a.tipo) {
    case 'mover': {
      if (a.desde === a.hasta || a.desde < 0 || a.desde >= h.length) return m
      const [x] = h.splice(a.desde, 1)
      h.splice(Math.min(a.hasta, h.length), 0, x)
      break
    }
    case 'rotar': {
      const s = en(a.claves)
      for (let i = 0; i < h.length; i++) if (s.has(h[i].clave)) h[i] = { ...h[i], rotar: (((h[i].rotar + a.grados) % 360) + 360) % 360 }
      break
    }
    case 'quitar': {
      const s = en(a.claves)
      const resto = h.filter((x) => !s.has(x.clave))
      if (resto.length === h.length) return m
      return { hojas: resto, historia: [...m.historia, m.hojas] }
    }
    case 'duplicar': {
      const s = en(a.claves)
      const salida: Hoja[] = []
      for (const x of h) {
        salida.push(x)
        if (s.has(x.clave)) salida.push({ ...x, clave: nueva() })
      }
      return { hojas: salida, historia: [...m.historia, m.hojas] }
    }
    case 'blanca': {
      const i = h.findIndex((x) => x.clave === a.despues)
      h.splice(i + 1, 0, { clave: nueva(), rotar: 0, blanca: true })
      break
    }
    case 'invertir':
      h.reverse()
      break
  }
  return { hojas: h, historia: [...m.historia, m.hojas].slice(-50) }
}

export const deshacer = (m: Mesa): Mesa =>
  m.historia.length ? { hojas: m.historia[m.historia.length - 1], historia: m.historia.slice(0, -1) } : m
