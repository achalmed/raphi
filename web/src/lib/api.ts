/**
 * Lo que la web de Raphi sabe de su API (`/api/raphi`): los tipos y las llamadas. Todo pasa por `api` y `subirArchivo`
 * del anfitrión (Tiqsi web), que ponen la sesión: la misma web sirve en Qillqa, sola y en el escritorio.
 */
import { api, descargarArchivo, subirArchivo } from '@qillqa/tiqsi'

export const BASE = '/api/raphi'

export interface Parametro {
  clave: string
  etiqueta: string
  tipo: 'texto' | 'multilinea' | 'entero' | 'decimal' | 'opcion' | 'casilla' | 'paginas' | 'clave' | 'color' | 'tamano' | 'json'
  defecto: unknown
  opciones: [string, string][]
  minimo: number | null
  maximo: number | null
  ayuda: string
  obligatorio: boolean
}

export interface Operacion {
  id: string
  categoria: string
  titulo: string
  descripcion: string
  entrada: 'pdf' | 'pdfs' | 'documentos' | 'imagenes' | 'medios' | 'archivos' | 'ninguna'
  lote: boolean
  parametros: Parametro[]
  requiere: string[]
  faltan: string[]
  extensiones: string[]
  minimo_entradas: number
  palabras: string[]
}

export interface Receta {
  id: string
  nombre: string
  descripcion: string
  sin_entradas: boolean
  origen: 'serie' | 'usuario'
  pasos: { operacion: string; params: Record<string, unknown> }[]
}

export interface Catalogo {
  operaciones: Operacion[]
  categorias: string[]
  fuentes: string[]
  modo: 'modulo' | 'sola' | 'escritorio'
  recetas: Receta[]
}

export interface Archivo {
  id: string
  nombre: string
  bytes: number
  local: boolean
  tipo: string
  paginas?: number | null
  ruta?: string
}

export interface Salida {
  n: number
  nombre: string
  bytes: number | null
  carpeta: boolean
  ruta: string | null
}

export interface ElementoInforme {
  entrada: string
  ok: boolean
  error: string
  segundos: number
  archivos?: string[]
  datos?: Record<string, unknown>
  mensajes?: string[]
  plan?: string[]
  sin_cambio?: boolean
}

export interface Trabajo {
  id: string
  operacion: string
  titulo: string
  params: Record<string, unknown>
  archivos: string[]
  simular: boolean
  estado: 'pendiente' | 'en_curso' | 'hecho' | 'parcial' | 'fallido' | 'cancelado'
  progreso: number
  mensaje: string
  informe: { ok: boolean; correctos: number; fallidos: number; elementos: ElementoInforme[] } | null
  salidas: Salida[]
  creado_en: string | null
  terminado_en: string | null
}

export interface Formato {
  a: string | null
  operacion: string
  params: Record<string, unknown>
  titulo: string
}

export interface Sistema {
  version: string
  modo: string
  concurrencia: number
  retencion_horas: number
  tope_subida_mb: number
  requisitos: { nombre: string; python: boolean; ok: boolean; usan: string[] }[]
  no_disponibles: string[]
  carpeta: string | null
}

export const TERMINADOS = new Set(['hecho', 'parcial', 'fallido', 'cancelado'])

let catalogo: Promise<Catalogo> | null = null

/** El catálogo se pide una vez por página (las operaciones no cambian sin reiniciar el servidor). */
export function cargarCatalogo(refrescar = false): Promise<Catalogo> {
  if (!catalogo || refrescar) catalogo = api<Catalogo>(`${BASE}/operaciones`).catch((e) => { catalogo = null; throw e })
  return catalogo
}

export async function subir(archivos: File[]): Promise<Archivo[]> {
  const datos = new FormData()
  for (const a of archivos) datos.append('archivos', a, a.name)
  return subirArchivo<Archivo[]>(`${BASE}/archivos`, datos)
}

export const locales = (rutas: string[]) =>
  api<Archivo[]>(`${BASE}/locales`, { method: 'POST', body: JSON.stringify({ rutas }) })

export const crearTrabajo = (p: { operacion: string; archivos: string[]; params?: Record<string, unknown>; simular?: boolean; destino?: string }) =>
  api<Trabajo>(`${BASE}/trabajos`, { method: 'POST', body: JSON.stringify({ params: {}, simular: false, destino: '', ...p }) })

export const trabajo = (id: string) => api<Trabajo>(`${BASE}/trabajos/${id}`)
export const trabajos = () => api<Trabajo[]>(`${BASE}/trabajos`)
export const cancelar = (id: string) => api<{ cancelado: boolean }>(`${BASE}/trabajos/${id}/cancelar`, { method: 'POST' })
export const salidaComoArchivo = (id: string, n: number) => api<Archivo>(`${BASE}/trabajos/${id}/salidas/${n}/a-archivo`, { method: 'POST' })
export const formatos = (nombre: string) => api<Formato[]>(`${BASE}/formatos?nombre=${encodeURIComponent(nombre)}`)
export const sistema = () => api<Sistema>(`${BASE}/sistema`)
export const recetas = () => api<Receta[]>(`${BASE}/recetas`)
export const guardarReceta = (r: Omit<Receta, 'origen' | 'sin_entradas'>) =>
  api<Receta>(`${BASE}/recetas`, { method: 'POST', body: JSON.stringify(r) })
export const borrarReceta = (id: string) => api<unknown>(`${BASE}/recetas/${id}`, { method: 'DELETE' })

export const descargarSalida = (t: Trabajo, s: Salida) =>
  descargarArchivo(`${BASE}/trabajos/${t.id}/salidas/${s.n}`, s.carpeta ? `${s.nombre}.zip` : s.nombre)
export const descargarTodo = (t: Trabajo) => descargarArchivo(`${BASE}/trabajos/${t.id}/zip`, `raphi-${t.id.slice(0, 8)}.zip`)
export const urlMiniatura = (archivo: string, pagina: number, ancho = 220) =>
  `${BASE}/archivos/${archivo}/miniatura?pagina=${pagina}&ancho=${ancho}`
export const urlContenido = (archivo: string) => `${BASE}/archivos/${archivo}/contenido`

/** Espera a que un trabajo termine, avisando de cada avance (un segundo entre preguntas, menos al principio). */
export async function seguir(id: string, alAvanzar: (t: Trabajo) => void, cancelado: () => boolean = () => false): Promise<Trabajo> {
  let espera = 250
  for (;;) {
    const t = await trabajo(id)
    alAvanzar(t)
    if (TERMINADOS.has(t.estado) || cancelado()) return t
    await new Promise((r) => setTimeout(r, espera))
    espera = Math.min(1000, espera * 1.5)
  }
}

export function tamano(bytes: number | null | undefined): string {
  if (bytes == null) return ''
  const u = ['B', 'KB', 'MB', 'GB']
  let n = bytes
  let i = 0
  while (n >= 1024 && i < u.length - 1) { n /= 1024; i++ }
  return i === 0 ? `${n} B` : `${n.toFixed(1).replace('.', ',')} ${u[i]}`
}

/** ¿Este archivo le sirve a esta operación? (por su extensión; las de «archivos» aceptan todo). */
export function admite(op: Operacion, nombre: string): boolean {
  if (!op.extensiones.length) return true
  const ext = nombre.toLowerCase().slice(nombre.lastIndexOf('.'))
  return op.extensiones.includes(ext)
}
