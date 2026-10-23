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
from esteira_auto import fila as F, pedido as pedido_mod  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
LOTES = RAIZ / "squads" / "ml-anuncios" / "output" / "lotes"
A_CRIAR = Path(r"G:\Meu Drive\TERRA CASA DECOR\ANUNCIOS\A CRIAR")
STEPS = {"capas": "step-07-capas.md", "curadoria": "step-02-curadoria-produtos.md",
         "categoria": "step-03-categorizacao.md", "pesquisa": "step-04-inteligencia-conversao.md",
         "texto": "step-05-copywriting.md", "revisao": "step-08-revisao.md"}
COM_CABECA = ["capas", "curadoria", "categoria", "pesquisa", "texto", "revisao"]
TENTATIVAS_COLETA = 3


def _manter_acordado(ligar):
    """Enquanto trabalha, o Windows nao suspende o PC por inatividade (fechar a tampa ainda suspende)."""
    try:
        import ctypes
        ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | (ES_SYSTEM_REQUIRED if ligar else 0))
    except Exception:  # noqa: BLE001  (fora do Windows: nada a fazer)
        pass


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
               buscar_campos=None, coletar=None, ler_pedido=None, entregar=None):
    abrir_tela = abrir_tela or _abrir_tela
    buscar_campos = buscar_campos or campos_mod.buscar_campos
    coletar = coletar or coletar_concorrentes.coletar
    ler_pedido = ler_pedido or pedido_mod.montar_entrada
    while True:
        etapa = L.proxima(lote)
        if etapa is None:
            return 0
        if etapa == "entregar":
            avisar(f"{agora():%H:%M} {L.NOMES['entregar']}…")
            if not entregar(lote):
                L.anotar(lote, "nao consegui entregar ao hub: tento de novo na proxima volta", agora())
                return 4
            L.marcar_feita(lote, "entregar", agora())
            L.concluir(lote, agora())
            return 0
        if etapa == "entrada":
            avisar(f"{agora():%H:%M} {L.NOMES['entrada']}…")
            d = L.ler(lote)
            problemas = ler_pedido(lote) if "pedido_id" in d else ler_planilha(Path(d["planilha"]), lote)
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
        if pais and etapa == "pesquisa":
            # concorrentes pela API (com o acesso da loja) + opinioes por Chrome de verdade. Sem opiniao o texto sai
            # fraco (pedido 9, 22/10: PC dormiu no meio, 0 opinioes, e a esteira pagou o texto assim mesmo):
            # falhou = tenta de novo na proxima volta; na 3a vez para o produto com o motivo.
            avisar(f"{agora():%H:%M} juntando concorrentes e opinioes do ML…")
            falhou = [p for p in coletar(lote) if p in pais]
            if falhou:
                d = L.ler(lote)
                n = d.get("coleta_tentativas", 0) + 1
                d["coleta_tentativas"] = n
                L._salvar(lote, d)
                if n < TENTATIVAS_COLETA:
                    L.anotar(lote, f"nao consegui ler concorrentes e opinioes do ML de {', '.join(falhou)} "
                                   f"(tentativa {n} de {TENTATIVAS_COLETA}): tento de novo na proxima volta", agora())
                    return 4
                for p in falhou:
                    L.parar_pai(lote, p, f"{TENTATIVAS_COLETA} tentativas sem conseguir ler as opinioes dos "
                                         "concorrentes no ML (o Chrome da esteira abriu?)", agora())
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


class PedidoPerdido(Exception):
    """O hub nao aceita mais este pedido desta maquina (devolvido ou cancelado no site)."""


def _espelho(fila, pid, lote):
    """Cada linha do andamento.txt tambem vai para o banco. Banco fora do ar = so o arquivo (a entrega confere)."""
    def espelhar(texto):
        try:
            ok = fila.anotar(pid, L.proxima(lote) or "fim", texto, Path(lote).name)
        except F.SemAcesso:
            return
        if not ok:
            raise PedidoPerdido()
    return espelhar


def _entregador(fila, pid):
    def entregar(lote):
        try:
            if not fila.gravar_resultado(pid, pedido_mod.resultado(lote)) or not fila.terminar(pid):
                raise PedidoPerdido()
        except F.SemAcesso:
            return False
        L.ESPELHO = None  # pedido ja terminado: o banco recusa anotar e isso nao e "devolvido no site"
        return True
    return entregar


def _marcar_erro_pendente(lote, erro):
    d = L.ler(lote)
    d["erro_para_o_hub"] = erro
    L._salvar(lote, d)


def _avisar_erros_pendentes(fila, lotes):
    """Lote parado cujo aviso ao hub ainda nao saiu: avisa agora (so isso; banco fora = tenta na proxima)."""
    raiz = Path(lotes)
    if not raiz.is_dir():
        return
    for p in sorted(x for x in raiz.iterdir() if (x / "andamento.json").is_file()):
        d = L.ler(p)
        if d.get("erro_para_o_hub") and "pedido_id" in d:
            try:
                fila.terminar(d["pedido_id"], erro=d["erro_para_o_hub"])
            except F.SemAcesso:
                return False
            d = L.ler(p)
            d.pop("erro_para_o_hub", None)
            L._salvar(p, d)
    return True


def _motivo(lote):
    """Por que parou, para o hub mostrar: o motivo de cada produto parado e as linhas de falha do caderno."""
    d = L.ler(lote)
    partes = [f"{pai}: {m}" for pai, m in d.get("parados", {}).items()]
    linhas = (Path(lote) / "andamento.txt").read_text(encoding="utf-8").splitlines()
    partes += [l.split(" - ", 1)[-1] for l in linhas
               if any(k in l for k in ("falhou em", "PAROU antes", "nao consegui"))]
    return " | ".join(partes) or " | ".join(linhas[-3:])


def _pegar_trava(lotes):
    """Uma rodada da fila por vez neste PC. A tarefa agendada dispara de 5 em 5 min e o lote leva ~15 min.
    Trava = arquivo aberto e trancado pelo Windows: fica presa enquanto o processo existir (PC suspenso horas
    inclusive) e solta sozinha quando ele morre. Antes era pela idade (90 min): PC suspenso mais que isso
    = rodada nova no mesmo lote enquanto a antiga acordava. Devolve o arquivo aberto (fechar = soltar) ou None."""
    p = Path(lotes) / ".fila.trava"
    p.parent.mkdir(parents=True, exist_ok=True)
    f = open(p, "a+b")
    try:
        f.seek(0)
        if sys.platform == "win32":
            import msvcrt
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        return None
    return f


def main_fila(lotes=LOTES, fila=None, rodar=None, agora=datetime.now):
    trava = _pegar_trava(lotes)
    if trava is None:
        print("Outra rodada da fila esta trabalhando.")
        return 0
    try:
        return _main_fila(lotes, fila, rodar, agora)
    finally:
        trava.close()


def _main_fila(lotes, fila, rodar, agora):
    """Tarefa agendada do PC: faz UM pedido da fila do hub por vez (retoma o que ficou aberto).
    Parou no meio = devolve ao hub com o motivo (o Almir pede de novo pelo site); nao repete etapa paga sozinho.
    So a entrega do fim e tentada de novo na proxima volta."""
    rodar = rodar or rodar_lote
    try:
        fila = fila or F.Fila()
        _avisar_erros_pendentes(fila, lotes)
        lote = L.lote_aberto(lotes, de_pedido=True)
        novo = lote is None
        if novo:
            pedido = fila.pegar()
            if not pedido:
                print("Nenhum pedido na fila do hub.")
                return 0
            lote = L.criar_lote_do_pedido(pedido, lotes, agora())
            print(f"Pedido {pedido['pedido_id']}: {pedido['produto']['sku_pai']}")
        pid = L.ler(lote)["pedido_id"]
        L.ESPELHO = _espelho(fila, pid, lote)
        try:
            if novo:
                L.anotar(lote, f"esteira trabalhando nisto ({fila.maquina})", agora())
            cod = rodar(lote, entregar=_entregador(fila, pid))
            L.ESPELHO = None
            if cod in (0, 4):
                return cod
            # concluir ANTES de avisar o hub: se o aviso falhar, a proxima volta so repete o aviso
            # (nunca refaz etapa paga)
            if not L.ler(lote).get("concluido"):
                L.concluir(lote, agora())
            _marcar_erro_pendente(lote, _motivo(lote))
            avisou = _avisar_erros_pendentes(fila, lotes)
            print(("\nParou e devolvi ao hub." if avisou else "\nParou; o aviso ao hub sai na proxima volta.")
                  + f" O que aconteceu esta em {Path(lote) / 'andamento.txt'}")
            return cod
        except PedidoPerdido:
            L.ESPELHO = None
            L.anotar(lote, "o hub nao aceita mais este pedido (devolvido ou cancelado no site): parei aqui", agora())
            L.concluir(lote, agora())
            return 1
        finally:
            L.ESPELHO = None
    except F.SemAcesso as e:
        print(f"Sem acesso a fila do hub: {e}")
        return 5


if __name__ == "__main__":
    _manter_acordado(True)
    try:
        cod = main_fila() if "--fila" in sys.argv else main()
    finally:
        _manter_acordado(False)
    sys.exit(cod)
