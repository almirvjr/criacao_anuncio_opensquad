import json

import yaml

from montar_payload import item_attributes_do_copy, montar


def test_color_sai_do_item_em_variacoes():
    attrs = {"BRAND": "Viel Higienica", "MODEL": "Quarto", "COLOR": "Preto", "CAPACITY": "5 L"}
    ids = [a["id"] for a in item_attributes_do_copy(attrs, "variacoes")]
    assert "COLOR" not in ids and "BRAND" in ids and "CAPACITY" in ids
    assert "COLOR" in [a["id"] for a in item_attributes_do_copy(attrs, "simples")]


def test_montar_ponta_a_ponta(tmp_path):
    entrada = {"anuncios": [{"modo": "variacoes", "pai_sku": "VIE-1066-PAI", "marca": None,
                             "peso_bruto_kg": 0.7, "dim_embalagem_cm": {"largura": 28, "altura": 21, "comprimento": 21},
                             "variacoes": [{"sku": "VIE-1066-3402-BR", "cor": "Branco", "ean": "789", "preco_venda": 100.0}]}]}
    cat = {"categorias": [{"pai_sku": "VIE-1066-PAI", "category_id": "MLB33375",
                           "cor_value_map": [{"cor": "Branco", "value_id": "52049", "value_name": "Branco"}]}]}
    copy_doc = {"pai_sku": "VIE-1066-PAI", "titulo_final": "Lixeira Inox 5L Pedal",
                "titles": [{"texto": "Outro", "recomendado": True}],
                "description": {"bloco_1_abertura": "Um.", "bloco_2_specs": "Dois."},
                "attributes": {"BRAND": "Viel Higienica", "MODEL": "Quarto", "COLOR": "Branco"}}
    capas = {"pai_sku": "VIE-1066-PAI", "picture_ids_por_variacao": [
        {"sku_variacao": "VIE-1066-3402-BR", "picture_ids": ["https://x/capa.jpg"]}]}
    p = {}
    for nome, doc in (("e.json", entrada), ("c.yaml", cat), ("y.yaml", copy_doc), ("k.yaml", capas)):
        f = tmp_path / nome
        f.write_text(json.dumps(doc) if nome.endswith(".json") else yaml.safe_dump(doc), encoding="utf-8")
        p[nome] = str(f)
    payload = montar(p["e.json"], p["c.yaml"], p["y.yaml"], p["k.yaml"], "VIE-1066-PAI")
    assert payload["title"] == "Lixeira Inox 5L Pedal"
    assert payload["description_plain"] == "Um.\n\nDois."
    assert payload["category_id"] == "MLB33375"
    assert payload["variacoes"][0]["picture_ids"] == ["https://x/capa.jpg"]
    assert payload["variacoes"][0]["price"] == 100.0
    assert "COLOR" not in [a["id"] for a in payload["attributes"]]
