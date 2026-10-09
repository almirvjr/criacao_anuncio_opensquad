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


def test_texto_roda_duas_travas(tmp_path):
    vistos = []
    def falso(cmd, **kw):
        vistos.append(os.path.basename(cmd[1]))
        return subprocess.CompletedProcess(cmd, 0, "", "")
    assert travas.conferir("texto", tmp_path, ["A"], rodar=falso) == {}
    assert vistos == ["validar_claims.py", "validar_ficha_seo.py"]


def test_capas_lista_quem_falta(tmp_path):
    falso = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "CAPAS INCOMPLETAS - 1:\n  - B: falta capa da cor 'Preto'", "")
    (tmp_path / "capas").mkdir(); (tmp_path / "capas" / "_busca.json").write_text("{}")
    r = travas.conferir("capas", tmp_path, ["A", "B"], rodar=falso)
    assert list(r) == ["B"] and "Preto" in r["B"]
