"""Monta o pacote que a Paula envia ao webhook ML Publicar (esteira sem fotos, 07/10/2026).

A Paula NAO monta o JSON na mao: roda este comando. Regras (1-10 fotos por cor, preco
igual, medida da caixa) moram no payload_builder e tem teste.

Uso:
  python montar_payload.py --entrada anuncios-entrada.json --categorias categorias.yaml \
      --copy anuncio-{pai}.yaml --capas capas-{pai}.yaml --pai {pai} --saida <pasta>

Grava um payload-{sku da cor}.json por cor (modelo novo do ML, 08/10/2026).
"""
import argparse
import json
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esteira.payload_builder import atributos_embalagem, build_payloads_familia, validate_anuncio  # noqa: E402


def _yaml(p):
    with open(p, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


NAO_SE_APLICA = "não se aplica"


def e_nao_se_aplica(v):
    """'não se aplica' em qualquer caixa, com ou sem acento."""
    s = str(v or "").strip().lower().replace("ã", "a")
    return s == "nao se aplica"


def item_attributes_do_copy(attrs, modo):
    """Ficha da Renata -> lista do ML. Em anuncio com cores, COLOR vai na variacao, nao no item.
    'não se aplica' (Almir 16/10/2026) vai com value_id -1, que e como o ML marca o campo."""
    out = []
    for k, v in (attrs or {}).items():
        if v in (None, ""):
            continue
        if modo == "variacoes" and k == "COLOR":
            continue
        if e_nao_se_aplica(v):
            out.append({"id": k, "value_id": "-1", "value_name": None})
        else:
            out.append({"id": k, "value_name": str(v)})
    return out


def _titulo(doc):
    """So o titulo escolhido no checkpoint (step-06) vai ao ar — nunca cai no recomendado."""
    if not doc.get("titulo_final"):
        raise ValueError("Copy sem 'titulo_final': o step-06 grava o titulo escolhido pelo Almir "
                         "no anuncio-{pai_sku}.yaml antes da publicacao.")
    return doc["titulo_final"]


def _descricao(doc):
    desc = doc.get("description") or {}
    return "\n\n".join(str(v).strip() for k, v in sorted(desc.items())
                       if str(k).startswith("bloco") and isinstance(v, str))


def montar(entrada, categorias, copy, capas, pai, preco=None):
    with open(entrada, encoding="utf-8") as fh:
        anuncio = next(a for a in json.load(fh)["anuncios"] if a["pai_sku"] == pai)
    if preco is not None:
        for v in anuncio["variacoes"]:
            v["preco_venda"] = round(float(preco), 2)
    cat = next(c for c in _yaml(categorias)["categorias"] if c["pai_sku"] == pai)
    doc = _yaml(copy)
    capas_doc = _yaml(capas)
    for nome, d in (("copy", doc), ("capas", capas_doc)):
        if d.get("pai_sku") != pai:
            raise ValueError(f"Arquivo de {nome} e do produto '{d.get('pai_sku')}', nao de '{pai}'.")
    if not isinstance(doc.get("attributes"), dict):
        raise ValueError("Copy com 'attributes' fora do formato: tem que ser um mapa {ID: valor} "
                         "(gabarito da Renata).")
    descricao = _descricao(doc)
    if not descricao.strip():
        raise ValueError("Copy sem descricao: esperado description.bloco_* (gabarito da Renata). "
                         "Anuncio nao vai ao ar sem descricao.")
    if not atributos_embalagem(anuncio):
        raise ValueError(f"{pai}: sem peso ou medida da caixa (cubagem) — o frete do ML sairia errado.")
    erros = validate_anuncio(anuncio)
    if erros:
        raise ValueError("; ".join(erros))
    # Modelo novo do ML (User Products, 08/10/2026): um pacote por cor, o titulo escolhido
    # vira o nome da familia (o ML monta o titulo e junta as cores na mesma pagina).
    return build_payloads_familia(
        anuncio, family_name=_titulo(doc), category_id=cat["category_id"],
        description_plain=descricao,
        picture_ids_por_variacao=capas_doc["picture_ids_por_variacao"],
        cor_value_map=cat.get("cor_value_map"),
        item_attributes=item_attributes_do_copy(doc.get("attributes"), anuncio.get("modo") or "variacoes"))


def main():
    ap = argparse.ArgumentParser()
    for a in ("--entrada", "--categorias", "--copy", "--capas", "--pai", "--saida"):
        ap.add_argument(a, required=True)
    x = ap.parse_args()
    pacotes = montar(x.entrada, x.categorias, x.copy, x.capas, x.pai)
    os.makedirs(x.saida, exist_ok=True)
    for p in pacotes:
        destino = os.path.join(x.saida, f"payload-{p['sku']}.json")
        with open(destino, "w", encoding="utf-8") as fh:
            json.dump(p, fh, ensure_ascii=False, indent=2)
        print(f"PAYLOAD OK - {p['sku']} -> {destino}")


if __name__ == "__main__":
    main()
