#!/usr/bin/env python3
"""Gate de ENQUADRAMENTO da faixa-clara (render_faixa.py) — 2026-06-24.

Problema que resolve (infalivel, nao depende da atencao do assistente):
o layout faixa-clara desenha uma faixa creme nos 486px de baixo (band_top=714)
COM UM FADE de `fade_h` px ACIMA dela. Qualquer parte do produto abaixo do
topo do fade (band_top - fade_h = 674) se dissolve no creme e parece "cortada".
Erro real 2026-06-24: base do produto colocada em y700 -> pedal sumiu 2x.

Mesma filosofia do produto-travado (23/06) e do prompt_lint/--lock:
a verificacao vira CODIGO inpulavel, nao um checklist que eu posso esquecer.

Duas pecas:
  - autofit(base, ...)  -> PREVINE: reescala/reposiciona o produto p/ caber
    inteiro acima do fade (so encolhe, nunca amplia). So atua em fundo ~uniforme.
  - check_clip(base, ...) -> PEGA: mede o fundo do produto (cutout.alpha_mask,
    confiavel; concorda com dark-pixel) e exige folga ate o topo do fade.

`alpha_mask` (BiRefNet) e confiavel p/ o fundo do produto e EXCLUI a sombra de
chao — nao confundir sombra com produto (a sombra pode ser cortada pela faixa).

CLI:
  python framing_gate.py --base base.jpg            # so mede (exit 0/3)
  exit 0 = enquadramento ok, 3 = produto invade o fade (igual ao --lock).
"""
import argparse, os, sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cutout

W = H = 1200
BAND_H_DEFAULT = 486          # render_faixa: BAND_H
FADE_H_DEFAULT = 40           # render_faixa: fade_h acima da faixa
MARGIN_DEFAULT = 8            # folga minima do produto ate o topo do fade


def band_top(band_h=BAND_H_DEFAULT):
    return H - band_h


def fade_top(band_h=BAND_H_DEFAULT, fade_h=FADE_H_DEFAULT):
    """Acima desta linha a area e 100% limpa (sem creme)."""
    return band_top(band_h) - fade_h


def product_bbox(img):
    """bbox do produto via BiRefNet (exclui sombra de chao). None se vazio."""
    return cutout.alpha_mask(img.convert("RGB")).getbbox()


def _bg_uniform(img, tol=10):
    """Fundo ~uniforme? (autofit so e seguro com repad de cor unica).
    Amostra os 4 cantos; uniforme se variarem pouco entre si."""
    w, h = img.size
    pts = [(3, 3), (w - 4, 3), (3, h - 4), (w - 4, h - 4)]
    cs = [img.getpixel(p) for p in pts]
    chans = list(zip(*cs))
    return all(max(c) - min(c) <= tol for c in chans), cs[0]


def check_clip(base, band_h=BAND_H_DEFAULT, fade_h=FADE_H_DEFAULT, margin=MARGIN_DEFAULT):
    """Mede se o produto da base invade o fade/faixa.
    Retorna dict {ok, prod_bottom, fade_top, folga, motivo}."""
    base = base.convert("RGB")
    ft = fade_top(band_h, fade_h)
    bb = product_bbox(base)
    if bb is None:
        return {"ok": False, "prod_bottom": None, "fade_top": ft, "folga": None,
                "motivo": "produto nao detectado na base"}
    pb = bb[3]
    folga = ft - pb
    ok = folga >= margin
    motivo = (f"produto termina em y{pb}; topo do fade y{ft}; folga {folga}px "
              f"(min {margin})") + ("" if ok else " -> INVADE o fade/faixa")
    return {"ok": ok, "prod_bottom": pb, "fade_top": ft, "folga": folga, "motivo": motivo}


def autofit(base, band_h=BAND_H_DEFAULT, fade_h=FADE_H_DEFAULT,
            margin=12, top_min=70, shadow_keep=60):
    """Reenquadra a base p/ o produto caber inteiro acima do fade.
    So ENCOLHE (nunca amplia) e so atua em fundo ~uniforme (repad seguro).
    Retorna (nova_base, info)."""
    base = base.convert("RGB")
    ft = fade_top(band_h, fade_h)
    limit = ft - margin                       # fundo-alvo do produto
    bb = product_bbox(base)
    if bb is None:
        return base, {"changed": False, "motivo": "sem produto"}
    l, t, r, b = bb
    if b <= limit:
        return base, {"changed": False, "prod_bottom": b, "motivo": "ja cabe"}
    uniform, bg = _bg_uniform(base)
    if not uniform:
        return base, {"changed": False, "prod_bottom": b,
                      "motivo": "fundo nao-uniforme; autofit pulado (gate ainda barra)"}
    avail = limit - top_min                    # altura disponivel
    ph = b - t
    s = min(1.0, avail / ph) if ph > 0 else 1.0
    pad_top = 10
    crop = base.crop((0, max(0, t - pad_top), base.width, min(base.height, b + shadow_keep)))
    nw, nh = max(1, round(base.width * s)), max(1, round(crop.height * s))
    crop2 = crop.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGB", base.size, bg)
    prod_bottom_in_crop = (b - max(0, t - pad_top)) * s
    oy = round(limit - prod_bottom_in_crop)
    pcx = (l + r) // 2
    ox = round(base.width // 2 - pcx * s)
    canvas.paste(crop2, (ox, oy))
    return canvas, {"changed": True, "scale": round(s, 3), "prod_bottom_alvo": limit,
                    "motivo": f"reescalado x{round(s,3)} p/ caber acima do fade"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--band-h", type=int, default=BAND_H_DEFAULT)
    ap.add_argument("--margin", type=int, default=MARGIN_DEFAULT)
    a = ap.parse_args()
    r = check_clip(Image.open(a.base), band_h=a.band_h, margin=a.margin)
    tag = "OK" if r["ok"] else "REPROVA"
    print(f"[framing_gate] {tag} | {r['motivo']}")
    sys.exit(0 if r["ok"] else 3)


if __name__ == "__main__":
    main()
