# tools/esteira_auto/tests/test_vagas.py — duas rodadas da fila ao mesmo tempo (peca 3 do plano de 04/11/2026)
import json
import os
import subprocess
import sys
import textwrap
from datetime import datetime

import pytest

RAIZ_TOOLS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, RAIZ_TOOLS)
from esteira_auto import chamar_claude as CC, coletar_concorrentes as C, lote as L, maestro as M, vaga as V  # noqa: E402

T = lambda: datetime(2026, 11, 4, 10, 0, 0)
PEDIDO = {"pedido_id": 9, "produto": {"sku_pai": "BEL-4001-PAI"}}


class FilaFalsa:
    def __init__(self, pedido=None):
        self.maquina, self.pedido, self.pegou = "PC-TESTE", pedido, 0
        self.anotados, self.terminados = [], []

    def pegar(self):
        self.pegou += 1
        p, self.pedido = self.pedido, None
        return p

    def anotar(self, pid, etapa, texto, lote=None):
        self.anotados.append(texto)
        return True

    def gravar_resultado(self, pid, r):
        return True

    def terminar(self, pid, erro=None):
        self.terminados.append((pid, erro))
        return True


@pytest.fixture(autouse=True)
def _vaga_volta_para_1():
    yield
    V.ATUAL = 1


def _filho(codigo):
    """Outro processo de verdade (a trava e do Windows, por processo/arquivo aberto). Imprime uma linha e espera."""
    return subprocess.Popen([sys.executable, "-c", textwrap.dedent(f"""
        import sys, time
        sys.path.insert(0, {RAIZ_TOOLS!r})
        from esteira_auto import maestro as M
        {codigo}
        time.sleep(60)
    """)], stdout=subprocess.PIPE, text=True)


def _lote_pedido(lotes, nome, pid, vaga=None, concluido=False):
    p = lotes / nome
    p.mkdir(parents=True)
    d = {"pedido_id": pid, "sku_pai": "X", "etapas": L.ETAPAS_PEDIDO, "feitas": [], "parados": {}, "concluido": concluido}
    if vaga is not None:
        d["vaga"] = vaga
    (p / "andamento.json").write_text(json.dumps(d), encoding="utf-8")
    (p / "andamento.txt").write_text("", encoding="utf-8")
    return p


# ── travas por vaga ───────────────────────────────────────────────────────────────────────────────────────────
def test_dois_processos_pegam_vagas_diferentes_e_o_terceiro_e_recusado(tmp_path):
    lotes = tmp_path / "lotes"
    pega = f"v, t = M._escolher_vaga({str(lotes)!r}, 2); print(v, flush=True)"
    a = _filho(pega)
    try:
        assert a.stdout.readline().strip() == "1"
        b = _filho(pega)
        try:
            assert b.stdout.readline().strip() == "2"
            assert M._escolher_vaga(lotes, 2) == (None, None)  # terceiro: as duas ocupadas
        finally:
            b.kill(); b.wait()
        v, t = M._escolher_vaga(lotes, 2)  # a vaga 2 soltou sozinha quando o processo morreu
        assert v == 2
        t.close()
    finally:
        a.kill(); a.wait()


def test_codigo_velho_rodando_ocupa_a_vaga_1(tmp_path):
    """Troca do codigo com uma rodada velha viva: ela tranca `.fila.trava` (nome de antes) = vaga 1 ocupada.
    O codigo novo nunca roda a vaga 1 junto com ela (mesmo arquivo), e com --vagas 1 fica parado como antes."""
    lotes = tmp_path / "lotes"
    velho = _filho(f"""
        import msvcrt, pathlib
        p = pathlib.Path({str(lotes)!r}); p.mkdir(parents=True, exist_ok=True)
        f = open(p / ".fila.trava", "a+b"); f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        print("velho", flush=True)""") if sys.platform == "win32" else _filho(
        f"t = M._pegar_trava({str(lotes)!r}); print('velho', flush=True)")
    try:
        assert velho.stdout.readline().strip() == "velho"
        assert M._escolher_vaga(lotes, 1) == (None, None)
        v, t = M._escolher_vaga(lotes, 2)
        assert v == 2
        t.close()
    finally:
        velho.kill(); velho.wait()


def test_vaga_1_usa_o_nome_de_trava_de_antes():
    assert V.nome_trava(1) == ".fila.trava" and V.nome_trava(2) == ".fila.trava.2"


# ── cada vaga so retoma o proprio lote ──────────────────────────────────────────────────────────────────────
def test_lote_aberto_respeita_a_vaga(tmp_path):
    lotes = tmp_path / "lotes"
    velho = _lote_pedido(lotes, "2026-11-01-100000-pedido1", 1)            # sem vaga = vaga 1
    _lote_pedido(lotes, "2026-11-01-110000-pedido2", 2, vaga=1, concluido=True)
    dois = _lote_pedido(lotes, "2026-11-01-120000-pedido3", 3, vaga=2)
    assert L.lote_aberto(lotes, de_pedido=True, vaga=1) == velho
    assert L.lote_aberto(lotes, de_pedido=True, vaga=2) == dois
    assert L.lote_aberto(lotes, de_pedido=True) == velho  # sem vaga: como antes (o 1o aberto)


def test_criar_lote_do_pedido_grava_a_vaga(tmp_path):
    lote = L.criar_lote_do_pedido(PEDIDO, tmp_path, T(), vaga=2)
    assert L.ler(lote)["vaga"] == 2
    assert L.vaga_do_lote({}) == 1


def test_segunda_rodada_pega_pedido_novo_sem_mexer_no_lote_da_primeira(tmp_path):
    """Gate da peca 3 (reprova no codigo antigo: la a 2a rodada so dizia "Outra rodada..." e nao pegava nada)."""
    lotes = tmp_path / "lotes"
    da_1 = _lote_pedido(lotes, "2026-11-04-090000-pedido8", 8, vaga=1)
    trava_1 = M._pegar_trava(lotes)  # a rodada da vaga 1 esta trabalhando no pedido 8 (chamada igual a de antes)
    vistos = []

    def rodar(lote, entregar):
        vistos.append((lote, V.ATUAL, V.porta_chrome(), V.perfil_opinioes().name))
        return 0
    f = FilaFalsa(PEDIDO)
    try:
        assert M.main_fila(lotes, fila=f, rodar=rodar, agora=T) == 0  # padrao = 2 vagas
    finally:
        trava_1.close()
    assert f.pegou == 1 and len(vistos) == 1, "a 2a rodada nao pegou pedido (codigo de uma vaga so)"
    lote, vaga, porta, perfil = vistos[0]
    assert lote != da_1 and L.ler(lote)["pedido_id"] == 9 and L.ler(lote)["vaga"] == 2
    assert (vaga, porta, perfil) == (2, 9337, "_perfil_opinioes_2")
    assert f.anotados[0] == "esteira trabalhando nisto (PC-TESTE, vaga 2)"
    assert not L.ler(da_1)["feitas"] and V.ATUAL == 1


def test_com_vagas_1_e_como_antes(tmp_path):
    lotes = tmp_path / "lotes"
    trava_1 = M._pegar_trava(lotes, 1)
    f = FilaFalsa(PEDIDO)
    try:
        assert M.main_fila(lotes, fila=f, rodar=lambda *a, **k: 1 / 0, vagas=1) == 0
    finally:
        trava_1.close()
    assert f.pegou == 0
    vistos = []
    assert M.main_fila(lotes, fila=f, rodar=lambda lote, entregar: vistos.append(V.ATUAL) or 0, agora=T, vagas=1) == 0
    assert vistos == [1] and L.ler(L.lote_aberto(lotes, de_pedido=True, vaga=1))["vaga"] == 1


def test_vaga_desligada_so_termina_o_lote_que_ja_tinha(tmp_path):
    """--vagas 1 com um lote da vaga 2 pela metade: a vaga 2 termina ele, mas nunca pega pedido novo."""
    lotes = tmp_path / "lotes"
    da_2 = _lote_pedido(lotes, "2026-11-04-090000-pedido8", 8, vaga=2)
    trava_1 = M._pegar_trava(lotes, 1)
    f = FilaFalsa(PEDIDO)
    vistos = []
    try:
        assert M.main_fila(lotes, fila=f, rodar=lambda lote, entregar: vistos.append(lote) or 0, agora=T, vagas=1) == 0
        assert vistos == [da_2] and f.pegou == 0
        L.concluir(da_2, T())
        assert M.main_fila(lotes, fila=f, rodar=lambda *a, **k: 1 / 0, vagas=1) == 0  # acabou: vaga 2 fica fechada
        assert f.pegou == 0
    finally:
        trava_1.close()


# ── navegadores por vaga ──────────────────────────────────────────────────────────────────────────────────────
def test_porta_e_perfis_por_vaga():
    assert (V.porta_chrome(1), V.porta_chrome(2)) == (9336, 9337)
    assert V.perfil_opinioes(1).name == "_perfil_opinioes" and V.perfil_opinioes(2).name == "_perfil_opinioes_2"
    assert V.perfil_navegador_rel(1) == "_opensquad/_browser_profile"
    assert V.perfil_navegador_rel(2) == "_opensquad/_browser_profile_2"
    assert V.env_claude(1) is None
    env = V.env_claude(2)
    assert env["PLAYWRIGHT_MCP_USER_DATA_DIR"].replace("\\", "/").endswith("_opensquad/_browser_profile_2")
    assert "PATH" in env or "Path" in env  # herda o resto do ambiente


def test_chrome_da_coleta_abre_na_porta_e_perfil_da_vaga(monkeypatch, tmp_path):
    import subprocess as sp
    import time
    chamadas = []
    monkeypatch.setattr(sp, "Popen", lambda args, **k: chamadas.append(args))
    monkeypatch.setattr(time, "sleep", lambda s: None)
    monkeypatch.setattr(V, "RAIZ", tmp_path)
    for v in (1, 2):
        V.ATUAL = v
        C._abrir_chrome()
    assert "--remote-debugging-port=9336" in chamadas[0] and "--remote-debugging-port=9337" in chamadas[1]
    assert chamadas[0][3].endswith("_perfil_opinioes") and chamadas[1][3].endswith("_perfil_opinioes_2")


def test_claude_da_vaga_2_usa_outro_perfil_do_navegador(tmp_path):
    kws = []

    def falso(cmd, **kw):
        kws.append(kw)
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps({"is_error": False, "result": "ok"}), stderr="")
    V.ATUAL = 1
    CC.chamar("x", tmp_path, rodar=falso)
    V.ATUAL = 2
    CC.chamar("x", tmp_path, rodar=falso)
    assert "env" not in kws[0]  # vaga 1: igual antes
    assert kws[1]["env"]["PLAYWRIGHT_MCP_USER_DATA_DIR"].endswith("_browser_profile_2")
    assert "Read(_opensquad/_browser_profile_2/**)" in CC.NEGADAS


@pytest.mark.parametrize("argv,env,esperado", [
    ([], {}, 2), (["--fila", "--vagas", "1"], {}, 1), (["--vagas", "5"], {}, 2), (["--vagas", "0"], {}, 1),
    (["--vagas", "x"], {}, 2), ([], {"ESTEIRA_VAGAS": "1"}, 1), (["--vagas", "2"], {"ESTEIRA_VAGAS": "1"}, 2),
])
def test_ler_vagas(argv, env, esperado):
    assert V.ler_vagas(argv, env) == esperado
