/**
 * Elegir los archivos de una operación: soltarlos, elegirlos del equipo (se suben) o, en el escritorio, del disco por su
 * ruta (no se copian). La lista se puede ordenar (en «Unir» o «Imágenes a PDF» el orden es el del resultado).
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import IconButton from '@mui/material/IconButton'
import LinearProgress from '@mui/material/LinearProgress'
import Stack from '@mui/material/Stack'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward'
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward'
import CloseIcon from '@mui/icons-material/Close'
import FolderOpenOutlinedIcon from '@mui/icons-material/FolderOpenOutlined'
import UploadFileOutlinedIcon from '@mui/icons-material/UploadFileOutlined'
import InsertDriveFileOutlinedIcon from '@mui/icons-material/InsertDriveFileOutlined'
import { PALETA } from '@qillqa/tiqsi'
import { locales, subir, tamano, type Archivo } from '../lib/api'
import { EVENTO_RUTAS, hayEscritorio, puente } from '../lib/escritorio'

export interface PropsElegir {
  archivos: Archivo[]
  alCambiar: (a: Archivo[]) => void
  /** Extensiones admitidas («.pdf»); vacío = todo. */
  extensiones?: string[]
  multiple?: boolean
  ordenable?: boolean
  texto?: string
}

/** La zona para soltar: también recibe las rutas que el escritorio entrega (soltadas sobre su ventana o su bandeja). */
export function ZonaSoltar({ alSoltar, alSoltarRutas, children, activa = true }: {
  alSoltar: (f: File[]) => void
  alSoltarRutas?: (rutas: string[]) => void
  children: React.ReactNode
  activa?: boolean
}) {
  const [encima, setEncima] = useState(false)
  useEffect(() => {
    if (!alSoltarRutas || !activa) return
    // preventDefault: le dice al escritorio que esta pantalla los tomó (si nadie lo hace, abre Herramientas).
    const oir = (e: Event) => { e.preventDefault(); alSoltarRutas((e as CustomEvent<string[]>).detail) }
    window.addEventListener(EVENTO_RUTAS, oir)
    return () => window.removeEventListener(EVENTO_RUTAS, oir)
  }, [alSoltarRutas, activa])
  return (
    <Box
      onDragOver={(e) => { if (!activa) return; e.preventDefault(); setEncima(true) }}
      onDragLeave={() => setEncima(false)}
      onDrop={(e) => {
        if (!activa) return
        e.preventDefault()
        setEncima(false)
        const f = Array.from(e.dataTransfer.files)
        if (f.length) alSoltar(f)
      }}
      sx={{
        border: '2px dashed', borderColor: encima ? 'primary.main' : 'divider', borderRadius: 3, p: { xs: 2, sm: 3 },
        bgcolor: encima ? 'action.hover' : 'transparent', transition: 'all .15s', textAlign: 'center',
      }}
    >
      {children}
    </Box>
  )
}

export default function ElegirArchivos({ archivos, alCambiar, extensiones = [], multiple = true, ordenable = false, texto }: PropsElegir) {
  const entrada = useRef<HTMLInputElement>(null)
  const [subiendo, setSubiendo] = useState(false)
  const [error, setError] = useState('')
  const sirve = (nombre: string) => !extensiones.length || extensiones.includes(nombre.toLowerCase().slice(nombre.lastIndexOf('.')))

  const agregar = useCallback((nuevos: Archivo[]) => {
    alCambiar(multiple ? [...archivos, ...nuevos] : nuevos.slice(0, 1))
  }, [archivos, alCambiar, multiple])

  const desdeEquipo = async (lista: File[]) => {
    const validos = lista.filter((f) => sirve(f.name))
    setError(validos.length < lista.length ? `Se dejaron fuera ${lista.length - validos.length}: esta herramienta acepta ${extensiones.join(', ')}.` : '')
    if (!validos.length) return
    setSubiendo(true)
    try { agregar(await subir(validos)) } catch (e) { setError((e as Error).message) } finally { setSubiendo(false) }
  }

  const desdeRutas = useCallback(async (rutas: string[]) => {
    const validas = rutas.filter(sirve)
    if (!validas.length) return
    try { agregar(await locales(validas)) } catch (e) { setError((e as Error).message) }
  }, [agregar]) // eslint-disable-line react-hooks/exhaustive-deps

  const delDisco = async () => {
    const rutas = await puente()?.elegirArchivos(extensiones.map((e) => `*${e}`).join(' '))
    if (rutas?.length) desdeRutas(rutas)
  }

  const mover = (i: number, d: number) => {
    const j = i + d
    if (j < 0 || j >= archivos.length) return
    const copia = [...archivos]
    ;[copia[i], copia[j]] = [copia[j], copia[i]]
    alCambiar(copia)
  }

  return (
    <Stack spacing={1.5}>
      <ZonaSoltar alSoltar={desdeEquipo} alSoltarRutas={hayEscritorio() ? desdeRutas : undefined}>
        <UploadFileOutlinedIcon sx={{ fontSize: 40, color: 'text.secondary' }} />
        <Typography sx={{ mt: 1 }}>{texto ?? (multiple ? 'Suelte aquí los archivos' : 'Suelte aquí el archivo')}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
          {extensiones.length ? extensiones.join(' · ') : 'cualquier archivo'}
        </Typography>
        <Stack direction="row" spacing={1} justifyContent="center" flexWrap="wrap" useFlexGap>
          <Button variant="contained" startIcon={<UploadFileOutlinedIcon />} onClick={() => entrada.current?.click()} disabled={subiendo}>
            Elegir del equipo
          </Button>
          {hayEscritorio() && (
            <Button variant="outlined" startIcon={<FolderOpenOutlinedIcon />} onClick={delDisco}>Del disco, sin copiar</Button>
          )}
        </Stack>
        <input ref={entrada} type="file" hidden multiple={multiple} accept={extensiones.join(',') || undefined}
          onChange={(e) => { desdeEquipo(Array.from(e.target.files ?? [])); e.target.value = '' }} />
      </ZonaSoltar>
      {subiendo && <LinearProgress />}
      {error && <Typography color="error" variant="body2">{error}</Typography>}
      {archivos.length > 0 && (
        <Stack spacing={0.5}>
          {archivos.map((a, i) => (
            <Stack key={`${a.id}-${i}`} direction="row" alignItems="center" spacing={1}
              sx={{ px: 1.5, py: 0.75, borderRadius: 2, bgcolor: PALETA.superficie ?? 'action.hover' }}>
              <InsertDriveFileOutlinedIcon fontSize="small" color="action" />
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography noWrap title={a.ruta ?? a.nombre}>{a.nombre}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {tamano(a.bytes)}{a.paginas ? ` · ${a.paginas} pág.` : ''}{a.local ? ' · en el disco' : ''}
                </Typography>
              </Box>
              {ordenable && archivos.length > 1 && (
                <>
                  <Tooltip title="Subir"><span><IconButton size="small" disabled={i === 0} onClick={() => mover(i, -1)}><ArrowUpwardIcon fontSize="small" /></IconButton></span></Tooltip>
                  <Tooltip title="Bajar"><span><IconButton size="small" disabled={i === archivos.length - 1} onClick={() => mover(i, 1)}><ArrowDownwardIcon fontSize="small" /></IconButton></span></Tooltip>
                </>
              )}
              <Tooltip title="Quitar de la lista"><IconButton size="small" onClick={() => alCambiar(archivos.filter((_, j) => j !== i))}><CloseIcon fontSize="small" /></IconButton></Tooltip>
            </Stack>
          ))}
        </Stack>
      )}
    </Stack>
  )
}
