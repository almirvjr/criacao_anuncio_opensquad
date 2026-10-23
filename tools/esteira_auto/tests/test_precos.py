"""Planilha de precificacao do hub (Almir 23/10/2026): a esteira propoe o preco por canal e SKU."""
import openpyxl

from esteira_auto import precos as P


def _planilha(caminho, abas):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for nome, linhas in abas.items():
        ws = wb.create_sheet(nome)
        for r in linhas:
            ws.append(r)
    wb.save(caminho)
    return caminho


def test_le_por_cabecalho_arredonda_e_ignora_zero(tmp_path):
    c = _planilha(tmp_path / "p.xlsx", {
        "ML": [("SKU", "DESCRIÇÃO", "PREÇO VENDA"), ("BRI-coza18-10570_0008-PT", "Prato", 41.285714285714285),
               ("BRI-coza18-10570_0007-BR", "Prato", 0), ("SEM-PRECO", "x", None)],
        "Magalu": [("PREÇO VENDA", "SKU"), (52, "bri_coza18-10570_0465-vm")],   # colunas em outra ordem
        "Outra": [("SKU", "PREÇO VENDA"), ("X", 1)],
    })
    t = P.carregar(c)
    assert t["ml"] == {"BRI-COZA18-10570-0008-PT": 41.29}
    assert t["magalu"] == {"BRI-COZA18-10570-0465-VM": 52.0}
    assert "shopee" not in t


def test_aba_sem_cabecalho_certo_fica_de_fora(tmp_path):
    c = _planilha(tmp_path / "p.xlsx", {"ML": [("CODIGO", "VALOR"), ("A", 10)]})
    assert P.carregar(c) == {}


def test_do_produto_so_os_skus_achados():
    t = {"ml": {"A-1": 10.0, "B-2": 20.0}, "magalu": {"Z": 5.0}}
    assert P.do_produto(t, ["A_1", "C-3"]) == {"ml": {"A_1": 10.0}}


def test_sem_planilha_segue_sem_preco(tmp_path):
    assert P.ler_para_lote(tmp_path, origem=tmp_path / "nao-existe.xlsx") == {}


def test_planilha_estragada_segue_sem_preco(tmp_path):
    ruim = tmp_path / "ruim.xlsx"
    ruim.write_text("isto nao e planilha")
    lote = tmp_path / "lote"
    lote.mkdir()
    assert P.ler_para_lote(lote, origem=ruim) == {}


def test_copia_e_le(tmp_path):
    c = _planilha(tmp_path / "p.xlsx", {"ML": [("SKU", "PREÇO VENDA"), ("A", 10)]})
    lote = tmp_path / "lote"
    lote.mkdir()
    assert P.ler_para_lote(lote, origem=c) == {"ml": {"A": 10.0}}
    assert (lote / "precificacao-hub.xlsx").is_file()
