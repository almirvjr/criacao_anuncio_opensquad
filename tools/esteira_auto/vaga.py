"""Vaga = uma das rodadas da fila que podem trabalhar ao mesmo tempo neste PC (teto 2: RAM do PC, 04/11/2026).

Cada vaga tem a propria trava, os proprios lotes (andamento.json guarda a vaga) e o proprio navegador:
- Chrome da coleta de opinioes: porta e perfil proprios (dois Chromes no mesmo perfil = o 2o nao abre).
- Navegador do MCP playwright do `claude -p`: perfil proprio (o perfil persistente so aceita um navegador por vez).
A vaga 1 usa exatamente os nomes de antes (trava `.fila.trava`, porta 9336, `_perfil_opinioes`, `_browser_profile`):
codigo velho rodando e codigo novo na vaga 1 se excluem pela mesma trava, e nada muda com `--vagas 1`.

ATUAL e global do processo (cada rodada da fila e um processo proprio), como o L.ESPELHO.

Volta-atras: `--vagas 1` no rodar_fila.ps1 (ou ESTEIRA_VAGAS=1). Lote da vaga 2 que estava pela metade ainda e
terminado por uma rodada da vaga 2; pedido novo nela, nunca.
O banco nao amarra pedido por maquina (pegar_pedido usa `for update skip locked`): as duas vagas mandam o mesmo
nome de maquina, e anotar/gravar/terminar conferem so `pego_por` = esse nome."""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
MAXIMO = 2
PADRAO = 2
ATUAL = 1

_PORTAS = {1: 9336, 2: 9337}


def _sufixo(v):
    return "" if v == 1 else f"_{v}"


def nome_trava(v):
    return ".fila.trava" if v == 1 else f".fila.trava.{v}"


def porta_chrome(v=None):
    return _PORTAS[v or ATUAL]


def perfil_opinioes(v=None):
    return RAIZ / "_opensquad" / f"_perfil_opinioes{_sufixo(v or ATUAL)}"


def perfil_navegador_rel(v=None):
    """Perfil do navegador do MCP playwright, relativo a raiz (como no _opensquad/config/playwright.config.json)."""
    return f"_opensquad/_browser_profile{_sufixo(v or ATUAL)}"


def env_claude(v=None):
    """Ambiente do `claude -p` da vaga. Vaga 1 = None (herda tudo, igual antes: o perfil vem do arquivo de config).
    Outras vagas: o MCP playwright le PLAYWRIGHT_MCP_USER_DATA_DIR, que vale por cima do arquivo de config."""
    v = v or ATUAL
    if v == 1:
        return None
    env = dict(os.environ)
    env["PLAYWRIGHT_MCP_USER_DATA_DIR"] = str(RAIZ / perfil_navegador_rel(v))
    return env


def ler_vagas(argv, environ=os.environ):
    """`--vagas N` na linha de comando (ou ESTEIRA_VAGAS); padrao 2; entre 1 e MAXIMO. Volta-atras = `--vagas 1`."""
    valor = environ.get("ESTEIRA_VAGAS")
    if "--vagas" in argv:
        i = argv.index("--vagas")
        valor = argv[i + 1] if i + 1 < len(argv) else None
    try:
        n = int(valor) if valor not in (None, "") else PADRAO
    except ValueError:
        n = PADRAO
    return max(1, min(MAXIMO, n))
