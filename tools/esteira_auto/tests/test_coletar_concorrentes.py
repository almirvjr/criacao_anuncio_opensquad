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


def test_material_ou_tipo_diferente_fica_fora_e_o_mais_parecido_vem_primeiro():
    perfil = C.perfil_de({"MATERIAL": "Plástico", "DISH_PLATE_TYPE": "Raso", "UNITS_PER_PACK": "1"})
    cands = [{**_c("MLB2", "Jogo De Prato Fundo Duralex", 9, True), "atributos": {"MATERIAL": "Vidro temperado", "DISH_PLATE_TYPE": "Fundo"}},
             {**_c("MLB3", "Prato Refeição Cozy Azul", 2), "atributos": {"MATERIAL": "Polipropileno", "DISH_PLATE_TYPE": "Raso", "UNITS_PER_PACK": "1"}},
             {**_c("MLB4", "Prato Raso Melamina", 8, True), "atributos": {"MATERIAL": "Melamina", "UNITS_PER_PACK": "12"}},
             {**_c("MLB5", "Prato Fundo Plástico", 9, True), "atributos": {"MATERIAL": "Plástico", "DISH_PLATE_TYPE": "Pratos Fundos"}},
             {**_c("MLB6", "Prato Sem Ficha", 9, True), "atributos": {}}]
    out = C.escolher({"id": "MLB1"}, cands, "prato refeição cozy", limite=3, perfil=perfil)
    assert [c["id"] for c in out] == ["MLB1", "MLB3", "MLB4", "MLB6"]


def test_grupo_material():
    assert C.grupo_material("Vidro temperado") == "vidro" and C.grupo_material("Polipropileno (PP)") == "plastico"
    assert C.grupo_material("Bambu e vidro") in ("vidro", "madeira") and C.grupo_material("Tecido") is None
    assert C.grupo_material("PP") == "plastico" and C.grupo_material(None) is None


def test_ficha_sem_comentario_nao_e_falha_e_chrome_caido_e(tmp_path):
    def montar(opinioes):
        lote = tmp_path / str(len(list(tmp_path.iterdir())))
        (lote / "categorizacao").mkdir(parents=True)
        (lote / "categorizacao" / "categorias.yaml").write_text(
            "categorias:\n  - pai_sku: ABC-1\n    category_id: MLB191838\n", encoding="utf-8")
        (lote / "anuncios-entrada.json").write_text(json.dumps(
            {"anuncios": [{"pai_sku": "ABC-1", "nome_base": "Prato", "variacoes": [{"ean": "7896553918021"}]}]}), encoding="utf-8")
        api = lambda c: ({"results": [{"id": "MLB1", "name": "Prato", "attributes": []}]} if "product_identifier" in c
                         else {"results": [{"item_id": "MLB9", "price": 1.0}]} if c.endswith("/items") else None)
        return C.coletar(lote, api=api, opinioes=opinioes, buscar=lambda t: [])
    assert montar(lambda ids, pag=None: {i: {"lidas": [], "sem_comentarios": True, "media_texto": "3.8"} for i in ids}) == []
    assert montar(lambda ids, pag=None: {i: {"erro": "TargetClosedError", "lidas": []} for i in ids}) == ["ABC-1"]


def test_coletar_grava_arquivo_e_falha_de_opiniao_volta_como_falha(tmp_path):
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

    def opinioes(ids, paginas=None):
        raise RuntimeError("chrome fechado")

    falhou = C.coletar(lote, api=api, opinioes=opinioes, buscar=lambda t: [])
    assert falhou == ["ABC-1"]  # o arquivo fica gravado; o maestro decide tentar de novo
    d = json.loads((lote / "inteligencia" / "_coleta" / "coleta-ABC-1.json").read_text(encoding="utf-8"))
    assert d["mesmo_produto"]["id"] == "MLB1"
    assert [c["id"] for c in d["concorrentes"]] == ["MLB1", "MLB2"]  # sem busca: mais vendidos completa
    assert d["concorrentes"][0]["perguntas"] == [{"pergunta": "Serve bolo?", "resposta": "Sim", "data": "2026-01-01"}]
    assert d["concorrentes"][0]["atributos"] == [{"id": "MATERIAL", "nome": "Material", "valor": "Bambu"}]
    assert d["opinioes_status"].startswith("falhou")
    assert d["resumo"]["perguntas"] == 2
    assert sorted(p.name for p in (lote / "inteligencia" / "_raw").glob("*.json")) == ["MLB1.json", "MLB2.json"]


def test_fica_quem_tem_opiniao_e_cor_repetida_sai(tmp_path):
    lote = tmp_path
    (lote / "categorizacao").mkdir()
    (lote / "categorizacao" / "categorias.yaml").write_text(
        "categorias:\n  - pai_sku: ABC-1\n    category_id: MLB191838\n", encoding="utf-8")
    (lote / "anuncios-entrada.json").write_text(json.dumps(
        {"anuncios": [{"pai_sku": "ABC-1", "nome_base": "Prato Cozy", "variacoes": [{"ean": "7896553918021"}]}]}), encoding="utf-8")
    plast = {"attributes": [{"id": "MATERIAL", "value_name": "Plástico"}, {"id": "DISH_PLATE_TYPE", "value_name": "Raso"}]}
    api = lambda c: ({"results": [{"id": "MLB1", "name": "Prato Cozy", **plast}]} if "product_identifier" in c
                     else {"id": "MLB1", "name": "Prato Cozy", **plast} if c == "/products/MLB1" else None)
    url = lambda i: f"https://www.mercadolivre.com.br/x/p/{i}"
    cartoes = [{"id": f"MLB{i}", "url": url(f"MLB{i}"), "titulo": f"Kit Pratos Rasos Plástico {i}", "nota": "4.5"} for i in range(2, 8)]
    op = lambda *ids: {"lidas": [{"id": x, "nota": 5, "texto": "bom"} for x in ids]}
    leitura = {"MLB2": op(1, 2, 3), "MLB3": op(1, 2, 3), "MLB4": {"lidas": []}, "MLB5": op(7), "MLB6": op(8, 9), "MLB7": op(10)}
    assert C.coletar(lote, api=api, opinioes=lambda ids, pag=None: leitura, buscar=lambda t: cartoes) == []
    d = json.loads((lote / "inteligencia" / "_coleta" / "coleta-ABC-1.json").read_text(encoding="utf-8"))
    assert [c["id"] for c in d["concorrentes"]] == ["MLB1", "MLB2", "MLB5", "MLB6"]
    assert d["resumo"]["opinioes"] == 6


def test_id_da_pagina():
    assert C.id_da_pagina("https://www.mercadolivre.com.br/kit-x/p/MLB65475077") == "MLB65475077"
    assert C.id_da_pagina("https://www.mercadolivre.com.br/jogo-4/up/MLBU3801523887") == "MLBU3801523887"
    assert C.id_da_pagina("https://produto.mercadolivre.com.br/MLB-1234567-prato-_JM") == "MLB1234567"
    assert C.id_da_pagina("https://click1.mercadolivre.com.br/x") is None


def test_escolher_da_busca_material_tipo_e_nota():
    perfil = C.perfil_de({"MATERIAL": "Plástico", "DISH_PLATE_TYPE": "Raso"})
    def k(i, t, nota="4.7"):
        return {"id": i, "url": f"https://www.mercadolivre.com.br/x/p/{i}", "titulo": t, "nota": nota}
    cartoes = [k("MLB1", "Prato Refeição Cozy"),                       # e o nosso: fora
               k("MLB2", "Jogo 6 Pratos Fundos de Vidro"),              # vidro: fora
               k("MLB3", "Kit 50 Pratos Plásticos Merenda"),            # plastico, sem 'raso'
               k("MLB4", "Kit 10 Pratos Rasos de Plástico Preto 26 cm"),  # plastico e raso: primeiro
               k("MLB5", "Prato Raso Branco Liso", nota=""),           # sem nota: fora
               k("MLB6", "Conjunto De Talheres Hambúrguer"),            # nao e prato
               k("MLB7", "Jogo De Pratos Rasos Resistente 4 Un")]       # raso, material nao diz
    out = C.escolher_busca(cartoes, "prato refeição cozy", perfil, {"MLB1"}, 6)
    assert [c["id"] for c in out] == ["MLB4", "MLB3", "MLB7"]
