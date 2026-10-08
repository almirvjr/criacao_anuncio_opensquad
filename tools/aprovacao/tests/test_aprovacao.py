# tools/aprovacao/tests/test_aprovacao.py
import json
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
        "variacoes": [{"sku": "VIE-1-BR", "cor": "Branco", "preco_venda": 100.0},
                      {"sku": "VIE-1-PT", "cor": "Preto", "preco_venda": 100.0}]}]}), encoding="utf-8")
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

    def test_aprovado_e_devolvido_nao_aparecem(self, saida):
        _gravar(saida, _doc(status_copy="aprovado"))
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
        assert ap.listar_pendentes(saida) == []

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
        ap.aprovar(saida, PAI, _edicao(marca="Viel Inox"), agora=AGORA)
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
