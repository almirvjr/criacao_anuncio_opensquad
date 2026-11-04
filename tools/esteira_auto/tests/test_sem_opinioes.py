# tools/esteira_auto/tests/test_sem_opinioes.py — sem as opinioes dos concorrentes a esteira segue e avisa
# (conselho do Almir, 04/11/2026; pedido 10, BRI-coza18-PAI, parou na 3a falha da coleta)
import json
import os
import subprocess
import sys
from datetime import datetime

import yaml

AQUI = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(AQUI, "..", "..")))
from esteira_auto import lote as L, pedido as P, travas  # noqa: E402

VAL = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "squads", "ml-anuncios", "pipeline", "validators"))
sys.path.insert(0, VAL)
from validar_brief import validate_brief  # noqa: E402

T = datetime(2026, 11, 4, 10, 0)
DECLARADO = ["sem opiniões de concorrentes: o texto sai sem a linguagem real do comprador"]


def brief_sem_opinioes(**extra):
    """Brief como a pesquisa grava no modo sem opinioes: nenhuma review, a falta declarada."""
    b = {"pai_sku": "BRI-coza18-PAI", "nome_base": "Pote", "confianca": "baixa", "sem_concorrente": True,
         "dados_produto": {"material": {"valor": "Vidro", "fonte": "olist"}},
         "diagnostico": {"dor_interna_mais_forte": {}, "only_factor": {"texto": "pote de vidro com tampa"},
                         "ansiedades": [], "linguagem_real_cliente": []},
         "escada_e_dai": [{"feature": "vidro", "logico": "nao pega cheiro", "emocional": "cozinha em ordem"}],
         "limitacoes": [{"texto": "tampa nao vai ao forno", "fonte": "olist"}],
         "limitacoes_pesquisa": list(DECLARADO)}
    b.update(extra)
    return b


def duros(erros):
    return [c for c, _ in erros if not c.startswith("WARN")]


# ── validador ──────────────────────────────────────────────────────────────────────────────────────────────────────

def test_modo_sem_opinioes_aceita_brief_sem_opinioes(tmp_path):
    assert duros(validate_brief(brief_sem_opinioes(), raw_dir=str(tmp_path / "_raw"), com_fotos=False,
                                sem_opinioes=True)) == []


def test_modo_sem_opinioes_reprova_sem_a_limitacao_declarada():
    b = brief_sem_opinioes()
    del b["limitacoes_pesquisa"]
    assert "SEM_OPINIOES_NAO_DECLARADO" in duros(validate_brief(b, com_fotos=False, sem_opinioes=True))
    # declarar em `limitacoes` (ponto fraco do produto, vai para a descricao) nao vale
    b["limitacoes"].append({"texto": "sem opiniões de concorrentes", "fonte": "esteira"})
    assert "SEM_OPINIOES_NAO_DECLARADO" in duros(validate_brief(b, com_fotos=False, sem_opinioes=True))


def test_modo_sem_opinioes_exige_confianca_baixa():
    assert "SEM_OPINIOES_CONFIANCA" in duros(validate_brief(brief_sem_opinioes(confianca="media"), com_fotos=False,
                                                            sem_opinioes=True))


def test_modo_sem_opinioes_nao_aceita_citacao_inventada(tmp_path):
    b = brief_sem_opinioes()
    b["diagnostico"]["ansiedades"] = [{"texto": "quebra", "evidencia": "chegou quebrado no primeiro dia"}]
    b["diagnostico"]["linguagem_real_cliente"] = ["perfeito para guardar a comida"]
    # sem nada de concorrente no _raw: citacao nao tem de onde vir
    assert duros(validate_brief(b, com_fotos=False, sem_opinioes=True)) == ["EVIDENCIA_SEM_FONTE"] * 2
    # com concorrente (so ficha e perguntas) no _raw: so vale o que existe nele
    raw = tmp_path / "_raw"
    raw.mkdir()
    (raw / "MLB1.json").write_text(json.dumps({"perguntas": [{"texto": "chegou quebrado no primeiro dia?"}]}),
                                   encoding="utf-8")
    assert duros(validate_brief(b, raw_dir=str(raw), com_fotos=False, sem_opinioes=True)) == ["EVIDENCIA_INVENTADA"]


def test_modo_normal_continua_exigindo_as_opinioes():
    """O mesmo brief sem opinioes, no modo normal, e reprovado como antes."""
    erros = duros(validate_brief(brief_sem_opinioes(), com_fotos=False))
    for c in ("DOR_INTERNA", "DOR_SEM_EVIDENCIA", "SEM_ANSIEDADES"):
        assert c in erros
    b = brief_sem_opinioes()
    b["diagnostico"]["ansiedades"] = [{"texto": "quebra"}]
    assert "ANSIEDADE_SEM_EVIDENCIA" in duros(validate_brief(b, com_fotos=False))


def test_linha_de_comando_com_a_opcao(tmp_path):
    f = tmp_path / "brief-X.yaml"
    f.write_text(yaml.safe_dump(brief_sem_opinioes(), allow_unicode=True), encoding="utf-8")
    roda = lambda *a: subprocess.run([sys.executable, os.path.join(VAL, "validar_brief.py"), str(f), "--sem-fotos", *a],
                                     capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert roda("--sem-opinioes").returncode == 0
    assert roda().returncode == 1


# ── trava da esteira e lote ────────────────────────────────────────────────────────────────────────────────────────

def _lote(tmp_path):
    lt = L.criar_lote(tmp_path / "p.xls", tmp_path / "lotes", T)
    return lt


def test_trava_passa_a_opcao_so_para_quem_seguiu_sem_opinioes(tmp_path):
    lt = _lote(tmp_path)
    L.marcar_sem_opinioes(lt, ["A"])
    vistos = {}
    def falso(cmd, **kw):
        vistos[os.path.basename(cmd[2])] = cmd[3:]
        return subprocess.CompletedProcess(cmd, 0, "ok", "")
    assert travas.conferir("pesquisa", lt, ["A", "B"], rodar=falso) == {}
    assert vistos["brief-A.yaml"] == ["--sem-fotos", "--sem-opinioes"]
    assert vistos["brief-B.yaml"] == ["--sem-fotos"]


def test_marcar_e_desmarcar_sem_opinioes(tmp_path):
    lt = _lote(tmp_path)
    assert L.marcar_sem_opinioes(lt, ["A", "B"]) == ["A", "B"]
    assert L.marcar_sem_opinioes(lt, ["A"]) == []  # ja estava: nao anota de novo
    assert L.marcar_sem_opinioes(lt, ["A"], sem=False) == ["A"]
    assert L.sem_opinioes(lt) == {"B"}


def test_coleta_sem_opinioes_nao_e_reaproveitada(tmp_path):
    pai = "BRI-coza18-PAI"
    velho = tmp_path / "velho"
    (velho / "categorizacao").mkdir(parents=True)
    (velho / "categorizacao" / "categorias.yaml").write_text("categorias: []", encoding="utf-8")
    (velho / "inteligencia" / "_coleta").mkdir(parents=True)
    (velho / "inteligencia" / "_coleta" / f"coleta-{pai}.json").write_text('{"concorrentes": []}', encoding="utf-8")
    (velho / "andamento.json").write_text(json.dumps({"sem_opinioes": [pai], "feitas": [], "parados": {}}),
                                          encoding="utf-8")
    novo = L.criar_lote_do_pedido({"pedido_id": 2, "produto": {"sku_pai": pai}}, tmp_path / "lotes", T)
    assert L.reaproveitar(novo, velho, T) == ["categoria"]
    assert not L.coleta_reaproveitada(novo)


# ── resultado para o hub ───────────────────────────────────────────────────────────────────────────────────────────

def _lote_pedido(tmp_path, sem):
    pai = "BRI-coza18-PAI"
    lote = tmp_path / "lote"
    for d in ("copywriting", "inteligencia"):
        (lote / d).mkdir(parents=True, exist_ok=True)
    (lote / "anuncios-entrada.json").write_text(json.dumps({"anuncios": [{"pai_sku": pai, "variacoes": []}]}),
                                                encoding="utf-8")
    (lote / "andamento.json").write_text(json.dumps({"pedido_id": 1, "feitas": [], "parados": {},
                                                     "sem_opinioes": [pai] if sem else []}), encoding="utf-8")
    (lote / "copywriting" / f"anuncio-{pai}.yaml").write_text("titulo_final: Pote", encoding="utf-8")
    b = brief_sem_opinioes()
    if not sem:
        b.pop("limitacoes_pesquisa")
    (lote / "inteligencia" / f"brief-{pai}.yaml").write_text(yaml.safe_dump(b, allow_unicode=True), encoding="utf-8")
    return lote


def test_resultado_leva_o_aviso_sem_opinioes_para_o_hub(tmp_path):
    b = P.resultado(_lote_pedido(tmp_path, True), ler_precos=lambda l: {})["produtos"][0]["brief"]
    assert b["pendencias"][0].startswith("sem opiniões de concorrentes")
    assert b["limitacoes_pesquisa"] == DECLARADO


def test_resultado_normal_sem_o_aviso(tmp_path):
    b = P.resultado(_lote_pedido(tmp_path, False), ler_precos=lambda l: {})["produtos"][0]["brief"]
    assert not any("sem opini" in x for x in b["pendencias"]) and b["limitacoes_pesquisa"] == []
