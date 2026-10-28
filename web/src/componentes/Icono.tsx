/**
 * El ícono de cada herramienta, en un cuadro con el tono de su categoría (`lib/identidad.ts`). Lo usan la cuadrícula de
 * Herramientas, la cabecera de cada herramienta y la lista de Trabajos: la misma herramienta se reconoce en todas.
 */
import type { SvgIconComponent } from '@mui/icons-material'
import Box from '@mui/material/Box'
import ApprovalOutlined from '@mui/icons-material/ApprovalOutlined'
import AudiotrackOutlined from '@mui/icons-material/AudiotrackOutlined'
import AutorenewOutlined from '@mui/icons-material/AutorenewOutlined'
import BorderColorOutlined from '@mui/icons-material/BorderColorOutlined'
import BrandingWatermarkOutlined from '@mui/icons-material/BrandingWatermarkOutlined'
import BuildOutlined from '@mui/icons-material/BuildOutlined'
import CallSplitOutlined from '@mui/icons-material/CallSplitOutlined'
import CompressOutlined from '@mui/icons-material/CompressOutlined'
import ContentCutOutlined from '@mui/icons-material/ContentCutOutlined'
import CropOutlined from '@mui/icons-material/CropOutlined'
import DashboardCustomizeOutlined from '@mui/icons-material/DashboardCustomizeOutlined'
import DescriptionOutlined from '@mui/icons-material/DescriptionOutlined'
import DifferenceOutlined from '@mui/icons-material/DifferenceOutlined'
import DocumentScannerOutlined from '@mui/icons-material/DocumentScannerOutlined'
import DrawOutlined from '@mui/icons-material/DrawOutlined'
import DynamicFormOutlined from '@mui/icons-material/DynamicFormOutlined'
import EditNoteOutlined from '@mui/icons-material/EditNoteOutlined'
import FactCheckOutlined from '@mui/icons-material/FactCheckOutlined'
import FolderZipOutlined from '@mui/icons-material/FolderZipOutlined'
import FormatListNumberedOutlined from '@mui/icons-material/FormatListNumberedOutlined'
import HandymanOutlined from '@mui/icons-material/HandymanOutlined'
import HideSourceOutlined from '@mui/icons-material/HideSourceOutlined'
import HtmlOutlined from '@mui/icons-material/HtmlOutlined'
import ImageOutlined from '@mui/icons-material/ImageOutlined'
import ImageSearchOutlined from '@mui/icons-material/ImageSearchOutlined'
import InfoOutlined from '@mui/icons-material/InfoOutlined'
import Inventory2Outlined from '@mui/icons-material/Inventory2Outlined'
import InventoryOutlined from '@mui/icons-material/InventoryOutlined'
import LayersClearOutlined from '@mui/icons-material/LayersClearOutlined'
import LayersOutlined from '@mui/icons-material/LayersOutlined'
import LockOpenOutlined from '@mui/icons-material/LockOpenOutlined'
import LockOutlined from '@mui/icons-material/LockOutlined'
import MergeTypeOutlined from '@mui/icons-material/MergeTypeOutlined'
import MovieOutlined from '@mui/icons-material/MovieOutlined'
import NotesOutlined from '@mui/icons-material/NotesOutlined'
import NumbersOutlined from '@mui/icons-material/NumbersOutlined'
import OutputOutlined from '@mui/icons-material/OutputOutlined'
import PhotoLibraryOutlined from '@mui/icons-material/PhotoLibraryOutlined'
import PhotoSizeSelectLargeOutlined from '@mui/icons-material/PhotoSizeSelectLargeOutlined'
import PictureAsPdfOutlined from '@mui/icons-material/PictureAsPdfOutlined'
import PlaylistRemoveOutlined from '@mui/icons-material/PlaylistRemoveOutlined'
import ReceiptLongOutlined from '@mui/icons-material/ReceiptLongOutlined'
import RotateRightOutlined from '@mui/icons-material/RotateRightOutlined'
import SpeedOutlined from '@mui/icons-material/SpeedOutlined'
import StickyNote2Outlined from '@mui/icons-material/StickyNote2Outlined'
import SubtitlesOutlined from '@mui/icons-material/SubtitlesOutlined'
import SwapVertOutlined from '@mui/icons-material/SwapVertOutlined'
import SyncAltOutlined from '@mui/icons-material/SyncAltOutlined'
import TableChartOutlined from '@mui/icons-material/TableChartOutlined'
import TextSnippetOutlined from '@mui/icons-material/TextSnippetOutlined'
import TuneOutlined from '@mui/icons-material/TuneOutlined'
import UnarchiveOutlined from '@mui/icons-material/UnarchiveOutlined'
import VerifiedOutlined from '@mui/icons-material/VerifiedOutlined'
import VideoSettingsOutlined from '@mui/icons-material/VideoSettingsOutlined'
import { colorDe, tinte } from '../lib/identidad'

const ICONOS: Record<string, SvgIconComponent> = {
  unir: MergeTypeOutlined, dividir: CallSplitOutlined, extraer: OutputOutlined, rotar: RotateRightOutlined,
  reordenar: SwapVertOutlined, eliminar: PlaylistRemoveOutlined, componer: DashboardCustomizeOutlined,
  comprimir: CompressOutlined, comparar_compresion: TuneOutlined, linearizar: SpeedOutlined, reparar: HandymanOutlined,
  validar: FactCheckOutlined, pdfa: Inventory2Outlined,
  a_pdf: PictureAsPdfOutlined, ofimatica: SyncAltOutlined, imagenes_a_pdf: PhotoLibraryOutlined, a_markdown: NotesOutlined,
  pdf_a_imagen: ImageOutlined, pdf_a_texto: TextSnippetOutlined, pdf_a_html: HtmlOutlined, pdf_a_word: DescriptionOutlined,
  tablas_a_excel: TableChartOutlined, extraer_imagenes: ImageSearchOutlined, ocr: DocumentScannerOutlined,
  marca_agua: BrandingWatermarkOutlined, numerar: FormatListNumberedOutlined, foliar: NumbersOutlined, sello: ApprovalOutlined,
  metadatos: EditNoteOutlined, quitar_metadatos: LayersClearOutlined, tachar: HideSourceOutlined, resaltar: BorderColorOutlined,
  nota: StickyNote2Outlined, estampar_imagen: DrawOutlined, formulario: DynamicFormOutlined, aplanar: LayersOutlined,
  cifrar: LockOutlined, descifrar: LockOpenOutlined, firmas: VerifiedOutlined,
  info: InfoOutlined, inventario_paginas: InventoryOutlined, detectar_ocr: DocumentScannerOutlined, comparar: DifferenceOutlined,
  miniatura: ImageOutlined, leer_comprobante: ReceiptLongOutlined,
  convertir_imagen: AutorenewOutlined, redimensionar_imagen: PhotoSizeSelectLargeOutlined, recortar_imagen: CropOutlined,
  comprimir_imagen: CompressOutlined, convertir_audio: AudiotrackOutlined, convertir_video: MovieOutlined,
  recortar_medio: ContentCutOutlined, comprimir_video: VideoSettingsOutlined, convertir_subtitulos: SubtitlesOutlined,
  quitar_metadatos_archivo: LayersClearOutlined, comprimir_archivos: FolderZipOutlined, extraer_archivo: UnarchiveOutlined,
}

export const iconoDe = (id: string): SvgIconComponent => ICONOS[id] ?? BuildOutlined

/** El cuadro con el ícono. `tamano` es el lado en px (el ícono ocupa algo más de la mitad). */
export default function IconoOperacion({ id, categoria, tamano = 40 }: { id: string; categoria: string; tamano?: number }) {
  const Icono = iconoDe(id)
  const color = colorDe(categoria)
  return (
    <Box className="raphi-icono" aria-hidden
      sx={{ width: tamano, height: tamano, flexShrink: 0, borderRadius: `${Math.round(tamano * 0.3)}px`, display: 'grid',
            placeItems: 'center', color, bgcolor: tinte(color, 0.12), transition: 'transform .18s ease' }}>
      <Icono sx={{ fontSize: Math.round(tamano * 0.56) }} />
    </Box>
  )
}
