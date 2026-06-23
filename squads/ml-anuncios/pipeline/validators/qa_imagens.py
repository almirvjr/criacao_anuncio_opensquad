#!/usr/bin/env python3
"""
qa_imagens.py — QA que OLHA a imagem (Fase 4 da blindagem StorySelling).

Fecha o maior buraco do pipeline: ate hoje o validador (Vinicius) so lia o
metadata que o Felipe escreveu sobre as fotos — nunca abria os JPGs. Resultado:
foto dourada, produto distorcido ou claim no pixel passavam.

Este script abre CADA foto entregue e trava deterministicamente o que da pra
medir por maquina:
  1. DIMENSAO  — tem que ser 1200x1200 exatos.
  2. PRODUTO PRESENTE — o cutout (BiRefNet) tem que achar o produto na imagem
     (geracao que perdeu/distorceu o produto a ponto de sumir = bloqueia).
  3. COR DO INOX — re-roda inox_cast.py; veredito 'dourado' BLOQUEIA
     (antes era "marca falha e segue (Vinicius decide)" — e o Vinicius nao via
      a imagem, entao ninguem decidia; agora e bloqueio duro).

O que NAO da pra medir por maquina (escala lixeira/bancada ~1/3, marca no pixel,
foto bate com a funcao do slot) fica como verificacao VISUAL OBRIGATORIA do
Vinicius no step-08 — que passa a abrir os JPGs, nao o metadata.

Uso:
  python qa_imagens.py <pasta_com_fotos> [--inox] [--brief <brief.yaml>]
Saida: codigo 0 = QA OK | codigo 1 = REPROVADO (lista de bloqueios).
"""

import argparse
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# skills/image-overlay/scripts fica 4 niveis acima (raiz do projeto)
SKILLS = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..",
                                      "skills", "image-overlay", "scripts"))
if SKILLS not in sys.path:
    sys.path.insert(0, SKILLS)

DIM_EXIGIDA = (1200, 1200)
AREA_MIN_PRODUTO = 0.02   # bbox do produto < 2% da imagem = produto sumiu
OFFSET_EIXO_MAX = 0.10    # centro do produto pode desviar no maximo 10% da largura
# slots em que o produto TEM que estar no eixo (centralizado): SO os studio.
# A CAPA (1) e ambiente: a lixeira vai num CANTO/nicho (encostada na bancada),
# nao no centro do piso — entao o gate de eixo NAO se aplica a ela (so visual).
SLOTS_CENTRALIZADOS = {4, 7, 9}


# ----- checagens puras (testaveis sem abrir imagem) ------------------------
def check_dimensao(size):
    if tuple(size) != DIM_EXIGIDA:
        return ("DIM_ERRADA",
                f"dimensao {size[0]}x{size[1]} != {DIM_EXIGIDA[0]}x{DIM_EXIGIDA[1]} exigida")
    return None


def check_produto_presente(bbox, img_w, img_h):
    if not bbox:
        return ("PRODUTO_AUSENTE", "cutout nao encontrou produto na imagem")
    l, t, r, b = bbox
    frac = ((r - l) * (b - t)) / float(img_w * img_h)
    if frac < AREA_MIN_PRODUTO:
        return ("PRODUTO_AUSENTE",
                f"produto ocupa so {frac*100:.1f}% da imagem (<{AREA_MIN_PRODUTO*100:.0f}%) — provavelmente sumiu/distorceu")
    return None


def check_eixo(bbox, img_w):
    """Produto centralizado: o centro horizontal do bbox tem que ficar perto do
    centro da imagem. Retorna erro se desviar mais que OFFSET_EIXO_MAX."""
    if not bbox:
        return None  # ausencia tratada em check_produto_presente
    l, _, r, _ = bbox
    centro_prod = (l + r) / 2.0
    offset = abs(centro_prod - img_w / 2.0) / float(img_w)
    if offset > OFFSET_EIXO_MAX:
        lado = "direita" if centro_prod > img_w / 2.0 else "esquerda"
        return ("FORA_DO_EIXO",
                f"produto desviado {offset*100:.0f}% pra {lado} (max {OFFSET_EIXO_MAX*100:.0f}%) — centralizar no eixo")
    return None


def slot_do_arquivo(path):
    """Numero do slot pelo nome do arquivo (foto-NN... ou capa->1)."""
    nome = os.path.basename(path).lower()
    if "capa" in nome:
        return 1
    m = re.search(r"foto-?(\d+)", nome)
    return int(m.group(1)) if m else None


def check_dourado(verdict_str):
    if verdict_str == "dourado":
        return ("COR_DOURADA",
                "inox puxou amarelo/laranja (parece latao) - regenerar com 'inox PRATA NEUTRO'. "
                "Vinicius confirma na imagem: se o cast quente esta num objeto NAO-metalico dominante "
                "(ex.: caixa de papelao na foto de clareza), e falso-positivo do cutout - documentar override.")
    return None


def _manifest_shas(manifest_path):
    import json
    with open(manifest_path, encoding="utf-8") as fh:
        man = json.load(fh)
    return {a["sha256"] for a in man.get("assets", {}).values()}


def check_produto_fiel(path, manifest_path):
    """PROVENIENCIA (rota composicao): se existe sidecar '<path>.lock.json', o
    produto foi composto a partir de um PNG travado — confere o sha contra o
    manifesto. Garantia FORTE e byte-exata (council 23/06). Fotos SEM sidecar
    (rota one-shot legitima) nao sao bloqueadas aqui — caem nos outros checks."""
    import json
    side = path + ".lock.json"
    if not os.path.exists(side):
        return None  # one-shot: sem proveniencia a conferir
    if not manifest_path or not os.path.isfile(manifest_path):
        return ("PRODUTO_INFIEL", "foto tem sidecar de composicao mas nenhum manifesto (--lock) foi dado p/ conferir")
    try:
        sha = json.load(open(side, encoding="utf-8")).get("baseline_sha256", "")
    except Exception as ex:
        return ("PRODUTO_INFIEL", f"sidecar .lock.json ilegivel: {ex}")
    if sha not in _manifest_shas(manifest_path):
        return ("PRODUTO_INFIEL",
                f"produto composto (sha {sha[:12]}...) nao consta no manifesto travado — produto trocado/adulterado")
    return None


# ----- wiring com PIL + cutout + inox_cast ---------------------------------
def qa_imagem(path, is_inox, lock_manifest=None):
    """Retorna lista de blocks (code,msg) para uma foto."""
    from PIL import Image
    import cutout
    blocks = []
    try:
        img = Image.open(path).convert("RGB")
    except Exception as e:
        return [("ABRIR_FALHOU", f"nao abriu a imagem: {e}")]

    e = check_dimensao(img.size)
    if e:
        blocks.append(e)

    e = check_produto_fiel(path, lock_manifest)
    if e:
        blocks.append(e)

    try:
        bbox = cutout.mask_bbox(img)
        e = check_produto_presente(bbox, img.size[0], img.size[1])
        if e:
            blocks.append(e)
        # eixo: so nos slots que exigem produto centralizado (capa + studio)
        if slot_do_arquivo(path) in SLOTS_CENTRALIZADOS:
            e = check_eixo(bbox, img.size[0])
            if e:
                blocks.append(e)
    except Exception as ex:
        blocks.append(("CUTOUT_FALHOU", f"cutout falhou: {ex}"))

    if is_inox:
        try:
            import inox_cast
            v = inox_cast.verdict(inox_cast.cast_stats(path))
            e = check_dourado(v)
            if e:
                blocks.append((e[0], e[1] + f" [w_med veredito={v}]"))
        except Exception as ex:
            blocks.append(("INOX_CAST_FALHOU", f"inox_cast falhou: {ex}"))

    return blocks


def material_eh_inox(brief):
    if not isinstance(brief, dict):
        return False
    mat = brief.get("dados_produto", {}).get("material", {})
    txt = mat.get("valor", "") if isinstance(mat, dict) else str(mat)
    return any(k in str(txt).lower() for k in ("inox", "aco", "aço", "steel"))


def coletar_fotos(pasta):
    """JPGs entregues na pasta (ignora subpastas _base/_redesign/etc)."""
    fotos = []
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        fotos += glob.glob(os.path.join(pasta, ext))
    return sorted(fotos)


def main():
    ap = argparse.ArgumentParser(description="QA deterministico das fotos do anuncio.")
    ap.add_argument("pasta", help="Pasta com as fotos entregues (foto-NN.jpg)")
    ap.add_argument("--inox", action="store_true", help="Forca o gate de cor do inox")
    ap.add_argument("--brief", help="brief.yaml — auto-detecta material inox")
    ap.add_argument("--lock", help="manifesto do produto travado (produtos-travados/SKU.json) p/ conferir proveniencia das fotos compostas")
    args = ap.parse_args()

    if not os.path.isdir(args.pasta):
        print(f"ERRO: pasta nao encontrada: {args.pasta}", file=sys.stderr)
        sys.exit(2)

    is_inox = args.inox
    if args.brief and os.path.isfile(args.brief):
        import yaml
        with open(args.brief, encoding="utf-8") as fh:
            is_inox = is_inox or material_eh_inox(yaml.safe_load(fh))

    fotos = coletar_fotos(args.pasta)
    if not fotos:
        print(f"ERRO: nenhuma foto em {args.pasta}", file=sys.stderr)
        sys.exit(2)

    total_blocks = []
    print(f"QA de {len(fotos)} foto(s) em {args.pasta} (inox={is_inox}):")
    for f in fotos:
        blocks = qa_imagem(f, is_inox, lock_manifest=args.lock)
        nome = os.path.basename(f)
        if blocks:
            for code, msg in blocks:
                print(f"  [REPROVA] {nome}: [{code}] {msg}")
                total_blocks.append((nome, code, msg))
        else:
            print(f"  [ok]      {nome}")

    if total_blocks:
        print(f"\nQA REPROVADO - {len(total_blocks)} bloqueio(s). Fotos voltam pro Felipe.")
        sys.exit(1)
    print("\nQA OK - todas as fotos passaram no gate deterministico (dimensao, produto, cor).")
    sys.exit(0)


if __name__ == "__main__":
    main()
