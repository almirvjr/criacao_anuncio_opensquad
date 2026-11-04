"""Preco sugerido para a COPIA do ML (Almir, 04/11/2026).

A copia de uma cor nova (pedido modo copiar_ml) nasce no banco do hub em segundos, e o banco nao enxerga a planilha
"Precificacao - HUB" (fica no Drive deste PC). Sem isto a ficha da copia abria sem preco. A cada disparo da fila, a
esteira pergunta ao hub quais copias estao sem preco (esteira.copias_sem_preco), le a planilha UMA vez e grava a
proposta (esteira.gravar_precos_copia). O preco continua proposta: o Almir confere na aprovacao.

Nunca atrapalha a fila: qualquer problema = segue sem preco. Copia que a planilha nao cobre so e tentada de novo depois
de ESPERA_MIN (para nao copiar a planilha do Drive a cada 5 minutos)."""
import json
from datetime import timedelta
from pathlib import Path

from esteira_auto import precos as precos_mod

ESPERA_MIN = 60
MEMORIA = ".precos_copias.json"


def _ler_memoria(lotes):
    try:
        return json.loads((Path(lotes) / MEMORIA).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar_memoria(lotes, mem):
    try:
        (Path(lotes) / MEMORIA).write_text(json.dumps(mem), encoding="utf-8")
    except OSError:
        pass


def ler_planilha(lotes, origem=precos_mod.PLANILHA):
    copia = precos_mod.copiar(origem, Path(lotes) / ".precificacao-copias.xlsx")
    if copia is None:
        return {}
    try:
        return precos_mod.carregar(copia)
    except Exception:  # noqa: BLE001
        return {}


def completar(fila, lotes, agora, ler_tabela=None):
    """Grava a proposta de preco nas copias do ML sem preco. Devolve quantas gravou."""
    pendentes = fila.copias_sem_preco() or []
    mem = _ler_memoria(lotes)
    limite = (agora() - timedelta(minutes=ESPERA_MIN)).isoformat()
    da_vez = [p for p in pendentes if mem.get(str(p.get("pedido_id")), "") < limite]
    if not da_vez:
        return 0
    tabela = (ler_tabela or (lambda: ler_planilha(lotes)))()
    gravou = 0
    for p in da_vez:
        pid = p.get("pedido_id")
        mem[str(pid)] = agora().isoformat()
        proposta = precos_mod.do_produto(tabela, p.get("skus") or [])
        if proposta and fila.gravar_precos_copia(pid, proposta):
            gravou += 1
    _gravar_memoria(lotes, mem)
    return gravou
