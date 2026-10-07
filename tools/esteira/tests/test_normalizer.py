from esteira.normalizer import parse_color, normalize

def _rec(sku, cod_pai=None, var=None, preco=None, ean=None, tipo="S", fotos=None, desc=None):
    return {"sku": sku, "nome": sku, "cod_pai": cod_pai, "variacoes_raw": var,
            "preco_venda": preco, "preco_custo": None, "ean": ean, "tipo": tipo,
            "marca": None, "peso_bruto": None, "dim_cm": {}, "fotos": fotos or [],
            "descricao_complementar": desc}

def test_parse_color_extrai_valor():
    assert parse_color("Cor:Branco||") == "Branco"
    assert parse_color("Cor:Preto") == "Preto"
    assert parse_color(None) is None

def test_pai_com_filhos_vira_anuncio_variacoes():
    recs = [
        _rec("VIE_1066-PAI", tipo="V"),
        _rec("VIE_1066_3402_BR", cod_pai="VIE_1066-PAI", var="Cor:Branco||", preco=150, ean="111"),
        _rec("VIE_1066_3405_PT", cod_pai="VIE_1066-PAI", var="Cor:Preto||", preco=150, ean="222"),
    ]
    out = normalize(recs)
    assert out["total_anuncios"] == 1
    anuncio = out["anuncios"][0]
    assert anuncio["modo"] == "variacoes"
    assert anuncio["pai_sku"] == "VIE_1066-PAI"
    assert [v["cor"] for v in anuncio["variacoes"]] == ["Branco", "Preto"]

def test_sku_avulso_vira_anuncio_simples():
    out = normalize([_rec("TCD-LXI15", preco=159.9, ean="333")])
    anuncio = out["anuncios"][0]
    assert anuncio["modo"] == "simples"
    assert anuncio["pai_sku"] == "TCD-LXI15"
    assert len(anuncio["variacoes"]) == 1
    assert anuncio["variacoes"][0]["cor"] is None

def test_descricao_complementar_propaga_para_anuncio():
    recs = [
        _rec("PAI", tipo="V", desc="Material: inox. Dimensões do produto: 20x15x15cm."),
        _rec("PAI_BR", cod_pai="PAI", var="Cor:Branco||", preco=10, ean="1"),
    ]
    out = normalize(recs)
    assert out["anuncios"][0]["descricao_complementar"].startswith("Material: inox")


def test_anuncio_usa_maior_medida_dos_filhos():
    recs = [
        {"sku": "P", "nome": "Pai", "peso_bruto": 0.0, "dim_cm": {"largura": 0, "altura": 0, "comprimento": 0}},
        {"sku": "P-BR", "cod_pai": "P", "variacoes_raw": "Cor:Branco||", "peso_bruto": 0.7,
         "dim_cm": {"largura": 28, "altura": 21, "comprimento": 21}, "fornecedor": "VIEL"},
        {"sku": "P-PT", "cod_pai": "P", "variacoes_raw": "Cor:Preto||", "peso_bruto": 0.9,
         "dim_cm": {"largura": 30, "altura": 21, "comprimento": 21}, "fornecedor": "VIEL"},
    ]
    a = normalize(recs)["anuncios"][0]
    assert a["peso_bruto_kg"] == 0.9
    assert a["dim_embalagem_cm"] == {"largura": 30, "altura": 21, "comprimento": 21}
    assert a["fornecedor"] == "VIEL"
    assert a["variacoes"][0]["peso_bruto_kg"] == 0.7
