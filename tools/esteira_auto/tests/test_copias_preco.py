"""Preco sugerido nas copias do ML (copias_preco.py + gancho no main_fila)."""
from datetime import datetime, timedelta

from esteira_auto import copias_preco, maestro

AGORA = datetime(2026, 11, 4, 10, 0)
TABELA = {"ml": {"BEL-4001-0808-PE-KT06": 142.71}, "magalu": {"BEL-4001-0808-PE-KT06": 185.57}}


class FilaFalsa:
    def __init__(self, pendentes):
        self.pendentes = pendentes
        self.gravados = []

    def copias_sem_preco(self):
        return self.pendentes

    def gravar_precos_copia(self, pid, precos):
        self.gravados.append((pid, precos))
        return True


def test_grava_a_proposta_da_planilha(tmp_path):
    fila = FilaFalsa([{"pedido_id": 626, "skus": ["BEL-4001-0808-PE-KT06", "BEL-4001-0960-LI-KT06"]}])
    n = copias_preco.completar(fila, tmp_path, lambda: AGORA, ler_tabela=lambda: TABELA)
    assert n == 1
    assert fila.gravados == [(626, {"ml": {"BEL-4001-0808-PE-KT06": 142.71},
                                    "magalu": {"BEL-4001-0808-PE-KT06": 185.57}})]


def test_sem_pendente_nao_le_a_planilha(tmp_path):
    def nao_pode():
        raise AssertionError("leu a planilha sem precisar")
    assert copias_preco.completar(FilaFalsa([]), tmp_path, lambda: AGORA, ler_tabela=nao_pode) == 0


def test_planilha_sem_o_sku_nao_grava_e_espera_antes_de_tentar_de_novo(tmp_path):
    fila = FilaFalsa([{"pedido_id": 700, "skus": ["NAO-TEM"]}])
    leituras = []

    def ler():
        leituras.append(1)
        return TABELA
    assert copias_preco.completar(fila, tmp_path, lambda: AGORA, ler_tabela=ler) == 0
    assert fila.gravados == []
    # 5 minutos depois: nao copia a planilha de novo
    copias_preco.completar(fila, tmp_path, lambda: AGORA + timedelta(minutes=5), ler_tabela=ler)
    assert len(leituras) == 1
    # passada a espera, tenta de novo
    copias_preco.completar(fila, tmp_path, lambda: AGORA + timedelta(minutes=copias_preco.ESPERA_MIN + 1), ler_tabela=ler)
    assert len(leituras) == 2


def test_problema_no_preco_nao_derruba_a_fila(tmp_path, capsys):
    def quebra(*a):
        raise RuntimeError("drive fora")
    maestro._precos_das_copias(tmp_path, FilaFalsa([]), lambda: AGORA, completar=quebra)
    assert "Nao consegui completar o preco" in capsys.readouterr().out
