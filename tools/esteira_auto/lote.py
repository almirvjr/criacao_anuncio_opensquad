"""Lote = uma planilha, uma pasta propria. O caderno (andamento.json) diz o que ja foi feito;
andamento.txt e o mesmo em portugues, para o Almir e para o Claude lerem depois."""
import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

ETAPAS = ["entrada", "capas", "curadoria", "categoria", "pesquisa", "texto", "revisao", "tela"]
NOMES = {"entrada": "lendo os produtos", "capas": "conferindo as fotos", "curadoria": "organizando os dados",
         "categoria": "escolhendo a categoria", "pesquisa": "pesquisando concorrentes",
         "texto": "escrevendo o texto", "revisao": "revisando", "tela": "esperando voce na tela",
         "entregar": "entregando ao hub"}
# Lote que veio da fila do hub: sem tela no PC (aprovacao e publicacao sao no site); no fim entrega ao banco.
ETAPAS_PEDIDO = ETAPAS[:-1] + ["entregar"]

# Lote de pedido: cada linha do andamento.txt tambem vai para o banco (o maestro liga isto). Recebe o texto.
ESPELHO = None


def _salvar(lote, d):
    p = Path(lote) / "andamento.json"
    tmp = p.with_name(p.name + ".novo")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)


def ler(lote):
    return json.loads((Path(lote) / "andamento.json").read_text(encoding="utf-8"))


def anotar(lote, texto, agora):
    with open(Path(lote) / "andamento.txt", "a", encoding="utf-8") as fh:
        fh.write(f"{agora:%d/%m %H:%M} - {texto}\n")
    if ESPELHO is not None:
        ESPELHO(texto)


def criar_lote(planilha, raiz_lotes, agora):
    lote = Path(raiz_lotes) / f"{agora:%Y-%m-%d-%H%M%S}"
    lote.mkdir(parents=True, exist_ok=False)
    _salvar(lote, {"planilha": str(planilha), "criado_em": f"{agora:%Y-%m-%d %H:%M}",
                   "feitas": [], "parados": {}, "concluido": False})
    anotar(lote, f"lote criado para a planilha {Path(planilha).name}", agora)
    return lote


def criar_lote_do_pedido(pedido, raiz_lotes, agora, vaga=1):
    """Pedido da fila do hub -> lote proprio. pedido.json guarda o que o banco mandou (leitura do Olist).
    `vaga` = qual rodada da fila e dona do lote (so ela retoma)."""
    pid, pai = pedido["pedido_id"], pedido["produto"]["sku_pai"]
    lote = Path(raiz_lotes) / f"{agora:%Y-%m-%d-%H%M%S}-pedido{pid}"
    lote.mkdir(parents=True, exist_ok=False)
    (lote / "pedido.json").write_text(json.dumps(pedido, ensure_ascii=False, indent=1), encoding="utf-8")
    _salvar(lote, {"pedido_id": pid, "sku_pai": pai, "criado_em": f"{agora:%Y-%m-%d %H:%M}",
                   "etapas": ETAPAS_PEDIDO, "feitas": [], "parados": {}, "concluido": False, "vaga": vaga})
    anotar(lote, f"lote criado para o pedido {pid} do hub ({pai}), vaga {vaga}", agora)
    return lote


def marcar_feita(lote, etapa, agora):
    d = ler(lote)
    if etapa not in d["feitas"]:
        d["feitas"].append(etapa)
        _salvar(lote, d)
        anotar(lote, f"pronto: {NOMES.get(etapa, etapa)}", agora)


def parar_pai(lote, pai, motivo, agora):
    d = ler(lote)
    d["parados"][pai] = motivo
    _salvar(lote, d)
    anotar(lote, f"PAROU {pai}: {motivo}", agora)


def contar_devolucao(lote, pai):
    """Quantas vezes o Almir ja devolveu este produto neste lote (conta e devolve o total)."""
    d = ler(lote)
    n = d.setdefault("devolucoes", {}).get(pai, 0) + 1
    d["devolucoes"][pai] = n
    _salvar(lote, d)
    return n


def concluir(lote, agora):
    d = ler(lote)
    d["concluido"] = True
    _salvar(lote, d)
    anotar(lote, "lote concluido", agora)


def proxima(lote):
    d = ler(lote)
    if d.get("concluido"):
        return None
    return next((e for e in d.get("etapas", ETAPAS) if e not in d["feitas"]), None)


def vaga_do_lote(d):
    """Lote de pedido sem `vaga` (antes das rodadas em paralelo, 04/11/2026) = vaga 1."""
    return d.get("vaga") or 1


def lote_aberto(raiz_lotes, de_pedido=False, vaga=None):
    """1o lote nao concluido do tipo pedido (fila do hub) ou planilha (botao): um nunca retoma o do outro.
    Com `vaga`: so lote de pedido daquela vaga (a outra rodada pode estar trabalhando no dela)."""
    raiz = Path(raiz_lotes)
    if not raiz.is_dir():
        return None
    for p in sorted(x for x in raiz.iterdir() if (x / "andamento.json").is_file()):
        d = ler(p)
        if not d.get("concluido") and ("pedido_id" in d) == de_pedido:
            if vaga is not None and de_pedido and vaga_do_lote(d) != vaga:
                continue
            return p
    return None


# ── Reaproveitar etapas caras de um lote anterior do mesmo produto (peca 4, 04/11/2026) ──────────────────────────
# Pedido parado e pedido de novo virava lote do zero (~13-28 min). Reaproveita so o que nao depende das decisoes do
# Almir: a categoria (categorizacao/*) e a COLETA de concorrentes da pesquisa (o brief e refeito: traz os fatos).
# Entrada, capas, curadoria, texto e revisao sempre de novo.
DIAS_REAPROVEITAR = 7


def skus_do_pedido(pedido):
    vs = pedido.get("variacoes") or ((pedido.get("olist") or {}).get("variacoes")) or []
    return {str(v.get("sku")) for v in vs if v.get("sku")}


def achar_reaproveitavel(raiz_lotes, pedido, agora, dias=DIAS_REAPROVEITAR):
    """Lote de pedido mais recente (ate `dias`) do mesmo pai que ja escolheu a categoria e cujos SKUs contem os do
    pedido novo. Pedido com recado do Almir ("Refazer do zero") nunca reaproveita."""
    raiz = Path(raiz_lotes)
    pai, skus = pedido["produto"]["sku_pai"], skus_do_pedido(pedido)
    if not raiz.is_dir() or not skus or str(pedido.get("recado") or "").strip():
        return None
    for p in sorted((x for x in raiz.iterdir() if (x / "andamento.json").is_file()), key=lambda x: x.name, reverse=True):
        try:
            d = ler(p)
            if d.get("sku_pai") != pai or "pedido_id" not in d or "categoria" not in d.get("feitas", []):
                continue
            if agora - datetime.strptime(d["criado_em"], "%Y-%m-%d %H:%M") > timedelta(days=dias):
                continue
            velho = json.loads((p / "pedido.json").read_text(encoding="utf-8"))
        except (OSError, ValueError, KeyError):
            continue
        if skus <= skus_do_pedido(velho) and (p / "categorizacao" / "categorias.yaml").is_file():
            return p
    return None


def reaproveitar(lote, velho, agora):
    """Copia a categoria (e a coleta de concorrentes, se o lote velho tem) e anota no caderno. Devolve o que veio."""
    lote, velho = Path(lote), Path(velho)
    pai = ler(lote)["sku_pai"]
    shutil.copytree(velho / "categorizacao", lote / "categorizacao", dirs_exist_ok=True)
    veio = ["categoria"]
    coleta = velho / "inteligencia" / "_coleta" / f"coleta-{pai}.json"
    if coleta.is_file():
        dados = json.loads(coleta.read_text(encoding="utf-8"))
        (lote / "inteligencia" / "_coleta").mkdir(parents=True, exist_ok=True)
        shutil.copy2(coleta, lote / "inteligencia" / "_coleta" / coleta.name)
        raw = lote / "inteligencia" / "_raw"
        raw.mkdir(parents=True, exist_ok=True)
        for k in dados.get("concorrentes") or []:  # o _raw de cada concorrente: a trava do brief confere a citacao nele
            f = velho / "inteligencia" / "_raw" / f"{k.get('id')}.json"
            if f.is_file():
                shutil.copy2(f, raw / f.name)
        veio.append("coleta")
    d = ler(lote)
    d["feitas"].append("categoria")
    d["reaproveitado"] = {"de": velho.name, "etapas": veio}
    _salvar(lote, d)
    nomes = {"categoria": "categoria", "coleta": "coleta de concorrentes"}
    anotar(lote, f"reaproveitei do lote {velho.name}: {', '.join(nomes[v] for v in veio)}", agora)
    return veio


def coleta_reaproveitada(lote):
    return "coleta" in (ler(lote).get("reaproveitado") or {}).get("etapas", [])
