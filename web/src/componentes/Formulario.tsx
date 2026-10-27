/**
 * El formulario de una operación, generado de su ficha (`parametros` del motor): ninguna operación tiene un formulario
 * escrito a mano, así que una operación nueva del motor aparece sola, en la web y en el escritorio.
 */
import Box from '@mui/material/Box'
import FormControlLabel from '@mui/material/FormControlLabel'
import InputAdornment from '@mui/material/InputAdornment'
import MenuItem from '@mui/material/MenuItem'
import Switch from '@mui/material/Switch'
import TextField from '@mui/material/TextField'
import type { Parametro } from '../lib/api'

export type Valores = Record<string, unknown>

/** Los valores por omisión de una ficha (lo que se ve al abrir el formulario). */
export const iniciales = (ps: Parametro[]): Valores =>
  Object.fromEntries(ps.filter((p) => p.tipo !== 'json').map((p) => [p.clave, p.defecto ?? (p.tipo === 'casilla' ? false : '')]))

/** Solo lo que cambió respecto de lo por omisión: la API completa el resto (y el informe queda más claro). */
export const cambiados = (ps: Parametro[], v: Valores): Valores =>
  Object.fromEntries(Object.entries(v).filter(([k, x]) => {
    const p = ps.find((y) => y.clave === k)
    return p && x !== '' && x !== null && x !== p.defecto
  }))

export default function Formulario({ parametros, valores, alCambiar, deshabilitado }: {
  parametros: Parametro[]
  valores: Valores
  alCambiar: (v: Valores) => void
  deshabilitado?: boolean
}) {
  const poner = (k: string, x: unknown) => alCambiar({ ...valores, [k]: x })
  const visibles = parametros.filter((p) => p.tipo !== 'json')
  if (!visibles.length) return null
  return (
    <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))' } }}>
      {visibles.map((p) => {
        const v = valores[p.clave]
        const comun = { label: p.etiqueta, helperText: p.ayuda || undefined, disabled: deshabilitado, fullWidth: true, size: 'small' as const }
        if (p.tipo === 'casilla') {
          return (
            <FormControlLabel key={p.clave} sx={{ gridColumn: { sm: 'span 2' } }} disabled={deshabilitado}
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
          return (
            <TextField key={p.clave} {...comun} type="color" value={(v as string) || '#000000'} onChange={(e) => poner(p.clave, e.target.value)} />
          )
        }
        if (p.tipo === 'multilinea') {
          return (
            <TextField key={p.clave} {...comun} multiline minRows={2} value={v ?? ''} sx={{ gridColumn: { sm: 'span 2' } }}
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
      })}
    </Box>
  )
}
