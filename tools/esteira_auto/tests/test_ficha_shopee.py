# tools/esteira_auto/tests/test_ficha_shopee.py — ficha da Shopee na esteira (hub, PLANO-SHOPEE etapa 2, 06/11/2026)
import json
import os
import sys

import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from esteira_auto import pedido as P, travas  # noqa: E402

PAI = "BEL-4007-PAI"
SKUS = ["BEL-4007-0740-PE", "BEL-4007-2617-BR"]
# forma que o hub-ler-pedido v20 grava (camposShopee), encurtada
TRAVESSAS = {"id": "101267", "nome": "Travessas", "caminho": "Casa e Decoração > Louça > Travessas", "de": "sugerida",
             "campos": [
                 {"id": 100134, "nome": "Material", "obrigatorio": True, "tipo": 5, "numero": False, "unidades": [],
                  "valores": [{"id": 1, "nome": "Porcelana"}, {"id": 2, "nome": "Cerâmica"}]},
                 {"id": 100666, "nome": "Diâmetro", "obrigatorio": False, "tipo": 5, "numero": True,
                  "unidades": ["cm", "inches"], "valores": []},
                 {"id": 100200, "nome": "Formato", "obrigatorio": False, "tipo": 1, "numero": False, "unidades": [],
                  "valores": [{"id": 7, "nome": "Oval"}, {"id": 8, "nome": "Redondo"}]},
                 {"id": 100300, "nome": "Usos", "obrigatorio": False, "tipo": 4, "numero": False, "unidades": [],
                  "valores": [{"id": 9, "nome": "Micro-ondas"}, {"id": 10, "nome": "Lava-louças"}]},
                 {"id": 100400, "nome": "Quantidade", "obrigatorio": True, "tipo": 3, "numero": False,
                  "unidades": [], "valores": []}]}
PRATOS = {"id": "101243", "nome": "Pratos", "caminho": "Casa e Decoração > Louça > Pratos", "de": "aprendida",
          "campos": [{"id": 1, "nome": "Material", "obrigatorio": True, "tipo": 3, "valores": []}]}
BOA = [{"nome": "Material", "valor": "Porcelana"}, {"nome": "Diâmetro", "motivo": "peca oval"},
       {"nome": "Formato", "valor": "Oval"}, {"nome": "Usos", "valor": ["Micro-ondas", "Lava-louças"]},
       {"nome": "Quantidade", "valor": "1 travessa"}]


def _lote(tmp_path, ficha, candidatas=(TRAVESSAS,), conferida=False, nome="Travessa Oval Porcelana"):
    lote = tmp_path / "lote"
    (lote / "copywriting").mkdir(parents=True, exist_ok=True)
    pedido = {"pedido_id": 1, "canais": ["ml", "shopee"], "produto": {"com_variacao": True},
              "olist": {"pai": {"sku": PAI}, "variacoes": [{"sku": s} for s in SKUS],
                        "shopee": {"conferida": conferida, "candidatas": list(candidatas), "avisos": []}}}
    (lote / "pedido.json").write_text(json.dumps(pedido), encoding="utf-8")
    ent = {"anuncios": [{"pai_sku": PAI, "nome_base": nome, "variacoes": [{"sku": s} for s in SKUS]}]}
    # a mesma montagem do pedido.py (sem cubagem/normalizer)
    ent["anuncios"][0]["shopee"] = {"candidatas": [{**c, "aprendida": c.get("de") == "aprendida"} for c in candidatas],
                                    "fixa": conferida, "termos": [], "decisoes": []}
    (lote / "anuncios-entrada.json").write_text(json.dumps(ent), encoding="utf-8")
    an = {"status_copy": "pendente", "titulo_final": "Travessa"}
    if ficha is not None:
        an["ficha_shopee"] = ficha
    (lote / "copywriting" / f"anuncio-{PAI}.yaml").write_text(yaml.safe_dump(an, allow_unicode=True), encoding="utf-8")
    (lote / "andamento.json").write_text(json.dumps({"pedido_id": 1, "feitas": [], "parados": {}}), encoding="utf-8")
    return lote


def _erro(lote):
    return travas._ficha_shopee(lote, PAI, lote / "copywriting" / f"anuncio-{PAI}.yaml")


def test_ficha_completa_passa_e_vai_para_o_hub(tmp_path):
    lote = _lote(tmp_path, {"categoria_id": "101267", "campos": BOA})
    assert _erro(lote) is None and travas.pendentes_shopee(lote, PAI) == []
    r = P.resultado(lote, ler_precos=lambda l: {})["produtos"][0]
    assert r["canais"]["shopee"]["categoria_id"] == "101267"
    assert "ficha_shopee" not in r["anuncio"]


def test_sem_ficha_reprova(tmp_path):
    assert "falta a ficha da Shopee" in _erro(_lote(tmp_path, None))


def test_categoria_fora_das_candidatas(tmp_path):
    assert "uma das candidatas" in _erro(_lote(tmp_path, {"categoria_id": "999", "campos": BOA}))


def test_categoria_longe_do_produto_reprova_aprendida_passa(tmp_path):
    # "Pratos" aprendida passa (ja deu certo); sugerida sem palavra do produto, nao
    lote = _lote(tmp_path, {"categoria_id": "101243", "campos": [{"nome": "Material", "valor": "Porcelana"}]},
                 candidatas=(TRAVESSAS, PRATOS))
    assert _erro(lote) is None
    longe = {**TRAVESSAS, "id": "5", "nome": "Abridor de Garrafas", "de": "sugerida"}
    lote = _lote(tmp_path, {"categoria_id": "5", "campos": BOA}, candidatas=(longe, TRAVESSAS))
    e = _erro(lote)
    assert "nao tem a ver com o produto" in e and "ficha_shopee" in e and "Travessas = 101267" in e


def test_lista_fechada_numero_e_varios(tmp_path):
    campos = [dict(c) for c in BOA]
    campos[2] = {"nome": "Formato", "valor": "Ovalado"}
    campos[1] = {"nome": "Diâmetro", "valor": "25,7 cm"}
    e = _erro(_lote(tmp_path, {"categoria_id": "101267", "campos": campos}))
    assert "Formato: \"Ovalado\" nao esta na lista" in e and "Diâmetro: so o numero" in e
    campos[2] = {"nome": "Formato", "valor": ["Oval", "Redondo"]}
    campos[1] = {"nome": "Diâmetro", "valor": "25,7", "unidade": "mm"}
    e = _erro(_lote(tmp_path, {"categoria_id": "101267", "campos": campos}))
    assert "Formato: so aceita um valor" in e and "`unidade` tem que ser uma de cm, inches" in e
    campos[2] = {"nome": "Formato", "valor": "oval"}  # maiuscula nao importa
    campos[1] = {"nome": "Diâmetro", "valor": "25,7", "unidade": "cm"}
    assert _erro(_lote(tmp_path, {"categoria_id": "101267", "campos": campos})) is None


def test_todo_campo_com_valor_ou_motivo(tmp_path):
    campos = [c for c in BOA if c["nome"] != "Formato"] + [{"nome": "Cor", "valor": "Azul"},
                                                          {"nome": "Usos", "valor": "x", "motivo": "y"}]
    campos = [c for c in campos if not (c["nome"] == "Usos" and "motivo" not in c)]
    e = _erro(_lote(tmp_path, {"categoria_id": "101267", "campos": campos}))
    assert "Formato: sem resposta" in e and "Cor: nao existe na categoria" in e and "Usos: precisa de valor OU" in e


def test_obrigatorio_sem_fonte_vira_pendencia(tmp_path):
    campos = [c for c in BOA if c["nome"] != "Quantidade"] + [{"nome": "Quantidade", "motivo": "nenhuma fonte"}]
    lote = _lote(tmp_path, {"categoria_id": "101267", "campos": campos})
    assert _erro(lote) is None and travas.pendentes_shopee(lote, PAI) == ["Quantidade"]
    q = next(c for c in P.resultado(lote, ler_precos=lambda l: {})["produtos"][0]["canais"]["shopee"]["campos"]
             if c["nome"] == "Quantidade")
    assert q["motivo"] == "PENDENTE: obrigatório na Shopee — preencher na ficha (nenhuma fonte)" and "valor" not in q


def test_sem_shopee_no_pedido_nao_cobra(tmp_path):
    lote = _lote(tmp_path, None, candidatas=())
    assert _erro(lote) is None
    assert "shopee" not in P.resultado(lote, ler_precos=lambda l: {})["produtos"][0]["canais"]


def test_montar_entrada_leva_a_shopee(tmp_path, monkeypatch):
    lote = _lote(tmp_path, None, candidatas=(TRAVESSAS, PRATOS), conferida=False)
    monkeypatch.setattr(P.tte, "aplicar_cubagem", lambda recs, cub: None)
    monkeypatch.setattr(P.precheck, "faltas_de_caixa", lambda out: [])
    monkeypatch.setattr(P, "normalize", lambda recs: {"anuncios": [{"pai_sku": PAI, "variacoes": [{"sku": s} for s in SKUS]}]})
    assert P.montar_entrada(lote, ler_cubagem=lambda c: {}) == []
    sp = json.loads((lote / "anuncios-entrada.json").read_text(encoding="utf-8"))["anuncios"][0]["shopee"]
    assert [c["id"] for c in sp["candidatas"]] == ["101267", "101243"]
    assert [c["aprendida"] for c in sp["candidatas"]] == [False, True] and sp["fixa"] is False


# categoria real "Pratos" da Shopee (get_attribute_tree lido em 06/11/2026, 17 campos, nenhum obrigatorio)
PRATOS_REAL = json.loads((__import__("pathlib").Path(__file__).parent / "dados" / "shopee_101243_pratos.json")
                         .read_text(encoding="utf-8"))
FICHA_PRATO = [
    {"nome": "Dimensões do Produto", "valor": "Único"},
    {"nome": "País de Origem", "valor": "Brasil"},
    {"nome": "Duração da Garantia", "valor": "1 Mês"},
    {"nome": "Funcionalidades", "valor": ["Durável"]},
    {"nome": "Material", "valor": "Cerâmica"},
    {"nome": "Estampa", "motivo": "muda por variacao"},
    {"nome": "Estilo", "motivo": "nenhuma fonte diz o estilo"},
    {"nome": "Tipo de Garantia", "valor": "Garantia do Fornecedor"},
    {"nome": "Diâmetro", "valor": "25,7", "unidade": "cm"},
    {"nome": "Coleção de Antiguidade", "valor": "Não"},
    {"nome": "Tipo de Prato", "valor": "Prato de Jantar"},
    {"nome": "Número de Pedaços", "valor": "1"},
    {"nome": "Quantidade da embalagem", "valor": "1 prato"},
    {"nome": "Tamanho Do Pacote", "motivo": "nenhuma fonte"},
    {"nome": "Produto personalizado", "valor": "Não"},
    {"nome": "Quantidade por Pacote", "valor": "1"},
    {"nome": "BPA Free", "motivo": "a Shopee nao da opcoes"},
]


def test_categoria_real_pratos(tmp_path):
    lote = _lote(tmp_path, {"categoria_id": "101243", "campos": FICHA_PRATO}, candidatas=(PRATOS_REAL,),
                 nome="Prato Raso Porcelana")
    assert _erro(lote) is None and travas.pendentes_shopee(lote, PAI) == []
    ruim = [dict(c) for c in FICHA_PRATO]
    ruim[-1] = {"nome": "BPA Free", "valor": "Sim"}
    ruim[9] = {"nome": "Coleção de Antiguidade", "valor": "Talvez"}
    e = _erro(_lote(tmp_path, {"categoria_id": "101243", "campos": ruim}, candidatas=(PRATOS_REAL,)))
    assert "BPA Free: a Shopee nao deu opcoes" in e and "Coleção de Antiguidade: \"Talvez\" nao esta na lista" in e


def test_decisao_do_almir_no_formato_do_hub(tmp_path):
    """O hub manda a decisao como guarda (mig 284): varios = "A | B", numero = "25,7 cm"."""
    lote = _lote(tmp_path, {"categoria_id": "101267", "campos": BOA})
    ent = json.loads((lote / "anuncios-entrada.json").read_text(encoding="utf-8"))
    ent["anuncios"][0]["shopee"]["decisoes"] = [
        {"categoria_id": "101267", "campo": "Usos", "valor": "Micro-ondas | Lava-louças"},
        {"categoria_id": "101267", "campo": "Diâmetro", "valor": "30 cm"}]
    (lote / "anuncios-entrada.json").write_text(json.dumps(ent), encoding="utf-8")
    e = _erro(lote)
    assert "Diâmetro: contra a decisao do Almir (30 cm)" in e and "Usos" not in e
    assert travas.valor_shopee_hub({"valor": "30", "unidade": "cm"}) == "30 cm"
