/**
 * El menú de Tangerine: se suelta un archivo y aparece a qué se puede convertir y qué herramientas le sirven. Una
 * conversión corre al instante; una herramienta abre su formulario con el archivo ya puesto.
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { crearTrabajo, formatos, type Archivo, type Formato, type Trabajo } from '../lib/api'

export default function MenuFormatos({ archivos, alTrabajo }: { archivos: Archivo[]; alTrabajo: (t: Trabajo) => void }) {
  const navegar = useNavigate()
  const [lista, setLista] = useState<Formato[] | null>(null)
  const primero = archivos[0]
  useEffect(() => { setLista(null); if (primero) formatos(primero.nombre).then(setLista).catch(() => setLista([])) }, [primero?.id]) // eslint-disable-line react-hooks/exhaustive-deps
  if (!primero) return null
  if (!lista) return <CircularProgress size={22} />
  const conversiones = lista.filter((f) => f.a)
  const herramientas = lista.filter((f) => !f.a)
  const mismos = archivos.filter((a) => a.nombre.slice(a.nombre.lastIndexOf('.')).toLowerCase() === primero.nombre.slice(primero.nombre.lastIndexOf('.')).toLowerCase())
  const convertir = async (f: Formato) => alTrabajo(await crearTrabajo({ operacion: f.operacion, archivos: mismos.map((a) => a.id), params: f.params }))
  const abrir = (f: Formato) => navegar(`/raphi/h/${f.operacion}?archivos=${mismos.map((a) => a.id).join(',')}`)
  return (
    <Stack spacing={1.5}>
      <Typography variant="body2" color="text.secondary">
        {mismos.length > 1 ? `${mismos.length} archivos como ${primero.nombre}` : primero.nombre}
      </Typography>
      {conversiones.length > 0 && (
        <Box>
          <Typography variant="overline" color="text.secondary">Convertir a</Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {conversiones.map((f) => (
              <Chip key={`${f.operacion}-${f.a}`} label={f.a!.toUpperCase()} onClick={() => convertir(f)} clickable color="primary" variant="outlined" />
            ))}
          </Stack>
        </Box>
      )}
      {herramientas.length > 0 && (
        <Box>
          <Typography variant="overline" color="text.secondary">Herramientas</Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {herramientas.map((f) => <Button key={f.operacion} size="small" variant="text" onClick={() => abrir(f)}>{f.titulo}</Button>)}
          </Stack>
        </Box>
      )}
    </Stack>
  )
}
