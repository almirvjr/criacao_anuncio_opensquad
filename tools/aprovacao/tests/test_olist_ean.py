# tools/aprovacao/tests/test_olist_ean.py
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import olist_ean as oe  # noqa: E402


def _entrada(tmp_path, ean=None):
    (tmp_path / "anuncios-entrada.json").write_text(json.dumps({"anuncios": [{"pai_sku": "P", "variacoes": [
        {"sku": "BRI-coza34-40652_3009", "ean": ean}]}]}), encoding="utf-8")


def test_grava_codigo_novo(tmp_path):
    _entrada(tmp_path)
    r = oe.reler_ean(tmp_path, "BRI-coza34-40652_3009", buscar=lambda sku: ("7898755999999", None))
    assert r == {"ok": True, "ean": "7898755999999", "motivo": None}
    e = json.loads((tmp_path / "anuncios-entrada.json").read_text(encoding="utf-8"))
    assert e["anuncios"][0]["variacoes"][0]["ean"] == "7898755999999"


def test_olist_ainda_sem_codigo(tmp_path):
    _entrada(tmp_path)
    r = oe.reler_ean(tmp_path, "BRI-coza34-40652_3009", buscar=lambda sku: (None, None))
    assert not r["ok"] and "ainda nao tem" in r["motivo"]


def test_falha_de_acesso(tmp_path):
    _entrada(tmp_path)
    r = oe.reler_ean(tmp_path, "BRI-coza34-40652_3009", buscar=lambda sku: (None, "sem acesso ao Olist"))
    assert not r["ok"] and r["motivo"] == "sem acesso ao Olist"


def test_sku_fora_do_lote(tmp_path):
    _entrada(tmp_path)
    r = oe.reler_ean(tmp_path, "OUTRO", buscar=lambda sku: ("1", None))
    assert not r["ok"] and "nao e deste lote" in r["motivo"]
