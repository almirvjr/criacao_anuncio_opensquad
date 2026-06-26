#!/usr/bin/env python3
"""
Mascara de produto via BiRefNet (rembg), com cache de sessao e FALLBACK
automatico pra heuristica do pixel-de-canto se rembg nao estiver instalado.

Substitui a deteccao fragil (diff do pixel do canto) usada em
render_faixa.py / fit_scale.py / compose_two.py. Bake-off que validou a troca:
tests/cutout-bakeoff/ (inox espelhado: cobertura do produto 22%->85%; fundo
degrade: bbox parava de estourar pra imagem inteira). Custo R$0, roda offline.

Modelo configuravel por env CUTOUT_MODEL (default birefnet-general).
Desligavel por env CUTOUT_DISABLE=1 (forca a heuristica antiga).
"""
import os
from PIL import Image, ImageChops, ImageFilter

_SESSION = None
_MODEL = os.environ.get("CUTOUT_MODEL", "birefnet-general")


def _heuristic_mask(img, corner=(15, 15), thr=45, maxf=5):
    """Heuristica legada (pixel do canto). Usada so como fallback."""
    rgb = img.convert("RGB")
    ref = rgb.getpixel(corner)
    diff = ImageChops.difference(rgb, Image.new("RGB", rgb.size, ref)).convert("L")
    return diff.point(lambda p: 255 if p > thr else 0).filter(ImageFilter.MaxFilter(maxf))


def alpha_mask(img, thr=128):
    """Mascara L binaria (0/255) do produto. BiRefNet; cai pra heuristica em erro."""
    global _SESSION
    if os.environ.get("CUTOUT_DISABLE") == "1":
        return _heuristic_mask(img)
    try:
        from rembg import remove, new_session
        if _SESSION is None:
            _SESSION = new_session(_MODEL)
        rgba = remove(img.convert("RGB"), session=_SESSION)
        return rgba.split()[-1].point(lambda p: 255 if p > thr else 0)
    except Exception:
        return _heuristic_mask(img)


def mask_bbox(img):
    """bbox (l,t,r,b) do produto, ou None se vazio."""
    return alpha_mask(img).getbbox()


def product_bottom(img):
    """y da base do produto (compat com fit_scale)."""
    bb = mask_bbox(img)
    return bb[3] if bb else img.size[1]
