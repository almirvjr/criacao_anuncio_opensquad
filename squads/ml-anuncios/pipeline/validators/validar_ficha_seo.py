#!/usr/bin/env python3
"""
validar_ficha_seo.py — regra de Marca, Modelo, Material e Linha da ficha (Almir, 07/10/2026; 23/10/2026).

Marca (revista 08/10): SO o nome do fornecedor (padrao) ou SO "Terra Casa Decor"
(o Almir troca na mao quando quiser) -- sem palavra-chave na sequencia. Modelo leva
palavras-chave de busca que NAO estao no titulo (~30 caracteres). Mundiart (MDA) e
marca propria: Marca = "Terra Casa Decor" e a descricao apresenta o produto como
Terra Casa Decor. Descricao so cita a loja quando a Marca e a propria. O titulo
nunca cita a loja.

23/10/2026 (hub): nenhum titulo (os do ML e os longos dos outros canais) cita a Marca
nem o fornecedor; a descricao pode. Material e Linha seguem a regra do Modelo (palavras
de busca que nao estao no titulo, ~30 caracteres, sem repetir entre os tres campos).
A 1a palavra da Linha e o nome da linha do fornecedor (que sai do titulo); a 1a palavra do
Material e o material de verdade (pode coincidir com o titulo). Cada bloco da descricao
abre com uma linha de titulo curta.

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
    # BEL = marca Bellagio; quem vende e a Zanotti e Zanotti Presentes (Almir 24/10/2026)
    "BEL": "Bellagio",
}
MARCA_PROPRIA = "Terra Casa Decor"
# Outros nomes ligados a marca (tambem nao entram no titulo). Coza = linha de plastico da Brinox;
# Zanotti = empresa que vende a Bellagio.
SUBMARCAS = {"Brinox": "Coza", "Bellagio": "Zanotti"}
TETO = 30
TETO_TITULO_BLOCO = 60
STOP = {"de", "da", "do", "das", "dos", "com", "e", "para", "pra", "em", "a", "o", "as", "os", "c", "p"}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return s.lower()


def tokens(s):
    return {t for t in re.split(r"[^a-z0-9]+", norm(s)) if t and t not in STOP and len(t) > 1}


def fornecedor_do_sku(sku):
    prefixo = re.split(r"[-_]", str(sku or ""))[0].upper()
    return FORNECEDOR_POR_PREFIXO.get(prefixo)


def _titulo_do_bloco(bloco):
    linhas = str(bloco or "").strip().splitlines()
    if len(linhas) < 2:
        return None
    t = linhas[0].strip()
    if not t or len(t) > TETO_TITULO_BLOCO or t.startswith("-") or t[-1] in ".,;!?":
        return None
    return t


def validar_ficha(pai_sku, titulo, marca, modelo, descricao, material=None, linha=None,
                  outros_titulos=(), blocos=None):
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
    # a loja ("Terra Casa Decor") ja tem a trava acima pelo nome inteiro; por palavra, "casa" barraria titulo certo
    nomes_marca = {n for n in (marca, fornecedor, SUBMARCAS.get(fornecedor)) if n and norm(n) != loja}
    nomes_marca = set().union(*(tokens(n) for n in nomes_marca)) if nomes_marca else set()
    for t in [titulo, *outros_titulos]:
        citadas = sorted(nomes_marca & tokens(t))
        if citadas:
            E("TITULO_CITA_MARCA",
              f"Titulo cita a marca/fornecedor {citadas} (regra do Almir 23/10: marca so na ficha e na "
              f"descricao, nunca no titulo; vale tambem para submarca do fornecedor): '{t}'.")

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
        if marca_propria and fornecedor and tokens(fornecedor) & tokens(descricao):
            E("FORNECEDOR_NA_DESCRICAO",
              f"A Marca e '{MARCA_PROPRIA}', mas a descricao ainda cita '{fornecedor}'. Trocar ou tirar.")

    rep_titulo = sorted(tokens(modelo) & tokens(titulo))
    if rep_titulo:
        E("PALAVRA_REPETIDA_TITULO",
          f"Palavras do Modelo que ja estao no titulo: {rep_titulo}. Trocar por termos novos.")
    extras = {"Material": (material or "").strip(), "Linha": (linha or "").strip()}
    for nome, valor in extras.items():
        if not valor or norm(valor) == "nao se aplica":
            continue
        if len(valor) > TETO:
            E(f"WARN_{nome.upper()}_LONGO", f"{nome} com {len(valor)} caracteres (alvo ~{TETO}): '{valor}'.")
        palavras = valor.split()
        resto = " ".join(palavras[1:]) if nome == "Material" else valor
        rep = sorted(tokens(resto) & tokens(titulo))
        if rep:
            E("PALAVRA_REPETIDA_TITULO",
              f"Palavras do campo {nome} que ja estao no titulo: {rep}. Trocar por termos novos.")
    nome_linha = tokens(extras["Linha"].split()[0]) if extras["Linha"] and norm(extras["Linha"]) != "nao se aplica" else set()
    for t in [titulo, *outros_titulos]:
        if nome_linha & tokens(t):
            E("TITULO_CITA_LINHA",
              f"Titulo cita o nome da linha {sorted(nome_linha)} (Almir 23/10: o nome da linha vai so como 1a "
              f"palavra do campo Linha e na descricao): '{t}'.")
    campos = {"Modelo": modelo, **extras}
    vistos = {}
    for nome, valor in campos.items():
        for tk in tokens(valor):
            if tk in vistos and vistos[tk] != nome:
                E("WARN_REPETIDA_ENTRE_CAMPOS", f"'{tk}' aparece em {vistos[tk]} e em {nome}: usar termo novo.")
            vistos.setdefault(tk, nome)
    for chave, bloco in (blocos or {}).items():
        if _titulo_do_bloco(bloco) is None:
            E("BLOCO_SEM_TITULO",
              f"O bloco '{chave}' da descricao tem que abrir com uma linha de titulo curta (ate "
              f"{TETO_TITULO_BLOCO} letras, sem ponto no fim), e o texto vem na linha de baixo.")
    return err


def titulo_do_copy(doc):
    if doc.get("titulo_final"):
        return doc["titulo_final"]
    for t in doc.get("titles") or []:
        if isinstance(t, dict) and t.get("recomendado"):
            return t.get("texto", "")
    return ""


def outros_titulos_do_copy(doc):
    out = []
    for chave in ("titles", "titulos_longos"):
        for t in doc.get(chave) or []:
            if isinstance(t, dict) and t.get("texto"):
                out.append(t["texto"])
    # titulo do ML de cada variacao (variacao que nao e de cor, hub 25/10/2026): mesma regra de marca e linha
    for x in (doc.get("por_variacao") or {}).values():
        if isinstance(x, dict) and x.get("titulo_ml"):
            out.append(x["titulo_ml"])
    return out


def blocos_do_copy(doc):
    desc = doc.get("description") or {}
    return {k: v for k, v in sorted(desc.items()) if str(k).startswith("bloco") and isinstance(v, str)}


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
                          descricao_do_copy(doc), material=attrs.get("MATERIAL") or attrs.get("MAIN_MATERIAL"), linha=attrs.get("LINE"),
                          outros_titulos=outros_titulos_do_copy(doc), blocos=blocos_do_copy(doc))
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
