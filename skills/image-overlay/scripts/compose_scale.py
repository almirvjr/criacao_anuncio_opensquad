#!/usr/bin/env python3
"""Composição determinística de escala (conselho 18/06).
A IA gera só o AMBIENTE VAZIO (com a bancada = régua). Este script assenta o
PRODUTO FIEL (recorte BiRefNet) na escala EXATA calculada por matemática + sombra
de contato procedural. Resolve o "Nano ignora escala" sem perder fidelidade.

Escala: altura_produto_px = (product_cm / counter_cm) * (floor_y - counter_top_y)
  onde (floor_y - counter_top_y) = altura da bancada em px (= counter_cm reais).
Se --body-top-frac for dado, a parte ESCALADA é só o corpo (do topo*frac até a base),
util quando o produto tem tampa aberta acima do corpo.

Uso:
  python compose_scale.py --scene cena_vazia.jpg --product hero_fiel.jpg --out capa.jpg \
     --floor-y 980 --counter-top-y 150 [--counter-cm 90] [--product-cm 28] \
     [--body-top-frac 0.30] [--x-frac 0.42] [--shadow-alpha 110]
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import cutout
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W = H = 1200

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--product", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--floor-y", type=int, required=True, help="Y (px) da linha do chao onde a base do produto encosta")
    ap.add_argument("--counter-top-y", type=int, required=True, help="Y (px) do TOPO do tampo da bancada")
    ap.add_argument("--counter-cm", type=float, default=90.0)
    ap.add_argument("--product-cm", type=float, default=28.0, help="altura REAL (cm) da parte escalada do produto")
    ap.add_argument("--body-top-frac", type=float, default=None, help="se a parte a escalar nao for o silhueta inteira: fracao do topo do bbox onde comeca o corpo")
    ap.add_argument("--x-frac", type=float, default=0.5, help="centro X do produto como fracao da largura")
    ap.add_argument("--shadow-alpha", type=int, default=115)
    a = ap.parse_args()

    scene = Image.open(a.scene).convert("RGB")
    if scene.size != (W, H): scene = scene.resize((W, H), Image.LANCZOS)
    prod = Image.open(a.product).convert("RGB")
    if prod.size != (W, H): prod = prod.resize((W, H), Image.LANCZOS)

    mask = cutout.alpha_mask(prod)              # L (BiRefNet)
    ma = np.asarray(mask) > 10
    ys, xs = np.where(ma)
    pt, pb, pl, pr = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    ph, pw = pb - pt, pr - pl

    prgba = prod.convert("RGBA"); prgba.putalpha(mask)
    crop = prgba.crop((pl, pt, pr + 1, pb + 1))   # produto recortado (RGBA)

    vanity_px = a.floor_y - a.counter_top_y
    target_part_px = (a.product_cm / a.counter_cm) * vanity_px
    # quantos px do bbox correspondem a "parte escalada"
    part_px = ph if a.body_top_frac is None else ph * (1.0 - a.body_top_frac)
    scale = target_part_px / part_px
    nw, nh = max(1, int(pw * scale)), max(1, int(ph * scale))
    prod_s = crop.resize((nw, nh), Image.LANCZOS)

    cx = int(a.x_frac * W)
    px = int(cx - nw / 2)
    py = int(a.floor_y - nh)                       # base do produto na linha do chao

    out = scene.convert("RGBA")
    # sombra de contato: elipse achatada sob a base, blur
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sw, shh = int(nw * 0.92), int(nh * 0.13)
    scx, scy = cx + int(nw * 0.05), a.floor_y - int(shh * 0.35)
    sd.ellipse([scx - sw // 2, scy - shh // 2, scx + sw // 2, scy + shh // 2], fill=(0, 0, 0, a.shadow_alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(20))
    out = Image.alpha_composite(out, sh)
    out.alpha_composite(prod_s, (px, py))
    out.convert("RGB").save(a.out, quality=95)
    print(f"OK {a.out} | bancada={vanity_px}px(={a.counter_cm}cm) -> produto(parte)={int(target_part_px)}px({a.product_cm}cm) | nh={nh} base_y={a.floor_y} x={cx}")

if __name__ == "__main__":
    main()
