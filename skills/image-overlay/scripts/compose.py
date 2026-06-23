#!/usr/bin/env python3
"""Composicao 'produto travado' (pipeline 23/06). Entrada unica da composicao:
produto FIEL (PNG recortado e travado, OU hero a recortar) assentado sobre uma
CENA, com sombra de contato procedural e harmonizacao de cor opcional.

Fidelidade por CONSTRUCAO: o produto e colado em pixels reais; nunca passa pelo
modelo generativo. Resolve o edit-drift do Nano Banana.

- --product aceita PNG RGBA ja recortado (produto travado) OU imagem RGB (recorta via BiRefNet).
- --bg studio          -> fundo gerado por codigo (degrade branco->cinza claro), custo IA zero.
- --bg <scene.jpg>     -> fundo fornecido (ambiente lifestyle gerado pela IA, SEM produto).
- --harmonize warm     -> leve overlay quente no produto p/ casar com cena quente (lifestyle).

Uso:
  python compose.py --product travado.png --bg studio --out foto.jpg --target-h 920 --x-frac 0.42 --base-y 1090
  python compose.py --product travado.png --bg cena.jpg --out foto.jpg --target-h 520 --x-frac 0.27 --base-y 1085 --harmonize warm
"""
import argparse, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cutout
from PIL import Image, ImageDraw, ImageFilter, ImageChops

W = H = 1200


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def carregar_produto(path):
    """Retorna o produto recortado em RGBA, ja no bbox. Usa o alpha do PNG se vier
    recortado; senao recorta via BiRefNet."""
    img = Image.open(path)
    if img.mode == "RGBA" and img.getextrema()[3][0] < 255:   # ja tem alpha real
        bb = img.getbbox()
        return img.crop(bb)
    img = img.convert("RGB")
    m = cutout.alpha_mask(img)
    bb = m.getbbox()
    if bb is None:
        raise SystemExit(f"ERRO: cutout vazio em {path}")
    rgba = img.convert("RGBA"); rgba.putalpha(m)
    return rgba.crop(bb)


def studio_bg(top=(248, 248, 250), bot=(214, 216, 220)):
    bg = Image.new("RGB", (W, H))
    px = bg.load()
    for y in range(H):
        t = y / H
        row = tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3))
        for x in range(W):
            px[x, y] = row
    return bg


def harmonizar_warm(prod_rgba, intensidade=0.12):
    """Multiplica um tom quente suave so nos pixels do produto (preserva alpha)."""
    r, g, b, a = prod_rgba.split()
    rgb = Image.merge("RGB", (r, g, b))
    warm = Image.new("RGB", rgb.size, (255, 233, 200))
    mixed = ImageChops.multiply(rgb, warm)
    out = Image.blend(rgb, mixed, intensidade)
    r2, g2, b2 = out.split()
    return Image.merge("RGBA", (r2, g2, b2, a))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--product", required=True)
    ap.add_argument("--bg", required=True, help="'studio' ou caminho de uma cena .jpg")
    ap.add_argument("--out", required=True)
    ap.add_argument("--target-h", type=int, required=True, help="altura do produto em px no canvas 1200")
    ap.add_argument("--x-frac", type=float, default=0.5, help="centro X do produto como fracao da largura")
    ap.add_argument("--base-y", type=int, required=True, help="Y (px) onde a base do produto encosta")
    ap.add_argument("--harmonize", choices=["warm"], default=None)
    ap.add_argument("--shadow-alpha", type=int, default=120)
    a = ap.parse_args()

    prod = carregar_produto(a.product)
    if a.harmonize == "warm":
        prod = harmonizar_warm(prod)

    pw, ph = prod.size
    scale = a.target_h / ph
    nw, nh = max(1, int(pw * scale)), max(1, int(ph * scale))
    prod_s = prod.resize((nw, nh), Image.LANCZOS)

    if a.bg == "studio":
        scene = studio_bg()
    else:
        scene = Image.open(a.bg).convert("RGB")
        if scene.size != (W, H):
            scene = scene.resize((W, H), Image.LANCZOS)

    cx = int(a.x_frac * W); px = int(cx - nw / 2); py = int(a.base_y - nh)
    out = scene.convert("RGBA")
    # sombra de contato: elipse achatada sob a base, blur gaussiano
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sw, shh = int(nw * 0.9), int(nh * 0.10)
    scx, scy = cx, a.base_y - int(shh * 0.3)
    sd.ellipse([scx - sw // 2, scy - shh // 2, scx + sw // 2, scy + shh // 2], fill=(0, 0, 0, a.shadow_alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    out = Image.alpha_composite(out, sh)
    out.alpha_composite(prod_s, (px, py))
    out.convert("RGB").save(a.out, quality=95)

    # sidecar de proveniencia: prova (hash) de que o produto travado foi usado.
    # E a garantia FORTE de fidelidade da rota composicao (council 23/06).
    lock = {
        "composed": True,
        "baseline_png": a.product.replace("\\", "/"),
        "baseline_sha256": _sha256(a.product),
        "bg": a.bg, "harmonize": a.harmonize,
        "target_h": a.target_h, "x_frac": a.x_frac, "base_y": a.base_y,
    }
    with open(a.out + ".lock.json", "w", encoding="utf-8") as f:
        json.dump(lock, f, ensure_ascii=False, indent=2)
    print(f"OK {a.out} | produto {nw}x{nh} base_y={a.base_y} x={cx} bg={a.bg} harmonize={a.harmonize} | +lock.json sha={lock['baseline_sha256'][:12]}...")


if __name__ == "__main__":
    main()
