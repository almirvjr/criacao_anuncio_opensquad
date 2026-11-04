# tools/esteira_auto/tests/test_pendente_magalu.py — campo obrigatorio do Magalu nao para mais o produto (peca 2, 04/11/2026)
import json
import os
import sys
from datetime import datetime

import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from esteira_auto import lote as L, maestro as M, pedido as P, travas  # noqa: E402

T = lambda: datetime(2026, 11, 4, 10, 0, 0)
PAI = "BEL-4007-PAI"
SKUS = ["BEL-4007-0740-PE", "BEL-4007-2617-BR"]
# forma real do pedido 625 (travessa Bellagio, 04/11/2026), encurtada
TRAVESSA = {"id": "0026", "nome": "Travessa", "variacao": ["Cor"], "campos": [
    {"nome": "Marca", "obrigatorio": True}, {"nome": "Tamanho", "obrigatorio": True},
    {"nome": "Cor", "obrigatorio": False}, {"nome": "Material", "obrigatorio": False}]}


def _lote(tmp_path, campos_produto, por_variacao, decisoes=()):
    lote = tmp_path / "lote"
    (lote / "copywriting").mkdir(parents=True, exist_ok=True)
    (lote / "anuncios-entrada.json").write_text(json.dumps({"anuncios": [{
        "pai_sku": PAI, "variacoes": [{"sku": s} for s in SKUS],
        "magalu": {"candidatas": [TRAVESSA], "fixa": False, "decisoes": list(decisoes)}}]}), encoding="utf-8")
    an = {"status_copy": "pendente", "titulo_final": "Travessa", "por_variacao": por_variacao,
          "ficha_magalu": {"categoria_id": "0026", "campos": campos_produto}}
    (lote / "copywriting" / f"anuncio-{PAI}.yaml").write_text(yaml.safe_dump(an, allow_unicode=True), encoding="utf-8")
    (lote / "andamento.json").write_text(json.dumps({"pedido_id": 625, "feitas": [], "parados": {}}), encoding="utf-8")
    (lote / "andamento.txt").write_text("", encoding="utf-8")
    return lote


def _var(tamanho_pe="52x28,5cm", tamanho_br="43x21cm"):
    pv = {}
    for s, t, cor in ((SKUS[0], tamanho_pe, "Peixes"), (SKUS[1], tamanho_br, "Branco")):
        linhas = [{"nome": "Cor", "valor": cor}]
        if t:
            linhas.append({"nome": "Tamanho", "valor": t})
        pv[s] = {"attributes": {"COLOR": cor}, "magalu": linhas}
    return pv


BASE = [{"nome": "Marca", "valor": "Bellagio"}, {"nome": "Cor", "motivo": "muda por variacao: ver cada SKU"},
        {"nome": "Material", "valor": "Porcelana"}]


def _ficha(lote):
    return travas._ficha_magalu(lote, PAI, lote / "copywriting" / f"anuncio-{PAI}.yaml")


def test_pedido_625_tamanho_em_todas_as_variacoes_passa(tmp_path):
    """Reprova no codigo antigo ("Tamanho: obrigatorio no Magalu, nao pode ficar em branco")."""
    lote = _lote(tmp_path, BASE + [{"nome": "Tamanho", "motivo": "muda por variacao: ver cada SKU"}], _var())
    assert _ficha(lote) is None
    assert travas.pendentes_magalu(lote, PAI) == []
    r = P.resultado(lote, ler_precos=lambda l: {})["produtos"][0]
    # nada se perde no caminho para o hub: o valor de cada SKU segue em anuncio.por_variacao
    assert r["anuncio"]["por_variacao"][SKUS[0]]["magalu"][1] == {"nome": "Tamanho", "valor": "52x28,5cm"}
    tam = next(c for c in r["canais"]["magalu"]["campos"] if c["nome"] == "Tamanho")
    assert tam == {"nome": "Tamanho", "motivo": "muda por variacao: ver cada SKU"}


def test_obrigatorio_sem_valor_vira_pendencia_e_nao_reprova(tmp_path):
    """Reprova no codigo antigo (la o produto parava)."""
    lote = _lote(tmp_path, BASE + [{"nome": "Tamanho", "motivo": "nao achei a medida"}], _var(None, None))
    assert _ficha(lote) is None
    assert travas.pendentes_magalu(lote, PAI) == ["Tamanho"]
    tam = next(c for c in P.resultado(lote, ler_precos=lambda l: {})["produtos"][0]["canais"]["magalu"]["campos"]
               if c["nome"] == "Tamanho")
    assert tam["motivo"].startswith("PENDENTE: obrigatório no Magalu — preencher na ficha") and "valor" not in tam
    assert "nao achei a medida" in tam["motivo"]


def test_valor_so_em_parte_das_variacoes_e_pendencia(tmp_path):
    lote = _lote(tmp_path, BASE + [{"nome": "Tamanho", "motivo": "muda por variacao"}], _var("52x28,5cm", None))
    assert _ficha(lote) is None and travas.pendentes_magalu(lote, PAI) == ["Tamanho"]


def test_obrigatorio_que_nem_veio_entra_como_pendente_no_resultado(tmp_path):
    lote = _lote(tmp_path, BASE, _var(None, None))
    assert _ficha(lote) is None
    campos = P.resultado(lote, ler_precos=lambda l: {})["produtos"][0]["canais"]["magalu"]["campos"]
    assert {"nome": "Tamanho", "motivo": P.PENDENTE_MAGALU} in campos


def test_outras_checagens_continuam_reprovando(tmp_path):
    tam = [{"nome": "Tamanho", "valor": "43x21cm"}]
    assert "enchimento" in _ficha(_lote(tmp_path, [{"nome": "Marca", "valor": "N/A"}] + BASE[1:] + tam, _var()))
    assert "nao existe na categoria" in _ficha(_lote(tmp_path, BASE + tam + [{"nome": "Forma", "valor": "x"}], _var()))
    assert "nunca os dois" in _ficha(_lote(tmp_path, BASE + [{"nome": "Tamanho", "valor": "1", "motivo": "x"}], _var()))
    sem_resposta = [BASE[0], BASE[2]] + tam  # Cor (nao obrigatorio) sem resposta e sem valor em todas as variacoes
    assert "Cor: sem resposta" in _ficha(_lote(tmp_path, sem_resposta, {}))
    dec = [{"categoria_id": "0026", "campo": "Material", "valor": "Ceramica"}]
    assert "contra a decisao do Almir" in _ficha(_lote(tmp_path, BASE + tam, _var(), dec))


def test_caderno_avisa_a_pendencia_depois_da_revisao(tmp_path):
    lote = _lote(tmp_path, BASE, _var(None, None))
    d = L.ler(lote)
    d.update({"etapas": L.ETAPAS_PEDIDO, "feitas": ["entrada", "capas", "curadoria", "categoria", "pesquisa", "texto"]})
    L._salvar(lote, d)
    cod = M.rodar_lote(lote, chamar=lambda *a: (True, "ok"), conferir=lambda *a: {}, agora=T, avisar=lambda s: None,
                       entregar=lambda l: True)
    assert cod == 0
    txt = (lote / "andamento.txt").read_text(encoding="utf-8")
    assert f"pendente para o Almir: Tamanho do Magalu ({PAI})" in txt
    assert "PAROU" not in txt
