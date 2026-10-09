import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from esteira_auto import lote as L  # noqa: E402

T = datetime(2026, 10, 9, 14, 30, 0)


def test_lote_novo_comeca_na_entrada(tmp_path):
    pl = tmp_path / "boleira.xls"; pl.write_text("x")
    lt = L.criar_lote(pl, tmp_path / "lotes", T)
    assert lt.name == "2026-10-09-143000"
    assert L.ler(lt)["planilha"] == str(pl)
    assert L.proxima(lt) == "entrada"


def test_retoma_da_proxima(tmp_path):
    lt = L.criar_lote(tmp_path / "a.xls", tmp_path / "lotes", T)
    L.marcar_feita(lt, "entrada", T); L.marcar_feita(lt, "capas", T)
    assert L.proxima(lt) == "curadoria"
    L.marcar_feita(lt, "capas", T)  # repetir nao duplica
    assert L.ler(lt)["feitas"] == ["entrada", "capas"]


def test_caderno_em_portugues(tmp_path):
    lt = L.criar_lote(tmp_path / "a.xls", tmp_path / "lotes", T)
    L.parar_pai(lt, "VIE-1-PAI", "faltou capa do Preto", T)
    txt = (lt / "andamento.txt").read_text(encoding="utf-8")
    assert "VIE-1-PAI" in txt and "faltou capa do Preto" in txt
    assert L.ler(lt)["parados"] == {"VIE-1-PAI": "faltou capa do Preto"}


def test_lote_aberto_pula_concluido(tmp_path):
    raiz = tmp_path / "lotes"
    a = L.criar_lote(tmp_path / "a.xls", raiz, T)
    b = L.criar_lote(tmp_path / "b.xls", raiz, datetime(2026, 10, 9, 15, 0, 0))
    assert L.lote_aberto(raiz) == a
    L.concluir(a, T)
    assert L.lote_aberto(raiz) == b
    assert L.proxima(a) is None


def test_lote_aberto_sem_pasta(tmp_path):
    assert L.lote_aberto(tmp_path / "nada") is None
