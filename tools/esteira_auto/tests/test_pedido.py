# tools/esteira_auto/tests/test_pedido.py — lote que vem da fila do hub (Fase 1 etapa 3 do hub)
import json
import os
import re
import sys
from datetime import datetime

import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from esteira_auto import fila as F, lote as L, maestro as M, pedido as P  # noqa: E402

T = lambda: datetime(2026, 10, 21, 20, 0, 0)

# Forma real da leitura que o hub guarda (hub-ler-pedido, BRI-coza18-PAI em 21/10/2026), encurtada.
DIM = {"altura": 5, "largura": 27, "comprimento": 27}
def _ficha(sku, gtin=None, **extra):
    f = {"id": 1, "sku": sku, "descricao": "PRATO REFEIÇÃO COZY", "descricao_complementar": None, "situacao": "ativo",
         "gtin": gtin, "marca": None, "ncm": "3924.10.00", "garantia": "30 Dias", "fornecedor": "BRINOX METALURGICA S A",
         "fotos": [f"https://x/{sku}.jpg"], "peso_bruto_kg": 0.8, "dim_embalagem_cm": dict(DIM)}
    f.update(extra)
    return f

PEDIDO = {"pedido_id": 7, "canais": ["ml", "magalu"], "observacao": None,
          "produto": {"id": 694, "sku_pai": "BRI-coza18-PAI", "nome": "PRATO REFEIÇÃO COZY", "com_variacao": True},
          "variacoes": [], "olist": {"pai": _ficha("BRI-coza18-PAI"), "avisos": [], "variacoes": [
              _ficha("BRI-coza18-10570_0007-BR", "7896553918021", grade={"cor": "Branco"}),
              _ficha("BRI-coza18-10570_0008-PT", "7896553928006", grade={"cor": "Preto"})]}}


def test_registros_viram_o_mesmo_formato_da_planilha_sem_preco():
    r = P.registros(PEDIDO)
    assert [x["sku"] for x in r] == ["BRI-coza18-PAI", "BRI-coza18-10570_0007-BR", "BRI-coza18-10570_0008-PT"]
    assert [x["cod_pai"] for x in r] == [None, "BRI-coza18-PAI", "BRI-coza18-PAI"]
    assert [x["variacoes_raw"] for x in r] == [None, "Cor:Branco", "Cor:Preto"]
    assert all(x["preco_venda"] is None and x["preco_custo"] is None for x in r)


def test_produto_simples_e_uma_linha_so():
    simples = dict(PEDIDO, produto=dict(PEDIDO["produto"], com_variacao=False),
                   olist={"pai": _ficha("VIE-1"), "variacoes": [_ficha("VIE-1", "789")], "avisos": []})
    r = P.registros(simples)
    assert len(r) == 1 and r[0]["cod_pai"] is None and r[0]["ean"] == "789"


def test_sem_leitura_para():
    try:
        P.registros(dict(PEDIDO, olist=None))
        assert False
    except ValueError:
        pass


def _lote_pedido(tmp_path, pedido=PEDIDO):
    return L.criar_lote_do_pedido(pedido, tmp_path / "lotes", T())


def test_montar_entrada_usa_cubagem_e_normalizer(tmp_path):
    lt = _lote_pedido(tmp_path)
    cub = {"BRI-COZA18-10570-0007-BR": {"peso_bruto": 1.1, "largura": 30, "altura": 6, "comprimento": 30}}
    assert P.montar_entrada(lt, ler_cubagem=lambda c: cub) == []
    e = json.loads((lt / "anuncios-entrada.json").read_text(encoding="utf-8"))
    a = e["anuncios"][0]
    assert e["total_anuncios"] == 1 and a["modo"] == "variacoes" and a["pai_sku"] == "BRI-coza18-PAI"
    assert [v["cor"] for v in a["variacoes"]] == ["Branco", "Preto"]
    assert a["variacoes"][0]["peso_bruto_kg"] == 1.1 and a["peso_bruto_kg"] == 1.1  # cubagem manda
    assert a["preco_provisorio"] is False and e["origem"] == "pedido 7 do hub"


def test_decisoes_do_almir_entram_no_anuncio(tmp_path):
    ped = dict(PEDIDO, decisoes=[{"atributo": "shape", "atributo_ml": "SHAPE", "valor": "Redonda", "sku": None},
                                 {"atributo": "cor_x", "atributo_ml": None, "valor": "Azul",
                                  "sku": "BRI-coza18-10570_0007-BR"}])
    lt = _lote_pedido(tmp_path, ped)
    P.montar_entrada(lt, ler_cubagem=lambda c: {})
    a = json.loads((lt / "anuncios-entrada.json").read_text(encoding="utf-8"))["anuncios"][0]
    assert a["decisoes_almir"] == [{"campo": "SHAPE", "valor": "Redonda", "sku": None},
                                   {"campo": "cor_x", "valor": "Azul", "sku": "BRI-coza18-10570_0007-BR"}]
    lt2 = _lote_pedido(tmp_path / "b")  # pedido antigo, sem a chave: lista vazia
    P.montar_entrada(lt2, ler_cubagem=lambda c: {})
    a2 = json.loads((lt2 / "anuncios-entrada.json").read_text(encoding="utf-8"))["anuncios"][0]
    assert a2["decisoes_almir"] == [] and a2["recado_almir"] == ""


def test_recado_do_almir_entra_no_anuncio(tmp_path):
    lt = _lote_pedido(tmp_path, dict(PEDIDO, recado="  é prato de louça, não descartável \n"))
    P.montar_entrada(lt, ler_cubagem=lambda c: {})
    a = json.loads((lt / "anuncios-entrada.json").read_text(encoding="utf-8"))["anuncios"][0]
    assert a["recado_almir"] == "é prato de louça, não descartável"


def test_montar_entrada_para_sem_medida(tmp_path):
    sem = json.loads(json.dumps(PEDIDO))
    for f in [sem["olist"]["pai"]] + sem["olist"]["variacoes"]:
        f["peso_bruto_kg"], f["dim_embalagem_cm"] = None, {}
    lt = _lote_pedido(tmp_path, sem)
    probs = P.montar_entrada(lt, ler_cubagem=lambda c: {})
    assert probs and "sem peso ou medida" in probs[0]


def test_resultado_junta_o_que_a_esteira_fez_sem_preco(tmp_path):
    lt = _lote_pedido(tmp_path)
    P.montar_entrada(lt, ler_cubagem=lambda c: {})
    for pasta, nome, dado in [("copywriting", "anuncio-BRI-coza18-PAI.yaml", {"titulo_final": "Prato", "preco": 99}),
                              ("revisao", "parecer-BRI-coza18-PAI.yaml", {"ok": True}),
                              ("capas", "capas-BRI-coza18-PAI.yaml", {"picture_ids_por_variacao": []}),
                              ("categorizacao", "categorias.yaml", {"categorias": [{"pai_sku": "BRI-coza18-PAI", "category_id": "MLB1"}]})]:
        (lt / pasta).mkdir(exist_ok=True)
        (lt / pasta / nome).write_text(yaml.safe_dump(dado), encoding="utf-8")
    tabela = {"ml": {"BRI-COZA18-10570-0008-PT": 49.9}, "magalu": {"OUTRO": 10}}
    r = P.resultado(lt, ler_precos=lambda lote: tabela)
    p = r["produtos"][0]
    assert p["anuncio"] == {"titulo_final": "Prato"} and p["categoria"]["category_id"] == "MLB1"
    assert p["parecer"] == {"ok": True} and r["lote"] == lt.name
    # preco do Olist nunca; preco da planilha do hub so do SKU que ela tem (Magalu sem nenhum = fora)
    assert p["precos"] == {"ml": {"BRI-coza18-10570_0008-PT": 49.9}}
    # a publicacao do hub precisa da caixa (cubagem) e do codigo de barras de cada cor
    assert set(p["pacote"]) == {"peso_bruto_kg", "dim_embalagem_cm"}
    assert [v["sku"] for v in p["variacoes"]] == ["BRI-coza18-10570_0007-BR", "BRI-coza18-10570_0008-PT"]
    assert p["variacoes"][1]["ean"] == "7896553928006"


def test_resultado_sem_planilha_segue_sem_preco(tmp_path):
    lt = _lote_pedido(tmp_path)
    P.montar_entrada(lt, ler_cubagem=lambda c: {})
    r = P.resultado(lt, ler_precos=lambda lote: {})
    assert r["produtos"][0]["precos"] == {}


def test_lote_de_pedido_e_de_planilha_nao_se_misturam(tmp_path):
    lp = L.criar_lote(tmp_path / "p.xls", tmp_path / "lotes", T())
    lt = L.criar_lote_do_pedido(PEDIDO, tmp_path / "lotes", datetime(2026, 10, 21, 20, 0, 1))
    assert L.lote_aberto(tmp_path / "lotes") == lp
    assert L.lote_aberto(tmp_path / "lotes", de_pedido=True) == lt
    assert L.ler(lt)["etapas"][-1] == "entregar" and "tela" not in L.ler(lt)["etapas"]


def test_lote_de_pedido_roda_sem_tela_e_entrega(tmp_path):
    lt = _lote_pedido(tmp_path)
    (lt / "anuncios-entrada.json").write_text(json.dumps({"anuncios": [{"pai_sku": "BRI-coza18-PAI"}]}), encoding="utf-8")
    entregues = []
    r = M.rodar_lote(lt, chamar=lambda *a, **k: (True, "pronto"), conferir=lambda e, l, p: {},
                     ler_pedido=lambda l: [], abrir_tela=lambda l: 1 / 0, agora=T, avisar=lambda *a: None,
                     buscar_campos=lambda l: [], coletar=lambda l: [], entregar=lambda l: entregues.append(l) or True)
    assert r == 0 and entregues == [lt] and L.ler(lt)["concluido"]


class FilaFalsa:
    def __init__(self, pedido=None, anotar_ok=True, terminar_falha=0):
        self.maquina, self.pedido, self.anotar_ok, self.terminar_falha = "PC-TESTE", pedido, anotar_ok, terminar_falha
        self.anotados, self.gravados, self.terminados = [], [], []

    def pegar(self):
        p, self.pedido = self.pedido, None
        return p

    def anotar(self, pid, etapa, texto, lote=None):
        self.anotados.append(texto)
        return self.anotar_ok

    def gravar_resultado(self, pid, r):
        self.gravados.append(r)
        return True

    def terminar(self, pid, erro=None):
        if self.terminar_falha:
            self.terminar_falha -= 1
            raise F.SemAcesso("fora")
        self.terminados.append((pid, erro))
        return True


def test_fila_vazia_nao_faz_nada(tmp_path):
    assert M.main_fila(tmp_path / "lotes", fila=FilaFalsa(), rodar=lambda *a, **k: 1 / 0) == 0


def test_pedido_novo_espelha_o_andamento_no_banco(tmp_path):
    f = FilaFalsa(PEDIDO)
    def rodar(lote, entregar):
        L.anotar(lote, "pronto: conferindo as fotos", T())
        return 0
    assert M.main_fila(tmp_path / "lotes", fila=f, rodar=rodar, agora=T) == 0
    assert f.anotados == ["esteira trabalhando nisto (PC-TESTE)", "pronto: conferindo as fotos"]
    assert L.ESPELHO is None


def test_parou_no_meio_devolve_ao_hub_com_o_motivo_e_nao_repete(tmp_path):
    f = FilaFalsa(PEDIDO)
    def rodar(lote, entregar):
        L.anotar(lote, "falhou em 'escrevendo o texto': x", T())
        return 1
    assert M.main_fila(tmp_path / "lotes", fila=f, rodar=rodar, agora=T) == 1
    assert f.terminados and "falhou em 'escrevendo o texto'" in f.terminados[0][1]
    # proxima volta: lote concluido, nao roda de novo
    assert M.main_fila(tmp_path / "lotes", fila=f, rodar=lambda *a, **k: 1 / 0) == 0


def test_aviso_de_erro_que_nao_saiu_sai_na_proxima_volta(tmp_path):
    f = FilaFalsa(PEDIDO, terminar_falha=1)
    assert M.main_fila(tmp_path / "lotes", fila=f, rodar=lambda lote, entregar: 1, agora=T) == 1
    assert f.terminados == []
    assert M.main_fila(tmp_path / "lotes", fila=f, rodar=lambda *a, **k: 1 / 0) == 0
    assert len(f.terminados) == 1


def test_pedido_devolvido_no_site_para_a_esteira(tmp_path):
    f = FilaFalsa(PEDIDO, anotar_ok=False)
    chamado = []
    assert M.main_fila(tmp_path / "lotes", fila=f, rodar=lambda *a, **k: chamado.append(1), agora=T) == 1
    lt = next(p for p in (tmp_path / "lotes").iterdir() if p.is_dir())
    assert chamado == [] and L.ler(lt)["concluido"]
    assert "nao aceita mais" in (lt / "andamento.txt").read_text(encoding="utf-8")


def test_entrega_grava_e_termina(tmp_path):
    lt = _lote_pedido(tmp_path)
    P.montar_entrada(lt, ler_cubagem=lambda c: {})
    f = FilaFalsa()
    assert M._entregador(f, 7)(lt) is True
    assert f.gravados[0]["lote"] == lt.name and f.terminados == [(7, None)]


def test_entrega_feita_nao_vira_pedido_perdido(tmp_path):
    # pedido 9 (22/10): depois de terminar, o banco recusa anotar (pedido ja 'produzido') e a esteira
    # achava que o pedido tinha sido devolvido no site.
    f = FilaFalsa(PEDIDO)
    anotar = f.anotar
    f.anotar = lambda pid, etapa, texto, lote=None: anotar(pid, etapa, texto, lote) and not f.terminados
    def rodar(lote, entregar):
        P.montar_entrada(lote, ler_cubagem=lambda c: {})
        assert entregar(lote) is True
        L.marcar_feita(lote, "entregar", T())
        L.concluir(lote, T())
        return 0
    assert M.main_fila(tmp_path / "lotes", fila=f, rodar=rodar, agora=T) == 0
    lt = next(p for p in (tmp_path / "lotes").iterdir() if p.is_dir())
    assert "nao aceita mais" not in (lt / "andamento.txt").read_text(encoding="utf-8")
    assert f.terminados == [(7, None)]


def test_uma_rodada_por_vez_mesmo_com_trava_velha(tmp_path):
    lotes = tmp_path / "lotes"
    trava = M._pegar_trava(lotes)
    assert trava is not None and M._pegar_trava(lotes) is None
    assert M.main_fila(lotes, fila=FilaFalsa(PEDIDO), rodar=lambda *a, **k: 1 / 0) == 0  # nem pegou o pedido
    os.utime(lotes / ".fila.trava", (0, 0))  # 1970: PC suspenso horas com a rodada viva
    assert M._pegar_trava(lotes) is None  # a rodada antiga ainda existe: nao toma
    trava.close()
    assert M._pegar_trava(lotes) is not None


def test_trava_de_processo_morto_e_tomada(tmp_path):
    import subprocess
    import textwrap
    lotes = tmp_path / "lotes"
    raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    filho = subprocess.Popen([sys.executable, "-c", textwrap.dedent(f"""
        import sys, time
        sys.path.insert(0, {raiz!r})
        from esteira_auto import maestro as M
        t = M._pegar_trava({str(lotes)!r})
        print("peguei" if t else "nao", flush=True)
        time.sleep(60)
    """)], stdout=subprocess.PIPE, text=True)
    try:
        assert filho.stdout.readline().strip() == "peguei"
        assert M._pegar_trava(lotes) is None
    finally:
        filho.kill()
        filho.wait()
    assert M._pegar_trava(lotes) is not None  # morreu = o Windows soltou


def test_motivo_que_vai_ao_hub_diz_por_que_parou(tmp_path):
    f = FilaFalsa(PEDIDO)
    def rodar(lote, entregar):
        L.parar_pai(lote, "BRI-coza18-PAI", "falta capa da cor 'Branco'", T())
        L.anotar(lote, "nenhum produto sobrou neste lote", T())
        L.concluir(lote, T())
        return 1
    M.main_fila(tmp_path / "lotes", fila=f, rodar=rodar, agora=T)
    assert f.terminados[0][1] == "BRI-coza18-PAI: falta capa da cor 'Branco'"
    lt = next(p for p in (tmp_path / "lotes").iterdir() if p.is_dir())
    assert (lt / "andamento.txt").read_text(encoding="utf-8").count("lote concluido") == 1
