import pytest

from esteira.payload_builder import build_payload, validate_anuncio

def _anuncio_var():
    return {"modo": "variacoes", "pai_sku": "VIE_1066-PAI", "marca": "Viel",
        "variacoes": [
            {"sku": "VIE_1066_3402_BR", "cor": "Branco", "ean": "111", "preco_venda": 150,
             "fotos_cor": ["http://b/branca.jpg"]},
            {"sku": "VIE_1066_3405_PT", "cor": "Preto", "ean": "222", "preco_venda": 150,
             "fotos_cor": ["http://b/preta.jpg"]},
        ]}

def _fotos(sku, n=10):
    """Lista pronta do Felipe: 10 picture_ids, capa na 1a posicao."""
    return [f"http://b/{sku}/capa.jpg"] + [f"http://b/{sku}/foto-{i:02d}.jpg" for i in range(2, n + 1)]

def _ctx():
    # cor_value_map no formato que a Cibele entrega DE FATO: lista de objetos,
    # uma linha por cor, podendo marcar cor sem value_id no ML (decisao 22/07).
    return {"title": "Lixeira 5L Inox Pedal", "category_id": "MLB33375",
            "description_plain": "desc",
            "picture_ids_por_variacao": [
                {"sku_variacao": "VIE_1066_3402_BR", "picture_ids": _fotos("VIE_1066_3402_BR")},
                {"sku_variacao": "VIE_1066_3405_PT", "picture_ids": _fotos("VIE_1066_3405_PT")},
            ],
            "cor_value_map": [
                {"cor": "Branco", "value_id": "52049", "value_name": "Branco"},
                {"cor": "Preto", "value_id": "52005", "value_name": "Preto"},
            ],
            "item_attributes": [{"id": "BRAND", "value_name": "Viel"}]}

def test_payload_variacoes_monta_variations():
    p = build_payload(_anuncio_var(), **_ctx())
    assert p["modo"] == "variacoes"
    assert len(p["variacoes"]) == 2
    v0 = p["variacoes"][0]
    assert v0["price"] == 150 and v0["available_quantity"] == 1
    assert v0["attribute_combinations"] == [{"id": "COLOR", "value_id": "52049", "value_name": "Branco"}]
    assert {"id": "SELLER_SKU", "value_name": "VIE_1066_3402_BR"} in v0["attributes"]
    assert {"id": "EAN", "value_name": "111"} in v0["attributes"]
    assert v0["fotos_cor"] == ["http://b/branca.jpg"]

def test_payload_simples_sem_variations():
    a = {"modo": "simples", "pai_sku": "TCD-LXI15", "marca": "X",
         "variacoes": [{"sku": "TCD-LXI15", "cor": None, "ean": "333", "preco_venda": 159.9,
                        "fotos_cor": []}]}
    ctx = _ctx()
    ctx["cor_value_map"] = []
    ctx["picture_ids_por_variacao"] = [
        {"sku_variacao": "TCD-LXI15", "picture_ids": _fotos("TCD-LXI15")}]
    p = build_payload(a, **ctx)
    assert p["modo"] == "simples"
    assert "variacoes" not in p or not p["variacoes"]
    assert p["price"] == 159.9 and p["available_quantity"] == 1

def test_validate_preco_nao_uniforme_falha():
    a = _anuncio_var(); a["variacoes"][1]["preco_venda"] = 199
    erros = validate_anuncio(a)
    assert any("uniforme" in e.lower() for e in erros)

def test_validate_anuncio_ok_sem_erros():
    assert validate_anuncio(_anuncio_var()) == []


# --- decisao 22/07: cor_value_map e LISTA (formato real da Cibele) ----------

def test_cor_value_map_lista_resolve_value_id():
    """O formato que a Cibele documenta e entrega. Antes o builder so aceitava dict."""
    p = build_payload(_anuncio_var(), **_ctx())
    v1 = p["variacoes"][1]
    assert v1["attribute_combinations"] == [{"id": "COLOR", "value_id": "52005", "value_name": "Preto"}]

def test_cor_sem_value_id_vai_como_value_name_livre():
    """Cor sem correspondencia no ML: vai so com value_name, sem inventar value_id."""
    ctx = _ctx()
    ctx["cor_value_map"] = [
        {"cor": "Branco", "value_id": "52049", "value_name": "Branco"},
        {"cor": "Preto", "value_name": "Preto", "value_name_livre": True},
    ]
    p = build_payload(_anuncio_var(), **ctx)
    assert p["variacoes"][1]["attribute_combinations"] == [{"id": "COLOR", "value_name": "Preto"}]

def test_cor_value_map_dict_legado_continua_funcionando():
    """Nao quebrar quem ainda passa o dict plano antigo."""
    ctx = _ctx()
    ctx["cor_value_map"] = {"Branco": "52049", "Preto": "52005"}
    p = build_payload(_anuncio_var(), **ctx)
    assert p["variacoes"][0]["attribute_combinations"][0]["value_id"] == "52049"


# --- decisao 22/07: fotos vem prontas do Felipe ----------------------------

def test_picture_ids_vem_prontos_do_felipe_sem_remontar():
    """10 fotos, capa na 1a posicao — o builder NAO soma nem recalcula (bug das 2 capas)."""
    p = build_payload(_anuncio_var(), **_ctx())
    v0 = p["variacoes"][0]
    assert len(v0["picture_ids"]) == 10
    assert v0["picture_ids"] == _fotos("VIE_1066_3402_BR")
    assert v0["picture_ids"][0].endswith("/capa.jpg")

def test_variacao_sem_fotos_do_felipe_falha_alto():
    """Faltou a lista daquele SKU: erro claro, nunca anuncio publicado sem foto."""
    ctx = _ctx()
    ctx["picture_ids_por_variacao"] = [ctx["picture_ids_por_variacao"][0]]
    with pytest.raises(ValueError, match="VIE_1066_3405_PT"):
        build_payload(_anuncio_var(), **ctx)

def test_aceita_de_1_a_10_fotos():
    ctx = _ctx()
    ctx["picture_ids_por_variacao"] = [
        {"sku_variacao": "VIE_1066_3402_BR", "picture_ids": ["http://b/capa-br.jpg"]},
        {"sku_variacao": "VIE_1066_3405_PT", "picture_ids": _fotos("VIE_1066_3405_PT", 10)},
    ]
    p = build_payload(_anuncio_var(), **ctx)
    assert p["variacoes"][0]["picture_ids"] == ["http://b/capa-br.jpg"]


def test_mais_de_10_fotos_falha():
    ctx = _ctx()
    ctx["picture_ids_por_variacao"][0]["picture_ids"] = _fotos("VIE_1066_3402_BR", 11)
    with pytest.raises(ValueError, match="11"):
        build_payload(_anuncio_var(), **ctx)


def test_validate_nao_exige_mais_foto_do_felipe():
    a = _anuncio_var()
    for v in a["variacoes"]:
        v["fotos_cor"] = []
    assert validate_anuncio(a) == []


def test_medida_da_caixa_vai_como_atributo():
    a = _anuncio_var()
    a["peso_bruto_kg"] = 0.7
    a["dim_embalagem_cm"] = {"largura": 28, "altura": 21, "comprimento": 21}
    p = build_payload(a, **_ctx())
    assert {"id": "SELLER_PACKAGE_WEIGHT", "value_name": "700 g"} in p["attributes"]
    assert {"id": "SELLER_PACKAGE_LENGTH", "value_name": "21 cm"} in p["attributes"]
    assert {"id": "SELLER_PACKAGE_WIDTH", "value_name": "28 cm"} in p["attributes"]
    assert {"id": "SELLER_PACKAGE_HEIGHT", "value_name": "21 cm"} in p["attributes"]


def test_sem_medida_nao_inventa_atributo():
    p = build_payload(_anuncio_var(), **_ctx())
    assert not [x for x in p["attributes"] if x["id"].startswith("SELLER_PACKAGE")]


# --- Modelo novo do ML (User Products, 08/10/2026): 1 anuncio por cor, mesmo family_name, sem title ---
from esteira.payload_builder import build_payloads_familia  # noqa: E402


def _ctx_familia():
    c = _ctx()
    c["family_name"] = c.pop("title")
    return c


def test_familia_um_pacote_por_cor():
    ps = build_payloads_familia(_anuncio_var(), **_ctx_familia())
    assert sorted(p["sku"] for p in ps) == ["VIE_1066_3402_BR", "VIE_1066_3405_PT"]
    for p in ps:
        assert p["modo"] == "simples"
        assert p["family_name"] == "Lixeira 5L Inox Pedal"
        assert "title" not in p and "variacoes" not in p and "variation_attribute" not in p
        assert p["price"] == 150 and p["available_quantity"] == 1


def test_familia_cor_sku_e_gtin_em_cada_anuncio():
    br = next(p for p in build_payloads_familia(_anuncio_var(), **_ctx_familia()) if p["sku"] == "VIE_1066_3402_BR")
    attrs = {a["id"]: a for a in br["attributes"]}
    assert attrs["COLOR"] == {"id": "COLOR", "value_id": "52049", "value_name": "Branco"}
    assert attrs["SELLER_SKU"]["value_name"] == "VIE_1066_3402_BR"
    assert attrs["GTIN"]["value_name"] == "111"
    assert attrs["BRAND"]["value_name"] == "Viel"


def test_familia_fotos_da_propria_cor():
    br = next(p for p in build_payloads_familia(_anuncio_var(), **_ctx_familia()) if p["sku"] == "VIE_1066_3402_BR")
    assert br["pictures"] == _fotos("VIE_1066_3402_BR")


def test_familia_cor_sem_foto_falha():
    ctx = _ctx_familia()
    ctx["picture_ids_por_variacao"] = ctx["picture_ids_por_variacao"][:1]
    with pytest.raises(ValueError, match="VIE_1066_3405_PT"):
        build_payloads_familia(_anuncio_var(), **ctx)


def test_familia_nome_acima_de_60_falha():
    ctx = _ctx_familia()
    ctx["family_name"] = "L" * 61
    with pytest.raises(ValueError, match="60"):
        build_payloads_familia(_anuncio_var(), **ctx)


def test_familia_produto_sem_cor_nao_inventa_color():
    a = {"modo": "simples", "pai_sku": "X-PAI", "variacoes": [{"sku": "X-1", "cor": None, "ean": "9", "preco_venda": 10}]}
    [p] = build_payloads_familia(a, **_ctx_familia() | {"picture_ids_por_variacao": [{"sku_variacao": "X-1", "picture_ids": ["u"]}]})
    assert "COLOR" not in [x["id"] for x in p["attributes"]]


def test_familia_preto_vem_primeiro():
    # Almir 08/10/2026: a cor preta e sempre a principal -> publicada primeiro na familia
    ps = build_payloads_familia(_anuncio_var(), **_ctx_familia())
    assert ps[0]["sku"] == "VIE_1066_3405_PT"


def test_familia_sem_preto_mantem_ordem():
    a = _anuncio_var()
    a["variacoes"][1]["cor"] = "Cinza"
    ps = build_payloads_familia(a, **_ctx_familia() | {"cor_value_map": []})
    assert [p["sku"] for p in ps] == ["VIE_1066_3402_BR", "VIE_1066_3405_PT"]


def test_regras_do_almir_em_todo_anuncio():
    # 09/10/2026: sempre na loja oficial da Terra, garantia do vendedor de 30 dias, classico
    for p in build_payloads_familia(_anuncio_var(), **_ctx_familia()):
        assert p["official_store_id"] == 458566
        assert p["listing_type_id"] == "gold_special"  # Classico no ML Brasil
        termos = {t["id"]: t["value_name"] for t in p["sale_terms"]}
        assert termos == {"WARRANTY_TYPE": "Garantia do vendedor", "WARRANTY_TIME": "30 dias"}
