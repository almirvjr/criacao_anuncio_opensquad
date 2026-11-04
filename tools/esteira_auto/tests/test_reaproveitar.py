# tools/esteira_auto/tests/test_reaproveitar.py — conserto nao refaz tudo (peca 4, 04/11/2026)
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from esteira_auto import lote as L, maestro as M  # noqa: E402

AGORA = datetime(2026, 11, 4, 10, 0, 0)
T = lambda: AGORA
PAI = "BEL-4007-PAI"
SKUS = ["BEL-4007-0740-PE", "BEL-4007-2617-BR"]


def _pedido(pid, skus=SKUS, recado=None):
    return {"pedido_id": pid, "recado": recado, "produto": {"sku_pai": PAI},
            "variacoes": [{"sku": s} for s in skus]}


def _lote_velho(lotes, nome="2026-11-03-205045-pedido624", criado="2026-11-03 20:50", feitas=("entrada", "capas",
                "curadoria", "categoria", "pesquisa"), skus=SKUS, coleta=True, pai=PAI):
    p = lotes / nome
    (p / "categorizacao").mkdir(parents=True)
    (p / "pedido.json").write_text(json.dumps(dict(_pedido(624, skus), produto={"sku_pai": pai})), encoding="utf-8")
    (p / "andamento.json").write_text(json.dumps({"pedido_id": 624, "sku_pai": pai, "criado_em": criado,
                                                  "feitas": list(feitas), "parados": {}, "concluido": True}), encoding="utf-8")
    (p / "andamento.txt").write_text("", encoding="utf-8")
    (p / "categorizacao" / "categorias.yaml").write_text(f"categorias:\n- pai_sku: {pai}\n  category_id: MLB123\n", encoding="utf-8")
    (p / "categorizacao" / f"campos-{pai}.json").write_text("[]", encoding="utf-8")
    if coleta:
        (p / "inteligencia" / "_coleta").mkdir(parents=True)
        (p / "inteligencia" / "_raw").mkdir(parents=True)
        (p / "inteligencia" / "_coleta" / f"coleta-{pai}.json").write_text(
            json.dumps({"concorrentes": [{"id": "MLB1"}, {"id": "MLBU2"}]}), encoding="utf-8")
        for i in ("MLB1", "MLBU2", "MLB999"):
            (p / "inteligencia" / "_raw" / f"{i}.json").write_text("{}", encoding="utf-8")
        (p / "inteligencia" / f"brief-{pai}.yaml").write_text("x: 1\n", encoding="utf-8")  # o brief NAO vem
    return p


class FilaFalsa:
    def __init__(self, pedido):
        self.maquina, self.pedido, self.anotados = "PC-TESTE", pedido, []

    def pegar(self):
        p, self.pedido = self.pedido, None
        return p

    def anotar(self, pid, etapa, texto, lote=None):
        self.anotados.append(texto)
        return True

    def terminar(self, pid, erro=None):
        return True


def _rodar(lotes, pedido, **kw):
    vistos = []
    f = FilaFalsa(pedido)
    M.main_fila(lotes, fila=f, rodar=lambda lote, entregar: vistos.append(lote) or 0, agora=T, **kw)
    return vistos[0], f


def test_pedido_de_novo_reaproveita_categoria_e_coleta(tmp_path):
    """Reprova no codigo antigo (la o lote novo comecava do zero)."""
    lotes = tmp_path / "lotes"
    velho = _lote_velho(lotes)
    lote, f = _rodar(lotes, _pedido(625))
    d = L.ler(lote)
    assert "categoria" in d["feitas"] and d["reaproveitado"] == {"de": velho.name, "etapas": ["categoria", "coleta"]}
    assert (lote / "categorizacao" / "categorias.yaml").is_file() and (lote / "categorizacao" / f"campos-{PAI}.json").is_file()
    assert (lote / "inteligencia" / "_coleta" / f"coleta-{PAI}.json").is_file()
    assert sorted(x.name for x in (lote / "inteligencia" / "_raw").iterdir()) == ["MLB1.json", "MLBU2.json"]
    assert not (lote / "inteligencia" / f"brief-{PAI}.yaml").exists()  # o brief e refeito
    linha = f"reaproveitei do lote {velho.name}: categoria, coleta de concorrentes"
    assert linha in (lote / "andamento.txt").read_text(encoding="utf-8") and linha in f.anotados  # vai ao hub tambem
    # entrada, capas, curadoria, pesquisa (brief), texto e revisao continuam por fazer
    assert L.proxima(lote) == "entrada"
    assert [e for e in L.ETAPAS_PEDIDO if e not in d["feitas"]] == ["entrada", "capas", "curadoria", "pesquisa",
                                                                       "texto", "revisao", "entregar"]


def test_pesquisa_pula_so_a_coleta(tmp_path):
    lotes = tmp_path / "lotes"
    _lote_velho(lotes)
    lote, _ = _rodar(lotes, _pedido(625))
    (lote / "anuncios-entrada.json").write_text(json.dumps({"anuncios": [{"pai_sku": PAI}]}), encoding="utf-8")
    d = L.ler(lote)
    d["feitas"] += ["entrada", "capas", "curadoria"]
    L._salvar(lote, d)
    chamadas = []

    def chamar(instr, raiz):
        chamadas.append(instr)
        return True, "ok"

    def coletar(lote):
        raise AssertionError("a coleta foi reaproveitada: nao pode rodar de novo")
    cod = M.rodar_lote(lote, chamar=chamar, conferir=lambda *a: {}, agora=T, avisar=lambda s: None, coletar=coletar,
                       entregar=lambda l: True, buscar_campos=lambda l: [], baixar_fotos=lambda l: [])
    assert cod == 0 and len(chamadas) == 3  # pesquisa (brief), texto, revisao: a cabeca roda de novo


def test_coleta_roda_quando_o_lote_velho_nao_tem(tmp_path):
    lotes = tmp_path / "lotes"
    _lote_velho(lotes, coleta=False)
    lote, _ = _rodar(lotes, _pedido(625))
    assert L.ler(lote)["reaproveitado"]["etapas"] == ["categoria"] and not L.coleta_reaproveitada(lote)


def test_quando_nao_reaproveita(tmp_path):
    casos = {
        "sku_novo": dict(pedido=_pedido(625, SKUS + ["BEL-4007-9999-AZ"])),
        "velho_demais": dict(velho=dict(criado="2026-10-27 09:59")),
        "sem_categoria": dict(velho=dict(feitas=("entrada", "capas", "curadoria"))),
        "outro_pai": dict(velho=dict(pai="BEL-4006-PAI")),
        "recado_refazer_do_zero": dict(pedido=_pedido(625, recado="categoria errada")),
        "desligado": dict(kw=dict(reaproveitar=False)),
    }
    for nome, c in casos.items():
        lotes = tmp_path / nome / "lotes"
        _lote_velho(lotes, **c.get("velho", {}))
        lote, _ = _rodar(lotes, c.get("pedido", _pedido(625)), **c.get("kw", {}))
        d = L.ler(lote)
        assert "reaproveitado" not in d and "categoria" not in d["feitas"], nome


def test_menos_skus_que_o_velho_reaproveita(tmp_path):
    lotes = tmp_path / "lotes"
    _lote_velho(lotes)
    lote, _ = _rodar(lotes, _pedido(625, SKUS[:1]))
    assert "reaproveitado" in L.ler(lote)


def test_pega_o_mais_recente(tmp_path):
    lotes = tmp_path / "lotes"
    _lote_velho(lotes, nome="2026-11-01-100000-pedido500", criado="2026-11-01 10:00")
    novo = _lote_velho(lotes, nome="2026-11-03-205045-pedido624", criado="2026-11-03 20:50")
    assert L.achar_reaproveitavel(lotes, _pedido(625), AGORA) == novo
