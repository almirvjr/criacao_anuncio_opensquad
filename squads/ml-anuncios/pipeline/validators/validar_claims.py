#!/usr/bin/env python3
"""
validar_claims.py — GUARDA ANTI-CLAIM-FALSO (Fase 2 da blindagem StorySelling).

Impede que o anuncio AFIRME uma feature que o produto NAO tem, e OBRIGA a
declarar as limitacoes (transparencia). E a trava que fecha o caso do "balde":
nossas lixeiras 5L/8L nao tem balde removivel — estampar "balde interno" numa
foto que deveria REDUZIR devolucao viraria gerador de devolucao.

Como funciona:
  1. De `limitacoes[]`, deriva os "termos policiados" (o que o produto NAO tem).
     Ex.: "Modelo sem balde interno" -> termo policiado "balde interno".
  2. Varre TODO texto de overlay do brief (headline/subheadline/badge/cta/selos
     dos 10 slots) — e, se informado, o overlay que o Felipe de fato renderizou.
  3. Se algum overlay AFIRMA um termo policiado (sem negacao) -> BLOQUEIA (claim falso).
     Se o mesmo termo aparece NEGADO ("sem balde") -> e transparencia, OK.
  4. Para cada limitacao com `disclosure_foto`, exige que a foto declare a
     limitacao (transparencia obrigatoria — inverte a regra de "esconder ponto fraco").

Uso:
  python validar_claims.py <brief.yaml> [--overlay <arquivo overlay do Felipe>]

Saida: codigo 0 = SEM CLAIM FALSO | codigo 1 = BLOQUEADO.
A autoridade e este script; ele roda no step-04 (apos validar_brief) e no step-07 (gate do Felipe).
"""

import argparse
import os
import re
import sys
import unicodedata

# Negacoes que indicam DISCLOSURE (limitacao declarada honestamente), nao claim.
NEGACOES = {"sem", "nao"}
# janela (em palavras) antes do termo onde procuramos a negacao
JANELA_NEGACAO = 3

# Features de alto risco comuns na categoria: se AFIRMADAS no overlay e NAO
# presentes em dados_produto.caracteristicas nem cobertas por limitacoes -> WARN.
FEATURES_ALTO_RISCO = [
    "balde interno", "balde removivel", "cesto interno", "cesto removivel",
    "sensor", "automatic", "automatico", "soft close", "amortecedor",
    "fechamento suave", "antiderrapante", "tampa basculante", "abertura automatica",
]


def norm(s):
    if not isinstance(s, str):
        s = str(s)
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"\([^)]*\)", " ", s)          # remove parenteticos
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()


def derivar_termo_policiado(limitacao_texto):
    """De 'Modelo sem balde interno (usa saco comum)' -> ('balde interno', True).
    Retorna (termo, eh_ausencia). eh_ausencia=True quando ha negacao explicita."""
    n = norm(limitacao_texto)
    toks = n.split()
    for i, t in enumerate(toks):
        if t in NEGACOES:
            resto = toks[i + 1:]
            # descarta conectores logo apos a negacao (ex.: "nao vem com")
            while resto and resto[0] in {"vem", "com", "o", "a", "de", "tem", "possui", "acompanha"}:
                resto = resto[1:]
            termo = " ".join(resto).strip()
            return (termo, True) if termo else ("", False)
    # sem negacao: nao da pra derivar termo de ausencia; usa palavra mais significativa
    conteudo = [t for t in toks if len(t) >= 4]
    chave = max(conteudo, key=len) if conteudo else ""
    return (chave, False)


def afirmado(termo, overlay_norm):
    """True se `termo` aparece em `overlay_norm` SEM negacao na janela anterior."""
    if not termo:
        return False
    toks = overlay_norm.split()
    termo_toks = termo.split()
    L = len(termo_toks)
    for i in range(len(toks) - L + 1):
        if toks[i:i + L] == termo_toks:
            janela = toks[max(0, i - JANELA_NEGACAO):i]
            if not any(w in NEGACOES for w in janela):
                return True  # apareceu afirmado
    return False


def declarado(termo, overlay_norm):
    """True se `termo` aparece NEGADO (disclosure) em `overlay_norm`."""
    if not termo:
        return False
    toks = overlay_norm.split()
    termo_toks = termo.split()
    L = len(termo_toks)
    for i in range(len(toks) - L + 1):
        if toks[i:i + L] == termo_toks:
            janela = toks[max(0, i - JANELA_NEGACAO):i]
            if any(w in NEGACOES for w in janela):
                return True
    return False


def coletar_overlays(brief):
    """Retorna lista de (numero_foto, texto) com todo overlay do brief."""
    out = []
    for f in brief.get("briefing_fotos") or []:
        n = f.get("numero")
        for campo in ("headline", "subheadline", "badge", "cta"):
            if f.get(campo):
                out.append((n, f[campo]))
        for selo in f.get("selos_visuais") or []:
            if isinstance(selo, dict) and selo.get("texto"):
                out.append((n, selo["texto"]))
            elif isinstance(selo, str):
                out.append((n, selo))
    return out


def validar_claims(brief, overlays_extra=None):
    """Retorna (blocks, warns). blocks vazio = passou."""
    blocks, warns = [], []
    if not isinstance(brief, dict):
        return [("BRIEF_INVALIDO", "brief nao e mapa")], []

    overlays = coletar_overlays(brief)
    if overlays_extra:
        overlays += [(None, t) for t in overlays_extra]

    carac_norm = norm(" ".join(
        str(v) for v in _flatten(brief.get("dados_produto", {}).get("caracteristicas", {}))
    ))

    lims = brief.get("limitacoes") or []
    termos = []  # (termo, eh_ausencia, disclosure_foto, texto_original)
    for lim in lims:
        if not isinstance(lim, dict) or not lim.get("texto"):
            continue
        termo, eh_aus = derivar_termo_policiado(lim["texto"])
        termos.append((termo, eh_aus, lim.get("disclosure_foto"), lim["texto"]))

    # 1) CLAIM FALSO: overlay afirma termo de ausencia
    for termo, eh_aus, _, texto_orig in termos:
        if not eh_aus or not termo:
            continue
        for numero, txt in overlays:
            if afirmado(termo, norm(txt)):
                blocks.append(("CLAIM_FALSO",
                               f"Foto {numero}: overlay afirma '{txt.strip()}' mas o produto "
                               f"TEM a limitacao '{texto_orig}'. Claim falso = devolucao."))

    # 2) TRANSPARENCIA: limitacao com disclosure_foto tem que ser declarada na foto
    overlays_por_foto = {}
    for numero, txt in overlays:
        overlays_por_foto.setdefault(numero, []).append(norm(txt))
    for termo, eh_aus, disc, texto_orig in termos:
        if disc is None:
            warns.append(("LIMITACAO_SEM_FOTO",
                          f"Limitacao '{texto_orig}' sem disclosure_foto: nao sera declarada em nenhuma foto."))
            continue
        blob = " ".join(overlays_por_foto.get(disc, []))
        ok = declarado(termo, blob) if eh_aus else (termo in blob)
        if not ok:
            if eh_aus:
                blocks.append(("LIMITACAO_NAO_DECLARADA",
                               f"Foto {disc} deveria declarar a limitacao '{texto_orig}' "
                               f"(ex.: selo de transparencia 'sem {termo}'), mas nao declara."))
            else:
                warns.append(("LIMITACAO_NAO_DECLARADA",
                              f"Foto {disc} deveria mencionar '{texto_orig}' e nao menciona (verificar)."))

    # 3) WARN: feature de alto risco afirmada sem respaldo
    cobertos = {t for t, _, _, _ in termos if t}
    for numero, txt in overlays:
        on = norm(txt)
        for feat in FEATURES_ALTO_RISCO:
            fn = norm(feat)
            if afirmado(fn, on) and fn not in carac_norm and fn not in cobertos:
                warns.append(("CLAIM_RISCO_NAO_CONFIRMADO",
                              f"Foto {numero}: afirma '{feat}' — nao consta em dados_produto.caracteristicas "
                              f"nem em limitacoes. Confirmar que o produto realmente tem antes de publicar."))
    return blocks, warns


def _flatten(x):
    if isinstance(x, dict):
        for v in x.values():
            yield from _flatten(v)
    elif isinstance(x, (list, tuple)):
        for v in x:
            yield from _flatten(v)
    else:
        yield x


def carregar_yaml(caminho):
    import yaml
    with open(caminho, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def main():
    ap = argparse.ArgumentParser(description="Guarda anti-claim-falso do overlay.")
    ap.add_argument("brief", help="Caminho do brief .yaml")
    ap.add_argument("--overlay", help="Arquivo opcional com overlays renderizados pelo Felipe (1 texto por linha)")
    args = ap.parse_args()

    if not os.path.isfile(args.brief):
        print(f"ERRO: brief nao encontrado: {args.brief}", file=sys.stderr)
        sys.exit(2)

    brief = carregar_yaml(args.brief)
    extra = None
    if args.overlay and os.path.isfile(args.overlay):
        extra = [ln.strip() for ln in open(args.overlay, encoding="utf-8") if ln.strip()]

    blocks, warns = validar_claims(brief, overlays_extra=extra)

    for code, msg in warns:
        print(f"  [aviso] {code}: {msg}")

    if blocks:
        print(f"\nCLAIM REJEITADO - {len(blocks)} bloqueio(s):")
        for code, msg in blocks:
            print(f"  [{code}] {msg}")
        sys.exit(1)

    print(f"CLAIMS OK - {os.path.basename(args.brief)}: nenhum claim falso, limitacoes declaradas.")
    sys.exit(0)


if __name__ == "__main__":
    main()
