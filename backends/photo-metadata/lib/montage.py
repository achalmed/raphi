"""Genera montajes PNG: recorte de la marca + etiqueta, para revisión humana.

Sirve para verificar de un vistazo las lecturas dudosas o las colisiones sin
abrir cada foto por separado.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from config import Settings
from lib import media
from lib.ocr import crop_for_display

_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
_ROW_HEIGHT = 120
_LABEL_WIDTH = 560
_CROP_WIDTH = 720


def _load_font(size: int) -> ImageFont.ImageFont:
    """Carga una fuente monoespaciada; usa la de PIL si no está disponible."""
    try:
        return ImageFont.truetype(_FONT_PATH, size)
    except OSError:
        return ImageFont.load_default()


def _row_crop(path: Path, settings: Settings) -> Image.Image:
    """Recorta y escala la franja de la marca a la altura de una fila."""
    crop = crop_for_display(media.load_image(path, settings), settings)
    scale = (_ROW_HEIGHT - 8) / crop.height
    resized = crop.resize((int(crop.width * scale), _ROW_HEIGHT - 8),
                          Image.Resampling.LANCZOS)
    return resized.crop((0, 0, min(_CROP_WIDTH, resized.width), resized.height))


def _draw_row(canvas: Image.Image, font: ImageFont.ImageFont, index: int,
              label: str, crop: Image.Image) -> None:
    """Dibuja una fila: etiqueta a la izquierda, recorte a la derecha."""
    draw = ImageDraw.Draw(canvas)
    top = index * _ROW_HEIGHT
    draw.rectangle([0, top, canvas.width, top + _ROW_HEIGHT], outline=(90, 90, 90))
    draw.multiline_text((6, top + 12), label, fill=(255, 255, 0), font=font)
    canvas.paste(crop, (_LABEL_WIDTH, top + 4))


def build_montage(items: list[tuple[str, Path]], out_path: Path,
                  settings: Settings) -> None:
    """Crea un montaje con una fila por elemento.

    Args:
        items: Pares (etiqueta_multilinea, ruta_imagen).
        out_path: Archivo PNG de salida.
        settings: Configuración de recorte.
    """
    font = _load_font(19)
    canvas = Image.new("RGB", (_LABEL_WIDTH + _CROP_WIDTH,
                               _ROW_HEIGHT * max(1, len(items))), (30, 30, 30))
    for index, (label, path) in enumerate(items):
        _draw_row(canvas, font, index, label, _row_crop(path, settings))
    canvas.save(out_path)


def build_montages_chunked(items: list[tuple[str, Path]], out_dir: Path,
                           base_name: str, settings: Settings) -> list[Path]:
    """Divide `items` en varios PNG para que las filas no queden diminutas."""
    chunk = settings.montage_rows_per_image
    outputs: list[Path] = []
    for part, start in enumerate(range(0, len(items), chunk), start=1):
        out_path = out_dir / f"{base_name}_{part}.png"
        build_montage(items[start:start + chunk], out_path, settings)
        outputs.append(out_path)
    return outputs
