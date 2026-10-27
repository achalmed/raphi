/**
 * Los trabajos: lo que corre, lo que terminó y su resultado. Mientras haya alguno en marcha, la lista se pone al día
 * sola; uno se abre con su panel (salidas, descargar, seguir con…). `/raphi/trabajos/:id` abre uno directo (el enlace
 * de la campana).
 */
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import ButtonBase from '@mui/material/ButtonBase'
import Chip from '@mui/material/Chip'
import LinearProgress from '@mui/material/LinearProgress'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { EstadoVacio, Marco } from '@qillqa/tiqsi'
import PanelTrabajo, { ESTADO } from '../componentes/PanelTrabajo'
import { OPCIONES } from '../modulo'
import { TERMINADOS, trabajos as pedirTrabajos, type Trabajo } from '../lib/api'

const hora = (iso: string | null) => (iso ? new Date(iso).toLocaleString('es-PE', { dateStyle: 'short', timeStyle: 'short' }) : '')

export default function Trabajos() {
  const { id } = useParams()
  const navegar = useNavigate()
  const [lista, setLista] = useState<Trabajo[] | null>(null)
  const [error, setError] = useState('')
  const [abierto, setAbierto] = useState<string | undefined>(id)

  useEffect(() => {
    let vivo = true
    let reloj: ReturnType<typeof setTimeout>
    const pedir = async () => {
      try {
        const l = await pedirTrabajos()
        if (!vivo) return
        setLista(l)
        if (l.some((t) => !TERMINADOS.has(t.estado))) reloj = setTimeout(pedir, 2000)
      } catch (e) { if (vivo) setError((e as Error).message) }
    }
    pedir()
    return () => { vivo = false; clearTimeout(reloj) }
  }, [])
  useEffect(() => setAbierto(id), [id])

  return (
    <Marco modulo="raphi" titulo="Trabajos" opciones={OPCIONES('/raphi/trabajos', navegar)}>
      <Stack spacing={1.25} sx={{ maxWidth: 960, mx: 'auto', p: { xs: 1, sm: 2 } }}>
        {error && <Alert severity="error">{error}</Alert>}
        {!lista && !error && <LinearProgress />}
        {lista && !lista.length && <EstadoVacio titulo="Todavía no hay trabajos" texto="Lo que haga en Raphi aparece aquí con su resultado (se guarda un día)." />}
        {lista?.map((t) => (abierto === t.id
          ? <PanelTrabajo key={t.id} trabajo={t} />
          : (
            <ButtonBase key={t.id} onClick={() => setAbierto(t.id)} sx={{ display: 'block', textAlign: 'left', borderRadius: 2 }}>
              <Stack direction="row" spacing={1.5} alignItems="center" sx={{ p: 1.5, border: 1, borderColor: 'divider', borderRadius: 2 }}>
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography noWrap sx={{ fontWeight: 500 }}>{t.titulo}{t.simular ? ' (simulación)' : ''}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {hora(t.creado_en)} · {t.archivos.length} archivo(s){t.mensaje ? ` · ${t.mensaje}` : ''}
                  </Typography>
                  {!TERMINADOS.has(t.estado) && <LinearProgress variant="determinate" value={t.progreso * 100} sx={{ mt: 0.5 }} />}
                </Box>
                <Chip size="small" label={ESTADO[t.estado].texto} color={ESTADO[t.estado].color} />
              </Stack>
            </ButtonBase>
          )))}
      </Stack>
    </Marco>
  )
}
