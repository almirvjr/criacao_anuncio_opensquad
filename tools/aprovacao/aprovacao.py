#!/usr/bin/env python3
"""
aprovacao.py — tela de aprovacao do anuncio (Almir, 08/10/2026).

Le os anuncios parados no step-06, confere com as MESMAS travas da esteira e grava
a escolha do Almir no anuncio-{pai}.yaml. Spec:
docs/superpowers/specs/2026-10-08-tela-aprovacao-design.md

Uso:  python aprovacao.py [--saida PASTA] [--esperar] [--sem-navegador]
"""
import argparse
import copy
import json
import os
import re
import shutil
import sys
import threading
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
SAIDA_PADRAO = RAIZ / "squads" / "ml-anuncios" / "output"
sys.path.insert(0, str(RAIZ / "squads" / "ml-anuncios" / "pipeline" / "validators"))
from validar_ficha_seo import validar_ficha, descricao_do_copy  # noqa: E402
from validar_claims import validar_claims  # noqa: E402

TETO_TITULO = 60
FINAIS = ("aprovado", "devolvido")


def _ler_yaml(p):
    with open(p, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _entrada_por_pai(saida):
    p = Path(saida) / "anuncios-entrada.json"
    if not p.is_file():
        return {}
    with open(p, encoding="utf-8") as fh:
        d = json.load(fh)
    return {a.get("pai_sku"): a for a in d.get("anuncios", [])}


def _titulo_inicial(doc):
    if doc.get("titulo_final"):
        return doc["titulo_final"]
    for t in doc.get("titles") or []:
        if isinstance(t, dict) and t.get("recomendado"):
            return t.get("texto", "")
    return ""


def _capas(saida, pai):
    p = Path(saida) / "capas" / f"capas-{pai}.yaml"
    if not p.is_file():
        return None
    doc = _ler_yaml(p) or {}
    return [{"cor": v.get("cor"), "urls": list(v.get("picture_ids") or [])}
            for v in doc.get("picture_ids_por_variacao") or []]


def _cartao(saida, doc, entrada):
    pai = doc.get("pai_sku")
    a = entrada.get(pai, {})
    attrs = doc.get("attributes") or {}
    desc = doc.get("description") or {}
    return {
        "pai_sku": pai,
        "nome_base": doc.get("nome_base"),
        "titles": [{"texto": t.get("texto", ""), "recomendado": bool(t.get("recomendado")),
                    "justificativa": t.get("justificativa", "")}
                   for t in doc.get("titles") or [] if isinstance(t, dict)],
        "titulo_inicial": _titulo_inicial(doc),
        "marca": attrs.get("BRAND") or "",
        "modelo": attrs.get("MODEL") or "",
        "descricao": {k: v for k, v in desc.items() if str(k).startswith("bloco") and isinstance(v, str)},
        "ficha": {k: v for k, v in attrs.items() if k not in ("BRAND", "MODEL")},
        "observacoes": list(doc.get("warnings") or []),
        "precos": [{"cor": v.get("cor"), "sku": v.get("sku"), "preco": v.get("preco_venda")}
                   for v in a.get("variacoes") or []],
        "preco_provisorio": bool(a.get("preco_provisorio")),
        "peso_kg": a.get("peso_bruto_kg"),
        "caixa_cm": a.get("dim_embalagem_cm"),
        "capas": _capas(saida, pai),
    }


def listar_pendentes(saida):
    saida = Path(saida)
    pasta = saida / "copywriting"
    if not pasta.is_dir():
        return []
    entrada = _entrada_por_pai(saida)
    cartoes = []
    for f in sorted(pasta.glob("anuncio-*.yaml")):
        try:
            doc = _ler_yaml(f)
            if not isinstance(doc, dict) or not doc.get("pai_sku"):
                raise ValueError("arquivo sem pai_sku")
        except Exception as e:  # noqa: BLE001
            cartoes.append({"arquivo": f.name, "erro": f"Este arquivo nao abriu ({type(e).__name__})."})
            continue
        if doc.get("status_copy") in FINAIS:
            continue
        cartoes.append(_cartao(saida, doc, entrada))
    return cartoes


PAI_OK = re.compile(r"^[A-Za-z0-9_-]+$")


def caminho_anuncio(saida, pai):
    if not PAI_OK.match(str(pai or "")):
        raise ValueError(f"SKU pai invalido: {pai!r}")
    return Path(saida) / "copywriting" / f"anuncio-{pai}.yaml"


def aplicar_edicao(doc, edicao):
    novo = copy.deepcopy(doc)
    novo["titulo_final"] = (edicao.get("titulo") or "").strip()
    attrs = novo.setdefault("attributes", {})
    attrs["BRAND"] = (edicao.get("marca") or "").strip()
    attrs["MODEL"] = (edicao.get("modelo") or "").strip()
    desc = novo.setdefault("description", {})
    for k, v in (edicao.get("descricao") or {}).items():
        if str(k).startswith("bloco"):
            desc[k] = v or ""
    return novo


def conferir(saida, pai, edicao):
    doc = _ler_yaml(caminho_anuncio(saida, pai))
    novo = aplicar_edicao(doc, edicao)
    titulo = novo["titulo_final"]
    itens = []
    if not titulo:
        itens.append({"codigo": "TITULO_VAZIO", "nivel": "bloqueio", "texto": "Falta escolher o titulo."})
    elif len(titulo) > TETO_TITULO:
        itens.append({"codigo": "TITULO_LONGO", "nivel": "bloqueio",
                      "texto": f"Titulo com {len(titulo)} letras; o Mercado Livre aceita ate {TETO_TITULO}."})
    attrs = novo["attributes"]
    for cod, msg in validar_ficha(pai, titulo, attrs["BRAND"], attrs["MODEL"], descricao_do_copy(novo)):
        itens.append({"codigo": cod, "nivel": "aviso" if cod.startswith("WARN") else "erro", "texto": msg})
    brief_p = Path(saida) / "inteligencia" / f"brief-{pai}.yaml"
    if not brief_p.is_file():
        itens.append({"codigo": "BRIEF_AUSENTE", "nivel": "erro",
                      "texto": "Nao achei a pesquisa deste anuncio: a conferencia de promessas NAO rodou."})
    else:
        blocks, warns = validar_claims(_ler_yaml(brief_p), copy_doc=novo, sem_fotos=True)
        itens += [{"codigo": c, "nivel": "erro", "texto": m} for c, m in blocks]
        itens += [{"codigo": c, "nivel": "aviso", "texto": m} for c, m in warns]
    return itens


def _gravar_seguro(caminho, doc, agora):
    caminho = Path(caminho)
    antes = caminho.parent / "_antes"
    antes.mkdir(exist_ok=True)
    shutil.copy2(caminho, antes / f"{caminho.stem}-{agora:%Y%m%d-%H%M%S}.yaml")
    tmp = caminho.with_name(caminho.name + ".novo")
    with open(tmp, "w", encoding="utf-8") as fh:
        yaml.safe_dump(doc, fh, allow_unicode=True, sort_keys=False, width=100000)
    os.replace(tmp, caminho)


def aprovar(saida, pai, edicao, agora=None):
    agora = agora or datetime.now()
    caminho = caminho_anuncio(saida, pai)
    doc = _ler_yaml(caminho)
    if doc.get("status_copy") in FINAIS:
        return {"ok": False, "motivo": f"Este anuncio ja esta '{doc['status_copy']}'.", "conferencia": []}
    itens = conferir(saida, pai, edicao)
    if any(i["nivel"] == "bloqueio" for i in itens):
        return {"ok": False, "motivo": "Tem bloqueio: corrija antes de aprovar.", "conferencia": itens}
    novo = aplicar_edicao(doc, edicao)
    novo["status_copy"] = "aprovado"
    novo["aprovado_em"] = f"{agora:%Y-%m-%d %H:%M}"
    novo["avisos_aceitos"] = [i["codigo"] for i in itens]
    _gravar_seguro(caminho, novo, agora)
    salvo = _ler_yaml(caminho)
    depois = conferir(saida, pai, {"titulo": salvo["titulo_final"], "marca": salvo["attributes"]["BRAND"],
                                   "modelo": salvo["attributes"]["MODEL"],
                                   "descricao": salvo.get("description") or {}})
    return {"ok": True, "conferencia": depois}


def devolver(saida, pai, nota, agora=None):
    agora = agora or datetime.now()
    nota = (nota or "").strip()
    if not nota:
        return {"ok": False, "motivo": "Escreva o que a Renata deve refazer."}
    caminho = caminho_anuncio(saida, pai)
    doc = _ler_yaml(caminho)
    if doc.get("status_copy") in FINAIS:
        return {"ok": False, "motivo": f"Este anuncio ja esta '{doc['status_copy']}'."}
    doc["status_copy"] = "devolvido"
    doc["nota_almir"] = nota
    doc["devolvido_em"] = f"{agora:%Y-%m-%d %H:%M}"
    _gravar_seguro(caminho, doc, agora)
    return {"ok": True}


PAGINA = Path(__file__).resolve().parent / "pagina.html"


def criar_servidor(saida, esperar=False):
    saida = Path(saida)

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _responder(self, codigo, corpo, tipo="application/json; charset=utf-8"):
            dados = corpo if isinstance(corpo, bytes) else json.dumps(corpo, ensure_ascii=False).encode("utf-8")
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(dados)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(dados)

        def do_GET(self):
            if self.path == "/":
                return self._responder(200, PAGINA.read_bytes(), "text/html; charset=utf-8")
            if self.path == "/api/pendentes":
                return self._responder(200, {"cartoes": listar_pendentes(saida)})
            self._responder(404, {"erro": "nao existe"})

        def do_POST(self):
            if not (self.headers.get("Content-Type") or "").startswith("application/json"):
                return self._responder(415, {"erro": "so JSON"})
            try:
                n = int(self.headers.get("Content-Length") or 0)
                corpo = json.loads(self.rfile.read(n) or b"{}")
                pai = corpo.get("pai")
                if self.path == "/api/conferir":
                    return self._responder(200, {"itens": conferir(saida, pai, corpo.get("edicao") or {})})
                if self.path == "/api/aprovar":
                    r = aprovar(saida, pai, corpo.get("edicao") or {})
                elif self.path == "/api/devolver":
                    r = devolver(saida, pai, corpo.get("nota"))
                    if r["ok"]:
                        srv.estado["devolvidos"] += 1
                else:
                    return self._responder(404, {"erro": "nao existe"})
            except ValueError as e:
                return self._responder(400, {"erro": str(e)})
            except Exception as e:  # noqa: BLE001
                return self._responder(500, {"erro": f"Falhou ({type(e).__name__}). Chame o Claude."})
            if r["ok"]:
                srv.estado["acoes"] += 1
                if esperar and not listar_pendentes(saida):
                    threading.Thread(target=lambda: (srv.shutdown(), srv.encerrado.set()), daemon=True).start()
            self._responder(200, r)

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    srv.estado = {"devolvidos": 0, "acoes": 0}
    srv.encerrado = threading.Event()
    return srv


def main():
    p = argparse.ArgumentParser(description="Tela de aprovacao do anuncio.")
    p.add_argument("--saida", default=str(SAIDA_PADRAO), help="pasta de saida da esteira")
    p.add_argument("--esperar", action="store_true",
                   help="encerra quando nao sobrar pendente; sai 0 = todos aprovados, 3 = algum devolvido")
    p.add_argument("--sem-navegador", action="store_true")
    a = p.parse_args()
    srv = criar_servidor(a.saida, esperar=a.esperar)
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    pend = listar_pendentes(a.saida)
    print(f"Tela de aprovacao aberta em {url}")
    print(f"{len(pend)} anuncio(s) esperando aprovacao. Feche esta janela para desligar a tela.")
    if not a.sem_navegador:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    if a.esperar:
        sys.exit(3 if srv.estado["devolvidos"] else 0)


if __name__ == "__main__":
    main()