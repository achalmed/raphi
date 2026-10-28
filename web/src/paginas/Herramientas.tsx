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
import MenuBookOutlinedIcon from '@mui/icons-material/MenuBookOutlined'
import { Marco, PALETA, api } from '@qillqa/tiqsi'
import ElegirArchivos from '../componentes/Archivos'
import MenuFormatos from '../componentes/MenuFormatos'
import PanelTrabajo from '../componentes/PanelTrabajo'
import IconoOperacion from '../componentes/Icono'
import { RESUMEN_CATEGORIA, acepta, colorDe, tinte } from '../lib/identidad'
import { OPCIONES } from '../modulo'
import { BASE, cargarCatalogo, subir, type Archivo, type Catalogo, type Operacion, type Trabajo } from '../lib/api'
import { buscar } from '../lib/buscar'

/**
 * Una herramienta: su ícono con el tono de su categoría, qué hace y qué acepta. Tocarla abre su formulario; soltarle un
 * archivo encima lo sube y la abre con él ya puesto (en el escritorio, lo soltado sobre la ventana lo atiende el puente).
 */
export function Tarjeta({ op, alPulsar, alSoltar }: { op: Operacion; alPulsar: () => void; alSoltar?: (f: File[]) => void }) {
  const falta = op.faltan.length > 0
  const color = colorDe(op.categoria)
  const [encima, setEncima] = useState(false)
  const recibe = !falta && Boolean(alSoltar)
  return (
    <ButtonBase onClick={alPulsar} disabled={falta} focusRipple
      onDragOver={(e) => { if (recibe && e.dataTransfer.types.includes('Files')) { e.preventDefault(); setEncima(true) } }}
      onDragLeave={() => setEncima(false)}
      onDrop={(e) => { if (!recibe) return; e.preventDefault(); setEncima(false); const f = Array.from(e.dataTransfer.files); if (f.length) alSoltar!(f) }}
      sx={{
        display: 'flex', alignItems: 'flex-start', gap: 1.5, textAlign: 'left', p: 1.75, height: '100%', width: '100%',
        borderRadius: '14px', border: '1px solid', borderColor: encima ? color : 'divider',
        bgcolor: encima ? tinte(color, 0.08) : (PALETA.superficie ?? 'background.paper'), opacity: falta ? 0.5 : 1,
        transition: 'border-color .15s ease, background-color .15s ease',
        '&:hover': { borderColor: tinte(color, 0.5) }, '&:hover .raphi-icono': { transform: 'scale(1.07)' },
        '&.Mui-focusVisible': { outline: `2px solid ${color}`, outlineOffset: 2 },
        '@media (prefers-reduced-motion: reduce)': { '&:hover .raphi-icono': { transform: 'none' } },
      }}>
      <IconoOperacion id={op.id} categoria={op.categoria} />
      <Box sx={{ minWidth: 0, flex: 1 }}>
        <Typography sx={{ fontWeight: 600, fontSize: 15, lineHeight: 1.3 }}>{op.titulo}</Typography>
        <Typography variant="body2" color="text.secondary"
          sx={{ mt: 0.25, lineHeight: 1.4, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {op.descripcion}
        </Typography>
        <Typography variant="caption" component="div" sx={{ mt: 0.75, color: falta ? 'warning.main' : encima ? color : (PALETA.textoTenue ?? 'text.secondary'), fontWeight: encima ? 600 : 400 }}>
          {falta ? `Falta ${op.faltan.map((f) => f.replace('py:', '')).join(', ')}` : encima ? 'Suéltelo para abrirla con este archivo' : acepta(op)}
        </Typography>
      </Box>
    </ButtonBase>
  )
}

/** El título de una categoría: su tono, lo que agrupa y cuántas herramientas tiene. */
function Categoria({ nombre, cuantas }: { nombre: string; cuantas: number }) {
  return (
    <Stack direction="row" alignItems="baseline" spacing={1.25} sx={{ mb: 1.25 }}>
      <Box sx={{ width: 10, height: 10, borderRadius: '3px', bgcolor: colorDe(nombre), alignSelf: 'center', flexShrink: 0 }} />
      <Typography sx={{ fontWeight: 700, fontSize: 17 }}>{nombre}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ flex: 1 }} noWrap>{RESUMEN_CATEGORIA[nombre] ?? ''}</Typography>
      <Typography variant="caption" sx={{ color: PALETA.textoTenue ?? 'text.secondary' }}>{cuantas}</Typography>
    </Stack>
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
  const abrir = (o: Operacion, ids: string[] = []) => {
    const ruta = o.id === 'componer' ? '/raphi/mesa' : `/raphi/h/${o.id}`
    navegar(ids.length ? `${ruta}?archivos=${ids.join(',')}` : ruta)
  }
  const soltarEn = (o: Operacion) => async (f: File[]) => {
    const validos = o.extensiones.length ? f.filter((x) => o.extensiones.includes(x.name.toLowerCase().slice(x.name.lastIndexOf('.')))) : f
    if (!validos.length) { setError(`«${o.titulo}» acepta ${acepta(o)}; ese archivo no le sirve.`); return }
    try { abrir(o, (await subir(validos)).map((a) => a.id)) } catch (e) { setError((e as Error).message) }
  }
  const lista = useMemo(() => {
    if (!cat) return []
    const base = categoria ? cat.operaciones.filter((o) => o.categoria === categoria) : cat.operaciones
    return consulta ? buscar(base, consulta) : base
  }, [cat, consulta, categoria])

  return (
    <Marco modulo="raphi" titulo="Herramientas" opciones={OPCIONES('/raphi', navegar)}>
      <Stack spacing={3} sx={{ maxWidth: 1200, width: '100%', minWidth: 0, mx: 'auto', p: { xs: 1, sm: 2 } }}>
        {error && <Alert severity="error">{error}</Alert>}
        <Box>
          <ElegirArchivos archivos={soltados} alCambiar={setSoltados} franja texto="Suelte un archivo y vea a qué se puede convertir"
            ayuda="PDF, Word, Excel, PowerPoint, fotos (también HEIC), audio, video y subtítulos. O suéltelo sobre una herramienta." />
          {soltados.length > 0 && <Box sx={{ mt: 2 }}><MenuFormatos archivos={soltados} alTrabajo={(t) => setRapidos([t, ...rapidos])} /></Box>}
          <Stack spacing={1} sx={{ mt: rapidos.length ? 2 : 0 }}>{rapidos.map((t) => <PanelTrabajo key={t.id} trabajo={t} />)}</Stack>
        </Box>

        {cat && cat.recetas.length > 0 && (
          <Box>
            <Stack direction="row" alignItems="baseline" spacing={1.25} sx={{ mb: 1 }}>
              <Typography sx={{ fontWeight: 700, fontSize: 17 }}>Recetas</Typography>
              <Typography variant="body2" color="text.secondary">Varios pasos de una vez, con un clic</Typography>
            </Stack>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {cat.recetas.filter((r) => !r.sin_entradas || cat.fuentes.includes('hub')).map((r) => (
                <Chip key={r.id} label={r.nombre} variant="outlined" onClick={() => navegar(`/raphi/h/receta:${r.id}`)} title={r.descripcion}
                  icon={<MenuBookOutlinedIcon sx={{ fontSize: '17px !important' }} />} sx={{ bgcolor: PALETA.superficie ?? 'background.paper' }} />
              ))}
            </Stack>
          </Box>
        )}

        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ md: 'center' }} sx={{ minWidth: 0 }}>
          <TextField size="small" placeholder="Buscar: unir, comprimir, foliar, heic…" value={consulta}
            onChange={(e) => setConsulta(e.target.value)} sx={{ flex: { md: '0 0 320px' }, width: { xs: '100%', md: 'auto' } }}
            InputProps={{ startAdornment: <InputAdornment position="start"><SearchIcon /></InputAdornment> }} />
          {/* En el celular, una sola fila que se desliza; en pantallas anchas, las que quepan. */}
          <Stack direction="row" spacing={0.75} useFlexGap
            sx={{ minWidth: 0, maxWidth: '100%', flexWrap: { xs: 'nowrap', md: 'wrap' }, overflowX: { xs: 'auto', md: 'visible' }, mx: { xs: -1, md: 0 }, px: { xs: 1, md: 0 },
                  pb: { xs: 0.5, md: 0 }, scrollbarWidth: 'none', '& > *': { flexShrink: 0 } }}>
            <Chip label="Todas" color={categoria ? 'default' : 'primary'} onClick={() => setCategoria('')} />
            {cat?.categorias.map((c) => (
              <Chip key={c} label={c} onClick={() => setCategoria(categoria === c ? '' : c)} variant={categoria === c ? 'filled' : 'outlined'}
                icon={<Box component="span" sx={{ width: 8, height: 8, borderRadius: '2px', bgcolor: colorDe(c), ml: '10px !important' }} />}
                sx={categoria === c ? { bgcolor: tinte(colorDe(c), 0.14), color: colorDe(c), fontWeight: 600, borderColor: 'transparent' } : undefined} />
            ))}
          </Stack>
        </Stack>

        {(consulta ? [''] : (categoria ? [categoria] : cat?.categorias ?? [])).map((c) => {
          const de = c ? lista.filter((o) => o.categoria === c) : lista
          if (!de.length) return null
          return (
            <Box key={c || 'resultados'}>
              {c && <Categoria nombre={c} cuantas={de.length} />}
              <Box sx={{ display: 'grid', gap: 1.25, gridTemplateColumns: { xs: '1fr', sm: 'repeat(auto-fill, minmax(260px, 1fr))' } }}>
                {de.map((o) => <Tarjeta key={o.id} op={o} alPulsar={() => abrir(o)} alSoltar={o.minimo_entradas > 0 ? soltarEn(o) : undefined} />)}
              </Box>
            </Box>
          )
        })}
        {cat && !lista.length && <Typography color="text.secondary">Nada coincide con «{consulta}».</Typography>}
      </Stack>
    </Marco>
  )
}
