#!/usr/bin/env python3
"""
validar_ficha_seo.py — regra de Marca e Modelo da ficha (Almir, 07/10/2026).

Marca (revista 08/10): SO o nome do fornecedor (padrao) ou SO "Terra Casa Decor"
(o Almir troca na mao quando quiser) -- sem palavra-chave na sequencia. Modelo leva
palavras-chave de busca que NAO estao no titulo (~30 caracteres). Mundiart (MDA) e
marca propria: Marca = "Terra Casa Decor" e a descricao apresenta o produto como
Terra Casa Decor. Descricao so cita a loja quando a Marca e a propria. O titulo
nunca cita a loja.

Uso:  python validar_ficha_seo.py <anuncio-{pai_sku}.yaml>
Saida: 0 = OK (avisos podem aparecer) | 1 = BLOQUEADO.
"""
import argparse
import os
import re
import sys
import unicodedata

FORNECEDOR_POR_PREFIXO = {
    "VIE": "Viel", "PAR": "Paramount", "BRI": "Brinox", "EMB": "Embalixo",
    "MMP": "Passerini", "SEC": "Secalux", "MDA": "Terra Casa Decor",
}
MARCA_PROPRIA = "Terra Casa Decor"
TETO = 30
STOP = {"de", "da", "do", "das", "dos", "com", "e", "para", "pra", "em", "a", "o", "as", "os", "c", "p"}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return s.lower()


def tokens(s):
    return {t for t in re.split(r"[^a-z0-9]+", norm(s)) if t and t not in STOP and len(t) > 1}


def fornecedor_do_sku(sku):
    prefixo = re.split(r"[-_]", str(sku or ""))[0].upper()
    return FORNECEDOR_POR_PREFIXO.get(prefixo)


def validar_ficha(pai_sku, titulo, marca, modelo, descricao):
    err = []
    E = lambda c, m: err.append((c, m))  # noqa: E731
    fornecedor = fornecedor_do_sku(pai_sku)
    mundiart = fornecedor == MARCA_PROPRIA
    marca, modelo = (marca or "").strip(), (modelo or "").strip()
    loja = norm(MARCA_PROPRIA)

    if fornecedor is None:
        E("FORNECEDOR_DESCONHECIDO",
          f"Prefixo do SKU '{pai_sku}' fora do mapa de fornecedores: perguntar ao Almir "
          f"(nunca deduzir pela sigla).")
    if not marca:
        E("MARCA_VAZIA", "Campo Marca vazio.")
    if not modelo:
        E("MODELO_VAZIO", "Campo Modelo vazio.")
    if len(marca) > TETO:
        E("WARN_MARCA_LONGA", f"Marca com {len(marca)} caracteres (alvo ~{TETO}): '{marca}'.")
    if len(modelo) > TETO:
        E("WARN_MODELO_LONGO", f"Modelo com {len(modelo)} caracteres (alvo ~{TETO}): '{modelo}'.")
    if loja in norm(titulo):
        E("TITULO_CITA_LOJA", "O titulo nunca cita 'Terra Casa Decor'.")

    marca_propria = norm(marca) == loja
    if mundiart:
        if marca and not marca_propria:
            E("MARCA_MUNDIART", f"Mundiart: Marca tem que ser exatamente '{MARCA_PROPRIA}', veio '{marca}'.")
        if loja not in norm(descricao):
            E("DESCRICAO_SEM_MARCA_PROPRIA",
              "Mundiart: a descricao precisa apresentar o produto como da marca Terra Casa Decor.")
    else:
        if fornecedor and marca and not marca_propria and norm(marca) != norm(fornecedor):
            E("MARCA_FORA_DO_PADRAO",
              f"Marca tem que ser so '{fornecedor}' ou so '{MARCA_PROPRIA}', veio '{marca}'.")
        if loja in norm(descricao) and not marca_propria:
            E("DESCRICAO_CITA_LOJA",
              "A descricao so cita 'Terra Casa Decor' quando a Marca e a propria.")

    rep_titulo = sorted(tokens(modelo) & tokens(titulo))
    if rep_titulo:
        E("PALAVRA_REPETIDA_TITULO",
          f"Palavras do Modelo que ja estao no titulo: {rep_titulo}. Trocar por termos novos.")
    return err


def titulo_do_copy(doc):
    if doc.get("titulo_final"):
        return doc["titulo_final"]
    for t in doc.get("titles") or []:
        if isinstance(t, dict) and t.get("recomendado"):
            return t.get("texto", "")
    return ""


def descricao_do_copy(doc):
    desc = doc.get("description") or {}
    return "\n\n".join(str(v) for k, v in sorted(desc.items())
                       if str(k).startswith("bloco") and isinstance(v, str))


def main():
    import yaml
    ap = argparse.ArgumentParser(description="Regra de Marca/Modelo da ficha (07/10/2026).")
    ap.add_argument("copy", help="anuncio-{pai_sku}.yaml da Renata")
    args = ap.parse_args()
    if not os.path.isfile(args.copy):
        print(f"ERRO: arquivo nao encontrado: {args.copy}", file=sys.stderr)
        sys.exit(2)
    with open(args.copy, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    attrs = doc.get("attributes") or {}
    pai = doc.get("pai_sku") or doc.get("sku")
    erros = validar_ficha(pai, titulo_do_copy(doc), attrs.get("BRAND"), attrs.get("MODEL"),
                          descricao_do_copy(doc))
    for c, m in erros:
        if c.startswith("WARN"):
            print(f"  [aviso] {c}: {m}")
    hard = [(c, m) for c, m in erros if not c.startswith("WARN")]
    if hard:
        print(f"\nFICHA REJEITADA - {len(hard)} erro(s):")
        for c, m in hard:
            print(f"  [{c}] {m}")
        sys.exit(1)
    print(f"FICHA OK - {pai}: Marca='{attrs.get('BRAND')}' Modelo='{attrs.get('MODEL')}'.")
    sys.exit(0)


if __name__ == "__main__":
    main()
