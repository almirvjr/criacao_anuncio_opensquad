#!/usr/bin/env python3
"""Gate de fidelidade do produto (pipeline 'produto travado', 23/06).

Duas garantias, conforme a ROTA da imagem (council 23/06):

1) PROVENIENCIA (rota COMPOSICAO) — garantia FORTE, por construcao.
   compose.py cola o PNG travado e grava um sidecar '<img>.lock.json' com o
   sha256 do PNG usado. verify_provenance() confere esse sha contra o manifesto
   do produto travado. Byte-exato, deterministico, sem ruido. E o "hash da
   camada produto" recomendado pelo council.

2) DISASTRE (rota ONE-SHOT, ex.: slot 7 com pe) — rede minima, honesta.
   O produto e re-renderizado (pose/luz/reflexo mudam), entao NAO da pra cravar
   fidelidade fina por pixel sem falso-positivo. disaster_check() so pega
   DESASTRE: produto ausente ou area absurda. Fidelidade fina nessa rota e
   julgada pelo olho humano + inox_cast (cor). Isso e explicito por design:
   por isso a composicao e o default e o one-shot e a excecao rara.

Usa cutout.alpha_mask (BiRefNet). Deps: numpy, PIL, skimage (informativo).

CLI:
  python fidelity.py --output img.jpg --manifest produtos-travados/SKU.json --modo provenancia
  python fidelity.py --output img.jpg --baseline travado.png --modo disastre
  exit 0 = passou, 1 = reprovou.
"""
import argparse, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath("skills/image-overlay/scripts"))
import numpy as np
from PIL import Image
try:
    import cutout
except Exception:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "image-overlay", "scripts"))
    import cutout

AREA_MIN, AREA_MAX = 0.02, 0.97   # fracao da imagem ocupada pelo produto


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest_shas(manifest_path):
    with open(manifest_path, encoding="utf-8") as f:
        man = json.load(f)
    return {a["sha256"]: a["png"] for a in man.get("assets", {}).values()}


def verify_provenance(image_path, manifest_path):
    """Rota COMPOSICAO: confere o sidecar .lock.json contra o manifesto."""
    side = image_path + ".lock.json"
    if not os.path.exists(side):
        return {"ok": False, "rota": "provenancia", "motivo": "sem sidecar .lock.json (imagem nao foi composta a partir de produto travado)"}
    with open(side, encoding="utf-8") as f:
        lock = json.load(f)
    sha = lock.get("baseline_sha256", "")
    shas = manifest_shas(manifest_path)
    if sha in shas:
        return {"ok": True, "rota": "provenancia", "motivo": f"produto travado confirmado (sha {sha[:12]}...)", "png": shas[sha]}
    return {"ok": False, "rota": "provenancia", "motivo": f"sha do sidecar ({sha[:12]}...) nao consta no manifesto {os.path.basename(manifest_path)}"}


def _area_frac(path):
    img = Image.open(path)
    if img.mode == "RGBA" and img.getextrema()[3][0] < 255:
        m = img.split()[-1]
    else:
        m = cutout.alpha_mask(img.convert("RGB"))
    arr = np.asarray(m) > 10
    return float(arr.mean()), m.getbbox()


def disaster_check(output_path):
    """Rota ONE-SHOT: so pega desastre (produto ausente/area absurda)."""
    frac, bb = _area_frac(output_path)
    if bb is None or frac < AREA_MIN:
        return {"ok": False, "rota": "disastre", "motivo": f"produto ausente/minusculo (area={frac:.3f}<{AREA_MIN})", "area": round(frac, 3)}
    if frac > AREA_MAX:
        return {"ok": False, "rota": "disastre", "motivo": f"produto ocupa quase tudo (area={frac:.3f}>{AREA_MAX})", "area": round(frac, 3)}
    return {"ok": True, "rota": "disastre", "motivo": f"produto presente (area={frac:.3f}); fidelidade fina = olho humano + inox_cast", "area": round(frac, 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ap.add_argument("--manifest", help="manifesto do produto travado (modo provenancia)")
    ap.add_argument("--baseline", help="PNG travado (compat; modo disastre nao usa)")
    ap.add_argument("--modo", choices=["provenancia", "disastre"], default="disastre")
    a = ap.parse_args()
    if a.modo == "provenancia":
        if not a.manifest:
            ap.error("--modo provenancia requer --manifest")
        r = verify_provenance(a.output, a.manifest)
    else:
        r = disaster_check(a.output)
    tag = "OK" if r["ok"] else "REPROVA"
    print(f"[fidelity:{r['rota']}] {tag} | {r['motivo']}")
    sys.exit(0 if r["ok"] else 1)


if __name__ == "__main__":
    main()
