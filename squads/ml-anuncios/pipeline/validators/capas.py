#!/usr/bin/env python3
"""
capas.py — monta as fotos de cada cor a partir das capas que o Almir sobe no
Cloudinary (esteira sem fotos, 07/10/2026).

O Almir sobe a capa na pasta do fornecedor e etiqueta com o SKU DA COR + 'capa-anuncio'.
As outras fotos com a etiqueta do SKU vao depois da capa (Almir 09/10/2026), ate 10.
Sem 'capa-anuncio', a foto 'foto-cadastro' do SKU vira a capa (Almir 26/10/2026); sem as duas = falta.
Fotos que vem do ChatGPT pelo hub (conector hub-fotos-chatgpt, 24/10/2026) chegam numeradas: 'anuncio-01'..'anuncio-10'
(01 = capa). Se o SKU tem foto numerada, valem SO as numeradas, nessa ordem (a foto de cadastro fica fora); numero
repetido = a mais nova.
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
TAG_CADASTRO = "foto-cadastro"
SKU_SEGURO = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
TRANSF = "c_pad,w_1200,h_1200,b_white,q_auto"
PREFIXO = f"https://res.cloudinary.com/{NUVEM}/image/upload/"
MAX_FOTOS = 10
NUMERADA = re.compile(r"^anuncio-(\d{2})$")


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
    capas_por_sku, extras_por_sku, numeradas_por_sku = {}, {}, {}
    for r in resources:
        nums = [int(m.group(1)) for t in (r.get("tags") or []) for m in [NUMERADA.match(t)] if m]
        if nums:
            for t in r.get("tags") or []:
                if t != TAG_CAPA and not NUMERADA.match(t):
                    numeradas_por_sku.setdefault(t, []).append((nums[0], r))
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
            numeradas = numeradas_por_sku.get(v["sku"])
            if numeradas:
                por_num = {}
                for n, r in sorted(numeradas, key=lambda x: ordem(x[1])):  # a mais nova fica
                    por_num[n] = r
                if 1 not in por_num:
                    erros.append(f"{a['pai_sku']}: cor '{v.get('cor')}' tem fotos numeradas (anuncio-NN) mas falta "
                                 f"a capa 'anuncio-01' do SKU '{v['sku']}'.")
                    continue
                achadas = [por_num[n] for n in sorted(por_num)][:MAX_FOTOS]
                pv.append({"sku_variacao": v["sku"], "cor": v.get("cor"),
                           "picture_ids": [url_ml(r["secure_url"]) for r in achadas],
                           "origem": [{k: r.get(k) for k in ("asset_id", "public_id", "width", "height")}
                                      for r in achadas]})
                continue
            achadas = sorted(capas_por_sku.get(v["sku"], []), key=ordem)
            de_cadastro = False
            if not achadas:
                # sem 'capa-anuncio': a foto de cadastro vira a capa (Almir 26/10/2026, pedido 57 do hub)
                achadas = sorted((r for r in extras_por_sku.get(v["sku"], []) if TAG_CADASTRO in (r.get("tags") or [])),
                                 key=ordem)
                de_cadastro = bool(achadas)
            if not achadas:
                qual = f"da cor '{v['cor']}'" if v.get("cor") else "do produto"
                erros.append(f"{a['pai_sku']}: falta capa {qual} — nenhuma foto "
                             f"com as etiquetas '{TAG_CAPA}' + '{v['sku']}' (conferir se o SKU da "
                             f"etiqueta esta igual ao Tiny).")
                continue
            if len(achadas) > MAX_FOTOS:
                erros.append(f"{a['pai_sku']}: cor '{v.get('cor')}' tem {len(achadas)} fotos, "
                             f"mais de {MAX_FOTOS}. Usando as {MAX_FOTOS} mais antigas.")
            achadas = (achadas + [r for r in sorted(extras_por_sku.get(v["sku"], []), key=ordem)
                                  if r not in achadas])[:MAX_FOTOS]
            pv.append({"sku_variacao": v["sku"], "cor": v.get("cor"),
                       "picture_ids": [url_ml(r["secure_url"]) for r in achadas],
                       "origem": [{k: r.get(k) for k in ("asset_id", "public_id", "width", "height")}
                                  for r in achadas],
                       **({"capa": "cadastro"} if de_cadastro else {})})
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
        if not SKU_SEGURO.fullmatch(pai) or ".." in pai:
            # o SKU vira nome de arquivo: barra ou ".." gravaria fora da pasta do lote
            erros.append(f"{pai!r}: SKU com caractere que nao pode ir em nome de arquivo")
            continue
        with open(os.path.join(pasta, f"capas-{pai}.yaml"), "w", encoding="utf-8") as fh:
            yaml.safe_dump(doc, fh, allow_unicode=True, sort_keys=False)
        print(f"{pai}: " + ", ".join(f"{p['cor']}={len(p['picture_ids'])}"
                                     + (" (capa = foto de cadastro)" if p.get("capa") == "cadastro" else "")
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
