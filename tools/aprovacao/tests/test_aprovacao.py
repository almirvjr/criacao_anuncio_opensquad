# tools/aprovacao/tests/test_aprovacao.py
import json
import threading
import urllib.error
import urllib.request
from datetime import datetime
import os
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import aprovacao as ap  # noqa: E402

PAI = "VIE-1-PAI"
TIT_OK = "Lixeira Inox 5 Litros Pedal Banheiro Cozinha Sofisticada"


def _doc(**extra):
    d = {
        "pai_sku": PAI, "nome_base": "LIXEIRA 5L", "modo": "variacoes", "status_copy": "warning",
        "warnings": ["Garantia ausente."],
        "titles": [
            {"texto": "Lixeira Inox 5 Litros Pedal Banheiro Lavabo", "recomendado": False, "justificativa": "a"},
            {"texto": TIT_OK, "recomendado": True, "justificativa": "b"},
        ],
        "description": {
            "bloco_1_abertura": "Lixeira bonita. Este modelo nao tem balde interno removivel.\n",
            "bloco_2_specs": "- Capacidade: 5 litros\n",
            "bloco_3_features_beneficios": "- Pedal: abre sem as maos\n",
            "word_count": 20,
        },
        "titulo_final": None,
        "attributes": {"BRAND": "Viel", "MODEL": "Cesto Lixo Redondo", "VOLUME_CAPACITY": "5 L"},
    }
    d.update(extra)
    return d


@pytest.fixture
def saida(tmp_path):
    (tmp_path / "copywriting").mkdir()
    (tmp_path / "inteligencia").mkdir()
    (tmp_path / "copywriting" / f"anuncio-{PAI}.yaml").write_text(
        yaml.safe_dump(_doc(), allow_unicode=True, sort_keys=False), encoding="utf-8")
    (tmp_path / "inteligencia" / f"brief-{PAI}.yaml").write_text(yaml.safe_dump({
        "pai_sku": PAI, "limitacoes": [{"texto": "Nao tem balde interno removivel"}],
        "dados_produto": {"caracteristicas": {}}}), encoding="utf-8")
    (tmp_path / "anuncios-entrada.json").write_text(json.dumps({"anuncios": [{
        "pai_sku": PAI, "preco_provisorio": True, "peso_bruto_kg": 0.7,
        "dim_embalagem_cm": {"largura": 28, "altura": 21, "comprimento": 21},
        "variacoes": [{"sku": "VIE-1-BR", "cor": "Branco", "preco_venda": 100.0, "ean": "7898755000001"},
                      {"sku": "VIE-1-PT", "cor": "Preto", "preco_venda": 100.0, "ean": "7898755000002"}]}]}), encoding="utf-8")
    (tmp_path / "categorizacao").mkdir()
    (tmp_path / "categorizacao" / "categorias.yaml").write_text(yaml.safe_dump({"categorias": [
        {"pai_sku": PAI, "category_id": "MLB33375", "breadcrumb": ["Casa", "Lixeiras"]}]}), encoding="utf-8")
    return tmp_path


def _gravar(saida, doc):
    (saida / "copywriting" / f"anuncio-{PAI}.yaml").write_text(
        yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")


class TestListar:
    def test_monta_o_cartao(self, saida):
        [c] = ap.listar_pendentes(saida)
        assert c["pai_sku"] == PAI
        assert c["titulo_inicial"] == TIT_OK
        assert c["marca"] == "Viel" and c["modelo"] == "Cesto Lixo Redondo"
        assert set(c["descricao"]) == {"bloco_1_abertura", "bloco_2_specs", "bloco_3_features_beneficios"}
        assert c["ficha"] == {"VOLUME_CAPACITY": "5 L"}
        assert c["precos"] == [{"cor": "Branco", "sku": "VIE-1-BR", "preco": 100.0},
                               {"cor": "Preto", "sku": "VIE-1-PT", "preco": 100.0}]
        assert c["preco_provisorio"] is True
        assert c["peso_kg"] == 0.7 and c["caixa_cm"]["largura"] == 28
        assert c["observacoes"] == ["Garantia ausente."]
        assert c["capas"] is None

    def test_titulo_final_ja_gravado_vem_primeiro(self, saida):
        _gravar(saida, _doc(titulo_final="Outro Titulo"))
        assert ap.listar_pendentes(saida)[0]["titulo_inicial"] == "Outro Titulo"

    def test_publicado_e_devolvido_nao_aparecem(self, saida):
        _gravar(saida, _doc(status_copy="aprovado"))
        assert ap.listar_pendentes(saida)[0]["situacao"] == "nao_publicado"  # aprovado sem publicar fica
        _publicado(saida, PAI)
        assert ap.listar_pendentes(saida) == []
        _gravar(saida, _doc(status_copy="devolvido"))
        assert ap.listar_pendentes(saida) == []

    def test_le_as_capas_quando_existem(self, saida):
        (saida / "capas").mkdir()
        (saida / "capas" / f"capas-{PAI}.yaml").write_text(yaml.safe_dump({
            "pai_sku": PAI, "picture_ids_por_variacao": [
                {"sku_variacao": "VIE-1-BR", "cor": "Branco", "picture_ids": ["https://x/a.jpg"]}]}),
            encoding="utf-8")
        assert ap.listar_pendentes(saida)[0]["capas"] == [{"cor": "Branco", "urls": ["https://x/a.jpg"]}]

    def test_arquivo_com_defeito_vira_cartao_de_erro(self, saida):
        (saida / "copywriting" / "anuncio-VIE-2-PAI.yaml").write_text("a: [", encoding="utf-8")
        cartoes = ap.listar_pendentes(saida)
        assert any(c.get("erro") and c["arquivo"] == "anuncio-VIE-2-PAI.yaml" for c in cartoes)
        assert any(c.get("pai_sku") == PAI for c in cartoes)

    def test_pasta_vazia(self, tmp_path):
        assert ap.listar_pendentes(tmp_path) == []
def _edicao(**kw):
    e = {"titulo": TIT_OK, "marca": "Viel", "modelo": "Cesto Lixo Redondo",
         "descricao": {"bloco_1_abertura": "Lixeira bonita. Este modelo nao tem balde interno removivel.\n",
                       "bloco_2_specs": "- Capacidade: 5 litros\n",
                       "bloco_3_features_beneficios": "- Pedal: abre sem as maos\n"}}
    e.update(kw)
    return e


def _codigos(itens, nivel=None):
    return [i["codigo"] for i in itens if nivel is None or i["nivel"] == nivel]


class TestConferir:
    def test_tudo_certo(self, saida):
        assert ap.conferir(saida, PAI, _edicao()) == []

    def test_titulo_acima_de_60_bloqueia(self, saida):
        itens = ap.conferir(saida, PAI, _edicao(titulo="L" * 61))
        assert "TITULO_LONGO" in _codigos(itens, "bloqueio")

    def test_titulo_vazio_bloqueia(self, saida):
        assert "TITULO_VAZIO" in _codigos(ap.conferir(saida, PAI, _edicao(titulo="  ")), "bloqueio")

    def test_marca_fora_do_padrao_e_erro_nao_bloqueio(self, saida):
        itens = ap.conferir(saida, PAI, _edicao(marca="Viel Inox"))
        assert "MARCA_FORA_DO_PADRAO" in _codigos(itens, "erro")
        assert _codigos(itens, "bloqueio") == []

    def test_promessa_falsa_aparece(self, saida):
        d = _edicao()["descricao"]
        d["bloco_3_features_beneficios"] = "- Com balde interno removivel\n"
        assert "CLAIM_FALSO_COPY" in _codigos(ap.conferir(saida, PAI, _edicao(descricao=d)), "erro")

    def test_bloco_apagado_nao_volta_o_texto_antigo(self, saida):
        d = _edicao()["descricao"]
        d["bloco_1_abertura"] = ""
        assert "LIMITACAO_FORA_DA_COPY" in _codigos(ap.conferir(saida, PAI, _edicao(descricao=d)))

    def test_modelo_longo_e_aviso(self, saida):
        itens = ap.conferir(saida, PAI, _edicao(modelo="Cesto Redondo Consultorio Escritorio Lavabo"))
        assert "WARN_MODELO_LONGO" in _codigos(itens, "aviso")

    def test_sem_brief_e_erro_visivel(self, saida):
        (saida / "inteligencia" / f"brief-{PAI}.yaml").unlink()
        assert "BRIEF_AUSENTE" in _codigos(ap.conferir(saida, PAI, _edicao()), "erro")

    def test_pai_invalido(self, saida):
        with pytest.raises(ValueError):
            ap.conferir(saida, "../x", _edicao())

    def test_aplicar_nao_mexe_no_original(self):
        doc = _doc()
        novo = ap.aplicar_edicao(doc, _edicao(marca="Terra Casa Decor"))
        assert doc["attributes"]["BRAND"] == "Viel"
        assert novo["attributes"]["BRAND"] == "Terra Casa Decor"
        assert novo["titulo_final"] == TIT_OK
        assert novo["description"]["word_count"] == 20


AGORA = datetime(2026, 10, 8, 14, 32, 5)


class TestAprovar:
    def test_grava_a_escolha(self, saida):
        r = ap.aprovar(saida, PAI, _edicao(marca="Terra Casa Decor"), agora=AGORA)
        assert r["ok"] is True
        doc = yaml.safe_load((saida / "copywriting" / f"anuncio-{PAI}.yaml").read_text(encoding="utf-8"))
        assert doc["status_copy"] == "aprovado"
        assert doc["titulo_final"] == TIT_OK
        assert doc["attributes"]["BRAND"] == "Terra Casa Decor"
        assert doc["aprovado_em"] == "2026-10-08 14:32"
        assert doc["avisos_aceitos"] == []
        assert ap.listar_pendentes(saida)[0]["situacao"] == "nao_publicado"

    def test_guarda_copia_do_anterior(self, saida):
        antes = (saida / "copywriting" / f"anuncio-{PAI}.yaml").read_text(encoding="utf-8")
        ap.aprovar(saida, PAI, _edicao(), agora=AGORA)
        copia = saida / "copywriting" / "_antes" / f"anuncio-{PAI}-20261008-143205.yaml"
        assert copia.read_text(encoding="utf-8") == antes

    def test_bloqueio_nao_grava(self, saida):
        antes = (saida / "copywriting" / f"anuncio-{PAI}.yaml").read_text(encoding="utf-8")
        r = ap.aprovar(saida, PAI, _edicao(titulo="L" * 61), agora=AGORA)
        assert r["ok"] is False
        assert (saida / "copywriting" / f"anuncio-{PAI}.yaml").read_text(encoding="utf-8") == antes

    def test_aviso_aceito_fica_registrado(self, saida):
        ap.aprovar(saida, PAI, _edicao(marca="Viel Inox"), vistos=["MARCA_FORA_DO_PADRAO"], agora=AGORA)
        doc = yaml.safe_load((saida / "copywriting" / f"anuncio-{PAI}.yaml").read_text(encoding="utf-8"))
        assert "MARCA_FORA_DO_PADRAO" in doc["avisos_aceitos"]

    def test_ja_aprovado_nao_aprova_de_novo(self, saida):
        ap.aprovar(saida, PAI, _edicao(), agora=AGORA)
        r = ap.aprovar(saida, PAI, _edicao(titulo="Outro"), agora=AGORA)
        assert r["ok"] is False


class TestDevolver:
    def test_grava_a_nota(self, saida):
        r = ap.devolver(saida, PAI, "Trocar o titulo, quero cozinha primeiro", agora=AGORA)
        assert r["ok"] is True
        doc = yaml.safe_load((saida / "copywriting" / f"anuncio-{PAI}.yaml").read_text(encoding="utf-8"))
        assert doc["status_copy"] == "devolvido"
        assert doc["nota_almir"] == "Trocar o titulo, quero cozinha primeiro"
        assert doc["devolvido_em"] == "2026-10-08 14:32"
        assert (saida / "copywriting" / "_antes" / f"anuncio-{PAI}-20261008-143205.yaml").is_file()

    def test_nota_vazia_nao_devolve(self, saida):
        assert ap.devolver(saida, PAI, "   ", agora=AGORA)["ok"] is False


def _publicado(saida, pai):
    """Publicacao de mentira: marca todas as cores como publicadas, sem rede."""
    p = saida / "copywriting" / f"anuncio-{pai}.yaml"
    doc = yaml.safe_load(p.read_text(encoding="utf-8"))
    doc["_total_cores"] = 2
    doc["publicacao"] = {s: {"sku": s, "ok": True, "mlb": "MLB" + s[-2:]} for s in ("VIE-1-PT", "VIE-1-BR")}
    p.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return list(doc["publicacao"].values())


def _nao_publica(*a, **k):
    raise AssertionError("teste tentou publicar de verdade")


def _subir(saida, esperar=False, publicar=_publicado):
    srv = ap.criar_servidor(saida, esperar=esperar, publicar=publicar, publicar_cor=_nao_publica)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def _post(url, corpo, tipo="application/json"):
    req = urllib.request.Request(url, data=json.dumps(corpo).encode(), method="POST",
                                 headers={"Content-Type": tipo})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


class TestServidor:
    def test_pagina_e_pendentes(self, saida):
        srv, base = _subir(saida)
        try:
            html = urllib.request.urlopen(base + "/").read().decode("utf-8")
            assert "<title>Aprovar anúncios</title>" in html
            dados = json.loads(urllib.request.urlopen(base + "/api/pendentes").read())
            assert dados["cartoes"][0]["pai_sku"] == PAI
        finally:
            srv.shutdown()

    def test_conferir_e_aprovar(self, saida):
        srv, base = _subir(saida)
        try:
            assert _post(base + "/api/conferir", {"pai": PAI, "edicao": _edicao()})["itens"] == []
            assert _post(base + "/api/aprovar", {"pai": PAI, "edicao": _edicao(preco="92,71")})["ok"] is True
            assert ap.listar_pendentes(saida) == []
        finally:
            srv.shutdown()

    def test_recusa_pedido_que_nao_e_json(self, saida):
        srv, base = _subir(saida)
        try:
            with pytest.raises(urllib.error.HTTPError) as e:
                _post(base + "/api/aprovar", {"pai": PAI, "edicao": _edicao()}, tipo="text/plain")
            assert e.value.code == 415
        finally:
            srv.shutdown()

    def test_pai_invalido_responde_400(self, saida):
        srv, base = _subir(saida)
        try:
            with pytest.raises(urllib.error.HTTPError) as e:
                _post(base + "/api/conferir", {"pai": "../x", "edicao": _edicao()})
            assert e.value.code == 400
        finally:
            srv.shutdown()

    def test_esperar_encerra_quando_acaba(self, saida):
        srv, base = _subir(saida, esperar=True)
        _post(base + "/api/devolver", {"pai": PAI, "nota": "refazer"})
        srv.encerrado.wait(5)
        assert srv.encerrado.is_set()
        assert srv.estado["devolvidos"] == 1

class TestRevisaoFinal:
    # I1: defeito em arquivo auxiliar nao derruba a lista
    def test_capas_com_defeito_so_afeta_o_proprio_cartao(self, saida):
        (saida / "capas").mkdir()
        (saida / "capas" / f"capas-{PAI}.yaml").write_text("a: [", encoding="utf-8")
        [c] = ap.listar_pendentes(saida)
        assert c.get("erro") and PAI in c["arquivo"]

    def test_entrada_com_defeito_nao_derruba(self, saida):
        (saida / "anuncios-entrada.json").write_text("{", encoding="utf-8")
        cartoes = ap.listar_pendentes(saida)
        assert any(c.get("erro") and c["arquivo"] == "anuncios-entrada.json" for c in cartoes)
        assert any(c.get("pai_sku") == PAI for c in cartoes)

    # I2: descricao vazia
    def test_descricao_toda_vazia_bloqueia(self, saida):
        d = {k: "" for k in _edicao()["descricao"]}
        assert "DESCRICAO_VAZIA" in _codigos(ap.conferir(saida, PAI, _edicao(descricao=d)), "bloqueio")

    def test_um_bloco_vazio_e_erro(self, saida):
        d = _edicao()["descricao"]
        d["bloco_2_specs"] = "  "
        assert "BLOCO_VAZIO" in _codigos(ap.conferir(saida, PAI, _edicao(descricao=d)), "erro")

    # I3: so aprova com erro que a pagina mostrou
    def test_recusa_erro_que_o_almir_nao_viu(self, saida):
        r = ap.aprovar(saida, PAI, _edicao(marca="Viel Inox"), vistos=[], agora=AGORA)
        assert r["ok"] is False
        assert "MARCA_FORA_DO_PADRAO" in [i["codigo"] for i in r["conferencia"]]
        assert ap.listar_pendentes(saida)[0]["pai_sku"] == PAI

    # I4: codigo de saida le os arquivos
    def test_situacao_do_lote(self, saida):
        assert ap.situacao_lote(saida) == 2
        ap.aprovar(saida, PAI, _edicao(), agora=AGORA)
        assert ap.situacao_lote(saida) == 2  # aprovado, ainda nao publicado
        _publicado(saida, PAI)
        assert ap.situacao_lote(saida) == 0
        _gravar(saida, _doc(status_copy="devolvido"))
        assert ap.situacao_lote(saida) == 3

    def test_arquivo_com_defeito_nao_e_tudo_aprovado(self, saida):
        ap.aprovar(saida, PAI, _edicao(), agora=AGORA)
        (saida / "copywriting" / "anuncio-VIE-2-PAI.yaml").write_text("a: [", encoding="utf-8")
        assert ap.situacao_lote(saida) == 2

    def test_esperar_encerra_mesmo_com_cartao_de_erro(self, saida):
        (saida / "copywriting" / "anuncio-VIE-2-PAI.yaml").write_text("a: [", encoding="utf-8")
        srv, base = _subir(saida, esperar=True)
        _post(base + "/api/aprovar", {"pai": PAI, "edicao": _edicao(preco="92,71"), "vistos": []})
        srv.encerrado.wait(5)
        assert srv.encerrado.is_set()


class TestMarcaPropria:
    def test_fornecedor_sobrando_na_descricao_aparece(self, saida):
        d = _edicao()["descricao"]
        d["bloco_2_specs"] = "- Capacidade: 5 litros\n- Marca: Viel\n"
        itens = ap.conferir(saida, PAI, _edicao(marca="Terra Casa Decor", descricao=d))
        assert "FORNECEDOR_NA_DESCRICAO" in _codigos(itens, "erro")


def test_ler_preco():
    assert ap.ler_preco("129,90") == 129.9
    assert ap.ler_preco("R$ 1.299,90") == 1299.9
    assert ap.ler_preco("92.71") == 92.71
    for ruim in ("", "0", "-5", "abc"):
        with pytest.raises(ValueError, match="Preco"):
            ap.ler_preco(ruim)


def _edicao_pub(**extra):
    e = {"titulo": TIT_OK, "marca": "Viel", "modelo": "Cesto Lixo Redondo",
         "descricao": _doc()["description"], "preco": "92,71", "decisoes": []}
    e.update(extra)
    return e


def test_aprovar_e_publicar_grava_preco_e_decisao(saida):
    chamadas = []
    def pub(s, pai):
        chamadas.append(pai)
        return [{"sku": "VIE-1-PT", "ok": True, "mlb": "MLB1"}]
    dec = [{"chave": "material", "valor": "Aço inox", "campo_ficha": "MATERIAL"}]
    vistos = [i["codigo"] for i in ap.conferir(saida, PAI, _edicao_pub())]
    r = ap.aprovar_e_publicar(saida, PAI, _edicao_pub(decisoes=dec), vistos=vistos, publicar=pub)
    assert r["ok"] and chamadas == [PAI]
    doc = yaml.safe_load((saida / "copywriting" / f"anuncio-{PAI}.yaml").read_text(encoding="utf-8"))
    assert doc["preco"] == 92.71 and doc["status_copy"] == "aprovado"
    assert doc["attributes"]["MATERIAL"] == "Aço inox"
    assert doc["dados_decididos"] == dec


def test_sem_preco_nao_aprova(saida):
    r = ap.aprovar_e_publicar(saida, PAI, _edicao_pub(preco=""), vistos=[], publicar=lambda s, p: 1 / 0)
    assert not r["ok"] and "Preco" in r["motivo"]


def test_ean_vazio_trava(saida):
    e = json.loads((saida / "anuncios-entrada.json").read_text(encoding="utf-8"))
    e["anuncios"][0]["variacoes"][0]["ean"] = None
    e["anuncios"][0]["variacoes"][1]["ean"] = "7898755000001"
    (saida / "anuncios-entrada.json").write_text(json.dumps(e), encoding="utf-8")
    itens = ap.conferir(saida, PAI, _edicao_pub())
    assert any(i["codigo"] == "SEM_EAN" and i["nivel"] == "bloqueio" and "Branco" in i["texto"] for i in itens)


def test_tirar_do_lote(saida):
    assert ap.tirar(saida, PAI)["ok"]
    assert ap.listar_pendentes(saida) == []
    assert ap.situacao_lote(saida) == 0


def test_aprovado_em_parte_continua_na_tela(saida):
    d = _doc(status_copy="aprovado", titulo_final=TIT_OK, preco=92.71, _total_cores=2,
             publicacao={"VIE-1-PT": {"sku": "VIE-1-PT", "ok": True, "mlb": "MLB1"},
                         "VIE-1-BR": {"sku": "VIE-1-BR", "ok": False, "mlb": None, "erro": "x"}})
    _gravar(saida, d)
    cart = ap.listar_pendentes(saida)
    assert len(cart) == 1 and cart[0]["situacao"] == "em_parte"
    assert ap.situacao_lote(saida) == 2


def test_cartao_tem_tudo(saida):
    c = ap.listar_pendentes(saida)[0]
    assert [x["cor"] for x in c["cores"]] == ["Preto", "Branco"]
    assert c["cores"][0]["titulo_ml"].endswith(" Preto")
    assert "quadro" in c and "categoria" in c and c["tipo_anuncio"] == "Premium"


def test_sku_com_sublinhado(saida):
    assert ap.caminho_anuncio(saida, "BRI-coza34-40652_3009").name == "anuncio-BRI-coza34-40652_3009.yaml"
