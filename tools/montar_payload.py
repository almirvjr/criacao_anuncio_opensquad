"""Monta o pacote que a Paula envia ao webhook ML Publicar (esteira sem fotos, 07/10/2026).

A Paula NAO monta o JSON na mao: roda este comando. Regras (1-10 fotos por cor, preco
igual, medida da caixa) moram no payload_builder e tem teste.

Uso:
  python montar_payload.py --entrada anuncios-entrada.json --categorias categorias.yaml \
      --copy anuncio-{pai}.yaml --capas capas-{pai}.yaml --pai {pai} --saida payload-{pai}.json
"""
import argparse
import json
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esteira.payload_builder import build_payload, validate_anuncio  # noqa: E402


def _yaml(p):
    with open(p, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def item_attributes_do_copy(attrs, modo):
    """Ficha da Renata -> lista do ML. Em anuncio com cores, COLOR vai na variacao, nao no item."""
    out = []
    for k, v in (attrs or {}).items():
        if v in (None, ""):
            continue
        if modo == "variacoes" and k == "COLOR":
            continue
        out.append({"id": k, "value_name": str(v)})
    return out


def _titulo(doc):
    if doc.get("titulo_final"):
        return doc["titulo_final"]
    return next(t["texto"] for t in doc.get("titles", []) if t.get("recomendado"))


def _descricao(doc):
    desc = doc.get("description") or {}
    return "\n\n".join(str(v).strip() for k, v in sorted(desc.items())
                       if str(k).startswith("bloco") and isinstance(v, str))


def montar(entrada, categorias, copy, capas, pai):
    with open(entrada, encoding="utf-8") as fh:
        anuncio = next(a for a in json.load(fh)["anuncios"] if a["pai_sku"] == pai)
    cat = next(c for c in _yaml(categorias)["categorias"] if c["pai_sku"] == pai)
    doc = _yaml(copy)
    erros = validate_anuncio(anuncio)
    if erros:
        raise ValueError("; ".join(erros))
    return build_payload(
        anuncio, title=_titulo(doc), category_id=cat["category_id"],
        description_plain=_descricao(doc),
        picture_ids_por_variacao=_yaml(capas)["picture_ids_por_variacao"],
        cor_value_map=cat.get("cor_value_map"),
        item_attributes=item_attributes_do_copy(doc.get("attributes"), anuncio["modo"]))


def main():
    ap = argparse.ArgumentParser()
    for a in ("--entrada", "--categorias", "--copy", "--capas", "--pai", "--saida"):
        ap.add_argument(a, required=True)
    x = ap.parse_args()
    payload = montar(x.entrada, x.categorias, x.copy, x.capas, x.pai)
    with open(x.saida, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"PAYLOAD OK - {x.pai} -> {x.saida}")


if __name__ == "__main__":
    main()
