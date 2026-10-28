/**
 * La identidad de cada herramienta, sin React (se prueba con `npm run web:pruebas`): el color de su categoría, lo que
 * dice cada categoría y qué archivos acepta una herramienta, dicho para quien la va a usar. El marco es del anfitrión
 * (neutro); el color vive solo en el ícono de cada herramienta y en lo que pasa al tocarla o al soltarle un archivo.
 */

/** Un tono por categoría: se distinguen de un vistazo y se leen sobre fondo claro y oscuro. */
export const COLOR_CATEGORIA: Record<string, string> = {
  Organizar: '#2F6FDB',
  Optimizar: '#12968A',
  Convertir: '#7552D9',
  Editar: '#D27A1F',
  Seguridad: '#C23D5C',
  'Información': '#56708F',
  Medios: '#C9468F',
  Archivos: '#6E8B2A',
}

export const RESUMEN_CATEGORIA: Record<string, string> = {
  Organizar: 'Juntar, partir y ordenar páginas',
  Optimizar: 'Peso, estructura y conservación',
  Convertir: 'De un formato a otro',
  Editar: 'Marcar, numerar, sellar y anotar',
  Seguridad: 'Claves, firmas y lo que no debe salir',
  'Información': 'Lo que un archivo tiene dentro',
  Medios: 'Fotos, audio, video y subtítulos',
  Archivos: 'Comprimir y extraer carpetas',
}

export const colorDe = (categoria: string): string => COLOR_CATEGORIA[categoria] ?? '#56708F'

/** Un color con transparencia (`#rrggbb` + alfa de 0 a 1), para el fondo del ícono y lo resaltado. */
export function tinte(hex: string, alfa: number): string {
  const a = Math.round(Math.min(1, Math.max(0, alfa)) * 255).toString(16).padStart(2, '0')
  return `${hex}${a}`
}

/** Un tono mezclado con blanco (`cuanto` de 0 a 1): sobre el fondo oscuro, el mismo tono subido de luz para que se lea. */
export function aclarar(hex: string, cuanto: number): string {
  const c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16))
  return `#${c.map((v) => Math.round(v + (255 - v) * cuanto).toString(16).padStart(2, '0')).join('')}`.toUpperCase()
}

/** El tono de una categoría según el modo del anfitrión: en oscuro, más claro. */
export const tonoDe = (categoria: string, oscuro: boolean): string => (oscuro ? aclarar(colorDe(categoria), 0.38) : colorDe(categoria))

/** Dos extensiones del mismo formato se dicen con un solo nombre. */
const MISMO: Record<string, string> = { JPEG: 'JPG', HTM: 'HTML', TIF: 'TIFF', HEIF: 'HEIC' }

interface ConEntrada {
  entrada: string
  extensiones: string[]
  minimo_entradas: number
}

/** Qué acepta una herramienta, en pocas palabras: «PDF», «Dos o más PDF», «JPG, PNG, HEIC…», «Cualquier archivo». */
export function acepta(op: ConEntrada): string {
  if (op.entrada === 'ninguna') return 'Sin archivo: trabaja con una fuente'
  if (!op.extensiones.length) return 'Cualquier archivo'
  const formatos = [...new Set(op.extensiones.map((e) => { const f = e.replace(/^\./, '').toUpperCase(); return MISMO[f] ?? f }))]
  if (formatos.length === 1) return op.minimo_entradas >= 2 ? `Dos o más ${formatos[0]}` : formatos[0]
  return formatos.length <= 4 ? formatos.join(', ') : `${formatos.slice(0, 3).join(', ')} y ${formatos.length - 3} más`
}
