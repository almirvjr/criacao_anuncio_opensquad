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


def test_link_que_nao_e_http_e_descartado():
    # o brief vem da pesquisa nos concorrentes (texto de fora): "javascript:" rodaria na tela
    b = {"dados_produto": {"material": {"valor": None, "status": "divergente", "valores_divergentes": [
        {"valor": "x", "fonte": "c1", "permalink": "javascript:fetch('/api/aprovar')"},
        {"valor": "y", "fonte": "c2", "permalink": "https://www.mercadolivre.com.br/p/1"}]}}}
    fontes = quadro.montar(b, {})[0]["fontes"]
    assert [f["link"] for f in fontes] == [None, "https://www.mercadolivre.com.br/p/1"]


CAMPOS = [{"id": "TOTAL_HEIGHT", "nome": "Altura total", "values": []}, {"id": "COLOR", "nome": "Cor", "values": ["Bege", "Marrom-claro"]},
          {"id": "WITH_PEDESTAL", "nome": "Com pé", "values": ["Não", "Sim"]}]


def test_altura_cai_na_altura_total_da_categoria():
    alt = quadro.montar(BRIEF, {}, campos=CAMPOS)[1]
    assert alt["campo_ficha"] == "TOTAL_HEIGHT"


def test_campo_pendente_da_categoria_vira_item_com_as_opcoes_do_ml():
    q = quadro.montar({}, {}, campos=CAMPOS, pendentes=["COLOR"])
    assert q == [{"chave": "COLOR", "rotulo": "Cor", "status": "pendente", "campo_ficha": "COLOR", "unidade": None,
                  "fontes": [{"origem": "lista do ML", "valor": "Bege", "link": None},
                             {"origem": "lista do ML", "valor": "Marrom-claro", "link": None}]}]


def test_pendente_que_ja_esta_no_brief_nao_repete():
    q = quadro.montar(BRIEF, {}, campos=CAMPOS, pendentes=["TOTAL_HEIGHT"])
    assert [i["chave"] for i in q].count("dimensoes_produto.altura_cm") == 1 and "TOTAL_HEIGHT" not in [i["chave"] for i in q]
