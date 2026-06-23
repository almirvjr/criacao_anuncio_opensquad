#!/usr/bin/env python3
"""Trava um PRODUTO como asset fiel imutavel (pipeline 'produto travado', 23/06).

Gera o recorte BiRefNet (PNG RGBA) do hero APROVADO, calcula o sha256 do PNG e
grava um manifesto <pai_sku>.json. O manifesto + PNG sao a FONTE UNICA do produto
fiel: compose.py compoe a partir do PNG; o gate de fidelidade (fidelity.py /
qa_imagens.py) compara as imagens geradas contra esse PNG travado.

Reusa cutout.alpha_mask (BiRefNet). Reusavel pro catalogo inteiro: 1 trava/produto.

Uso:
  python lock_product.py --pai-sku VIE_1066-PAI --cor-heroi Branco \
     --hero <hero_aberto.jpg> [--hero-fechado <hero_fechado.jpg>] \
     [--out-dir squads/ml-anuncios/pipeline/data/produtos-travados]
"""
import argparse, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cutout
from PIL import Image

DEFAULT_OUT = "squads/ml-anuncios/pipeline/data/produtos-travados"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def recortar(hero_path, png_out):
    """Recorte BiRefNet -> PNG RGBA recortado no bbox do produto. Retorna bbox."""
    img = Image.open(hero_path).convert("RGB")
    m = cutout.alpha_mask(img)
    bb = m.getbbox()
    if bb is None:
        raise SystemExit(f"ERRO: cutout vazio em {hero_path}")
    rgba = img.convert("RGBA"); rgba.putalpha(m)
    rgba.crop(bb).save(png_out)
    return bb, img.size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pai-sku", required=True)
    ap.add_argument("--cor-heroi", required=True)
    ap.add_argument("--hero", required=True, help="hero aprovado (tampa aberta)")
    ap.add_argument("--hero-fechado", default=None, help="hero aprovado (tampa fechada), opcional")
    ap.add_argument("--out-dir", default=DEFAULT_OUT)
    ap.add_argument("--data-aprovacao", required=True, help="YYYY-MM-DD (passe a data; o ambiente nao tem clock)")
    a = ap.parse_args()

    os.makedirs(a.out_dir, exist_ok=True)
    man = {
        "pai_sku": a.pai_sku,
        "cor_heroi": a.cor_heroi,
        "data_aprovacao": a.data_aprovacao,
        "assets": {},
    }

    for nome, hero in [("aberto", a.hero), ("fechado", a.hero_fechado)]:
        if not hero:
            continue
        if not os.path.exists(hero):
            raise SystemExit(f"ERRO: hero nao encontrado: {hero}")
        png_out = os.path.join(a.out_dir, f"{a.pai_sku}_{nome}.png")
        bb, size = recortar(hero, png_out)
        man["assets"][nome] = {
            "hero_fonte": hero.replace("\\", "/"),
            "png": png_out.replace("\\", "/"),
            "sha256": sha256(png_out),
            "bbox_no_hero": list(bb),
            "hero_size": list(size),
        }
        print(f"  travado [{nome}]: {png_out} | bbox={bb} | sha256={man['assets'][nome]['sha256'][:12]}...")

    man_path = os.path.join(a.out_dir, f"{a.pai_sku}.json")
    with open(man_path, "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=2)
    print(f"OK manifesto: {man_path}")


if __name__ == "__main__":
    main()
