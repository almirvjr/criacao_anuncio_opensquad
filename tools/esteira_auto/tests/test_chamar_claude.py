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


def test_python_so_dos_programas_que_ja_existem():
    # Bash(python *) deixaria o Claude escrever um .py proprio que le o .env e publica
    assert "Bash(python *)" not in cc.PERMITIDAS
    bash = [p for p in cc.PERMITIDAS if p.startswith("Bash(python")]
    assert bash and all(p.startswith(("Bash(python squads/ml-anuncios/pipeline/validators/",
                                      "Bash(python tools/tiny_to_esteira.py")) for p in bash)


def test_nao_cria_nem_mexe_em_programa():
    for regra in ("Write(**/*.py)", "Edit(**/*.py)", "Write(tools/**)", "Edit(tools/**)",
                  "Write(squads/ml-anuncios/pipeline/**)", "Edit(squads/ml-anuncios/pipeline/**)", "Bash(*..*)"):
        assert regra in cc.NEGADAS
