#!/usr/bin/env python3
"""
capas.py — monta as fotos de cada cor a partir das capas que o Almir sobe no
Cloudinary (esteira sem fotos, 07/10/2026).

O Almir sobe a capa na pasta do fornecedor e etiqueta com o SKU DA COR + 'capa-anuncio'.
As outras fotos com a etiqueta do SKU vao depois da capa (Almir 09/10/2026), ate 10.
O orquestrador busca no Cloudinary (MCP search-assets: as fotos com as etiquetas dos SKUs
do lote, com e sem 'capa-anuncio') e salva o JSON da resposta; este script casa por SKU e trava se faltar cor.

Uso:  python capas.py <busca.json> <anuncios-entrada.json> <pasta_saida>
Saida: 0 = toda cor tem capa (grava capas-{pai_sku}.yaml) | 1 = falta capa (lista quais).
"""
import json
import os
import re
import sys

NUVEM = "wa5lvi98"
TAG_CAPA = "capa-anuncio"
TRANSF = "c_pad,w_1200,h_1200,b_white,q_auto"
PREFIXO = f"https://res.cloudinary.com/{NUVEM}/image/upload/"
MAX_FOTOS = 10


def url_ml(secure_url):
    """Endereco que o ML baixa: 1200x1200 em JPG, sem mexer no original."""
    if not str(secure_url).startswith(PREFIXO):
        raise ValueError(f"Foto fora da nuvem {NUVEM}: {secure_url}")
    resto = secure_url[len(PREFIXO):]
    if resto.startswith(TRANSF + "/"):
        resto = resto[len(TRANSF) + 1:]
    resto = re.sub(r"\.[A-Za-z0-9]+$", "", resto) + ".jpg"
    return f"{PREFIXO}{TRANSF}/{resto}"


def montar(resources, anuncios):
    """Fotos de cada cor: as com 'capa-anuncio' + SKU da cor primeiro (a 1a e a capa), depois as
    OUTRAS fotos com a etiqueta do SKU (Almir 09/10/2026), ate 10. Sem capa = falta."""
    capas_por_sku, extras_por_sku = {}, {}
    for r in resources:
        tags = r.get("tags") or []
        destino = capas_por_sku if TAG_CAPA in tags else extras_por_sku
        for t in tags:
            if t != TAG_CAPA:
                destino.setdefault(t, []).append(r)

    ordem = lambda r: (r.get("created_at", ""), r.get("public_id", ""))  # noqa: E731
    saida, erros = {}, []
    for a in anuncios:
        pv = []
        for v in a.get("variacoes", []):
            achadas = sorted(capas_por_sku.get(v["sku"], []), key=ordem)
            if not achadas:
                erros.append(f"{a['pai_sku']}: falta capa da cor '{v.get('cor')}' — nenhuma foto "
                             f"com as etiquetas '{TAG_CAPA}' + '{v['sku']}' (conferir se o SKU da "
                             f"etiqueta esta igual ao Tiny).")
                continue
            if len(achadas) > MAX_FOTOS:
                erros.append(f"{a['pai_sku']}: cor '{v.get('cor')}' tem {len(achadas)} fotos, "
                             f"mais de {MAX_FOTOS}. Usando as {MAX_FOTOS} mais antigas.")
            achadas = (achadas + sorted(extras_por_sku.get(v["sku"], []), key=ordem))[:MAX_FOTOS]
            pv.append({"sku_variacao": v["sku"], "cor": v.get("cor"),
                       "picture_ids": [url_ml(r["secure_url"]) for r in achadas],
                       "origem": [{k: r.get(k) for k in ("asset_id", "public_id", "width", "height")}
                                  for r in achadas]})
        saida[a["pai_sku"]] = {"pai_sku": a["pai_sku"], "picture_ids_por_variacao": pv}
    return saida, erros


def main():
    import yaml
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    busca, entrada, pasta = sys.argv[1:]
    with open(busca, encoding="utf-8") as fh:
        resources = json.load(fh).get("resources", [])
    with open(entrada, encoding="utf-8") as fh:
        anuncios = json.load(fh)["anuncios"]
    capas, erros = montar(resources, anuncios)
    os.makedirs(pasta, exist_ok=True)
    for pai, doc in capas.items():
        with open(os.path.join(pasta, f"capas-{pai}.yaml"), "w", encoding="utf-8") as fh:
            yaml.safe_dump(doc, fh, allow_unicode=True, sort_keys=False)
        print(f"{pai}: " + ", ".join(f"{p['cor']}={len(p['picture_ids'])}"
                                     for p in doc["picture_ids_por_variacao"]))
    if erros:
        print(f"\nCAPAS INCOMPLETAS - {len(erros)}:")
        for e in erros:
            print(f"  - {e}")
        sys.exit(1)
    print("CAPAS OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
