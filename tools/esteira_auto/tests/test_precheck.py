import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from esteira_auto import precheck as P  # noqa: E402

BOM = {"pai_sku": "BRI-1", "modo": "simples", "peso_bruto_kg": 1.2,
       "dim_embalagem_cm": {"largura": 30, "altura": 12, "comprimento": 30},
       "variacoes": [{"sku": "BRI-1", "cor": None, "ean": "7891", "preco_venda": 10}]}


def test_caixa_ok():
    assert P.faltas_de_caixa({"anuncios": [BOM]}) == []


def test_caixa_faltando_diz_qual():
    ruim = dict(BOM, pai_sku="BRI-2", peso_bruto_kg=None)
    faltas = P.faltas_de_caixa({"anuncios": [BOM, ruim]})
    assert len(faltas) == 1 and "BRI-2" in faltas[0] and "cubagem" in faltas[0]


def test_planilha_vazia(tmp_path):
    def falso(cmd, **kw):
        (tmp_path / "anuncios-entrada.json").write_text(json.dumps({"anuncios": []}), encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "", "")
    probs = P.ler_planilha(tmp_path / "x.xls", tmp_path, cubagem=tmp_path / "c.xlsx", rodar=falso)
    assert probs and "nenhum produto" in probs[0]


def test_planilha_que_nao_abre(tmp_path):
    falso = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "", "Traceback ... segredo")
    probs = P.ler_planilha(tmp_path / "x.xls", tmp_path, cubagem=tmp_path / "c.xlsx", rodar=falso)
    assert probs and "nao consegui ler a planilha" in probs[0] and "segredo" not in probs[0]


def test_planilha_boa(tmp_path):
    def falso(cmd, **kw):
        assert "--cubagem" in cmd
        (tmp_path / "anuncios-entrada.json").write_text(json.dumps({"anuncios": [BOM]}), encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "", "")
    assert P.ler_planilha(tmp_path / "x.xls", tmp_path, cubagem=tmp_path / "c.xlsx", rodar=falso) == []
