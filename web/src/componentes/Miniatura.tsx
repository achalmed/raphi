/**
 * La miniatura de una página. Un `<img src>` no lleva la sesión, así que la imagen se pide con `descargarBlob` del
 * anfitrión y se guarda como URL local; las mismas no se piden dos veces en la misma página.
 */
import { useEffect, useState } from 'react'
import Box from '@mui/material/Box'
import Skeleton from '@mui/material/Skeleton'
import { descargarBlob } from '@qillqa/tiqsi'
import { urlMiniatura } from '../lib/api'

const cache = new Map<string, Promise<string>>()

export function urlLocal(ruta: string): Promise<string> {
  let p = cache.get(ruta)
  if (!p) {
    p = descargarBlob(ruta).then((b) => URL.createObjectURL(b))
    p.catch(() => cache.delete(ruta))
    cache.set(ruta, p)
  }
  return p
}

export default function Miniatura({ archivo, pagina, ancho = 160, rotar = 0, alto }: {
  archivo: string
  pagina: number
  ancho?: number
  rotar?: number
  alto?: number
}) {
  const [src, setSrc] = useState<string | null>(null)
  const [fallo, setFallo] = useState(false)
  useEffect(() => {
    let vivo = true
    urlLocal(urlMiniatura(archivo, pagina, Math.round(ancho * 1.5))).then((u) => vivo && setSrc(u)).catch(() => vivo && setFallo(true))
    return () => { vivo = false }
  }, [archivo, pagina, ancho])
  const h = alto ?? Math.round(ancho * 1.414)
  if (!src) return <Skeleton variant="rectangular" width={ancho} height={h} sx={{ borderRadius: 1, opacity: fallo ? 0.3 : 1 }} />
  return (
    <Box sx={{ width: ancho, height: h, display: 'grid', placeItems: 'center', overflow: 'hidden' }}>
      <Box component="img" src={src} alt={`Página ${pagina}`} draggable={false}
        sx={{ maxWidth: rotar % 180 ? h : ancho, maxHeight: rotar % 180 ? ancho : h, transform: `rotate(${rotar}deg)`,
              transition: 'transform .2s', boxShadow: 1, bgcolor: 'white', borderRadius: 0.5 }} />
    </Box>
  )
}
