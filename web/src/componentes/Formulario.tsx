/**
 * El formulario de una operación, generado de su ficha (`parametros` del motor): ninguna operación tiene un formulario
 * escrito a mano, así que una operación nueva del motor aparece sola, en la web y en el escritorio.
 *
 * Lo que la ficha pide y este formulario cumple, sin saber de qué operación se trata:
 * - `si`: el parámetro se muestra solo si otro vale eso («Formato del audio» solo con «Solo el audio»);
 * - `grupo`: los parámetros de un grupo van plegados bajo su título («Más opciones»);
 * - `vista`: «enlace» consulta los enlaces y muestra qué son; «tramo» elige un tramo sobre lo que dijo el enlace.
 */
import { useState } from 'react'
import Accordion from '@mui/material/Accordion'
import AccordionDetails from '@mui/material/AccordionDetails'
import AccordionSummary from '@mui/material/AccordionSummary'
import Box from '@mui/material/Box'
import FormControlLabel from '@mui/material/FormControlLabel'
import InputAdornment from '@mui/material/InputAdornment'
import MenuItem from '@mui/material/MenuItem'
import Switch from '@mui/material/Switch'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import type { InfoEnlace, Parametro } from '../lib/api'
import CampoEnlace from './CampoEnlace'
import EditorTramo from './EditorTramo'

export type Valores = Record<string, unknown>

/** Los valores por omisión de una ficha (lo que se ve al abrir el formulario). */
export const iniciales = (ps: Parametro[]): Valores =>
  Object.fromEntries(ps.filter((p) => p.tipo !== 'json').map((p) => [p.clave, p.defecto ?? (p.tipo === 'casilla' ? false : '')]))

/** ¿Se muestra (y se manda) este parámetro con estos valores? */
export const aplica = (p: Parametro, v: Valores): boolean => !p.si?.length || p.si.slice(1).includes(v[p.si[0] as string])

/** Solo lo que cambió respecto de lo por omisión, y solo lo que aplica: la API completa el resto. */
export const cambiados = (ps: Parametro[], v: Valores): Valores =>
  Object.fromEntries(Object.entries(v).filter(([k, x]) => {
    const p = ps.find((y) => y.clave === k)
    return p && aplica(p, v) && x !== '' && x !== null && x !== p.defecto
  }))

const ancho = { gridColumn: { sm: 'span 2' } }
const rejilla = { display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))' } }

export default function Formulario({ parametros, valores, alCambiar, deshabilitado }: {
  parametros: Parametro[]
  valores: Valores
  alCambiar: (v: Valores) => void
  deshabilitado?: boolean
}) {
  const [info, setInfo] = useState<InfoEnlace | null>(null)
  const poner = (k: string, x: unknown) => alCambiar({ ...valores, [k]: x })
  const visibles = parametros.filter((p) => p.tipo !== 'json' && aplica(p, valores))
  if (!visibles.length) return null
  // Las cookies del navegador sirven también para consultar un enlace privado
  const cookies = String(valores.cookies ?? '')

  const campo = (p: Parametro) => {
    const v = valores[p.clave]
    if (p.vista === 'enlace') {
      return <CampoEnlace key={p.clave} parametro={p} valor={String(v ?? '')} alCambiar={(x) => poner(p.clave, x)}
        alInformar={setInfo} cookies={cookies} deshabilitado={deshabilitado} />
    }
    if (p.vista === 'tramo') {
      return <EditorTramo key={p.clave} parametro={p} valor={String(v ?? '')} alCambiar={(x) => poner(p.clave, x)}
        info={info} deshabilitado={deshabilitado} />
    }
    const comun = { label: p.etiqueta, helperText: p.ayuda || undefined, disabled: deshabilitado, fullWidth: true, size: 'small' as const }
    if (p.tipo === 'casilla') {
      return (
        <FormControlLabel key={p.clave} sx={ancho} disabled={deshabilitado}
          control={<Switch checked={Boolean(v)} onChange={(e) => poner(p.clave, e.target.checked)} />} label={p.etiqueta} />
      )
    }
    if (p.tipo === 'opcion') {
      return (
        <TextField key={p.clave} select {...comun} value={v ?? ''} onChange={(e) => poner(p.clave, e.target.value)}>
          {p.opciones.map(([valor, etiqueta]) => <MenuItem key={valor} value={valor}>{etiqueta}</MenuItem>)}
        </TextField>
      )
    }
    if (p.tipo === 'color') {
      return <TextField key={p.clave} {...comun} type="color" value={(v as string) || '#000000'} onChange={(e) => poner(p.clave, e.target.value)} />
    }
    if (p.tipo === 'multilinea') {
      return (
        <TextField key={p.clave} {...comun} multiline minRows={2} value={v ?? ''} sx={ancho}
          onChange={(e) => poner(p.clave, e.target.value)} />
      )
    }
    const numero = p.tipo === 'entero' || p.tipo === 'decimal' || p.tipo === 'tamano'
    return (
      <TextField key={p.clave} {...comun} required={p.obligatorio}
        type={p.tipo === 'clave' ? 'password' : numero ? 'number' : 'text'}
        value={v ?? ''}
        inputProps={numero ? { min: p.minimo ?? undefined, max: p.maximo ?? undefined, step: p.tipo === 'entero' ? 1 : 'any' } : undefined}
        InputProps={p.tipo === 'tamano' ? { endAdornment: <InputAdornment position="end">MB</InputAdornment> } : undefined}
        onChange={(e) => poner(p.clave, numero && e.target.value !== '' ? Number(e.target.value) : e.target.value)} />
    )
  }

  const principales = visibles.filter((p) => !p.grupo)
  const grupos = [...new Set(visibles.map((p) => p.grupo).filter(Boolean))] as string[]
  return (
    <Box sx={{ display: 'grid', gap: 2 }}>
      {principales.length > 0 && <Box sx={rejilla}>{principales.map(campo)}</Box>}
      {grupos.map((g) => (
        <Accordion key={g} disableGutters variant="outlined" sx={{ borderRadius: 2, '&:before': { display: 'none' } }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}><Typography>{g}</Typography></AccordionSummary>
          <AccordionDetails><Box sx={rejilla}>{visibles.filter((p) => p.grupo === g).map(campo)}</Box></AccordionDetails>
        </Accordion>
      ))}
    </Box>
  )
}
