"""Variacao que nao e de cor e fato fisico tirado das fotos (hub, Almir 25/10/2026, tigela BEL-4006-PAI).

Por que existe: a tigela M e G (mesma estampa "Peixes") saiu com o mesmo titulo nos dois anuncios do ML, com a
variacao do Magalu preenchida com a cor (a categoria Tigela varia pela Capacidade) e com a forma "Redonda" copiada
de um anuncio de concorrente, quando a peca e oval e as medidas estavam nas fotos do Almir.

- eixo(): por onde a familia varia (cor, tamanho...) a partir da grade do Olist.
- baixar_fotos(): copia pequena das fotos de cada SKU para {lote}/capas/fotos/<sku>/NN.jpg, para a etapa do texto
  LER as medidas, a capacidade e a forma nas fotos (o Claude da esteira nao baixa da internet).
- conferir(): trava da etapa do texto (medidas com fonte que nao e concorrente; forma igual a das fotos; titulo do ML
  de cada variacao com as medidas dela; campo de variacao do Magalu preenchido e diferente em cada SKU).
"""
import json
import re
import urllib.request
from pathlib import Path

import yaml

TRANSF = "c_pad,w_1200,h_1200,b_white,q_auto"
PEQUENA = "c_pad,w_900,h_900,b_white,q_75"
TETO_ML = 60
FONTE_PROIBIDA = re.compile(r"concorr|cat[aá]logo|\bmlb|anuncio do ml|anúncio do ml|outro vendedor", re.I)


def eixo(grades):
    """grades = [{"cor": "Peixes", "tamanho": "M"}, ...] -> "cor" se a cor muda; senao o 1o eixo que muda; None."""
    grades = [g or {} for g in grades]
    if len(grades) < 2:
        return None
    muda = [k for k in dict.fromkeys(k for g in grades for k in g)
            if len({str(g.get(k, "")).strip().casefold() for g in grades}) > 1]
    if not muda:
        return None
    return "cor" if "cor" in muda else muda[0]


def baixar_fotos(lote, abrir=urllib.request.urlopen):
    """Copia pequena das fotos de cada SKU (as do capas-<pai>.yaml). Devolve os SKUs que falharam (nao para o lote)."""
    lote = Path(lote)
    falhou = []
    for f in sorted((lote / "capas").glob("capas-*.yaml")):
        doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for v in doc.get("picture_ids_por_variacao") or []:
            sku = str(v.get("sku_variacao") or "")
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", sku):
                continue
            pasta = lote / "capas" / "fotos" / sku
            pasta.mkdir(parents=True, exist_ok=True)
            for i, url in enumerate(v.get("picture_ids") or [], 1):
                try:
                    with abrir(str(url).replace(TRANSF, PEQUENA), timeout=30) as r:
                        (pasta / f"{i:02d}.jpg").write_bytes(r.read())
                except Exception:  # noqa: BLE001
                    falhou.append(sku)
                    break
    return sorted(set(falhou))


def _num(x):
    try:
        return float(str(x).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _fmt(n):
    return (f"{n:.1f}".rstrip("0").rstrip(".")).replace(".", ",")


def _norm(v):
    return " ".join(str(v or "").split()).casefold()


def conferir(lote, pai, anuncio):
    """Motivo da reprovacao (texto) ou None."""
    lote, anuncio = Path(lote), Path(anuncio)
    entrada = lote / "anuncios-entrada.json"
    if not (anuncio.is_file() and entrada.is_file()):
        return None
    ent = next((x for x in json.loads(entrada.read_text(encoding="utf-8")).get("anuncios", []) if x.get("pai_sku") == pai), None)
    if not ent:
        return None
    a = yaml.safe_load(anuncio.read_text(encoding="utf-8")) or {}
    if a.get("status_copy") in ("aprovado", "tirado"):
        return None
    skus = [v.get("sku") for v in ent.get("variacoes") or [] if v.get("sku")]
    erros = []

    # 1) medidas de cada variacao, lidas nas nossas fotos (ou Olist/fornecedor), nunca de concorrente
    medidas = a.get("medidas_por_variacao") if isinstance(a.get("medidas_por_variacao"), dict) else {}
    com_foto = [s for s in skus if any((lote / "capas" / "fotos" / s).glob("*.jpg"))]
    for s in com_foto:
        m = medidas.get(s)
        if not isinstance(m, dict):
            erros.append(f"{s}: falta medidas_por_variacao (leia as fotos em capas/fotos/{s}/)")
            continue
        fonte = str(m.get("fonte") or "").strip()
        if not fonte or FONTE_PROIBIDA.search(fonte):
            erros.append(f"{s}: a fonte das medidas tem que ser a nossa foto, o Olist ou o fornecedor (veio: {fonte or 'vazia'})")
        tem_plano = _num(m.get("diametro_cm")) or (_num(m.get("comprimento_cm")) and _num(m.get("largura_cm")))
        if not (tem_plano and _num(m.get("altura_cm"))):
            erros.append(f"{s}: medidas incompletas (altura + diametro, ou altura + comprimento e largura)")
    formas = {_norm(m.get("forma"))[:4] for m in medidas.values() if isinstance(m, dict) and m.get("forma")}
    shape = _norm((a.get("attributes") or {}).get("SHAPE"))
    if shape and shape != "nao se aplica" and formas and shape[:4] not in formas:
        erros.append(f"SHAPE '{(a.get('attributes') or {}).get('SHAPE')}' diferente da forma nas fotos "
                     f"({', '.join(sorted({str(m.get('forma')) for m in medidas.values() if isinstance(m, dict) and m.get('forma')}))})")

    # 2) variacao que nao e cor: cada anuncio do ML com titulo proprio, com a largura e o comprimento dela
    por_var = a.get("por_variacao") if isinstance(a.get("por_variacao"), dict) else {}
    attrs = a.get("attributes") or {}
    for s, x in por_var.items():
        if s not in skus:
            erros.append(f"por_variacao: {s} nao e SKU deste produto")
            continue
        dup = sorted(set(((x or {}).get("attributes") or {})) & set(attrs))
        if dup:
            erros.append(f"{s}: {', '.join(dup)} esta na familia e na variacao (valor que muda por variacao fica SO em por_variacao)")
    if ent.get("eixo_variacao") and ent.get("eixo_variacao") != "cor":
        titulos = {}
        for s in skus:
            t = str(((por_var.get(s) or {}).get("titulo_ml")) or "").strip()
            if not t:
                erros.append(f"{s}: falta por_variacao.{s}.titulo_ml (as variacoes nao mudam de cor: cada anuncio do ML precisa de titulo proprio)")
                continue
            if len(t) > TETO_ML:
                erros.append(f"{s}: titulo do ML com {len(t)} letras (maximo {TETO_ML})")
            m = medidas.get(s) or {}
            nums = [_num(m.get(k)) for k in ("comprimento_cm", "largura_cm")] if _num(m.get("comprimento_cm")) else [_num(m.get("diametro_cm"))]
            falta = [_fmt(n) for n in nums if n and _fmt(n) not in t.replace(".", ",")]
            if falta:
                erros.append(f"{s}: o titulo do ML tem que trazer a medida dele ({' x '.join(_fmt(n) for n in nums if n)} cm); faltou {', '.join(falta)}")
            titulos.setdefault(_norm(t), []).append(s)
        erros += [f"titulo do ML igual em {', '.join(v)}" for v in titulos.values() if len(v) > 1]

    # 3) Magalu: o campo que a categoria usa para separar as variacoes, preenchido e diferente em cada SKU
    fm = a.get("ficha_magalu") if isinstance(a.get("ficha_magalu"), dict) else None
    cand = next((c for c in (ent.get("magalu") or {}).get("candidatas") or [] if fm and str(c.get("id")) == str(fm.get("categoria_id"))), None)
    if cand and len(skus) > 1:
        for nome in cand.get("variacao") or []:
            vals = {}
            for s in skus:
                linha = next((y for y in (por_var.get(s) or {}).get("magalu") or [] if _norm((y or {}).get("nome")) == _norm(nome)), None)
                v = str((linha or {}).get("valor") or "").strip()
                if not v and _norm(nome) == "cor":
                    v = next((str(x.get("cor") or "") for x in ent.get("variacoes") or [] if x.get("sku") == s), "")
                if not v:
                    erros.append(f"{s}: falta o '{nome}' do Magalu em por_variacao.{s}.magalu (e o campo que separa as variacoes nessa categoria)")
                    continue
                vals.setdefault(_norm(v), []).append(s)
            erros += [f"Magalu: '{nome}' igual em {', '.join(v)} (o Magalu nao separa as variacoes)" for v in vals.values() if len(v) > 1]
    if erros:
        return "variacoes e medidas: " + "; ".join(erros[:12]) + (f" (+{len(erros) - 12})" if len(erros) > 12 else "")
    return None
