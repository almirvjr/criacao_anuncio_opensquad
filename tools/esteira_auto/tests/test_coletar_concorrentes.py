import json

from esteira_auto import coletar_concorrentes as C


def _c(cid, nome, vend, mv=False):
    return {"id": cid, "nome": nome, "vendedores": vend, "mais_vendido": mv}


def test_escolhe_mesmo_produto_depois_mais_vendidos_parecidos_depois_mais_vendedores():
    cands = [_c("MLB2", "Suporte Giratório Fotografia", 9, True),   # mais vendido, mas nao e boleira: fora
             _c("MLB3", "Boleira Vidro com Tampa", 3, True),
             _c("MLB1", "Boleira Bambu", 10, True),                  # e o mesmo produto: nao repete
             _c("MLB4", "Boleira Prato Bolo Vidro", 0),              # sem vendedor: fora
             _c("MLB5", "Boleira Cerâmica com Pé", 5),
             _c("MLB6", "BOLEIRA giratória", 7)]
    out = C.escolher({"id": "MLB1"}, cands, "boleira prato com cúpula", limite=3)
    assert [c["id"] for c in out] == ["MLB1", "MLB3", "MLB6", "MLB5"]
    assert [c["origem"] for c in out] == ["mesmo_produto", "mais_vendidos", "busca", "busca"]


def test_sem_mesmo_produto_pega_so_o_limite():
    cands = [_c(f"MLB{i}", "Lixeira Inox", 10 - i) for i in range(2, 7)]
    out = C.escolher(None, cands, "lixeira inox pedal", limite=3)
    assert [c["id"] for c in out] == ["MLB2", "MLB3", "MLB4"]


def test_codigo_estranho_nao_vira_endereco():
    out = C.escolher({"id": "../x"}, [_c("MLB2?a=1", "boleira", 5), _c("MLB7", "boleira", 1)], "boleira", limite=3)
    assert [c["id"] for c in out] == ["MLB7"]


def test_termo_busca_tira_medida_e_simbolo():
    assert C.termo_busca("BOLEIRA PRATO COM CÚPULA BRISA Ø26,5 cm") == "boleira prato com cúpula"
    assert C.termo_busca("Lixeira Inox 5L Pedal") == "lixeira inox pedal"
    assert C.termo_busca(None) == ""


def test_limpar_opiniao_guarda_so_nota_texto_data():
    bruta = {"id": 3071790867, "rating": 5, "variant": "", "comment": {"content": {"text": "Achei lindo.", "see_more": "Saiba mais"},
             "date": "Há 2 meses", "country": "Brasil"}, "menu_options": {"track": {"x": 1}}}
    assert C.limpar_opiniao(bruta) == {"id": 3071790867, "nota": 5, "texto": "Achei lindo.", "quando": "Há 2 meses"}


def test_limpar_opiniao_sem_texto_vira_none():
    assert C.limpar_opiniao({"id": 1, "rating": 4, "comment": {}}) is None


def test_resumo_conta_por_nota():
    ops = [{"nota": 5}, {"nota": 5}, {"nota": 1}, {"nota": 3}]
    assert C.por_nota(ops) == {"1": 1, "2": 0, "3": 1, "4": 0, "5": 2}


def test_coletar_grava_arquivo_e_falha_de_opiniao_nao_para(tmp_path):
    lote = tmp_path
    (lote / "categorizacao").mkdir()
    (lote / "categorizacao" / "categorias.yaml").write_text(
        "categorias:\n  - pai_sku: ABC-1\n    category_id: MLB193523\n", encoding="utf-8")
    (lote / "anuncios-entrada.json").write_text(json.dumps(
        {"anuncios": [{"pai_sku": "ABC-1", "nome_base": "Boleira", "variacoes": [{"ean": "7900161004929"}]}]}), encoding="utf-8")

    def api(caminho):
        if caminho.startswith("/products/search") and "product_identifier" in caminho:
            return {"results": [{"id": "MLB1"}]}
        if caminho.startswith("/highlights/"):
            return {"content": [{"id": "MLB2", "type": "PRODUCT"}]}
        if caminho.startswith("/products/search"):
            return {"results": []}
        if caminho.endswith("/items"):
            return {"results": [{"item_id": "MLB900", "price": 50.0, "seller_id": 7}]}
        if caminho.startswith("/products/"):
            return {"id": caminho.split("/")[2], "name": "Boleira X", "attributes": [{"id": "MATERIAL", "name": "Material", "value_name": "Bambu"}],
                    "main_features": [{"text": "Leve"}], "pictures": [1, 2]}
        if caminho.endswith("/description"):
            return {"plain_text": "Descrição"}
        if caminho.startswith("/questions/search"):
            return {"total": 1, "questions": [{"text": "Serve bolo?", "answer": {"text": "Sim"}, "date_created": "2026-01-01", "from": {"id": 5}}]}
        return None

    def opinioes(ids):
        raise RuntimeError("chrome fechado")

    falhou = C.coletar(lote, api=api, opinioes=opinioes)
    assert falhou == []
    d = json.loads((lote / "inteligencia" / "_coleta" / "coleta-ABC-1.json").read_text(encoding="utf-8"))
    assert d["mesmo_produto"]["id"] == "MLB1"
    assert [c["id"] for c in d["concorrentes"]] == ["MLB1", "MLB2"]  # sem busca: mais vendidos completa
    assert d["concorrentes"][0]["perguntas"] == [{"pergunta": "Serve bolo?", "resposta": "Sim", "data": "2026-01-01"}]
    assert d["concorrentes"][0]["atributos"] == [{"id": "MATERIAL", "nome": "Material", "valor": "Bambu"}]
    assert d["opinioes_status"].startswith("falhou")
    assert d["resumo"]["perguntas"] == 2
    assert sorted(p.name for p in (lote / "inteligencia" / "_raw").glob("*.json")) == ["MLB1.json", "MLB2.json"]
