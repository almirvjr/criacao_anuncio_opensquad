"""Lote = uma planilha, uma pasta propria. O caderno (andamento.json) diz o que ja foi feito;
andamento.txt e o mesmo em portugues, para o Almir e para o Claude lerem depois."""
import json
import os
from pathlib import Path

ETAPAS = ["entrada", "capas", "curadoria", "categoria", "pesquisa", "texto", "revisao", "tela"]
NOMES = {"entrada": "lendo a planilha", "capas": "conferindo as fotos", "curadoria": "organizando os dados",
         "categoria": "escolhendo a categoria", "pesquisa": "pesquisando concorrentes",
         "texto": "escrevendo o texto", "revisao": "revisando", "tela": "esperando voce na tela"}


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


def criar_lote(planilha, raiz_lotes, agora):
    lote = Path(raiz_lotes) / f"{agora:%Y-%m-%d-%H%M%S}"
    lote.mkdir(parents=True, exist_ok=False)
    _salvar(lote, {"planilha": str(planilha), "criado_em": f"{agora:%Y-%m-%d %H:%M}",
                   "feitas": [], "parados": {}, "concluido": False})
    anotar(lote, f"lote criado para a planilha {Path(planilha).name}", agora)
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


def concluir(lote, agora):
    d = ler(lote)
    d["concluido"] = True
    _salvar(lote, d)
    anotar(lote, "lote concluido", agora)


def proxima(lote):
    d = ler(lote)
    if d.get("concluido"):
        return None
    return next((e for e in ETAPAS if e not in d["feitas"]), None)


def lote_aberto(raiz_lotes):
    raiz = Path(raiz_lotes)
    if not raiz.is_dir():
        return None
    for p in sorted(x for x in raiz.iterdir() if (x / "andamento.json").is_file()):
        if not ler(p).get("concluido"):
            return p
    return None
