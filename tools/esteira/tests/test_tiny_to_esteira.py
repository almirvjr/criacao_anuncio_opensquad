import openpyxl

from tiny_to_esteira import sku_chave, aplicar_cubagem, carregar_cubagem, ler_linhas


def test_sku_chave_iguala_traco_e_underline():
    assert sku_chave("VIE_1066_3402_BR") == sku_chave("vie-1066-3402-br") == "VIE-1066-3402-BR"


def test_aplicar_cubagem_preenche_so_o_zerado():
    recs = [{"sku": "VIE-1066-3402-BR", "peso_bruto": 0.0,
             "dim_cm": {"largura": 0.0, "altura": 0.0, "comprimento": 0.0}},
            {"sku": "VIE-1066-3405-PT", "peso_bruto": 1.5,
             "dim_cm": {"largura": 10, "altura": 10, "comprimento": 10}}]
    cub = {"VIE-1066-3402-BR": {"peso_bruto": 0.7, "largura": 28, "altura": 21, "comprimento": 21},
           "VIE-1066-3405-PT": {"peso_bruto": 0.7, "largura": 28, "altura": 21, "comprimento": 21}}
    assert aplicar_cubagem(recs, cub) == 1
    assert recs[0]["peso_bruto"] == 0.7 and recs[0]["dim_cm"]["largura"] == 28
    assert recs[1]["peso_bruto"] == 1.5  # nao sobrescreve o que ja tinha


def test_carregar_cubagem_le_aba_produtos(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Produtos"
    ws.append(["Codigo (SKU)", "Descricao", "Fornecedor", "Peso bruto (kg)", "Largura", "Altura", "Comprimento"])
    ws.append(["VIE_1067_3403_BR", "LIXEIRA 8L", "VIEL", 0.9, 37, 21, 21])
    p = tmp_path / "cub.xlsx"
    wb.save(p)
    cub = carregar_cubagem(str(p))
    assert cub["VIE-1067-3403-BR"] == {"peso_bruto": 0.9, "largura": 37, "altura": 21, "comprimento": 21}


def test_ler_linhas_xlsx(tmp_path):
    wb = openpyxl.Workbook()
    wb.active.append(["Código (SKU)", "Preço"])
    wb.active.append(["X-1", 10.0])
    p = tmp_path / "t.xlsx"
    wb.save(p)
    assert ler_linhas(str(p))[1] == ("X-1", 10.0)
