#!/usr/bin/env python3
"""juiz_escala.py — Peca A do PLANO-LOOP-JUIZ-VISUAL (camada 1, deterministica).

Mede sozinho as duas coisas que ate 17/09/2026 dependiam do olho do Almir:

  1. FORMA do produto   = altura / largura do corpo. Alvo = medidas reais da ficha
                          (8L: 34/18 = 1,89). Pega produto esticado ou achatado.
  2. ESCALA na cena     = altura do produto / altura do movel (chao -> tampo).
                          Alvo = altura real / 90 cm (8L: 0,38; 5L: 0,27).

PRINCIPIO: **recusar vale mais que chutar.** Tres coisas podem dar errado, e em
todas o juiz devolve NAO_MEDIDO com o motivo, em vez de um numero inventado:
  - o detector de produto pegou o objeto errado (acontece quando a lixeira e
    pequena no quadro: na capa-v8 ele pegou o ARMARIO, 829 px de altura);
  - a bancada esta fora do quadro (foto ja aproximada) — ai a escala nao e
    medivel nessa foto, tem que medir na cena aberta ANTES de aproximar;
  - as bordas candidatas a bancada discordam muito entre si.

Exit: 0 tudo ok · 3 reprovou · 4 nao consegui medir (olho humano decide).
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..",
    "skills", "image-overlay", "scripts")))
import cutout  # noqa: E402

BANCADA_CM = 90.0
TOLERANCIA_FORMA = 0.05      # +/-5% na forma do produto
# ESCALA: faixa ACEITA, nao "alvo +/- x". Decisao do Almir em 22/09/2026, olhando as
# fotos: "~0,45 e aceitavel". A verdade fisica do 8L e 0,38 (34/90); o motor entrega
# 0,42-0,48. Entao:
#   - piso = a verdade fisica menos uma folguinha. ABAIXO disso o 8L fica com cara de
#     5L, que e exatamente o defeito da capa v8 que foi descartada.
#   - teto = o que o Almir aceitou olhando a imagem.
ESCALA_PISO_FATOR = 0.95     # 8L: 0,36
ESCALA_TETO_FATOR = 1.27     # 8L: 0,48
# Se o objeto detectado tiver forma muito fora do esperado, nao e o produto.
FATOR_PLAUSIVEL = 1.6        # aceita de 1,89/1,6 ate 1,89*1,6
# O detector (BiRefNet) e pesado: 20 fotos de 2048px em sequencia derrubaram a maquina
# por falta de memoria em 22/09/2026. Medimos RAZOES (altura/largura, produto/movel),
# que nao mudam com o tamanho da imagem — entao reduzir antes de medir e de graça.
# Conferido: a mesma foto deu 1,91 em 1200px e 1,92 em 2048px.
MAX_LADO = 1200


def _caixa(im):
    m = np.array(cutout.alpha_mask(im)) > 128
    lin, col = m.sum(axis=1), m.sum(axis=0)
    ys, xs = np.nonzero(lin)[0], np.nonzero(col)[0]
    if len(ys) == 0 or len(xs) == 0:
        return None
    y0, y1 = int(ys[0]), int(ys[-1])
    alt = y1 - y0 + 1
    faixa = lin[y0 + int(alt * 0.35): y0 + int(alt * 0.75)]
    larg = int(np.percentile(faixa, 90)) if len(faixa) else int(col.max())
    return {"x0": int(xs[0]), "x1": int(xs[-1]), "y0": y0, "y1": y1,
            "altura": alt, "largura": max(1, larg)}


def _bordas_da_bancada(im, caixa):
    """Bordas horizontais largas ACIMA do produto. A bancada e uma delas."""
    W, H = im.size
    g = np.array(im.convert("L")).astype(float)
    folga = int(0.06 * W)
    usar = np.ones(W, bool)
    usar[max(0, caixa["x0"] - folga): min(W, caixa["x1"] + folga)] = False
    if usar.sum() < 0.2 * W:            # produto ocupa quase toda a largura
        usar[:] = True
    grad = np.abs(np.diff(g, axis=0))[:, usar]
    energia, atravessa = grad.mean(axis=1), (grad > 12).mean(axis=1)
    topo = caixa["y0"]
    if topo < 30:
        return []
    corte = np.percentile(energia[:topo], 90)
    achados = []
    for r in range(5, topo):
        if atravessa[r] > 0.45 and energia[r] > corte:
            if not achados or r - achados[-1]["y"] > 25:
                achados.append({"y": r, "atravessa": float(atravessa[r]),
                                "forca": float(energia[r])})
            elif energia[r] > achados[-1]["forca"]:
                achados[-1] = {"y": r, "atravessa": float(atravessa[r]),
                               "forca": float(energia[r])}
    return achados


def julgar(path, alt_cm, diam_cm, bancada_cm=BANCADA_CM, tampa="fechada", max_lado=MAX_LADO):
    """tampa="aberta": a silhueta inclui a tampa levantada, entao NEM forma NEM escala
    valem (calibracao 18/09/2026: a capa do 5L aprovada reprovava por isso, falso
    positivo). Nesses casos o juiz recusa e o olho humano decide."""
    im = Image.open(path).convert("RGB")
    orig = im.size
    if max_lado and max(im.size) > max_lado:
        f = max_lado / max(im.size)
        im = im.resize((max(1, round(im.width * f)), max(1, round(im.height * f))), Image.LANCZOS)
    W, H = im.size
    forma_alvo = alt_cm / diam_cm
    escala_alvo = alt_cm / bancada_cm
    r = {"arquivo": os.path.basename(path), "px": f"{orig[0]}x{orig[1]}",
         "medido_em": f"{W}x{H}",
         "alvos": {"forma": round(forma_alvo, 2), "escala": round(escala_alvo, 2)}}

    if tampa == "aberta":
        r["veredito"] = "NAO_MEDIDO"
        r["motivo"] = ("foto de tampa ABERTA: a tampa levantada entra na silhueta e estica "
                       "a medida (forma e escala). Este juiz so cobre tampa FECHADA. "
                       "Conferir a olho.")
        return r

    caixa = _caixa(im)
    if caixa is None:
        r["veredito"] = "NAO_MEDIDO"
        r["motivo"] = "nao achei produto nenhum na imagem"
        return r

    # produto cortado pelo quadro (foto de estudio/detalhe) -> a altura medida nao e
    # a altura do produto. Calibracao 18/09/2026 contra as fotos 3, 4 e 9 do 5L.
    margem = max(3, int(0.004 * max(W, H)))
    encosta = []
    if caixa["y0"] <= margem: encosta.append("topo")
    if caixa["y1"] >= H - 1 - margem: encosta.append("base")
    if caixa["x0"] <= margem: encosta.append("esquerda")
    if caixa["x1"] >= W - 1 - margem: encosta.append("direita")
    if encosta:
        r["veredito"] = "NAO_MEDIDO"
        r["motivo"] = (f"o produto encosta na borda do quadro ({', '.join(encosta)}): esta "
                       f"cortado, entao a altura medida nao e a altura dele. Este juiz cobre "
                       f"foto ambientada com o produto INTEIRO no quadro. Conferir a olho.")
        return r

    if caixa["largura"] <= 2:
        r["veredito"] = "NAO_MEDIDO"
        r["motivo"] = ("a silhueta detectada nao tem corpo (largura ~0 px): a mascara saiu "
                       "vazada ou pegou so um contorno. Conferir a olho.")
        return r
    forma = caixa["altura"] / caixa["largura"]
    r["produto"] = {"altura_px": caixa["altura"], "largura_px": caixa["largura"],
                    "ocupa_da_altura": round(caixa["altura"] / H, 3)}

    # o detector pegou o objeto certo?
    if not (forma_alvo / FATOR_PLAUSIVEL <= forma <= forma_alvo * FATOR_PLAUSIVEL):
        r["veredito"] = "NAO_MEDIDO"
        r["motivo"] = (f"o objeto detectado tem forma {forma:.2f}, longe demais do produto "
                       f"({forma_alvo:.2f}) — provavelmente o detector pegou outra coisa "
                       f"(movel, parede). Conferir a olho.")
        r["forma"] = {"medida": round(forma, 2)}
        return r

    ok_forma = abs(forma / forma_alvo - 1) <= TOLERANCIA_FORMA
    r["forma"] = {"medida": round(forma, 2), "alvo": round(forma_alvo, 2),
                  "erro_pct": round(100 * (forma / forma_alvo - 1), 1), "ok": ok_forma}

    bordas = _bordas_da_bancada(im, caixa)
    razoes = sorted(caixa["altura"] / (caixa["y1"] - b["y"]) for b in bordas
                    if caixa["y1"] - b["y"] > caixa["altura"])
    if not razoes:
        r["escala"] = {"ok": None,
                       "motivo": "bancada fora do quadro (ou nao achei borda larga acima "
                                 "do produto). Medir a escala na cena ABERTA, antes de aproximar."}
        r["veredito"] = "REPROVA" if not ok_forma else "NAO_MEDIDO"
        r["motivo"] = ("forma reprovou" if not ok_forma else
                       "forma ok, mas a escala nao e medivel nesta foto")
        return r

    espalhamento = razoes[-1] - razoes[0]
    medida = float(np.median(razoes))
    # Calibracao 18/09/2026: nas cenas boas o detector acha 2 a 4 bordas concordantes.
    # UMA borda sozinha nao se confirma — foi o caso da foto-08 do 5L (banheiro com
    # gabinete SUSPENSO, onde a regua chao->tampo nem se aplica). Uma so = nao cravo.
    confianca = "alta" if (espalhamento <= 0.05 and len(razoes) >= 2) else "baixa"
    piso, teto = escala_alvo * ESCALA_PISO_FATOR, escala_alvo * ESCALA_TETO_FATOR
    ok_escala = piso <= medida <= teto
    r["escala"] = {"medida": round(medida, 2), "alvo": round(escala_alvo, 2),
                   "faixa_aceita": [round(piso, 2), round(teto, 2)],
                   "candidatos": [round(x, 2) for x in razoes],
                   "espalhamento": round(espalhamento, 2),
                   "confianca": confianca, "ok": ok_escala}

    # A FORMA se mede sozinha e nao depende da bancada: se ela reprova, e reprova,
    # mesmo que a escala fique sem medida.
    if not ok_forma:
        r["veredito"] = "REPROVA"
        r["motivo"] = f"forma {forma:.2f} (alvo {forma_alvo:.2f})"
        if confianca == "baixa":
            r["motivo"] += "; escala nao cravada"
        elif not ok_escala:
            r["motivo"] += f" e escala {medida:.2f} (faixa {piso:.2f}-{teto:.2f})"
    elif confianca == "baixa":
        r["veredito"] = "NAO_MEDIDO"
        r["motivo"] = ("forma ok; achei so uma borda candidata a bancada, nao cravo a escala"
                       if len(razoes) < 2 else
                       f"forma ok; as bordas candidatas a bancada discordam "
                       f"({razoes[0]:.2f} a {razoes[-1]:.2f}), nao cravo a escala")
    elif ok_escala:
        r["veredito"] = "APROVA"
        r["motivo"] = "forma e escala dentro do alvo"
    else:
        r["veredito"] = "REPROVA"
        r["motivo"] = (f"escala {medida:.2f} fora da faixa aceita "
                       f"{piso:.2f}-{teto:.2f} (verdade fisica {escala_alvo:.2f})")
    return r


def _texto(r):
    v = r["veredito"]
    linhas = [f"{r['arquivo']}  ->  {v}: {r['motivo']}"]
    if "forma" in r and "alvo" in r.get("forma", {}):
        f = r["forma"]
        linhas.append(f"   forma do produto: {f['medida']} (alvo {f['alvo']}, "
                      f"{f['erro_pct']:+.1f}%) {'OK' if f['ok'] else 'FORA'}")
    e = r.get("escala") or {}
    if "medida" in e:
        linhas.append(f"   escala na cena  : {e['medida']} (aceita {e['faixa_aceita'][0]}-{e['faixa_aceita'][1]}) "
                      f"{'OK' if e['ok'] else 'FORA'} | confianca {e['confianca']} "
                      f"| candidatos {e['candidatos']}")
    elif e.get("motivo"):
        linhas.append(f"   escala na cena  : {e['motivo']}")
    return "\n".join(linhas)


def main():
    ap = argparse.ArgumentParser(description="Juiz de escala e forma do produto (camada 1).")
    ap.add_argument("fotos", nargs="+")
    ap.add_argument("--altura-cm", type=float, required=True, help="altura real do produto")
    ap.add_argument("--diametro-cm", type=float, required=True, help="diametro real do corpo")
    ap.add_argument("--bancada-cm", type=float, default=BANCADA_CM)
    ap.add_argument("--tampa", choices=["fechada", "aberta"], default="fechada",
                    help="aberta = o juiz recusa medir (a tampa levantada falseia a silhueta)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    saidas = [julgar(f, a.altura_cm, a.diametro_cm, a.bancada_cm, a.tampa) for f in a.fotos]
    if a.json:
        print(json.dumps(saidas, indent=2, ensure_ascii=False))
    else:
        for s in saidas:
            print(_texto(s))
    if any(s["veredito"] == "REPROVA" for s in saidas):
        sys.exit(3)
    if any(s["veredito"] == "NAO_MEDIDO" for s in saidas):
        sys.exit(4)
    sys.exit(0)


if __name__ == "__main__":
    main()
