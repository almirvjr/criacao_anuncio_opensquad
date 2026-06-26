#!/usr/bin/env python3
"""
Detector deterministico de "dourado" no inox (lacuna #1 da geracao Nano Banana).
Quality-gate: mede o desvio de cor (calor) do corpo METALICO do produto e
reprova quando o aco inteiro puxa amarelo/laranja (parece latao/cobre).

Usa a mascara do cutout (cutout.py) pra isolar o produto. Metrica = calor
normalizado em RGB (invariante a brilho), NAO o LAB do Pillow (que neste build
nao centra a/b em 128 e dava lixo).

  w_med     = mediana de 100*(R-B)/(R+G+B) no metal  -> sinal principal
  warm_frac = fracao do metal com w por pixel > WARM_PX (quao espalhado o calor)

Calibrado (VIE_1066, BiRefNet) com ground-truth visual:
  fotos reais de estudio (prata neutro real) ......... w_med ~ -2 a 0
  v3 (prata neutro, melhor gerada) ................... 3.9
  v4 / capa-branco (bom, reflexo leve) ............... 9-10
  capa-branco-slim / preto (aceitavel) ............... 11-12
  v5 (borderline dourado) ............................ 15.7  <- reprova
  v2 (dourado) ....................................... 16.6  <- reprova
  capa-cinza (champanhe/dourado) ..................... 19.1  <- reprova
A marca QUER reflexo quente pontual (corpo prata + bordas quentes); o gate so
reprova quando o calor toma o corpo todo. Folga: bom<=12, ruim>=15 -> corte 14.

Uso:  python inox_cast.py FOTO.jpg [--json]
Exit: 2 = dourado (gate reprova / pedir retry), 0 = ok.
"""
import argparse, json, sys
import numpy as np
from PIL import Image
import cutout

WARM_PX = 14         # w por-pixel a partir do qual conta como "quente"
TH_DOURADO = 14.0    # w_med >= -> dourado (reprova)
TH_OK = 9.0          # w_med >= TH_OK e < TH_DOURADO -> reflexo quente desejado
TH_WARM_FRAC = 0.50  # ou metade+ do metal quente -> cast global = dourado


def cast_stats(path):
    img = Image.open(path).convert("RGB")
    mask = np.asarray(cutout.alpha_mask(img)) > 0
    rgb = np.asarray(img).astype(np.float32)
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    s = R + G + B
    # corpo de aco: dentro da mascara, tirando branco da tampa e preto do trim
    metal = mask & (s > 180) & (s < 660)
    if metal.sum() < 500:
        metal = mask
    w = 100.0 * (R - B) / (s + 1e-6)
    wm = w[metal]
    return {
        "w_med": round(float(np.median(wm)), 1),
        "warm_frac": round(float((wm > WARM_PX).mean()), 3),
        "n_metal": int(metal.sum()),
    }


def verdict(s):
    if s["w_med"] >= TH_DOURADO or s["warm_frac"] >= TH_WARM_FRAC:
        return "dourado"
    if s["w_med"] >= TH_OK:
        return "ok"           # reflexo quente desejado (corpo prata, bordas quentes)
    return "neutro"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("foto")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    s = cast_stats(a.foto)
    v = verdict(s)
    s["veredito"] = v
    if a.json:
        print(json.dumps(s))
    else:
        print(f"{a.foto.split('/')[-1]:26s} w_med={s['w_med']:+5.1f} "
              f"warm={100*s['warm_frac']:4.1f}%  -> {v.upper()}")
    sys.exit(2 if v == "dourado" else 0)


if __name__ == "__main__":
    main()
