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
    [payload] = montar(p["e.json"], p["c.yaml"], p["y.yaml"], p["k.yaml"], "VIE-1066-PAI")
    # modelo novo do ML (08/10): um pacote por cor, titulo escolhido vira o nome da familia
    assert payload["family_name"] == "Lixeira Inox 5L Pedal" and "title" not in payload
    assert payload["sku"] == "VIE-1066-3402-BR"
    assert payload["description_plain"] == "Um.\n\nDois."
    assert payload["category_id"] == "MLB33375"
    assert payload["pictures"] == ["https://x/capa.jpg"]
    assert payload["price"] == 100.0
    cores = [a for a in payload["attributes"] if a["id"] == "COLOR"]
    assert cores == [{"id": "COLOR", "value_id": "52049", "value_name": "Branco"}]  # da variacao, nao da ficha


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


def test_cli_grava_um_arquivo_por_cor(tmp_path):
    import os
    import subprocess
    import sys
    e, c, y, k = _arquivos(tmp_path)
    saida = tmp_path / "pub"
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "..", "..", "montar_payload.py"),
                        "--entrada", e, "--categorias", c, "--copy", y, "--capas", k,
                        "--pai", "VIE-1066-PAI", "--saida", str(saida)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert json.loads((saida / "payload-VIE-1066-3402-BR.json").read_text(encoding="utf-8"))["sku"] == "VIE-1066-3402-BR"


def test_nao_se_aplica_vai_com_o_codigo_menos_1():
    # regra do Almir 16/10: campo que nao faz sentido = "nao se aplica" (value_id -1), nunca vazio nem inventado
    out = {a["id"]: a for a in item_attributes_do_copy({"PATTERN_NAME": "não se aplica", "LENGTH": "Não se aplica",
                                                         "WIDTH": "nao se aplica", "BRAND": "Brinox"}, "simples")}
    for k in ("PATTERN_NAME", "LENGTH", "WIDTH"):
        assert out[k] == {"id": k, "value_id": "-1", "value_name": None}
    assert out["BRAND"] == {"id": "BRAND", "value_name": "Brinox"}


def test_produto_sem_cor_mantem_a_cor_da_ficha(tmp_path):
    import montar_payload as mp
    capt = {}
    real = mp.build_payloads_familia
    mp.build_payloads_familia = lambda anuncio, **kw: capt.update(kw) or []
    try:
        entrada = tmp_path / "e.json"; entrada.write_text(json.dumps({"anuncios": [{
            "modo": "simples", "pai_sku": "P", "peso_bruto_kg": 1, "dim_embalagem_cm": {"largura": 1, "altura": 1, "comprimento": 1},
            "variacoes": [{"sku": "P", "cor": None, "ean": "1", "preco_venda": 10}]}]}), encoding="utf-8")
        cat = tmp_path / "c.yaml"; cat.write_text(yaml.safe_dump({"categorias": [{"pai_sku": "P", "category_id": "MLB1"}]}), encoding="utf-8")
        cp = tmp_path / "a.yaml"; cp.write_text(yaml.safe_dump({"pai_sku": "P", "titulo_final": "T", "attributes": {"COLOR": "Bege"},
                                                                "description": {"bloco_1": "x"}}), encoding="utf-8")
        ca = tmp_path / "k.yaml"; ca.write_text(yaml.safe_dump({"pai_sku": "P", "picture_ids_por_variacao": []}), encoding="utf-8")
        mp.montar(entrada, cat, cp, ca, "P")
    finally:
        mp.build_payloads_familia = real
    assert {"id": "COLOR", "value_name": "Bege"} in capt["item_attributes"]
