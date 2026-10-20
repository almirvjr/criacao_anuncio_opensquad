"""Maestro da esteira de anuncios: conduz um lote da planilha ate a tela, sem conversa.
Spec: docs/superpowers/specs/2026-10-09-botao-criar-anuncios-design.md"""
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from esteira_auto import campos as campos_mod, chamar_claude, coletar_concorrentes, lote as L, precheck, travas  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
LOTES = RAIZ / "squads" / "ml-anuncios" / "output" / "lotes"
A_CRIAR = Path(r"G:\Meu Drive\TERRA CASA DECOR\ANUNCIOS\A CRIAR")
STEPS = {"capas": "step-07-capas.md", "curadoria": "step-02-curadoria-produtos.md",
         "categoria": "step-03-categorizacao.md", "pesquisa": "step-04-inteligencia-conversao.md",
         "texto": "step-05-copywriting.md", "revisao": "step-08-revisao.md"}
COM_CABECA = ["capas", "curadoria", "categoria", "pesquisa", "texto", "revisao"]


def _rel(lote):
    """Caminho do lote relativo a raiz, com '/': a permissao de gravar do Claude e por esse caminho."""
    try:
        return Path(lote).resolve().relative_to(RAIZ).as_posix()
    except ValueError:
        return Path(lote).as_posix()


def instrucao(etapa, lote, pais, motivo=None):
    t = (Path(__file__).parent / "instrucoes" / f"{etapa}.md").read_text(encoding="utf-8")
    return (t.replace("{LOTE}", _rel(lote)).replace("{PAIS}", ", ".join(pais))
             .replace("{MOTIVO}", motivo or ""))


def _pais(lote):
    entrada = json.loads((Path(lote) / "anuncios-entrada.json").read_text(encoding="utf-8"))
    parados = L.ler(lote)["parados"]
    return [a["pai_sku"] for a in entrada.get("anuncios", []) if a["pai_sku"] not in parados]


TETO_DEVOLVER = 3  # devolveu mais que isso = o texto precisa do Claude com o Almir, nao de mais rodada paga


def _devolvidos(lote):
    import yaml
    parados = L.ler(lote)["parados"]
    out = []
    for f in sorted((Path(lote) / "copywriting").glob("anuncio-*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if d.get("status_copy") == "devolvido" and d.get("pai_sku") not in parados:
            out.append(d.get("pai_sku"))
    return out


def _preparar_devolvidos(lote, agora):
    """Conta a devolucao, para quem passou do teto e volta o resto para 'pendente' (nao depende
    do Claude lembrar de mudar o status, senao a tela fecharia na hora e o ciclo pago se repetiria)."""
    import yaml
    refazer = []
    for pai in _devolvidos(lote):
        if L.contar_devolucao(lote, pai) > TETO_DEVOLVER:
            L.parar_pai(lote, pai, f"devolvido mais de {TETO_DEVOLVER} vezes: chame o Claude para acertar o texto junto", agora)
            continue
        f = Path(lote) / "copywriting" / f"anuncio-{pai}.yaml"
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        d["status_copy"] = "pendente"
        f.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False, width=100000), encoding="utf-8")
        refazer.append(pai)
    return refazer


def _etapa(etapa, lote, pais, chamar, conferir, agora, avisar):
    """Roda uma etapa com cabeca + trava, com 1 nova tentativa por reprovacao. False = parar o lote."""
    avisar(f"{agora():%H:%M} {L.NOMES[etapa]}…")
    ok, resumo = chamar(instrucao(etapa, lote, pais), RAIZ)
    if not ok:
        L.anotar(lote, f"falhou em '{L.NOMES[etapa]}': {resumo}. Clique de novo para continuar daqui.", agora())
        return False
    ruins = conferir(etapa, lote, pais)
    if ruins:
        motivo = "; ".join(f"{p}: {m}" for p, m in ruins.items())
        L.anotar(lote, f"reprovado em '{L.NOMES[etapa]}', tentando de novo: {motivo}", agora())
        ok, resumo = chamar(instrucao(etapa, lote, list(ruins), motivo), RAIZ)
        ruins = conferir(etapa, lote, list(ruins)) if ok else ruins
        for p, m in ruins.items():
            L.parar_pai(lote, p, m, agora())
            avisar(f"  parou {p}: {m}")
    return True


def rodar_lote(lote, chamar=chamar_claude.chamar, conferir=travas.conferir,
               ler_planilha=precheck.ler_planilha, abrir_tela=None, agora=datetime.now, avisar=print,
               buscar_campos=None, coletar=None):
    abrir_tela = abrir_tela or _abrir_tela
    buscar_campos = buscar_campos or campos_mod.buscar_campos
    coletar = coletar or coletar_concorrentes.coletar
    while True:
        etapa = L.proxima(lote)
        if etapa is None:
            return 0
        if etapa == "entrada":
            avisar(f"{agora():%H:%M} {L.NOMES['entrada']}…")
            problemas = ler_planilha(Path(L.ler(lote)["planilha"]), lote)
            if problemas:
                for p in problemas:
                    L.anotar(lote, f"PAROU antes de comecar: {p}", agora())
                    avisar("  " + p)
                return 1
            L.marcar_feita(lote, "entrada", agora())
            continue
        if etapa == "tela":
            while True:
                avisar(f"{agora():%H:%M} abrindo a tela de aprovacao…")
                cod = abrir_tela(lote)
                if cod == 3:
                    dev = _preparar_devolvidos(lote, agora())
                    if not dev:
                        L.anotar(lote, "devolvido sem mais rodada possivel: veja o motivo acima", agora())
                        return 1
                    for e in ("texto", "revisao"):
                        if not _etapa(e, lote, dev, chamar, conferir, agora, avisar):
                            return 1
                    continue
                if cod == 0:
                    L.marcar_feita(lote, "tela", agora())
                    L.concluir(lote, agora())
                    return 0
                L.anotar(lote, "tela fechada com anuncio pendente: clique de novo para reabrir", agora())
                return 2
        pais = _pais(lote)
        if not pais:
            L.anotar(lote, "nenhum produto sobrou neste lote", agora())
            L.concluir(lote, agora())
            return 1
        if not _etapa(etapa, lote, pais, chamar, conferir, agora, avisar):
            return 1
        L.marcar_feita(lote, etapa, agora())
        if etapa == "categoria":
            # campos da ficha que o comprador ve (regra do "não se aplica"); falhar so anota
            falhou = buscar_campos(lote)
            if falhou:
                L.anotar(lote, f"nao consegui ler os campos da categoria de {', '.join(falhou)}; "
                               "a ficha sai sem a conferencia de campo esquecido", agora())
            # concorrentes pela API (com o acesso da loja) + opinioes por Chrome de verdade; falhar so anota
            avisar(f"{agora():%H:%M} juntando concorrentes e opinioes do ML…")
            falhou = coletar(lote)
            if falhou:
                L.anotar(lote, f"nao consegui juntar os concorrentes de {', '.join(falhou)}; "
                               "a pesquisa usa o caminho antigo para eles", agora())


def _abrir_tela(lote):
    r = subprocess.run([sys.executable, str(RAIZ / "tools" / "aprovacao" / "aprovacao.py"),
                        "--saida", str(lote), "--esperar"])
    return r.returncode


def mover_para_feitos(planilha):
    planilha = Path(planilha)
    feitos = planilha.parent / "FEITOS"
    feitos.mkdir(exist_ok=True)
    destino, n = feitos / planilha.name, 2
    while destino.exists():
        destino = feitos / f"{planilha.stem}-{n}{planilha.suffix}"
        n += 1
    shutil.move(str(planilha), str(destino))
    return destino


def proxima_planilha(pasta):
    pasta = Path(pasta)
    if not pasta.is_dir():
        return None
    cands = [p for p in pasta.iterdir() if p.is_file() and p.suffix.lower() in (".xls", ".xlsx")
             and not p.name.startswith("~$")]
    return min(cands, key=lambda p: p.stat().st_mtime) if cands else None


def main(a_criar=A_CRIAR, lotes=LOTES, rodar=None):
    rodar = rodar or rodar_lote
    while True:
        lote = L.lote_aberto(lotes)
        if lote is None:
            pl = proxima_planilha(a_criar)
            if pl is None:
                print("Nada para criar: a pasta A CRIAR esta vazia.")
                return 0
            lote = L.criar_lote(pl, lotes, datetime.now())
            print(f"Lote novo: {pl.name}")
        else:
            print(f"Continuando o lote de {Path(L.ler(lote)['planilha']).name}")
        cod = rodar(lote)
        if cod != 0:
            # a planilha fica em A CRIAR: corrigido o motivo, clicar de novo recomeca
            print(f"\nParou. O que aconteceu esta em {Path(lote) / 'andamento.txt'}")
            return cod
        pl = Path(L.ler(lote)["planilha"])
        if pl.is_file():
            print(f"Planilha guardada em {mover_para_feitos(pl)}")


if __name__ == "__main__":
    sys.exit(main())
