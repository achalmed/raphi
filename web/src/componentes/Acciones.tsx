/**
 * «Raphi ▸» junto a un archivo de otro módulo: la pieza «raphi.Acciones» (propuesta-raphi.md §4.2). Abre el mismo menú
 * que soltar el archivo en Raphi (a qué se convierte y qué herramientas le sirven). El módulo que la pinta le pasa cómo
 * traer el archivo (`archivo`) y, si quiere, cómo guardar el resultado (`guardar`, por su propia API): Raphi nunca
 * escribe en la carpeta ni en la base de otro. Si Raphi no está montada, el anfitrión no tiene la pieza y no aparece.
 */
import { useState } from 'react'
import { useNavigate } from 'react-router'
import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import Divider from '@mui/material/Divider'
import IconButton from '@mui/material/IconButton'
import ListSubheader from '@mui/material/ListSubheader'
import Menu from '@mui/material/Menu'
import MenuItem from '@mui/material/MenuItem'
import Tooltip from '@mui/material/Tooltip'
import AutoFixHighOutlinedIcon from '@mui/icons-material/AutoFixHighOutlined'
import SaveAltOutlinedIcon from '@mui/icons-material/SaveAltOutlined'
import CheckIcon from '@mui/icons-material/Check'
import { avisar, descargarBlob } from '@qillqa/tiqsi'
import { BASE, crearTrabajo, formatos, subir, type Archivo, type Formato, type Salida, type Trabajo } from '../lib/api'
import PanelTrabajo from './PanelTrabajo'

export interface PropsAcciones {
  /** El nombre del archivo, con su extensión: de ella sale el menú. */
  nombre: string
  /** Trae el archivo del módulo que pinta la pieza (se llama al abrir el menú, no antes). */
  archivo: () => Promise<Blob>
  /** Guarda un resultado en ese módulo (adjuntarlo al recibido, al comprobante…); sin ella, solo se descarga. Si falla,
   *  lanza un error con el motivo; si sale bien, el botón queda en «Guardado» y el aviso, si quiere darlo, es del módulo. */
  guardar?: (resultado: Blob, nombre: string) => Promise<void>
  /** El texto del botón de guardar («Adjuntar al recibido»). */
  etiquetaGuardar?: string
  /** Operaciones que van primero y corren sin formulario (por id: «ocr», «sello», «comprimir»). */
  sugeridas?: string[]
  /** Un botón con texto o solo el icono (en una fila apretada). */
  variante?: 'boton' | 'icono'
  /** El color del botón cuando el módulo lo pinta sobre un fondo propio (el visor oscuro de la Mediateca). */
  color?: string
}

export default function Acciones({ nombre, archivo, guardar, etiquetaGuardar = 'Guardar aquí', sugeridas = [], variante = 'boton', color }: PropsAcciones) {
  const navegar = useNavigate()
  const [ancla, setAncla] = useState<HTMLElement | null>(null)
  const [subido, setSubido] = useState<Archivo | null>(null)
  const [lista, setLista] = useState<Formato[] | null>(null)
  const [error, setError] = useState('')
  const [trabajo, setTrabajo] = useState<Trabajo | null>(null)
  const [guardando, setGuardando] = useState<number | null>(null)
  const [guardadas, setGuardadas] = useState<Set<string>>(new Set())

  // Se sube una sola vez por pieza: abrir el menú de nuevo reusa el mismo archivo de Raphi.
  const abrir = async (e: React.MouseEvent<HTMLElement>) => {
    setAncla(e.currentTarget)
    if (subido && lista) return
    setError('')
    try {
      const blob = await archivo()
      const [a] = await subir([new File([blob], nombre, { type: blob.type })])
      setSubido(a)
      setLista(await formatos(nombre))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Raphi no pudo leer el archivo.')
    }
  }
  const correr = async (f: Formato) => {
    setAncla(null)
    try { setTrabajo(await crearTrabajo({ operacion: f.operacion, archivos: [subido!.id], params: f.params })) }
    catch (err) { await avisar(err instanceof Error ? err.message : 'No se pudo empezar.') }
  }
  const herramienta = (f: Formato) => { setAncla(null); navegar(`/raphi/h/${f.operacion}?archivos=${subido!.id}`) }
  const guardarSalida = async (t: Trabajo, s: Salida) => {
    setGuardando(s.n)
    try {
      await guardar!(await descargarBlob(`${BASE}/trabajos/${t.id}/salidas/${s.n}`), s.nombre)
      setGuardadas((g) => new Set(g).add(`${t.id}/${s.n}`))
    } catch (err) {
      await avisar(err instanceof Error ? err.message : 'No se pudo guardar.')
    } finally { setGuardando(null) }
  }

  const primero = (lista ?? []).filter((f) => sugeridas.includes(f.operacion))
  // Una sugerida con varios destinos (convertir_imagen: JPG, PNG…) lleva el formato en su texto.
  const varias = new Set(primero.map((f) => f.operacion).filter((op, i, todas) => todas.indexOf(op) !== i))
  const conversiones = (lista ?? []).filter((f) => f.a && !sugeridas.includes(f.operacion))
  const herramientas = (lista ?? []).filter((f) => !f.a && !sugeridas.includes(f.operacion))
  const titulo = 'Convertir, comprimir y más con Raphi'
  return (
    <>
      {variante === 'icono'
        ? <Tooltip title={titulo}><IconButton size="small" onClick={abrir} aria-label={titulo} sx={color ? { color } : undefined}><AutoFixHighOutlinedIcon fontSize="small" /></IconButton></Tooltip>
        : <Button size="small" startIcon={<AutoFixHighOutlinedIcon />} onClick={abrir} title={titulo} sx={color ? { color } : undefined}>Raphi ▸</Button>}
      <Menu anchorEl={ancla} open={Boolean(ancla)} onClose={() => setAncla(null)} PaperProps={{ sx: { maxHeight: 460, minWidth: 220 } }}>
        {error && <Alert severity="error" sx={{ m: 1 }}>{error}</Alert>}
        {!error && !lista && <MenuItem disabled><CircularProgress size={18} sx={{ mr: 1 }} /> Preparando…</MenuItem>}
        {primero.map((f) => <MenuItem key={`s-${f.operacion}-${f.a}`} onClick={() => correr(f)}>{varias.has(f.operacion) && f.a ? `${f.titulo}: ${f.a.toUpperCase()}` : f.titulo}</MenuItem>)}
        {primero.length > 0 && <Divider />}
        {conversiones.length > 0 && <ListSubheader>Convertir a</ListSubheader>}
        {conversiones.map((f) => <MenuItem key={`c-${f.operacion}-${f.a}`} onClick={() => correr(f)}>{f.a!.toUpperCase()}</MenuItem>)}
        {herramientas.length > 0 && <ListSubheader>Herramientas</ListSubheader>}
        {herramientas.map((f) => <MenuItem key={`h-${f.operacion}`} onClick={() => herramienta(f)}>{f.titulo}…</MenuItem>)}
      </Menu>
      <Dialog open={Boolean(trabajo)} onClose={() => setTrabajo(null)} fullWidth maxWidth="sm">
        <DialogContent>
          {trabajo && (
            <PanelTrabajo trabajo={trabajo} extra={guardar && ((t, s) => !s.carpeta && (guardadas.has(`${t.id}/${s.n}`)
              ? <Button size="small" startIcon={<CheckIcon />} disabled>Guardado</Button>
              : <Button size="small" startIcon={guardando === s.n ? <CircularProgress size={14} /> : <SaveAltOutlinedIcon />}
                  disabled={guardando !== null} onClick={() => guardarSalida(t, s)}>{etiquetaGuardar}</Button>
            ))} />
          )}
        </DialogContent>
        <DialogActions><Button onClick={() => setTrabajo(null)}>Cerrar</Button></DialogActions>
      </Dialog>
    </>
  )
}
