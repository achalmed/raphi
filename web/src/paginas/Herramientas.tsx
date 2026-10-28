/**
 * La portada de Raphi: soltar cualquier archivo (el menú de a qué se convierte, como Tangerine), las recetas y todas
 * las herramientas por categoría con un buscador, como iLovePDF. Lo que no se puede usar en esta máquina se ve, con
 * lo que le falta, en vez de esconderse.
 */
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import ButtonBase from '@mui/material/ButtonBase'
import Chip from '@mui/material/Chip'
import InputAdornment from '@mui/material/InputAdornment'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import SearchIcon from '@mui/icons-material/Search'
import { Marco, PALETA, api } from '@qillqa/tiqsi'
import ElegirArchivos from '../componentes/Archivos'
import MenuFormatos from '../componentes/MenuFormatos'
import PanelTrabajo from '../componentes/PanelTrabajo'
import { OPCIONES } from '../modulo'
import { BASE, cargarCatalogo, type Archivo, type Catalogo, type Operacion, type Trabajo } from '../lib/api'
import { buscar } from '../lib/buscar'

export function Tarjeta({ op, alPulsar }: { op: Operacion; alPulsar: () => void }) {
  const falta = op.faltan.length > 0
  return (
    <ButtonBase onClick={alPulsar} disabled={falta} focusRipple
      sx={{ display: 'block', textAlign: 'left', p: 2, borderRadius: 3, border: 1, borderColor: 'divider', height: '100%',
            bgcolor: PALETA.superficie ?? 'background.paper', opacity: falta ? 0.55 : 1,
            transition: 'box-shadow .15s, transform .15s', '&:hover': { boxShadow: 3, transform: 'translateY(-1px)' } }}>
      <Typography sx={{ fontWeight: 600 }}>{op.titulo}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>{op.descripcion}</Typography>
      {falta && <Typography variant="caption" color="warning.main">Falta {op.faltan.map((f) => f.replace('py:', '')).join(', ')}</Typography>}
    </ButtonBase>
  )
}

export default function Herramientas() {
  const navegar = useNavigate()
  const [cat, setCat] = useState<Catalogo | null>(null)
  const [error, setError] = useState('')
  const [consulta, setConsulta] = useState('')
  const [categoria, setCategoria] = useState('')
  const [soltados, setSoltados] = useState<Archivo[]>([])
  const [parametros] = useSearchParams()
  useEffect(() => {        // lo soltado en el escritorio con Alt (o donde no había zona) y los enlaces llegan con ?archivos=
    const ids = (parametros.get('archivos') ?? '').split(',').filter(Boolean)
    if (ids.length) Promise.all(ids.map((a) => api<Archivo>(`${BASE}/archivos/${a}`))).then(setSoltados).catch(() => undefined)
  }, [parametros])
  const [rapidos, setRapidos] = useState<Trabajo[]>([])
  useEffect(() => { cargarCatalogo().then(setCat).catch((e) => setError(e.message)) }, [])
  const lista = useMemo(() => {
    if (!cat) return []
    const base = categoria ? cat.operaciones.filter((o) => o.categoria === categoria) : cat.operaciones
    return consulta ? buscar(base, consulta) : base
  }, [cat, consulta, categoria])

  return (
    <Marco modulo="raphi" titulo="Herramientas" opciones={OPCIONES('/raphi', navegar)}>
      <Stack spacing={3} sx={{ maxWidth: 1200, mx: 'auto', p: { xs: 1, sm: 2 } }}>
        {error && <Alert severity="error">{error}</Alert>}
        <Box>
          <ElegirArchivos archivos={soltados} alCambiar={setSoltados} texto="Suelte cualquier archivo: Raphi le dice a qué se puede convertir" />
          {soltados.length > 0 && <Box sx={{ mt: 2 }}><MenuFormatos archivos={soltados} alTrabajo={(t) => setRapidos([t, ...rapidos])} /></Box>}
          <Stack spacing={1} sx={{ mt: rapidos.length ? 2 : 0 }}>{rapidos.map((t) => <PanelTrabajo key={t.id} trabajo={t} />)}</Stack>
        </Box>

        {cat && cat.recetas.length > 0 && (
          <Box>
            <Typography variant="overline" color="text.secondary">Recetas</Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {cat.recetas.filter((r) => !r.sin_entradas || cat.fuentes.includes('hub')).map((r) => (
                <Chip key={r.id} label={r.nombre} onClick={() => navegar(`/raphi/h/receta:${r.id}`)} title={r.descripcion} />
              ))}
            </Stack>
          </Box>
        )}

        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems={{ sm: 'center' }}>
          <TextField size="small" placeholder="Buscar: unir, comprimir, foliar, heic…" value={consulta}
            onChange={(e) => setConsulta(e.target.value)} sx={{ flex: 1, maxWidth: { sm: 420 } }}
            InputProps={{ startAdornment: <InputAdornment position="start"><SearchIcon /></InputAdornment> }} />
          <Stack direction="row" spacing={0.75} flexWrap="wrap" useFlexGap>
            <Chip label="Todas" color={categoria ? 'default' : 'primary'} onClick={() => setCategoria('')} />
            {cat?.categorias.map((c) => <Chip key={c} label={c} color={categoria === c ? 'primary' : 'default'} onClick={() => setCategoria(c)} />)}
          </Stack>
        </Stack>

        {(consulta ? [''] : (categoria ? [categoria] : cat?.categorias ?? [])).map((c) => {
          const de = c ? lista.filter((o) => o.categoria === c) : lista
          if (!de.length) return null
          return (
            <Box key={c || 'resultados'}>
              {c && <Typography variant="h6" sx={{ mb: 1 }}>{c}</Typography>}
              <Box sx={{ display: 'grid', gap: 1.5, gridTemplateColumns: 'repeat(auto-fill, minmax(230px, 1fr))' }}>
                {de.map((o) => <Tarjeta key={o.id} op={o} alPulsar={() => navegar(o.id === 'componer' ? '/raphi/mesa' : `/raphi/h/${o.id}`)} />)}
              </Box>
            </Box>
          )
        })}
        {cat && !lista.length && <Typography color="text.secondary">Nada coincide con «{consulta}».</Typography>}
      </Stack>
    </Marco>
  )
}
