/**
 * Las recetas: las de serie y las propias, cada una con sus pasos; aplicarlas abre su herramienta. Una receta nueva
 * se arma paso a paso eligiendo operaciones y sus parámetros (el mismo formulario generado de la ficha).
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import IconButton from '@mui/material/IconButton'
import MenuItem from '@mui/material/MenuItem'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import AddIcon from '@mui/icons-material/Add'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline'
import { Marco, PALETA, confirmar } from '@qillqa/tiqsi'
import Formulario, { cambiados, iniciales, type Valores } from '../componentes/Formulario'
import { OPCIONES } from '../modulo'
import { borrarReceta, cargarCatalogo, guardarReceta, recetas as pedirRecetas, type Operacion, type Receta } from '../lib/api'
import { normalizar } from '../lib/buscar'

interface PasoEditable { operacion: string; valores: Valores }

const idDe = (nombre: string) => normalizar(nombre).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 60)

function Editor({ ops, alGuardar, alCancelar }: { ops: Operacion[]; alGuardar: () => void; alCancelar: () => void }) {
  const [nombre, setNombre] = useState('')
  const [descripcion, setDescripcion] = useState('')
  const [pasos, setPasos] = useState<PasoEditable[]>([])
  const [error, setError] = useState('')
  const disponibles = ops.filter((o) => !o.faltan.length && o.lote)
  const agregar = (id: string) => {
    const op = ops.find((o) => o.id === id)
    if (op) setPasos([...pasos, { operacion: id, valores: iniciales(op.parametros) }])
  }
  const guardar = async () => {
    setError('')
    try {
      await guardarReceta({ id: idDe(nombre), nombre, descripcion, pasos: pasos.map((p) => ({
        operacion: p.operacion, params: cambiados(ops.find((o) => o.id === p.operacion)!.parametros, p.valores) })) })
      alGuardar()
    } catch (e) { setError((e as Error).message) }
  }
  return (
    <Stack spacing={2} sx={{ p: 2, borderRadius: 3, border: 1, borderColor: 'divider', bgcolor: PALETA.superficie ?? 'background.paper' }}>
      <Typography variant="h6">Receta nueva</Typography>
      <TextField size="small" label="Nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} helperText={nombre ? `id: ${idDe(nombre)}` : ' '} />
      <TextField size="small" label="Para qué sirve" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />
      {pasos.map((p, i) => {
        const op = ops.find((o) => o.id === p.operacion)!
        return (
          <Box key={i} sx={{ p: 1.5, borderRadius: 2, bgcolor: 'action.hover' }}>
            <Stack direction="row" alignItems="center" sx={{ mb: 1 }}>
              <Typography sx={{ flex: 1, fontWeight: 600 }}>{i + 1}. {op.titulo}</Typography>
              <IconButton size="small" onClick={() => setPasos(pasos.filter((_, j) => j !== i))}><DeleteOutlineIcon fontSize="small" /></IconButton>
            </Stack>
            <Formulario parametros={op.parametros} valores={p.valores}
              alCambiar={(v) => setPasos(pasos.map((x, j) => (j === i ? { ...x, valores: v } : x)))} />
          </Box>
        )
      })}
      <TextField select size="small" label="Agregar un paso" value="" onChange={(e) => agregar(e.target.value)}>
        {disponibles.map((o) => <MenuItem key={o.id} value={o.id}>{o.categoria} · {o.titulo}</MenuItem>)}
      </TextField>
      {error && <Alert severity="error">{error}</Alert>}
      <Stack direction="row" spacing={1}>
        <Button variant="contained" disabled={!nombre || !pasos.length} onClick={guardar}>Guardar receta</Button>
        <Button onClick={alCancelar}>Cancelar</Button>
      </Stack>
    </Stack>
  )
}

export default function Recetas() {
  const navegar = useNavigate()
  const [lista, setLista] = useState<Receta[]>([])
  const [ops, setOps] = useState<Operacion[]>([])
  const [editando, setEditando] = useState(false)
  const recargar = () => pedirRecetas().then(setLista)
  useEffect(() => { recargar(); cargarCatalogo().then((c) => setOps(c.operaciones)) }, [])
  const titulo = (id: string) => ops.find((o) => o.id === id)?.titulo ?? id
  return (
    <Marco modulo="raphi" titulo="Recetas" opciones={OPCIONES('/raphi/recetas', navegar)}>
      <Stack spacing={1.5} sx={{ maxWidth: 900, mx: 'auto', p: { xs: 1, sm: 2 } }}>
        <Typography color="text.secondary">
          Una receta encadena herramientas: lo que sale de un paso entra al siguiente y solo se guarda el resultado final.
        </Typography>
        {!editando && <Box><Button startIcon={<AddIcon />} variant="outlined" onClick={() => setEditando(true)}>Receta nueva</Button></Box>}
        {editando && <Editor ops={ops} alGuardar={() => { setEditando(false); recargar(); cargarCatalogo(true) }} alCancelar={() => setEditando(false)} />}
        {lista.map((r) => (
          <Stack key={r.id} direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems={{ sm: 'center' }}
            sx={{ p: 2, borderRadius: 3, border: 1, borderColor: 'divider' }}>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Stack direction="row" spacing={1} alignItems="center">
                <Typography sx={{ fontWeight: 600 }}>{r.nombre}</Typography>
                <Chip size="small" label={r.origen === 'serie' ? 'de serie' : 'propia'} variant="outlined" />
              </Stack>
              <Typography variant="body2" color="text.secondary">{r.descripcion}</Typography>
              <Typography variant="caption" color="text.secondary">{r.pasos.map((p) => titulo(p.operacion)).join(' → ')}</Typography>
            </Box>
            <Button variant="contained" onClick={() => navegar(`/raphi/h/receta:${r.id}`)}>Aplicar</Button>
            {r.origen === 'usuario' && (
              <IconButton onClick={async () => { if (await confirmar(`¿Borrar la receta «${r.nombre}»?`, { peligro: true })) { await borrarReceta(r.id); recargar() } }}>
                <DeleteOutlineIcon />
              </IconButton>
            )}
          </Stack>
        ))}
      </Stack>
    </Marco>
  )
}
