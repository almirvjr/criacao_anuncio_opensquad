import openpyxl

from tiny_to_esteira import sku_chave, aplicar_cubagem, carregar_cubagem, ler_linhas


def test_sku_chave_iguala_traco_e_underline():
    assert sku_chave("VIE_1066_3402_BR") == sku_chave("vie-1066-3402-br") == "VIE-1066-3402-BR"


def test_cubagem_manda_e_tiny_e_reserva():
    """Regra do Almir: peso e medida SEMPRE da cubagem; Tiny so quando o SKU nao esta la."""
    recs = [{"sku": "VIE-1066-3402-BR", "peso_bruto": 0.1,
             "dim_cm": {"largura": 10, "altura": 10, "comprimento": 10}},
            {"sku": "FORA-DA-CUBAGEM", "peso_bruto": 1.5,
             "dim_cm": {"largura": 10, "altura": 10, "comprimento": 10}}]
    cub = {"VIE-1066-3402-BR": {"peso_bruto": 0.7, "largura": 28, "altura": 21, "comprimento": 21}}
    assert aplicar_cubagem(recs, cub) == 1
    assert recs[0]["peso_bruto"] == 0.7 and recs[0]["dim_cm"] == {"largura": 28, "altura": 21, "comprimento": 21}
    assert recs[1]["peso_bruto"] == 1.5  # fora da cubagem: fica o do Tiny


def test_cubagem_com_campo_vazio_nao_apaga_o_tiny():
    recs = [{"sku": "X-1", "peso_bruto": 0.5, "dim_cm": {"largura": 10, "altura": 10, "comprimento": 10}}]
    cub = {"X-1": {"peso_bruto": None, "largura": 28, "altura": None, "comprimento": 21}}
    aplicar_cubagem(recs, cub)
    assert recs[0]["peso_bruto"] == 0.5
    assert recs[0]["dim_cm"] == {"largura": 28, "altura": 10, "comprimento": 21}


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
