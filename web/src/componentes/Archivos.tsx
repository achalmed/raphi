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
  /** Qué se puede soltar, dicho para la persona (sin él, las extensiones admitidas). */
  ayuda?: string
  /** En una franja (ícono, texto y botones en fila), para cuando la zona encabeza una página. */
  franja?: boolean
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
        border: '1.5px dashed', borderColor: encima ? (PALETA.acento ?? 'primary.main') : (PALETA.bordeFuerte ?? 'divider'),
        borderRadius: '18px', p: { xs: 2.5, sm: 4 }, textAlign: 'center',
        bgcolor: encima ? (PALETA.focoVelo ?? 'action.hover') : (PALETA.superficie ?? 'background.paper'),
        transition: 'border-color .15s ease, background-color .15s ease',
      }}
    >
      {children}
    </Box>
  )
}

export default function ElegirArchivos({ archivos, alCambiar, extensiones = [], multiple = true, ordenable = false, texto, ayuda, franja = false }: PropsElegir) {
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
        <Stack direction={franja ? { xs: 'column', sm: 'row' } : 'column'} alignItems="center" spacing={franja ? 2 : 0}
          sx={{ textAlign: franja ? { xs: 'center', sm: 'left' } : 'center' }}>
        <Box sx={{ width: 56, height: 56, flexShrink: 0, borderRadius: '50%', display: 'grid', placeItems: 'center',
                   bgcolor: PALETA.velo ?? 'action.hover', color: PALETA.acento ?? 'primary.main' }}>
          <UploadFileOutlinedIcon sx={{ fontSize: 28 }} />
        </Box>
        <Box sx={{ flex: franja ? 1 : undefined, minWidth: 0, mt: franja ? 0 : 1.5 }}>
          <Typography sx={{ fontWeight: 600, fontSize: 16 }}>{texto ?? (multiple ? 'Suelte aquí los archivos' : 'Suelte aquí el archivo')}</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: franja ? 0 : 1.5 }}>
            {ayuda ?? (extensiones.length ? `Acepta ${extensiones.map((e) => e.slice(1).toUpperCase()).join(', ')}` : 'Acepta cualquier archivo')}
          </Typography>
        </Box>
        <Stack direction="row" spacing={1} justifyContent="center" flexWrap="wrap" useFlexGap sx={{ flexShrink: 0 }}>
          <Button variant="contained" startIcon={<UploadFileOutlinedIcon />} onClick={() => entrada.current?.click()} disabled={subiendo}>
            Elegir del equipo
          </Button>
          {hayEscritorio() && (
            <Button variant="outlined" startIcon={<FolderOpenOutlinedIcon />} onClick={delDisco}>Del disco, sin copiar</Button>
          )}
        </Stack>
        <input ref={entrada} type="file" hidden multiple={multiple} accept={extensiones.join(',') || undefined}
          onChange={(e) => { desdeEquipo(Array.from(e.target.files ?? [])); e.target.value = '' }} />
        </Stack>
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
