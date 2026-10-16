"""Ficha sem valor inventado e sem campo esquecido (Almir 16/10/2026)."""
import json
import os
import subprocess
import sys

import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from validar_ficha_nsa import campos_sem_destino, valores_inventados  # noqa: E402


def test_valor_inventado_e_pego():
    r = valores_inventados({"PATTERN_NAME": "N/A", "LENGTH": "-", "WIDTH": "nenhum", "COLOR": "Não informado",
                            "BRAND": "Brinox", "WITH_PEDESTAL": "Não", "X": "não se aplica"})
    assert sorted(c for c, _ in r) == ["COLOR", "LENGTH", "PATTERN_NAME", "WIDTH"]


def test_nao_e_resposta_valida_de_sim_ou_nao():
    assert valores_inventados({"WITH_PEDESTAL": "Não", "INCLUDES_LID": "Sim"}) == []


def test_campo_da_categoria_sem_destino():
    campos = [{"id": "BRAND"}, {"id": "COLOR"}, {"id": "TOTAL_HEIGHT"}, {"id": "PATTERN_NAME"}]
    attrs = {"BRAND": "Brinox", "PATTERN_NAME": "não se aplica"}
    assert campos_sem_destino(attrs, campos, pendentes=["TOTAL_HEIGHT"]) == ["COLOR"]


def test_cli(tmp_path):
    a = tmp_path / "anuncio.yaml"
    a.write_text(yaml.safe_dump({"attributes": {"BRAND": "X", "LENGTH": "N/A"}, "campos_pendentes": []}), encoding="utf-8")
    c = tmp_path / "campos.json"; c.write_text(json.dumps([{"id": "BRAND"}, {"id": "LENGTH"}, {"id": "COLOR"}]), encoding="utf-8")
    script = os.path.join(os.path.dirname(__file__), "..", "validar_ficha_nsa.py")
    r = subprocess.run([sys.executable, script, str(a), str(c)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 1 and "LENGTH" in r.stdout and "COLOR" in r.stdout
    a.write_text(yaml.safe_dump({"attributes": {"BRAND": "X", "LENGTH": "não se aplica"}, "campos_pendentes": ["COLOR"]}), encoding="utf-8")
    r = subprocess.run([sys.executable, script, str(a), str(c)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0
