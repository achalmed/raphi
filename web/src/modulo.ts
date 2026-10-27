/**
 * El módulo web de Raphi: sus pantallas, sus rutas y cómo entra al menú del anfitrión. Qillqa arma con esto su entrada
 * de menú y sus rutas; la página sola y el escritorio, su cáscara mínima (src/sola.tsx).
 */
import BuildOutlinedIcon from '@mui/icons-material/BuildOutlined'
import DashboardCustomizeOutlinedIcon from '@mui/icons-material/DashboardCustomizeOutlined'
import HistoryOutlinedIcon from '@mui/icons-material/HistoryOutlined'
import MenuBookOutlinedIcon from '@mui/icons-material/MenuBookOutlined'
import SettingsOutlinedIcon from '@mui/icons-material/SettingsOutlined'
import AutoFixHighOutlinedIcon from '@mui/icons-material/AutoFixHighOutlined'
import { definirModuloWeb, type OpcionPagina } from '@qillqa/tiqsi'
import { createElement } from 'react'

const MENU = [
  { etiqueta: 'Herramientas', ruta: '/raphi', icono: BuildOutlinedIcon, ayuda: 'Todas las herramientas y soltar un archivo para convertirlo' },
  { etiqueta: 'Mesa de trabajo', ruta: '/raphi/mesa', icono: DashboardCustomizeOutlinedIcon, ayuda: 'Ordenar, girar y combinar páginas de varios PDF' },
  { etiqueta: 'Trabajos', ruta: '/raphi/trabajos', icono: HistoryOutlinedIcon, ayuda: 'Lo que corre y lo que terminó, con sus resultados' },
  { etiqueta: 'Recetas', ruta: '/raphi/recetas', icono: MenuBookOutlinedIcon, ayuda: 'Cadenas de pasos guardadas' },
  { etiqueta: 'Sistema', ruta: '/raphi/sistema', icono: SettingsOutlinedIcon, ayuda: 'Qué hay instalado y, en el escritorio, sus ajustes' },
]

/** Las opciones de página del marco (las mismas pestañas en cada pantalla, la actual marcada). */
export const OPCIONES = (actual: string, navegar: (ruta: string) => void): OpcionPagina[] =>
  MENU.map((m) => ({ clave: m.ruta, etiqueta: m.etiqueta, icono: createElement(m.icono, { fontSize: 'small' }), activa: m.ruta === actual,
                     alPulsar: () => navegar(m.ruta) }))

export const RAPHI = definirModuloWeb({
  id: 'raphi',
  nombre: 'Raphi',
  corto: 'Raphi',
  ruta: '/raphi',
  icono: AutoFixHighOutlinedIcon,
  descripcion: 'PDF, ofimática y conversión de archivos: unir, comprimir, OCR, foliar, sellar, convertir y más.',
  opciones: MENU,
  cargar: () => import('./paginas/Herramientas'),
  pantallas: [
    { ruta: '/raphi/h/:id', cargar: () => import('./paginas/Herramienta') },
    { ruta: '/raphi/mesa', cargar: () => import('./paginas/Mesa') },
    { ruta: '/raphi/trabajos', cargar: () => import('./paginas/Trabajos') },
    { ruta: '/raphi/trabajos/:id', cargar: () => import('./paginas/Trabajos') },
    { ruta: '/raphi/recetas', cargar: () => import('./paginas/Recetas') },
    { ruta: '/raphi/sistema', cargar: () => import('./paginas/Sistema') },
  ],
})
