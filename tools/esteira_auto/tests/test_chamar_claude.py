import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from esteira_auto import chamar_claude as cc  # noqa: E402


def test_comando_fecha_publicacao():
    cmd = cc.montar_comando("faz a etapa")
    assert cmd[:3] == ["claude", "-p", "faz a etapa"]
    negadas = cmd[cmd.index("--disallowedTools") + 1]
    for proibido in ("disparar_publicacao", "completar_anuncio", ".env", "python -c", "curl", "mcp__n8n"):
        assert proibido in negadas
    assert "--output-format" in cmd and cmd[cmd.index("--output-format") + 1] == "json"


def test_chamar_ok(tmp_path):
    def falso(cmd, **kw):
        assert kw["cwd"] == str(tmp_path)
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps({"is_error": False, "result": "feito"}), stderr="")
    assert cc.chamar("x", tmp_path, rodar=falso) == (True, "feito")


def test_chamar_erro_nao_vaza_excecao(tmp_path):
    def estoura(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, 1)
    ok, txt = cc.chamar("x", tmp_path, rodar=estoura)
    assert not ok and "tempo" in txt


def test_chamar_saida_nao_json(tmp_path):
    falso = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, stdout="lixo", stderr="segredo123")
    ok, txt = cc.chamar("x", tmp_path, rodar=falso)
    assert not ok and "segredo123" not in txt


def test_python_so_pelo_nome_exato_dos_validadores():
    # tiny_to_esteira e capas.py gravam onde o argumento mandar: quem roda e o maestro, nao o Claude
    bash = [p for p in cc.PERMITIDAS if p.startswith("Bash(")]
    assert sorted(bash) == sorted(f"Bash(python {s} *)" for s in cc.PROGRAMAS)
    assert all(s.startswith("squads/ml-anuncios/pipeline/validators/validar_") for s in cc.PROGRAMAS)


def test_grava_so_na_pasta_dos_lotes():
    assert "Write" not in cc.PERMITIDAS and "Edit" not in cc.PERMITIDAS
    escrita = [p for p in cc.PERMITIDAS if p.startswith(("Write(", "Edit("))]
    assert escrita == ["Edit(squads/ml-anuncios/output/lotes/**)", "Write(squads/ml-anuncios/output/lotes/**)"]


def test_leitura_sem_liberacao_geral_e_sem_arquivo_de_chave():
    # sem "Read" geral o dontAsk so deixa ler dentro do projeto (sondado 09/10)
    assert not {"Read", "Glob", "Grep"} & set(cc.PERMITIDAS)
    for r in ("Read(**/.mcp.json)", "Read(**/.env*)", "Read(_opensquad/_browser_profile/**)",
              "Read(.playwright-mcp/**)", "Read(.git/**)", "Read(.claude/**)"):
        assert r in cc.NEGADAS


def test_internet_so_do_ml_e_sem_mcp_do_ml():
    web = [p for p in cc.PERMITIDAS if p.startswith("WebFetch")]
    assert web and all("mercadoli" in p for p in web)
    assert "mcp__mercadolibre" not in cc.PERMITIDAS and "mcp__mercadolibre" in cc.NEGADAS
    for f in ("browser_type", "browser_fill_form", "browser_file_upload"):
        assert f"mcp__playwright__{f}" in cc.NEGADAS


def test_env_bloqueado_em_qualquer_caixa():
    for v in (".env", ".ENV", ".Env", ".eNv"):
        assert f"Read(**/{v})" in cc.NEGADAS


def test_navegador_sem_rodar_codigo():
    assert "mcp__playwright__browser_evaluate" in cc.NEGADAS
    assert "mcp__playwright__browser_run_code" in cc.NEGADAS


def test_modo_nega_o_que_nao_esta_liberado():
    # o settings.json do hub usa defaultMode "auto" (classificador aprova sozinho) e o
    # claude -p herdava isso, ignorando a lista de liberados (sondado 09/10/2026)
    cmd = cc.montar_comando("x")
    assert cmd[cmd.index("--permission-mode") + 1] == "dontAsk"
