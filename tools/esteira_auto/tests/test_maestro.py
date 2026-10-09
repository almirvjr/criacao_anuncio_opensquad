# tools/esteira_auto/tests/test_maestro.py
import json
import os
import re
import sys
from datetime import datetime

import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from esteira_auto import lote as L, maestro as M  # noqa: E402

T = lambda: datetime(2026, 10, 9, 14, 0, 0)


def _lote(tmp_path, pais=("A", "B")):
    lt = L.criar_lote(tmp_path / "p.xls", tmp_path / "lotes", T())
    def ler_planilha(planilha, lote):
        (lote / "anuncios-entrada.json").write_text(json.dumps({"anuncios": [{"pai_sku": p} for p in pais]}), encoding="utf-8")
        return []
    return lt, ler_planilha


def test_ordem_e_tela(tmp_path):
    lt, lp = _lote(tmp_path)
    etapas = []
    chamar = lambda instr, raiz, **kw: (etapas.append(re.search(r"step-\d+[a-z]?-[\w-]+\.md", instr).group(0)) or (True, "pronto"))
    r = M.rodar_lote(lt, chamar=chamar, conferir=lambda e, l, p: {}, ler_planilha=lp,
                     abrir_tela=lambda l: 0, agora=T, avisar=lambda *a: None)
    assert r == 0
    assert etapas[0] == "step-07-capas.md"
    assert etapas[1:] == ["step-02-curadoria-produtos.md", "step-03-categorizacao.md",
        "step-04-inteligencia-conversao.md", "step-05-copywriting.md", "step-08-revisao.md"]
    assert L.ler(lt)["concluido"]


def test_retoma_sem_refazer(tmp_path):
    lt, lp = _lote(tmp_path)
    lp(None, lt)  # a entrada ja tinha sido lida antes de a janela fechar
    for e in ("entrada", "capas", "curadoria"):
        L.marcar_feita(lt, e, T())
    chamadas = []
    chamar = lambda instr, raiz, **kw: (chamadas.append(1) or (True, "pronto"))
    M.rodar_lote(lt, chamar=chamar, conferir=lambda e, l, p: {}, ler_planilha=lambda *a: 1 / 0,
                 abrir_tela=lambda l: 0, agora=T, avisar=lambda *a: None)
    assert len(chamadas) == 4  # categoria, pesquisa, texto, revisao


def test_planilha_com_problema_para_cedo(tmp_path):
    lt, _ = _lote(tmp_path)
    r = M.rodar_lote(lt, chamar=lambda *a, **k: 1 / 0, conferir=None,
                     ler_planilha=lambda p, l: ["BRI-1: sem peso ou medida da caixa"],
                     abrir_tela=None, agora=T, avisar=lambda *a: None)
    assert r == 1 and "sem peso" in (lt / "andamento.txt").read_text(encoding="utf-8")


def test_reprovado_duas_vezes_para_so_aquele(tmp_path):
    lt, lp = _lote(tmp_path)
    vistos = []
    def conferir(etapa, lote, pais):
        vistos.append((etapa, tuple(pais)))
        return {"B": "texto inventou balde"} if etapa == "texto" else {}
    M.rodar_lote(lt, chamar=lambda instr, raiz, **kw: (True, "pronto"), conferir=conferir, ler_planilha=lp,
                 abrir_tela=lambda l: 0, agora=T, avisar=lambda *a: None)
    assert L.ler(lt)["parados"] == {"B": "texto inventou balde"}
    assert ("revisao", ("A",)) in vistos


def test_claude_falhou_nao_marca_etapa(tmp_path):
    lt, lp = _lote(tmp_path)
    r = M.rodar_lote(lt, chamar=lambda instr, raiz, **kw: (False, "passou do tempo"), conferir=lambda e, l, p: {},
                     ler_planilha=lp, abrir_tela=lambda l: 0, agora=T, avisar=lambda *a: None)
    assert r == 1 and L.proxima(lt) == "capas"


def test_devolvido_refaz_texto_e_volta_pra_tela(tmp_path):
    lt, lp = _lote(tmp_path)
    (lt / "copywriting").mkdir()
    (lt / "copywriting" / "anuncio-A.yaml").write_text(yaml.safe_dump({"pai_sku": "A", "status_copy": "devolvido"}), encoding="utf-8")
    telas = iter([3, 0])
    instr = []
    def chamar(i, raiz, **kw):
        instr.append(i)
        return True, "pronto"
    r = M.rodar_lote(lt, chamar=chamar, conferir=lambda e, l, p: {}, ler_planilha=lp,
                     abrir_tela=lambda l: next(telas), agora=T, avisar=lambda *a: None)
    assert r == 0
    refeitas = [i for i in instr[-2:]]
    assert "step-05" in refeitas[0] and "Produtos deste lote: A" in refeitas[0] and "step-08" in refeitas[1]


def test_tela_fechada_com_pendencia(tmp_path):
    lt, lp = _lote(tmp_path)
    r = M.rodar_lote(lt, chamar=lambda i, raiz, **kw: (True, "pronto"), conferir=lambda e, l, p: {},
                     ler_planilha=lp, abrir_tela=lambda l: 2, agora=T, avisar=lambda *a: None)
    assert r == 2 and not L.ler(lt)["concluido"]


def test_mover_para_feitos_sem_sobrescrever(tmp_path):
    a_criar = tmp_path / "A CRIAR"; (a_criar / "FEITOS").mkdir(parents=True)
    (a_criar / "FEITOS" / "p.xls").write_text("velho")
    pl = a_criar / "p.xls"; pl.write_text("novo")
    destino = M.mover_para_feitos(pl)
    assert destino.name == "p-2.xls" and (a_criar / "FEITOS" / "p.xls").read_text() == "velho"


def test_proxima_planilha_ignora_temporario_do_excel(tmp_path):
    (tmp_path / "~$p.xlsx").write_text("x"); (tmp_path / "b.xls").write_text("x")
    assert M.proxima_planilha(tmp_path).name == "b.xls"


def test_instrucao_usa_caminho_relativo_do_lote():
    # a permissao de gravar e "squads/ml-anuncios/output/lotes/**", relativa a raiz do projeto
    lt = M.RAIZ / "squads" / "ml-anuncios" / "output" / "lotes" / "2026-10-09-140000"
    txt = M.instrucao("curadoria", lt, ["A", "B"])
    assert "Pasta deste lote: squads/ml-anuncios/output/lotes/2026-10-09-140000" in txt
    assert "Produtos deste lote: A, B" in txt and "{" not in txt


def test_planilha_so_vai_pra_feitos_se_o_lote_terminou_bem(tmp_path):
    a_criar = tmp_path / "A CRIAR"; a_criar.mkdir()
    pl = a_criar / "p.xls"; pl.write_text("x")
    def para_tudo(lote):
        L.concluir(lote, T())  # ex.: todos os produtos pararam por falta de capa
        return 1
    assert M.main(a_criar=a_criar, lotes=tmp_path / "lotes", rodar=para_tudo) == 1
    assert pl.exists() and not (a_criar / "FEITOS").exists()


def test_main_termina_bem_e_guarda_a_planilha(tmp_path):
    a_criar = tmp_path / "A CRIAR"; a_criar.mkdir()
    (a_criar / "p.xls").write_text("x")
    def ok(lote):
        L.concluir(lote, T())
        return 0
    assert M.main(a_criar=a_criar, lotes=tmp_path / "lotes", rodar=ok) == 0
    assert (a_criar / "FEITOS" / "p.xls").exists()
