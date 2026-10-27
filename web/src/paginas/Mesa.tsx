/**
 * La mesa de trabajo (como la barra lateral de Vista Previa o PDF Expert): las páginas de varios PDF como miniaturas,
 * que se arrastran para ordenarlas, se giran, se quitan, se duplican o se separan con una página en blanco; al final,
 * «Guardar PDF» arma el documento con la operación «componer» del motor. Nada se escribe hasta guardar.
 */
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Checkbox from '@mui/material/Checkbox'
import IconButton from '@mui/material/IconButton'
import Slider from '@mui/material/Slider'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import RotateLeftIcon from '@mui/icons-material/RotateLeft'
import RotateRightIcon from '@mui/icons-material/RotateRight'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline'
import ContentCopyIcon from '@mui/icons-material/ContentCopy'
import NoteAddOutlinedIcon from '@mui/icons-material/NoteAddOutlined'
import SaveOutlinedIcon from '@mui/icons-material/SaveOutlined'
import UndoIcon from '@mui/icons-material/Undo'
import { Marco, PALETA, api } from '@qillqa/tiqsi'
import ElegirArchivos from '../componentes/Archivos'
import Miniatura from '../componentes/Miniatura'
import PanelTrabajo from '../componentes/PanelTrabajo'
import { OPCIONES } from '../modulo'
import { BASE, crearTrabajo, type Archivo, type Trabajo } from '../lib/api'
import { aplicar, deshacer, inicialDe, type Hoja, type Mesa } from '../lib/mesa'

export default function MesaDeTrabajo() {
  const navegar = useNavigate()
  const [archivos, setArchivos] = useState<Archivo[]>([])
  const [mesa, setMesa] = useState<Mesa>({ hojas: [], historia: [] })
  const [elegidas, setElegidas] = useState<Set<string>>(new Set())
  const [arrastrada, setArrastrada] = useState<number | null>(null)
  const [ancho, setAncho] = useState(140)
  const [nombre, setNombre] = useState('compuesto')
  const [trabajo, setTrabajo] = useState<Trabajo | null>(null)
  const [error, setError] = useState('')

  const [consulta] = useSearchParams()
  useEffect(() => {        // «Seguir con…» y los enlaces de otros módulos llegan con ?archivos=
    const ids = (consulta.get('archivos') ?? '').split(',').filter(Boolean)
    if (ids.length) Promise.all(ids.map((a) => api<Archivo>(`${BASE}/archivos/${a}`))).then(setArchivos).catch(() => undefined)
  }, [consulta])
  // Los archivos nuevos suman sus páginas al final; los quitados se llevan las suyas.
  useEffect(() => { setMesa((m) => inicialDe(archivos, m)) }, [archivos])
  const indice = useMemo(() => new Map(archivos.map((a, i) => [a.id, i])), [archivos])
  const hacer = (accion: Parameters<typeof aplicar>[1]) => setMesa((m) => aplicar(m, accion))
  const sel = (claves: string[]) => (claves.length ? claves : [...elegidas])

  const guardar = async () => {
    setError('')
    const plan = mesa.hojas.map((h: Hoja) => (h.blanca ? { blanca: true } : { archivo: indice.get(h.archivo!)!, pagina: h.pagina, rotar: h.rotar }))
    try {
      setTrabajo(await crearTrabajo({ operacion: 'componer', archivos: archivos.map((a) => a.id), params: { plan, nombre } }))
    } catch (e) { setError((e as Error).message) }
  }

  const BotonesHoja = ({ h }: { h: Hoja }) => (
    <Stack direction="row" justifyContent="center" sx={{ opacity: 0.85 }}>
      <Tooltip title="Girar a la izquierda"><IconButton size="small" onClick={() => hacer({ tipo: 'rotar', claves: [h.clave], grados: -90 })}><RotateLeftIcon fontSize="small" /></IconButton></Tooltip>
      <Tooltip title="Girar a la derecha"><IconButton size="small" onClick={() => hacer({ tipo: 'rotar', claves: [h.clave], grados: 90 })}><RotateRightIcon fontSize="small" /></IconButton></Tooltip>
      <Tooltip title="Duplicar"><IconButton size="small" onClick={() => hacer({ tipo: 'duplicar', claves: [h.clave] })}><ContentCopyIcon fontSize="small" /></IconButton></Tooltip>
      <Tooltip title="Página en blanco después"><IconButton size="small" onClick={() => hacer({ tipo: 'blanca', despues: h.clave })}><NoteAddOutlinedIcon fontSize="small" /></IconButton></Tooltip>
      <Tooltip title="Quitar"><IconButton size="small" onClick={() => hacer({ tipo: 'quitar', claves: [h.clave] })}><DeleteOutlineIcon fontSize="small" /></IconButton></Tooltip>
    </Stack>
  )

  return (
    <Marco titulo="Mesa de trabajo" opciones={OPCIONES('/raphi/mesa', navegar)}>
      <Stack spacing={2} sx={{ p: { xs: 1, sm: 2 } }}>
        <ElegirArchivos archivos={archivos} alCambiar={setArchivos} extensiones={['.pdf']} ordenable
          texto="Suelte uno o varios PDF: sus páginas aparecen abajo para ordenarlas" />
        {mesa.hojas.length > 0 && (
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ md: 'center' }}
            sx={{ position: 'sticky', top: 0, zIndex: 2, py: 1, bgcolor: PALETA.fondo ?? 'background.default' }}>
            <Typography sx={{ fontWeight: 600 }}>{mesa.hojas.length} páginas{elegidas.size ? ` · ${elegidas.size} elegidas` : ''}</Typography>
            <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
              <Button size="small" startIcon={<UndoIcon />} disabled={!mesa.historia.length} onClick={() => setMesa(deshacer)}>Deshacer</Button>
              <Button size="small" disabled={!elegidas.size} onClick={() => hacer({ tipo: 'rotar', claves: sel([]), grados: 90 })}>Girar elegidas</Button>
              <Button size="small" disabled={!elegidas.size} onClick={() => { hacer({ tipo: 'quitar', claves: sel([]) }); setElegidas(new Set()) }}>Quitar elegidas</Button>
              <Button size="small" onClick={() => hacer({ tipo: 'invertir' })}>Invertir orden</Button>
              <Button size="small" onClick={() => setElegidas(elegidas.size ? new Set() : new Set(mesa.hojas.map((h) => h.clave)))}>{elegidas.size ? 'Ninguna' : 'Todas'}</Button>
            </Stack>
            <Box sx={{ flex: 1 }} />
            <Stack direction="row" spacing={1} alignItems="center" sx={{ minWidth: 160 }}>
              <Typography variant="caption">Tamaño</Typography>
              <Slider size="small" min={90} max={260} value={ancho} onChange={(_, v) => setAncho(v as number)} />
            </Stack>
            <TextField size="small" label="Nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} sx={{ width: 180 }} />
            <Button variant="contained" startIcon={<SaveOutlinedIcon />} onClick={guardar}>Guardar PDF</Button>
          </Stack>
        )}
        {error && <Alert severity="error">{error}</Alert>}
        {trabajo && <PanelTrabajo trabajo={trabajo} />}
        <Box sx={{ display: 'grid', gap: 1.5, gridTemplateColumns: `repeat(auto-fill, minmax(${ancho + 24}px, 1fr))` }}>
          {mesa.hojas.map((h, i) => {
            const elegida = elegidas.has(h.clave)
            return (
              <Box key={h.clave} draggable
                onDragStart={() => setArrastrada(i)}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => { e.preventDefault(); e.stopPropagation(); if (arrastrada !== null) hacer({ tipo: 'mover', desde: arrastrada, hasta: i }); setArrastrada(null) }}
                sx={{ p: 1, borderRadius: 2, border: 2, borderColor: elegida ? 'primary.main' : 'transparent', cursor: 'grab',
                      bgcolor: arrastrada === i ? 'action.selected' : 'transparent', '&:hover': { bgcolor: 'action.hover' } }}>
                <Box sx={{ position: 'relative', display: 'grid', placeItems: 'center' }}
                  onClick={() => { const s = new Set(elegidas); if (elegida) s.delete(h.clave); else s.add(h.clave); setElegidas(s) }}>
                  {h.blanca
                    ? <Box sx={{ width: ancho, height: ancho * 1.414, bgcolor: 'white', border: 1, borderColor: 'divider', borderRadius: 0.5 }} />
                    : <Miniatura archivo={h.archivo!} pagina={h.pagina!} ancho={ancho} rotar={h.rotar} />}
                  <Checkbox size="small" checked={elegida} sx={{ position: 'absolute', top: -6, left: -6 }} />
                </Box>
                <Typography variant="caption" component="div" align="center" noWrap color="text.secondary">
                  {i + 1} · {h.blanca ? 'en blanco' : `${archivos[indice.get(h.archivo!) ?? 0]?.nombre ?? ''} p. ${h.pagina}`}
                </Typography>
                <BotonesHoja h={h} />
              </Box>
            )
          })}
        </Box>
      </Stack>
    </Marco>
  )
}
