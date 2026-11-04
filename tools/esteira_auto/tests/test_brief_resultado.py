# tools/esteira_auto/tests/test_brief_resultado.py — o diagnostico do brief vai no resultado para o hub (peca 5, 04/11/2026)
import json
import os
import sys

import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from esteira_auto import pedido as P  # noqa: E402

PAI = "BEL-4007-PAI"
# forma real do brief (pedido 625, encurtada); a resposta da ansiedade ja veio com 3 nomes diferentes
BRIEF = {
    "pai_sku": PAI,
    "fontes": {"concorrentes_consultados": [{"mlb_id": "MLB1", "permalink": "https://www.mercadolivre.com.br/p/MLB1"}]},
    "diagnostico": {
        "dor_interna_mais_forte": {"texto": "Quero que a minha mesa fique bonita", "evidencias": ["opiniao X"]},
        "only_factor": {"texto": "Travessa em formato de peixe", "justificativa": "j"},
        "ansiedades": [
            {"texto": "Tamanho", "evidencia": "achei pequena", "como_combater": "Medida de cada cor"},
            {"texto": "Quebrar", "resposta_na_copy": "Embalagem cuidadosa"},
            {"texto": "Torta", "como_responder": "Conferida antes de enviar https://produto.mercadolivre.com.br/MLB-9"},
            {"texto": "Sem resposta"}],
        "linguagem_real_cliente": ["mesa posta", {"frase": "parece porcelana"}],
        "persona": {"texto": "Mulher que monta mesa posta", "pistas": "p"}},
    "escada_e_dai": [{"feature": "Formato de peixe", "logico": "decora", "emocional": "capricho"}],
    "limitacoes": [{"texto": "E melamina, nao porcelana", "fonte": "fotos"}],
    "pendencias": ["pode_ir", {"campo": "capacidade"}],
}


def _lote(tmp_path, brief=BRIEF, extra_anuncio=None):
    lote = tmp_path / "lote"
    for d in ("copywriting", "inteligencia"):
        (lote / d).mkdir(parents=True, exist_ok=True)
    (lote / "anuncios-entrada.json").write_text(json.dumps({"anuncios": [{"pai_sku": PAI, "variacoes": []}]}), encoding="utf-8")
    (lote / "andamento.json").write_text(json.dumps({"pedido_id": 1, "feitas": [], "parados": {}}), encoding="utf-8")
    (lote / "copywriting" / f"anuncio-{PAI}.yaml").write_text(
        yaml.safe_dump({"titulo_final": "Travessa", **(extra_anuncio or {})}, allow_unicode=True), encoding="utf-8")
    if brief is not None:
        (lote / "inteligencia" / f"brief-{PAI}.yaml").write_text(yaml.safe_dump(brief, allow_unicode=True), encoding="utf-8")
    return lote


def test_resultado_leva_o_diagnostico_do_brief_sem_endereco(tmp_path):
    """Reprova no codigo antigo (la o resultado nao tinha `brief`)."""
    r = P.resultado(_lote(tmp_path), ler_precos=lambda l: {})["produtos"][0]
    b = r["brief"]
    assert b["diagnostico"]["dor_interna_mais_forte"] == "Quero que a minha mesa fique bonita"
    assert b["diagnostico"]["only_factor"] == "Travessa em formato de peixe"
    assert b["diagnostico"]["persona"] == "Mulher que monta mesa posta"
    assert b["diagnostico"]["ansiedades"] == [
        {"texto": "Tamanho", "resposta_na_copy": "Medida de cada cor"},
        {"texto": "Quebrar", "resposta_na_copy": "Embalagem cuidadosa"},
        {"texto": "Torta", "resposta_na_copy": "Conferida antes de enviar"},
        {"texto": "Sem resposta", "resposta_na_copy": None}]
    assert b["diagnostico"]["linguagem_real_cliente"] == ["mesa posta", "parece porcelana"]
    assert b["escada_e_dai"] == [{"feature": "Formato de peixe", "logico": "decora", "emocional": "capricho"}]
    assert b["limitacoes"] == ["E melamina, nao porcelana"] and b["pendencias"] == ["pode_ir", "capacidade"]
    texto = json.dumps(b, ensure_ascii=False)
    assert "http" not in texto and "mercadolivre" not in texto and "achei pequena" not in texto  # sem evidencia


def test_sem_brief_sem_a_chave(tmp_path):
    assert "brief" not in P.resultado(_lote(tmp_path, brief=None), ler_precos=lambda l: {})["produtos"][0]


def test_brief_sai_se_o_resultado_passaria_do_limite(tmp_path, monkeypatch):
    lote = _lote(tmp_path)
    tamanho = len(json.dumps(P.resultado(lote, ler_precos=lambda l: {}), ensure_ascii=False).encode("utf-8"))
    monkeypatch.setattr(P, "LIMITE_RESULTADO", tamanho - 1)
    assert "brief" not in P.resultado(lote, ler_precos=lambda l: {})["produtos"][0]
