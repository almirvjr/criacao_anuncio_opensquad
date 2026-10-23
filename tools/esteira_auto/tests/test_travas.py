# tools/esteira_auto/tests/test_travas.py
import json
import os
import subprocess
import sys

import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from esteira_auto import travas  # noqa: E402


def test_categoria_falta_um(tmp_path):
    (tmp_path / "categorizacao").mkdir()
    (tmp_path / "categorizacao" / "categorias.yaml").write_text(yaml.safe_dump(
        {"categorias": [{"pai_sku": "A", "category_id": "MLB1"}]}), encoding="utf-8")
    r = travas.conferir("categoria", tmp_path, ["A", "B"])
    assert list(r) == ["B"] and "categoria" in r["B"]


def test_pesquisa_reprovada_traz_saida_do_validador(tmp_path):
    def falso(cmd, **kw):
        ok = "brief-A.yaml" in " ".join(cmd)
        return subprocess.CompletedProcess(cmd, 0 if ok else 1, "" if ok else "BLOQUEIO: limitacoes vazias", "")
    r = travas.conferir("pesquisa", tmp_path, ["A", "B"], rodar=falso)
    assert r == {"B": "BLOQUEIO: limitacoes vazias"}


def test_texto_roda_as_tres_travas(tmp_path):
    vistos = []
    def falso(cmd, **kw):
        vistos.append(os.path.basename(cmd[1]))
        return subprocess.CompletedProcess(cmd, 0, "", "")
    assert travas.conferir("texto", tmp_path, ["A"], rodar=falso) == {}
    assert vistos == ["validar_claims.py", "validar_ficha_seo.py", "validar_ficha_nsa.py"]


def test_capas_lista_quem_falta(tmp_path):
    falso = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "CAPAS INCOMPLETAS - 1:\n  - B: falta capa da cor 'Preto'", "")
    (tmp_path / "capas").mkdir(); (tmp_path / "capas" / "_busca.json").write_text("{}")
    r = travas.conferir("capas", tmp_path, ["A", "B"], rodar=falso)
    assert list(r) == ["B"] and "Preto" in r["B"]


def test_ficha_nsa_recebe_a_lista_de_campos_quando_existe(tmp_path):
    (tmp_path / "categorizacao").mkdir()
    (tmp_path / "categorizacao" / "campos-A.json").write_text("[]", encoding="utf-8")
    vistos = []
    def falso(cmd, **kw):
        vistos.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")
    travas.conferir("texto", tmp_path, ["A"], rodar=falso)
    nsa = [c for c in vistos if c[1].endswith("validar_ficha_nsa.py")][0]
    assert nsa[-1].endswith("campos-A.json")


def _anuncio(tmp_path, longos, **extra):
    (tmp_path / "copywriting").mkdir(exist_ok=True)
    (tmp_path / "copywriting" / "anuncio-A.yaml").write_text(yaml.safe_dump(
        {"pai_sku": "A", "titulos_longos": longos, **extra}, allow_unicode=True), encoding="utf-8")


def _ok(cmd, **kw):
    return subprocess.CompletedProcess(cmd, 0, "", "")


def test_titulos_longos_conferidos_pelo_tamanho_de_verdade(tmp_path):
    bom = [{"texto": "x" * 100, "length": 100, "recomendado": True}, {"texto": "y" * 85, "recomendado": False}]
    _anuncio(tmp_path, bom)
    assert travas.conferir("texto", tmp_path, ["A"], rodar=_ok) == {}
    _anuncio(tmp_path, [bom[0], {"texto": "y" * 101, "length": 99, "recomendado": False}])  # length mente
    assert "101" in travas.conferir("texto", tmp_path, ["A"], rodar=_ok)["A"]
    _anuncio(tmp_path, [dict(bom[0]), dict(bom[1], recomendado=True)])
    assert "recomendado" in travas.conferir("texto", tmp_path, ["A"], rodar=_ok)["A"]
    _anuncio(tmp_path, [bom[0]])
    assert "2 a 3" in travas.conferir("texto", tmp_path, ["A"], rodar=_ok)["A"]
    _anuncio(tmp_path, None)
    assert "titulos longos" in travas.conferir("texto", tmp_path, ["A"], rodar=_ok)["A"]


def test_titulos_longos_nao_cobram_anuncio_ja_aprovado(tmp_path):
    _anuncio(tmp_path, None, status_copy="aprovado")
    assert travas.conferir("texto", tmp_path, ["A"], rodar=_ok) == {}


def _lote_decisao(tmp_path, attrs, pendentes=(), decisoes=None):
    (tmp_path / "categorizacao").mkdir(exist_ok=True)
    (tmp_path / "categorizacao" / "campos-A.json").write_text(json.dumps(
        [{"id": "SHAPE"}, {"id": "DIAMETER"}]), encoding="utf-8")
    (tmp_path / "anuncios-entrada.json").write_text(json.dumps({"anuncios": [{"pai_sku": "A", "decisoes_almir":
        decisoes if decisoes is not None else [{"campo": "SHAPE", "valor": "Redonda", "sku": None},
                                               {"campo": "SALE_FORMAT", "valor": "Unidade", "sku": None}]}]}),
        encoding="utf-8")
    longos = [{"texto": "x" * 95, "recomendado": True}, {"texto": "y" * 95, "recomendado": False}]
    _anuncio(tmp_path, longos, attributes=attrs, campos_pendentes=list(pendentes))


def test_texto_segue_a_decisao_do_almir(tmp_path):
    _lote_decisao(tmp_path, {"SHAPE": "redonda "})  # maiuscula/espaco nao importam; SALE_FORMAT fora da categoria
    assert travas.conferir("texto", tmp_path, ["A"], rodar=_ok) == {}
    _lote_decisao(tmp_path, {"SHAPE": "Quadrada"})
    assert "Almir" in travas.conferir("texto", tmp_path, ["A"], rodar=_ok)["A"]
    _lote_decisao(tmp_path, {}, pendentes=["SHAPE"])
    assert "SHAPE" in travas.conferir("texto", tmp_path, ["A"], rodar=_ok)["A"]
    _lote_decisao(tmp_path, {"SHAPE": "Quadrada"}, decisoes=[])  # sem decisao, a esteira decide
    assert travas.conferir("texto", tmp_path, ["A"], rodar=_ok) == {}
