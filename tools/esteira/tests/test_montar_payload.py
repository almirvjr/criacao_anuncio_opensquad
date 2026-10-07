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


import pytest


def _arquivos(tmp_path, copy_over=None, entrada_over=None, capas_pai="VIE-1066-PAI"):
    entrada = {"anuncios": [{"modo": "variacoes", "pai_sku": "VIE-1066-PAI", "marca": None,
                             "peso_bruto_kg": 0.7, "dim_embalagem_cm": {"largura": 28, "altura": 21, "comprimento": 21},
                             "variacoes": [{"sku": "VIE-1066-3402-BR", "cor": "Branco", "ean": "789", "preco_venda": 100.0}]}]}
    if entrada_over:
        entrada["anuncios"][0].update(entrada_over)
    cat = {"categorias": [{"pai_sku": "VIE-1066-PAI", "category_id": "MLB33375", "cor_value_map": []}]}
    copy_doc = {"pai_sku": "VIE-1066-PAI", "titulo_final": "Lixeira Inox 5L Pedal",
                "description": {"bloco_1_abertura": "Um."},
                "attributes": {"BRAND": "Viel Higienica", "MODEL": "Quarto"}}
    if copy_over is not None:
        copy_doc.update(copy_over)
        copy_doc = {k: v for k, v in copy_doc.items() if v is not None}
    capas = {"pai_sku": capas_pai, "picture_ids_por_variacao": [
        {"sku_variacao": "VIE-1066-3402-BR", "picture_ids": ["https://x/capa.jpg"]}]}
    p = {}
    for nome, doc in (("e.json", entrada), ("c.yaml", cat), ("y.yaml", copy_doc), ("k.yaml", capas)):
        f = tmp_path / nome
        f.write_text(json.dumps(doc) if nome.endswith(".json") else yaml.safe_dump(doc), encoding="utf-8")
        p[nome] = str(f)
    return p["e.json"], p["c.yaml"], p["y.yaml"], p["k.yaml"]


def test_descricao_no_formato_plain_text_e_recusada(tmp_path):
    e, c, y, k = _arquivos(tmp_path, copy_over={"description": {"plain_text": "Texto."}})
    with pytest.raises(ValueError, match="descri"):
        montar(e, c, y, k, "VIE-1066-PAI")


def test_attributes_em_lista_e_recusado(tmp_path):
    e, c, y, k = _arquivos(tmp_path, copy_over={"attributes": [{"id": "BRAND", "value_name": "Viel"}]})
    with pytest.raises(ValueError, match="attributes"):
        montar(e, c, y, k, "VIE-1066-PAI")


def test_sem_titulo_final_recusa(tmp_path):
    e, c, y, k = _arquivos(tmp_path, copy_over={"titulo_final": None,
                                                 "titles": [{"texto": "Recomendado", "recomendado": True}]})
    with pytest.raises(ValueError, match="titulo_final"):
        montar(e, c, y, k, "VIE-1066-PAI")


def test_copy_de_outro_produto_recusa(tmp_path):
    e, c, y, k = _arquivos(tmp_path, copy_over={"pai_sku": "VIE-1067-PAI"})
    with pytest.raises(ValueError, match="VIE-1067-PAI"):
        montar(e, c, y, k, "VIE-1066-PAI")


def test_capas_de_outro_produto_recusa(tmp_path):
    e, c, y, k = _arquivos(tmp_path, capas_pai="VIE-1067-PAI")
    with pytest.raises(ValueError, match="VIE-1067-PAI"):
        montar(e, c, y, k, "VIE-1066-PAI")


def test_sem_medida_da_caixa_recusa(tmp_path):
    e, c, y, k = _arquivos(tmp_path, entrada_over={"peso_bruto_kg": None})
    with pytest.raises(ValueError, match="caixa"):
        montar(e, c, y, k, "VIE-1066-PAI")
