/**
 * La vista «tramo» de un parámetro: «Todo» o «Solo un tramo», y el tramo se elige con una barra y dos horas.
 * - En un video, sobre su duración: 1:02:00-1:05:30 (desde el comienzo).
 * - En una transmisión EN VIVO, sobre su ventana de rebobinado y por la HORA del reloj (@11:18:44-@11:20:47), que no se
 *   corre mientras el directo avanza; con atajos «los últimos 5, 15 o 30 minutos».
 * Sin datos del enlace (varios enlaces, o aún no consultado), un campo de texto con los ejemplos. El valor es siempre el
 * texto que entiende el motor (`leer_tramo`).
 */
import { useEffect, useMemo, useState } from 'react'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Slider from '@mui/material/Slider'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import ToggleButton from '@mui/material/ToggleButton'
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup'
import Typography from '@mui/material/Typography'
import { ventanaAhora, type InfoEnlace, type Parametro } from '../lib/api'
import { horaDe, reloj } from './CampoEnlace'

const segundos = (t: string) => t.trim().split(':').reduce((acc, p) => acc * 60 + Number(p), 0)
const valido = (t: string) => /^\d+(:\d{1,2}){0,2}$/.test(t.trim())

/** El tramo escrito → [inicio, fin] en la escala de la barra (segundos del video, o época en vivo); null si no encaja. */
function leer(valor: string, info: InfoEnlace | null): [number, number] | null {
  const m = valor.match(/^\s*(@?[\d:]+)\s*(?:-|\.\.|\sa\s)\s*(@?[\d:]+)\s*$/)
  if (!m || !info) return null
  if (info.en_vivo && info.ventana?.desde != null) {
    if (!m[1].startsWith('@') || !m[2].startsWith('@')) return null
    const dia = (t: string) => { const x = t.slice(1); return segundos(x.split(':').length === 2 ? `${x}:00` : x) }
    const hasta = ventanaAhora(info)![1]
    const base = hasta + info.zona
    const medianoche = base - (base % 86400) - info.zona
    let a = medianoche + dia(m[1]), b = medianoche + dia(m[2])
    if (a > hasta + 300) { a -= 86400; b -= 86400 }
    if (b <= a) b += 86400
    return [a, b]
  }
  if (m[1].startsWith('@')) return null
  return [segundos(m[1]), segundos(m[2])]
}

export default function EditorTramo({ parametro, valor, alCambiar, info, deshabilitado }: {
  parametro: Parametro
  valor: string
  alCambiar: (v: string) => void
  info: InfoEnlace | null
  deshabilitado?: boolean
}) {
  const vivo = Boolean(info?.en_vivo && info.ventana?.desde != null && info.ventana.hasta != null)
  // En vivo, la ventana crece mientras se mira: el reloj la corre cada segundo (el «ahora» de la barra avanza)
  const [ahora, setAhora] = useState(() => Date.now() / 1000)
  useEffect(() => {
    if (!vivo) return
    const t = setInterval(() => setAhora(Date.now() / 1000), 1000)
    return () => clearInterval(t)
  }, [vivo])
  const escala = useMemo<[number, number] | null>(() => {
    if (!info) return null
    if (vivo) return ventanaAhora(info, ahora)
    return info.duracion ? [0, info.duracion] : null
  }, [info, vivo, ahora])
  const [pide, setPide] = useState(Boolean(valor))
  // Un directo siempre se baja por tramos: «todo» lo grabaría hasta que termine
  const quiere = vivo || pide
  const [textos, setTextos] = useState<[string, string]>(['', ''])

  const formato = (x: number) => (vivo ? horaDe(x, info!.zona) : reloj(x))
  const escribir = ([a, b]: [number, number]) => alCambiar(vivo ? `@${formato(a)}-@${formato(b)}` : `${formato(a)}-${formato(b)}`)
  const actual = useMemo(() => leer(valor, info), [valor, info])

  // Al cambiar de enlace: si el tramo de antes no cabe en la escala nueva, uno por omisión (el último par de minutos
  // de un directo; el primer minuto de un video)
  useEffect(() => {
    if (!quiere || !escala) return
    const [lo, hi] = escala
    if (actual && actual[0] >= lo && actual[1] <= hi + 1) return
    escribir(vivo ? [Math.max(lo, hi - 120), hi] : [lo, Math.min(hi, lo + 60)])
  }, [info, quiere]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (actual) setTextos([formato(actual[0]), formato(actual[1])]) }, [valor]) // eslint-disable-line react-hooks/exhaustive-deps

  const elegir = (q: boolean) => { setPide(q); if (!q) alCambiar('') }
  const ponerTexto = (k: 0 | 1, t: string) => {
    const xs: [string, string] = k === 0 ? [t, textos[1]] : [textos[0], t]
    setTextos(xs)
    if (!valido(xs[0]) || !valido(xs[1]) || !escala) return
    if (vivo) {
      const v = `@${xs[0]}-@${xs[1]}`
      if (leer(v, info)) alCambiar(v)
    } else alCambiar(`${xs[0]}-${xs[1]}`)
  }

  return (
    <Stack spacing={1.5} sx={{ gridColumn: { sm: 'span 2' } }}>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems={{ sm: 'center' }}>
        <Typography variant="body2" sx={{ minWidth: 120 }}>{parametro.etiqueta}</Typography>
        {vivo
          ? <Typography variant="body2" color="text.secondary">Está en vivo: elige qué parte bajar (por la hora).</Typography>
          : (
            <ToggleButtonGroup exclusive size="small" value={quiere ? 'tramo' : 'todo'} disabled={deshabilitado}
              onChange={(_e, v) => v && elegir(v === 'tramo')} aria-label={parametro.etiqueta}>
              <ToggleButton value="todo">Todo el video</ToggleButton>
              <ToggleButton value="tramo">Solo un tramo</ToggleButton>
            </ToggleButtonGroup>
          )}
      </Stack>
      {quiere && escala && (
        <Box sx={{ px: { xs: 1, sm: 2 }, py: 1.5, borderRadius: 2, bgcolor: 'action.hover' }}>
          {vivo && (
            <Stack direction="row" spacing={1} sx={{ mb: 1, flexWrap: 'wrap', rowGap: 1 }} alignItems="center">
              <Typography variant="body2" color="text.secondary">Atajos:</Typography>
              {[5, 15, 30].map((min) => (
                <Button key={min} size="small" variant="outlined" disabled={deshabilitado}
                  onClick={() => escribir([Math.max(escala[0], escala[1] - min * 60), escala[1]])}>
                  Los últimos {min} min
                </Button>
              ))}
            </Stack>
          )}
          <Slider value={actual ?? escala} min={escala[0]} max={escala[1]} step={1} disabled={deshabilitado}
            onChange={(_e, v) => escribir(v as [number, number])} valueLabelDisplay="auto" valueLabelFormat={formato}
            getAriaValueText={formato} getAriaLabel={(k) => (k === 0 ? 'Inicio del tramo' : 'Fin del tramo')}
            marks={[{ value: escala[0], label: formato(escala[0]) }, { value: escala[1], label: vivo ? `${formato(escala[1])} (ahora)` : formato(escala[1]) }]}
            sx={{
              mx: 1, width: 'calc(100% - 16px)', '& .MuiSlider-markLabel': { fontSize: 12 },
              // las dos marcas de los extremos, hacia adentro: centradas se salían de una ventana angosta
              '& .MuiSlider-markLabel[data-index="0"]': { transform: 'translateX(0)' },
              '& .MuiSlider-markLabel[data-index="1"]': { transform: 'translateX(-100%)' },
            }} />
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} sx={{ mt: 2.5 }} alignItems={{ sm: 'center' }}>
            <TextField size="small" label={vivo ? 'Desde las' : 'Desde'} value={textos[0]} disabled={deshabilitado}
              error={Boolean(textos[0]) && !valido(textos[0])} onChange={(e) => ponerTexto(0, e.target.value)}
              placeholder={vivo ? 'HH:MM:SS' : 'H:MM:SS'} sx={{ width: { sm: 150 } }} />
            <TextField size="small" label={vivo ? 'Hasta las' : 'Hasta'} value={textos[1]} disabled={deshabilitado}
              error={Boolean(textos[1]) && !valido(textos[1])} onChange={(e) => ponerTexto(1, e.target.value)}
              placeholder={vivo ? 'HH:MM:SS' : 'H:MM:SS'} sx={{ width: { sm: 150 } }} />
            {actual && (
              <Typography variant="body2" color="text.secondary">
                Se bajarán <b>{reloj(actual[1] - actual[0])}</b>{vivo ? ' (horas locales)' : ''}.
              </Typography>
            )}
          </Stack>
        </Box>
      )}
      {quiere && !escala && (
        <TextField size="small" fullWidth label="Tramo" value={valor ?? ''} disabled={deshabilitado} onChange={(e) => alCambiar(e.target.value)}
          placeholder="1:02:00-1:05:30" helperText={parametro.ayuda || 'INICIO-FIN'} />
      )}
    </Stack>
  )
}
