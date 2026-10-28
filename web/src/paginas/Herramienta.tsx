/**
 * Una herramienta (o una receta): sus archivos, su formulario (generado de la ficha), «Simular» para ver qué haría y
 * «Aplicar». En el escritorio, además, dónde escribir: en la carpeta de Raphi, junto al original o en una elegida.
 */
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import MenuItem from '@mui/material/MenuItem'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import VisibilityOutlinedIcon from '@mui/icons-material/VisibilityOutlined'
import { Marco, api } from '@qillqa/tiqsi'
import ElegirArchivos from '../componentes/Archivos'
import IconoOperacion from '../componentes/Icono'
import Formulario, { cambiados, iniciales, type Valores } from '../componentes/Formulario'
import PanelTrabajo from '../componentes/PanelTrabajo'
import { BASE, cargarCatalogo, crearTrabajo, type Archivo, type Catalogo, type Trabajo } from '../lib/api'
import { hayEscritorio, puente } from '../lib/escritorio'

export default function Herramienta() {
  const { id = '' } = useParams()
  const [consulta] = useSearchParams()
  const navegar = useNavigate()
  const [cat, setCat] = useState<Catalogo | null>(null)
  const [archivos, setArchivos] = useState<Archivo[]>([])
  const [valores, setValores] = useState<Valores>({})
  const [trabajos, setTrabajos] = useState<Trabajo[]>([])
  const [error, setError] = useState('')
  const [destino, setDestino] = useState('')
  const [carpeta, setCarpeta] = useState('')
  const esReceta = id.startsWith('receta:')
  const op = useMemo(() => cat?.operaciones.find((o) => o.id === id), [cat, id])
  const receta = useMemo(() => cat?.recetas.find((r) => `receta:${r.id}` === id), [cat, id])

  useEffect(() => { cargarCatalogo().then(setCat).catch((e) => setError(e.message)) }, [])
  useEffect(() => { if (op) setValores(iniciales(op.parametros)) }, [op])
  useEffect(() => {
    const ids = (consulta.get('archivos') ?? '').split(',').filter(Boolean)
    if (ids.length) Promise.all(ids.map((a) => api<Archivo>(`${BASE}/archivos/${a}`))).then(setArchivos).catch(() => undefined)
  }, [consulta])

  if (cat && !op && !receta) return <Marco modulo="raphi" titulo="Raphi" volver="/raphi"><Alert severity="warning">No hay una herramienta «{id}».</Alert></Marco>
  const titulo = op?.titulo ?? receta?.nombre ?? ''
  const descripcion = op?.descripcion ?? receta?.descripcion ?? ''
  const sinEntradas = op ? op.minimo_entradas === 0 : Boolean(receta?.sin_entradas)
  const faltan = op?.faltan ?? []
  const listo = (sinEntradas || archivos.length >= (op?.minimo_entradas ?? 1)) && !faltan.length

  const correr = async (simular: boolean) => {
    setError('')
    try {
      const t = await crearTrabajo({
        operacion: id, archivos: archivos.map((a) => a.id), simular,
        params: op ? cambiados(op.parametros, valores) : {},
        destino: destino === 'carpeta' ? carpeta : destino,
      })
      setTrabajos([t, ...trabajos])
    } catch (e) { setError((e as Error).message) }
  }

  return (
    <Marco modulo="raphi" titulo={titulo} volver="/raphi">
      <Stack spacing={2.5} sx={{ maxWidth: 860, mx: 'auto', p: { xs: 1, sm: 2 } }}>
        <Stack direction="row" spacing={1.75} alignItems="center">
          {op && <IconoOperacion id={op.id} categoria={op.categoria} tamano={48} />}
          <Typography color="text.secondary" sx={{ maxWidth: '68ch' }}>{descripcion}</Typography>
        </Stack>
        {receta && (
          <Typography variant="body2" color="text.secondary">
            Pasos: {receta.pasos.map((p) => cat?.operaciones.find((o) => o.id === p.operacion)?.titulo ?? p.operacion).join(' → ')}
          </Typography>
        )}
        {faltan.length > 0 && <Alert severity="warning">Esta máquina no tiene {faltan.map((f) => f.replace('py:', '')).join(', ')}.</Alert>}
        {!sinEntradas && (
          <ElegirArchivos archivos={archivos} alCambiar={setArchivos} franja={archivos.length > 0} extensiones={op?.extensiones ?? (esReceta ? [] : [])}
            multiple={op ? op.lote || op.minimo_entradas !== 1 || op.entrada !== 'pdf' : true}
            ordenable={Boolean(op && !op.lote)} />
        )}
        {op && <Formulario parametros={op.parametros} valores={valores} alCambiar={setValores} />}
        {hayEscritorio() && (
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems={{ sm: 'center' }}>
            <TextField select size="small" label="Dónde guardar" value={destino} onChange={(e) => setDestino(e.target.value)} sx={{ minWidth: 260 }}>
              <MenuItem value="">En la carpeta de trabajos de Raphi</MenuItem>
              <MenuItem value="junto" disabled={!archivos.every((a) => a.local)}>Junto a cada original</MenuItem>
              <MenuItem value="carpeta">En una carpeta que elijo…</MenuItem>
            </TextField>
            {destino === 'carpeta' && (
              <Button onClick={async () => setCarpeta((await puente()?.elegirCarpeta()) ?? '')}>{carpeta || 'Elegir carpeta'}</Button>
            )}
          </Stack>
        )}
        {error && <Alert severity="error">{error}</Alert>}
        <Stack direction="row" spacing={1.5}>
          <Button variant="outlined" startIcon={<VisibilityOutlinedIcon />} disabled={!listo} onClick={() => correr(true)}>Simular</Button>
          <Button variant="contained" startIcon={<PlayArrowIcon />} disabled={!listo || (destino === 'carpeta' && !carpeta)} onClick={() => correr(false)}>
            Aplicar
          </Button>
          <Box sx={{ flex: 1 }} />
          {trabajos.length > 0 && <Button onClick={() => navegar('/raphi/trabajos')}>Ver todos los trabajos</Button>}
        </Stack>
        <Stack spacing={1.5}>{trabajos.map((t) => <PanelTrabajo key={t.id} trabajo={t} />)}</Stack>
      </Stack>
    </Marco>
  )
}
