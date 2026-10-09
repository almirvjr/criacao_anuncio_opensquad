# tools/aprovacao/tests/test_quadro.py
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import quadro  # noqa: E402

BRIEF = {"dados_produto": {
    "material": {"valor": None, "fonte": None, "status": "pendente"},
    "dimensoes_produto": {
        "altura_cm": {"valor": 25, "fonte": "almir", "status": "divergente",
                      "valores_divergentes": [{"valor": 27, "fonte": "concorrente-MLB1", "permalink": "https://ml/1"}]},
        "largura_cm": {"valor": 18, "fonte": "almir", "status": "ok"},
        "nota": "texto solto"},
    "caracteristicas": {"valor": ["a"], "status": "ok"}}}


def test_so_pendente_e_divergente():
    q = quadro.montar(BRIEF, {"HEIGHT": "25 cm", "BRAND": "Viel"})
    assert [i["chave"] for i in q] == ["material", "dimensoes_produto.altura_cm"]


def test_divergente_traz_as_duas_fontes_e_campo():
    alt = quadro.montar(BRIEF, {"HEIGHT": "25 cm"})[1]
    assert [f["valor"] for f in alt["fontes"]] == ["25", "27"]
    assert alt["fontes"][1]["link"] == "https://ml/1"
    assert alt["campo_ficha"] == "HEIGHT" and alt["unidade"] == "cm"


def test_campo_inexistente_na_ficha_fica_sem_campo():
    mat = quadro.montar(BRIEF, {"HEIGHT": "25 cm"})[0]
    assert mat["campo_ficha"] is None and mat["fontes"] == []


def test_brief_vazio():
    assert quadro.montar({}, {}) == []


def test_material_cai_no_material_do_corpo_quando_nao_ha_material():
    mat = quadro.montar(BRIEF, {"STRUCTURE_MATERIALS": "Aço inox"})[0]
    assert mat["campo_ficha"] == "STRUCTURE_MATERIALS"
