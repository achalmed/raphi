/**
 * La vista «enlace» de un parámetro: donde se pegan los enlaces y, debajo, qué es cada uno (miniatura, título, canal,
 * duración, si es una lista o si está EN VIVO y desde qué hora se puede bajar), consultado al sitio sin bajar nada.
 * Genérica: la usa cualquier operación con un parámetro `vista="enlace"`; avisa del primero a `alInformar`, que el
 * formulario pasa a la vista «tramo».
 */
import { useEffect, useRef, useState } from 'react'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Chip from '@mui/material/Chip'
import Skeleton from '@mui/material/Skeleton'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import { consultarEnlace, type InfoEnlace, type Parametro } from '../lib/api'

export const reloj = (s: number) => {
  const t = Math.max(0, Math.round(s))
  const h = Math.floor(t / 3600), m = Math.floor((t % 3600) / 60), x = t % 60
  return h ? `${h}:${String(m).padStart(2, '0')}:${String(x).padStart(2, '0')}` : `${m}:${String(x).padStart(2, '0')}`
}

/** La hora HH:MM:SS de una época, en la zona de la máquina que baja. */
export const horaDe = (epoca: number, zona: number) => new Date((epoca + zona) * 1000).toISOString().slice(11, 19)

type Estado = { url: string; info?: InfoEnlace; error?: string }

function Ficha({ e }: { e: Estado }) {
  if (!e.info && !e.error) {
    return (
      <Stack direction="row" spacing={1.5} alignItems="center">
        <Skeleton variant="rounded" width={128} height={72} />
        <Box sx={{ flex: 1 }}>
          <Typography variant="body2" color="text.secondary">Consultando el enlace…</Typography>
          <Skeleton width="60%" />
        </Box>
      </Stack>
    )
  }
  if (e.error) return <Alert severity="warning" sx={{ wordBreak: 'break-word' }}>{e.error}</Alert>
  const i = e.info!
  const ventana = i.ventana
  return (
    <Stack direction="row" spacing={1.5} alignItems="flex-start" aria-label={`Enlace: ${i.titulo}`}>
      {i.miniatura
        ? <Box component="img" src={i.miniatura} alt="" sx={{ width: i.vertical ? 72 : 128, height: i.vertical ? 128 : 72, objectFit: 'cover', borderRadius: 1, flexShrink: 0, bgcolor: 'action.hover' }} />
        : <Box sx={{ width: 128, height: 72, borderRadius: 1, bgcolor: 'action.hover', flexShrink: 0 }} />}
      <Box sx={{ minWidth: 0 }}>
        <Typography fontWeight={500} sx={{ wordBreak: 'break-word' }}>{i.titulo}</Typography>
        <Typography variant="body2" color="text.secondary">{[i.canal !== i.titulo ? i.canal : '', i.sitio].filter(Boolean).join(' · ')}</Typography>
        <Stack direction="row" spacing={1} sx={{ mt: 0.75, flexWrap: 'wrap', rowGap: 0.75 }}>
          {i.en_vivo && <Chip size="small" color="error" label="EN VIVO" />}
          {i.en_vivo && ventana?.desde && ventana.hasta && (
            <Typography variant="body2" color="text.secondary">
              se puede bajar desde las {horaDe(ventana.desde, i.zona)}{ventana.llena ? ' (corre con el vivo)' : ''} hasta ahora
            </Typography>
          )}
          {!i.en_vivo && i.duracion != null && <Typography variant="body2" color="text.secondary">Dura {reloj(i.duracion)}</Typography>}
          {i.lista && <Typography variant="body2" color="text.secondary">Lista de {i.elementos} videos</Typography>}
          {i.vertical && <Typography variant="body2" color="text.secondary">· vertical</Typography>}
          {i.calidades.length > 0 && <Typography variant="body2" color="text.secondary">· hasta {i.calidades[0]}p</Typography>}
        </Stack>
      </Box>
    </Stack>
  )
}

export default function CampoEnlace({ parametro, valor, alCambiar, alInformar, cookies, deshabilitado }: {
  parametro: Parametro
  valor: string
  alCambiar: (v: string) => void
  alInformar: (info: InfoEnlace | null) => void
  cookies: string
  deshabilitado?: boolean
}) {
  const [estados, setEstados] = useState<Estado[]>([])
  const pedido = useRef(0)
  const urls = (valor || '').split('\n').map((u) => u.trim()).filter(Boolean)
  const clave = urls.slice(0, 5).join('\n') + '|' + cookies

  useEffect(() => {
    const yo = ++pedido.current
    if (!urls.length) { setEstados([]); alInformar(null); return }
    const lista = urls.slice(0, 5)
    const espera = setTimeout(() => {
      setEstados(lista.map((url) => ({ url })))
      lista.forEach((url, n) => {
        consultarEnlace(url, cookies)
          .then((info) => {
            if (yo !== pedido.current) return
            setEstados((xs) => xs.map((x, k) => (k === n ? { url, info } : x)))
            if (n === 0) alInformar(lista.length === 1 ? info : null)
          })
          .catch((e: Error) => {
            if (yo !== pedido.current) return
            setEstados((xs) => xs.map((x, k) => (k === n ? { url, error: e.message } : x)))
            if (n === 0) alInformar(null)
          })
      })
    }, 600)
    return () => clearTimeout(espera)
  }, [clave]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Stack spacing={1.5} sx={{ gridColumn: { sm: 'span 2' } }}>
      <TextField label={parametro.etiqueta} required={parametro.obligatorio} multiline minRows={1} fullWidth size="small"
        placeholder="https://www.youtube.com/watch?v=… · https://www.facebook.com/… · https://www.tiktok.com/…"
        helperText={parametro.ayuda || 'Pega el enlace: Raphi muestra qué video es antes de bajarlo.'}
        value={valor ?? ''} disabled={deshabilitado} onChange={(e) => alCambiar(e.target.value)} />
      {estados.map((e) => <Ficha key={e.url} e={e} />)}
      {urls.length > 5 && <Typography variant="body2" color="text.secondary">Y {urls.length - 5} enlaces más.</Typography>}
    </Stack>
  )
}
