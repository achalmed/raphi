/**
 * Sistema: lo que esta máquina tiene y lo que le falta (antes «Sistema → Diagnóstico» de la GUI), y, en el escritorio,
 * sus ajustes propios: los menús de Dolphin y las carpetas vigiladas (antes «Vigilancia»).
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import FormControlLabel from '@mui/material/FormControlLabel'
import IconButton from '@mui/material/IconButton'
import MenuItem from '@mui/material/MenuItem'
import Stack from '@mui/material/Stack'
import Switch from '@mui/material/Switch'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline'
import { Marco } from '@qillqa/tiqsi'
import { OPCIONES } from '../modulo'
import { cargarCatalogo, sistema as pedirSistema, type Receta, type Sistema as Datos } from '../lib/api'
import { hayEscritorio, puente } from '../lib/escritorio'

function Escritorio() {
  const [menus, setMenus] = useState(false)
  const [vigiladas, setVigiladas] = useState<{ carpeta: string; receta: string }[]>([])
  const [recetas, setRecetas] = useState<Receta[]>([])
  const [receta, setReceta] = useState('')
  const p = puente()!
  const recargar = () => p.vigiladas().then(setVigiladas)
  useEffect(() => { p.hayMenusDolphin().then(setMenus); recargar(); cargarCatalogo().then((c) => setRecetas(c.recetas.filter((r) => !r.sin_entradas))) }, []) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <Stack spacing={2}>
      <Typography variant="h6">En este escritorio</Typography>
      <FormControlLabel control={<Switch checked={menus} onChange={async (e) => { await p.menusDolphin(e.target.checked); setMenus(await p.hayMenusDolphin()) }} />}
        label="Clic derecho en Dolphin → Raphi (convertir, comprimir, quitar metadatos…)" />
      <Box>
        <Typography sx={{ fontWeight: 600 }}>Carpetas vigiladas</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          Lo que aparezca en la carpeta pasa por la receta y el resultado queda en una subcarpeta «raphi».
        </Typography>
        {vigiladas.map((v) => (
          <Stack key={v.carpeta} direction="row" alignItems="center" spacing={1}>
            <Typography sx={{ flex: 1 }} noWrap>{v.carpeta}</Typography>
            <Chip size="small" label={recetas.find((r) => r.id === v.receta)?.nombre ?? v.receta} />
            <IconButton size="small" onClick={async () => { await p.dejarDeVigilar(v.carpeta); recargar() }}><DeleteOutlineIcon fontSize="small" /></IconButton>
          </Stack>
        ))}
        <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
          <TextField select size="small" label="Receta" value={receta} onChange={(e) => setReceta(e.target.value)} sx={{ minWidth: 240 }}>
            {recetas.map((r) => <MenuItem key={r.id} value={r.id}>{r.nombre}</MenuItem>)}
          </TextField>
          <Button disabled={!receta} onClick={async () => { const c = await p.elegirCarpeta(); if (c) { await p.vigilar(c, receta); recargar() } }}>
            Vigilar una carpeta…
          </Button>
        </Stack>
      </Box>
    </Stack>
  )
}

export default function Sistema() {
  const navegar = useNavigate()
  const [d, setD] = useState<Datos | null>(null)
  const [error, setError] = useState('')
  useEffect(() => { pedirSistema().then(setD).catch((e) => setError(e.message)) }, [])
  return (
    <Marco modulo="raphi" titulo="Sistema" opciones={OPCIONES('/raphi/sistema', navegar)}>
      <Stack spacing={3} sx={{ maxWidth: 900, mx: 'auto', p: { xs: 1, sm: 2 } }}>
        {error && <Alert severity="error">{error}</Alert>}
        {d && (
          <>
            <Typography color="text.secondary">
              Raphi {d.version} · modo {d.modo} · {d.concurrencia} trabajo(s) a la vez · lo subido y los resultados se guardan {d.retencion_horas} h
              {d.carpeta ? ` · carpeta ${d.carpeta}` : ''}
            </Typography>
            {d.no_disponibles.length > 0
              ? <Alert severity="warning">{d.no_disponibles.length} herramienta(s) sin lo que necesitan: {d.no_disponibles.join(', ')}.</Alert>
              : <Alert severity="success">Todas las herramientas tienen lo que necesitan.</Alert>}
            <Box sx={{ display: 'grid', gap: 1, gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))' }}>
              {d.requisitos.map((r) => (
                <Stack key={r.nombre} direction="row" spacing={1} alignItems="center" sx={{ p: 1.25, borderRadius: 2, border: 1, borderColor: 'divider' }}>
                  <Chip size="small" color={r.ok ? 'success' : 'warning'} label={r.ok ? 'sí' : 'falta'} />
                  <Box sx={{ minWidth: 0 }}>
                    <Typography noWrap>{r.nombre}{r.python ? ' (Python)' : ''}</Typography>
                    <Typography variant="caption" color="text.secondary" noWrap component="div">{r.usan.length} herramienta(s)</Typography>
                  </Box>
                </Stack>
              ))}
            </Box>
          </>
        )}
        {hayEscritorio() && <Escritorio />}
      </Stack>
    </Marco>
  )
}
