"""Lote = uma planilha, uma pasta propria. O caderno (andamento.json) diz o que ja foi feito;
andamento.txt e o mesmo em portugues, para o Almir e para o Claude lerem depois."""
import json
import os
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


def criar_lote_do_pedido(pedido, raiz_lotes, agora):
    """Pedido da fila do hub -> lote proprio. pedido.json guarda o que o banco mandou (leitura do Olist)."""
    pid, pai = pedido["pedido_id"], pedido["produto"]["sku_pai"]
    lote = Path(raiz_lotes) / f"{agora:%Y-%m-%d-%H%M%S}-pedido{pid}"
    lote.mkdir(parents=True, exist_ok=False)
    (lote / "pedido.json").write_text(json.dumps(pedido, ensure_ascii=False, indent=1), encoding="utf-8")
    _salvar(lote, {"pedido_id": pid, "sku_pai": pai, "criado_em": f"{agora:%Y-%m-%d %H:%M}",
                   "etapas": ETAPAS_PEDIDO, "feitas": [], "parados": {}, "concluido": False})
    anotar(lote, f"lote criado para o pedido {pid} do hub ({pai})", agora)
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


def lote_aberto(raiz_lotes, de_pedido=False):
    """1o lote nao concluido do tipo pedido (fila do hub) ou planilha (botao): um nunca retoma o do outro."""
    raiz = Path(raiz_lotes)
    if not raiz.is_dir():
        return None
    for p in sorted(x for x in raiz.iterdir() if (x / "andamento.json").is_file()):
        d = ler(p)
        if not d.get("concluido") and ("pedido_id" in d) == de_pedido:
            return p
    return None
