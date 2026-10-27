/**
 * Un trabajo mientras avanza y cuando termina: avance, lo que pasó con cada archivo (o lo que haría, al simular), las
 * salidas para descargar (o abrir, en el escritorio) y «Seguir con…»: una salida pasa a ser la entrada de otra
 * herramienta sin descargarla ni volver a subirla. `extra` añade un botón por salida (la pieza «raphi.Acciones» pone
 * ahí el de guardar en el módulo que la pinta).
 */
import { useEffect, useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import LinearProgress from '@mui/material/LinearProgress'
import Menu from '@mui/material/Menu'
import MenuItem from '@mui/material/MenuItem'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline'
import DownloadOutlinedIcon from '@mui/icons-material/DownloadOutlined'
import FolderOpenOutlinedIcon from '@mui/icons-material/FolderOpenOutlined'
import ArrowForwardIcon from '@mui/icons-material/ArrowForward'
import { PALETA } from '@qillqa/tiqsi'
import { cancelar, cargarCatalogo, descargarSalida, descargarTodo, salidaComoArchivo, seguir, tamano, TERMINADOS,
  type Operacion, type Salida, type Trabajo } from '../lib/api'
import { hayEscritorio, puente } from '../lib/escritorio'

export const ESTADO: Record<Trabajo['estado'], { texto: string; color: 'default' | 'info' | 'success' | 'warning' | 'error' }> = {
  pendiente: { texto: 'En cola', color: 'default' },
  en_curso: { texto: 'Trabajando', color: 'info' },
  hecho: { texto: 'Listo', color: 'success' },
  parcial: { texto: 'Con errores', color: 'warning' },
  fallido: { texto: 'Falló', color: 'error' },
  cancelado: { texto: 'Cancelado', color: 'default' },
}

/** Sigue un trabajo hasta que termine (preguntando a la API) y devuelve su última foto. */
export function useTrabajo(inicial: Trabajo | null): Trabajo | null {
  const [t, setT] = useState(inicial)
  useEffect(() => {
    setT(inicial)
    if (!inicial || TERMINADOS.has(inicial.estado)) return
    let vivo = true
    seguir(inicial.id, (x) => vivo && setT(x), () => !vivo).catch(() => undefined)
    return () => { vivo = false }
  }, [inicial?.id]) // eslint-disable-line react-hooks/exhaustive-deps
  return t
}

function SeguirCon({ trabajo, salida }: { trabajo: Trabajo; salida: Salida }) {
  const navegar = useNavigate()
  const [ancla, setAncla] = useState<HTMLElement | null>(null)
  const [ops, setOps] = useState<Operacion[]>([])
  useEffect(() => { if (ancla && !ops.length) cargarCatalogo().then((c) => setOps(c.operaciones)) }, [ancla, ops.length])
  const ext = salida.nombre.toLowerCase().slice(salida.nombre.lastIndexOf('.'))
  const sirven = ops.filter((o) => !o.faltan.length && o.minimo_entradas > 0 && (!o.extensiones.length || o.extensiones.includes(ext)))
  const ir = async (op: Operacion) => {
    setAncla(null)
    const a = await salidaComoArchivo(trabajo.id, salida.n)
    navegar(`/raphi/h/${op.id}?archivos=${a.id}`)
  }
  if (salida.carpeta) return null
  return (
    <>
      <Button size="small" endIcon={<ArrowForwardIcon />} onClick={(e) => setAncla(e.currentTarget)}>Seguir con…</Button>
      <Menu anchorEl={ancla} open={Boolean(ancla)} onClose={() => setAncla(null)} PaperProps={{ sx: { maxHeight: 420 } }}>
        {sirven.map((o) => <MenuItem key={o.id} onClick={() => ir(o)}>{o.titulo}</MenuItem>)}
      </Menu>
    </>
  )
}

export default function PanelTrabajo({ trabajo: inicial, extra }: { trabajo: Trabajo; extra?: (t: Trabajo, s: Salida) => ReactNode }) {
  const t = useTrabajo(inicial) ?? inicial
  const terminado = TERMINADOS.has(t.estado)
  const estado = ESTADO[t.estado]
  const elementos = t.informe?.elementos ?? []
  return (
    <Box sx={{ p: 2, borderRadius: 3, bgcolor: PALETA.superficie ?? 'background.paper', border: 1, borderColor: 'divider' }}>
      <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600, flex: 1 }}>{t.titulo}{t.simular ? ' (simulación)' : ''}</Typography>
        <Chip size="small" label={estado.texto} color={estado.color} />
        {!terminado && <Button size="small" onClick={() => cancelar(t.id)}>Cancelar</Button>}
      </Stack>
      {!terminado && (
        <>
          <LinearProgress variant={t.estado === 'pendiente' ? 'indeterminate' : 'determinate'} value={Math.round(t.progreso * 100)} />
          <Typography variant="caption" color="text.secondary">{t.estado === 'pendiente' ? 'Esperando turno…' : `${Math.round(t.progreso * 100)} % ${t.mensaje}`}</Typography>
        </>
      )}
      {terminado && t.estado === 'fallido' && !elementos.length && <Alert severity="error">{t.mensaje}</Alert>}
      {elementos.length > 0 && (
        <Stack spacing={0.75} sx={{ mt: 1 }}>
          {elementos.map((e, i) => (
            <Stack key={i} direction="row" spacing={1} alignItems="flex-start">
              {e.ok ? <CheckCircleOutlineIcon color="success" fontSize="small" /> : <ErrorOutlineIcon color="error" fontSize="small" />}
              <Box sx={{ minWidth: 0 }}>
                <Typography variant="body2" noWrap title={e.entrada}>{e.entrada.split('/').pop()}</Typography>
                {e.error && <Typography variant="body2" color="error">{e.error}</Typography>}
                {[...(e.plan ?? []), ...(e.mensajes ?? [])].map((m, j) => (
                  <Typography key={j} variant="caption" color="text.secondary" component="div">{m}</Typography>
                ))}
              </Box>
            </Stack>
          ))}
        </Stack>
      )}
      {t.salidas.length > 0 && (
        <Stack spacing={0.5} sx={{ mt: 1.5 }}>
          {t.salidas.map((s) => (
            <Stack key={s.n} direction="row" alignItems="center" spacing={1} flexWrap="wrap" useFlexGap
              sx={{ px: 1.5, py: 0.5, borderRadius: 2, bgcolor: 'action.hover' }}>
              <Typography sx={{ flex: 1, minWidth: 140 }} noWrap title={s.ruta ?? s.nombre}>
                {s.nombre}{s.carpeta ? '/' : ''} <Typography component="span" variant="caption" color="text.secondary">{tamano(s.bytes)}</Typography>
              </Typography>
              {hayEscritorio() && s.ruta
                ? <Button size="small" startIcon={<FolderOpenOutlinedIcon />} onClick={() => puente()?.abrirCarpeta(s.ruta!)}>Mostrar</Button>
                : <Button size="small" startIcon={<DownloadOutlinedIcon />} onClick={() => descargarSalida(t, s)}>Descargar</Button>}
              {extra?.(t, s)}
              <SeguirCon trabajo={t} salida={s} />
            </Stack>
          ))}
          {t.salidas.length > 1 && !hayEscritorio() && (
            <Box><Button size="small" variant="outlined" startIcon={<DownloadOutlinedIcon />} onClick={() => descargarTodo(t)}>Descargar todo (zip)</Button></Box>
          )}
        </Stack>
      )}
    </Box>
  )
}
