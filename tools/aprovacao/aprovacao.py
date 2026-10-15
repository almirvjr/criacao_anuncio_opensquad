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
import hmac
import secrets
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
SAIDA_PADRAO = RAIZ / "squads" / "ml-anuncios" / "output"
sys.path.insert(0, str(RAIZ / "squads" / "ml-anuncios" / "pipeline" / "validators"))
from validar_ficha_seo import validar_ficha, descricao_do_copy  # noqa: E402
from validar_claims import validar_claims  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import publicar as pub  # noqa: E402
import quadro as quadro_mod  # noqa: E402
from olist_ean import reler_ean  # noqa: E402

TETO_TITULO = 60
FINAIS = ("aprovado", "devolvido", "tirado")
TIPOS = {"gold_special": "Clássico", "gold_pro": "Premium", "free": "Grátis"}  # ML Brasil


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


def ler_preco(texto):
    """'129,90', '1.299', '1.299,90', '1,299.90', 'R$ 92,71' -> numero. O ultimo separador com 1-2
    casas depois e o decimal; ponto seguido de 3 algarismos e milhar (o jeito brasileiro)."""
    t = re.sub(r"[^\d,.\-]", "", str(texto or ""))
    if "," in t and "." in t:
        dec = "," if t.rfind(",") > t.rfind(".") else "."
        t = t.replace("." if dec == "," else ",", "").replace(dec, ".")
    elif "," in t:
        t = t.replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", t):
        t = t.replace(".", "")
    try:
        v = round(float(t), 2)
    except ValueError:
        raise ValueError("Preco invalido: digite so o valor, ex.: 129,90")
    if v <= 0:
        raise ValueError("Preco invalido: tem que ser maior que zero")
    return v


def _categoria(saida, pai):
    p = Path(saida) / "categorizacao" / "categorias.yaml"
    if not p.is_file():
        return {}
    return next((c for c in (_ler_yaml(p) or {}).get("categorias") or [] if c.get("pai_sku") == pai), {})


def _parecer(saida, pai):
    p = Path(saida) / "revisao" / f"parecer-{pai}.yaml"
    if not p.is_file():
        return None
    d = _ler_yaml(p) or {}
    partes = []
    for k in ("decisao_final", "resumo", "correcoes_necessarias", "correcoes_pendentes", "pendencias_para_tela"):
        v = d.get(k)
        if v:
            partes += [str(x) for x in v] if isinstance(v, list) else [str(v)]
    resumo = " | ".join(partes)
    return {"status": d.get("status"), "score": d.get("score_total"), "resumo": resumo}


def _cores(saida, pai, a, titulo):
    p = Path(saida) / "capas" / f"capas-{pai}.yaml"
    capas = {}
    if p.is_file():
        for k in (_ler_yaml(p) or {}).get("picture_ids_por_variacao") or []:
            capas[k.get("sku_variacao")] = list(k.get("picture_ids") or [])
    vs = sorted(a.get("variacoes") or [], key=lambda v: str(v.get("cor") or "").strip().lower() != "preto")
    return [{"sku": v["sku"], "cor": v.get("cor"), "ean": v.get("ean"), "estoque": v.get("estoque"),
             "capas": capas.get(v["sku"], []),
             "titulo_ml": f"{titulo} {v['cor']}".strip() if v.get("cor") else titulo} for v in vs]


def _brief(saida, pai):
    p = Path(saida) / "inteligencia" / f"brief-{pai}.yaml"
    return (_ler_yaml(p) or {}) if p.is_file() else {}


def _cartao(saida, doc, entrada):
    pai = doc.get("pai_sku")
    a = entrada.get(pai, {})
    attrs = doc.get("attributes") or {}
    desc = doc.get("description") or {}
    cat = _categoria(saida, pai)
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
        "categoria": " > ".join(cat.get("breadcrumb") or []) or cat.get("category_name"),
        "tipo_anuncio": TIPOS.get(cat.get("listing_type_id") or "gold_special", "Clássico"),
        "parecer": _parecer(saida, pai),
        "cores": _cores(saida, pai, a, _titulo_inicial(doc)),
        "preco": doc.get("preco"),
        "quadro": quadro_mod.montar(_brief(saida, pai), attrs),
        "publicacao": list((doc.get("publicacao") or {}).values()),
        "publicacao_por_cor": [(doc.get("publicacao") or {}).get(v["sku"])
                               or {"sku": v["sku"], "cor": v.get("cor"), "ok": False, "mlb": None,
                                   "erro": "ainda nao publicada"}
                               for v in _cores(saida, pai, a, _titulo_inicial(doc))],
        "situacao": pub.situacao(doc),
    }


def _parados(saida):
    """Produtos que o maestro parou (andamento.json do lote) e que o Almir ainda nao tirou."""
    p = Path(saida) / "andamento.json"
    try:
        parados = (json.loads(p.read_text(encoding="utf-8")) or {}).get("parados") or {} if p.is_file() else {}
    except Exception:  # noqa: BLE001
        return {}
    out = {}
    for pai, motivo in parados.items():
        f = Path(saida) / "copywriting" / f"anuncio-{pai}.yaml"
        try:
            if f.is_file() and (_ler_yaml(f) or {}).get("status_copy") == "tirado":
                continue
        except Exception:  # noqa: BLE001
            pass
        out[pai] = motivo
    return out


def listar_pendentes(saida):
    saida = Path(saida)
    pasta = saida / "copywriting"
    parados = _parados(saida)
    cartoes = [{"pai_sku": pai, "parado": motivo} for pai, motivo in parados.items()]
    if not pasta.is_dir():
        return cartoes
    try:
        entrada = _entrada_por_pai(saida)
    except Exception as e:  # noqa: BLE001
        entrada = {}
        cartoes.append({"arquivo": "anuncios-entrada.json",
                        "erro": f"Este arquivo nao abriu ({type(e).__name__}): preco, peso e caixa nao aparecem."})
    for f in sorted(pasta.glob("anuncio-*.yaml")):
        try:
            doc = _ler_yaml(f)
            if not isinstance(doc, dict) or not doc.get("pai_sku"):
                raise ValueError("arquivo sem pai_sku")
            st = doc.get("status_copy")
            if doc["pai_sku"] in parados or st in ("devolvido", "tirado") or (
                    st == "aprovado" and pub.situacao(doc) == "publicado"):
                continue
            cartoes.append(_cartao(saida, doc, entrada))
        except Exception as e:  # noqa: BLE001
            cartoes.append({"arquivo": f.name, "erro": f"Este anuncio nao abriu ({type(e).__name__}): "
                                                        f"o arquivo dele ou o das capas tem defeito."})
    return cartoes


def tem_o_que_mostrar(saida):
    """A tela abre se houver QUALQUER cartao, inclusive de defeito ou de produto parado."""
    return bool(listar_pendentes(saida))


def situacao_lote(saida):
    """0 = tudo publicado ou tirado; 3 = algum devolvido; 2 = pendente, em parte, parado, defeito ou vazio."""
    if _parados(saida):
        return 2
    devolvido = False
    arquivos = sorted((Path(saida) / "copywriting").glob("anuncio-*.yaml"))
    if not arquivos:
        return 2
    for f in arquivos:
        try:
            doc = _ler_yaml(f) or {}
        except Exception:  # noqa: BLE001
            return 2
        st = doc.get("status_copy")
        if st == "devolvido":
            devolvido = True
        elif st == "tirado" or (st == "aprovado" and pub.situacao(doc) == "publicado"):
            continue
        else:
            return 2
    return 3 if devolvido else 0


def _pendentes_validos(saida):
    return [c for c in listar_pendentes(saida) if not c.get("erro")]


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
    try:
        a = _entrada_por_pai(saida).get(pai, {})
    except Exception:  # noqa: BLE001
        a = {}
    sem = [v.get("cor") or v["sku"] for v in a.get("variacoes") or [] if not v.get("ean")]
    if sem:
        itens.append({"codigo": "SEM_EAN", "nivel": "bloqueio",
                      "texto": f"Sem código de barras: {', '.join(sem)}. Gere pelo botão da GS1 e clique em Reler do Olist."})
    blocos = {k: v for k, v in (novo.get("description") or {}).items() if str(k).startswith("bloco")}
    if not any(str(v or "").strip() for v in blocos.values()):
        itens.append({"codigo": "DESCRICAO_VAZIA", "nivel": "bloqueio", "texto": "A descricao esta vazia."})
    else:
        for k, v in blocos.items():
            if not str(v or "").strip():
                itens.append({"codigo": "BLOCO_VAZIO", "nivel": "erro",
                              "texto": f"Uma parte da descricao ficou vazia ({k})."})
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


_TRAVAS = {}
_TRAVA_DAS_TRAVAS = threading.Lock()


def trava(pai):
    """Uma acao por anuncio de cada vez: dois cliques (ou recarregar no meio) nao publicam a mesma cor 2x."""
    with _TRAVA_DAS_TRAVAS:
        return _TRAVAS.setdefault(pai, threading.Lock())


def _gravar_seguro(caminho, doc, agora):
    caminho = Path(caminho)
    antes = caminho.parent / "_antes"
    antes.mkdir(exist_ok=True)
    if caminho.is_file():
        shutil.copy2(caminho, antes / f"{caminho.stem}-{agora:%Y%m%d-%H%M%S}.yaml")
    tmp = caminho.with_name(f"{caminho.name}.{threading.get_ident()}.novo")
    with open(tmp, "w", encoding="utf-8") as fh:
        yaml.safe_dump(doc, fh, allow_unicode=True, sort_keys=False, width=100000)
    os.replace(tmp, caminho)


def aprovar(saida, pai, edicao, vistos=None, agora=None, reaprovar=False):
    agora = agora or datetime.now()
    caminho = caminho_anuncio(saida, pai)
    doc = _ler_yaml(caminho)
    ja_aprovado_sem_publicar = doc.get("status_copy") == "aprovado" and pub.situacao(doc) != "publicado"
    if doc.get("status_copy") in FINAIS and not (reaprovar and ja_aprovado_sem_publicar):
        return {"ok": False, "motivo": f"Este anuncio ja esta '{doc['status_copy']}'.", "conferencia": []}
    itens = conferir(saida, pai, edicao)
    if any(i["nivel"] == "bloqueio" for i in itens):
        return {"ok": False, "motivo": "Tem bloqueio: corrija antes de aprovar.", "conferencia": itens}
    novos = [i for i in itens if i["nivel"] == "erro" and i["codigo"] not in set(vistos or [])]
    if novos:
        return {"ok": False, "conferencia": itens,
                "motivo": "A conferencia mudou e tem erro que voce ainda nao viu. Confira e clique de novo."}
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


def aprovar_e_publicar(saida, pai, edicao, vistos=None, publicar=pub.publicar_anuncio, agora=None):
    with trava(pai):
        return _aprovar_e_publicar(saida, pai, edicao, vistos, publicar, agora)


def _aprovar_e_publicar(saida, pai, edicao, vistos, publicar, agora):
    agora = agora or datetime.now()
    try:
        preco = ler_preco(edicao.get("preco"))
    except ValueError as e:
        return {"ok": False, "motivo": str(e), "conferencia": []}
    if pai in _parados(saida):
        return {"ok": False, "motivo": "Este anuncio parou na esteira: nao da para publicar. Tire do lote.",
                "conferencia": []}
    caminho = caminho_anuncio(saida, pai)
    # sempre passa pela conferencia e grava a edicao da tela, mesmo se ja aprovado antes
    r = aprovar(saida, pai, edicao, vistos=vistos, agora=agora, reaprovar=True)
    if not r["ok"]:
        return r
    doc = _ler_yaml(caminho)
    doc["preco"] = preco
    decisoes = [d for d in edicao.get("decisoes") or [] if str(d.get("valor") or "").strip()]
    for d in decisoes:
        if d.get("campo_ficha"):
            doc.setdefault("attributes", {})[d["campo_ficha"]] = str(d["valor"]).strip()
    doc["dados_decididos"] = decisoes
    _gravar_seguro(caminho, doc, agora)
    try:
        resultado = publicar(saida, pai)
    except ValueError as e:
        return {"ok": False, "motivo": str(e), "conferencia": []}
    return {"ok": True, "publicacao": resultado}


def tentar_cor(saida, pai, sku, publicar_cor=pub.publicar_cor):
    caminho_anuncio(saida, pai)  # valida o pai
    with trava(pai):
        return {"ok": True, "item": publicar_cor(saida, pai, sku)}


def tirar(saida, pai, agora=None):
    agora = agora or datetime.now()
    caminho = caminho_anuncio(saida, pai)
    with trava(pai):
        doc = _ler_yaml(caminho) if caminho.is_file() else {"pai_sku": pai}  # parado antes do texto
        doc["status_copy"] = "tirado"
        doc["tirado_em"] = f"{agora:%Y-%m-%d %H:%M}"
        caminho.parent.mkdir(exist_ok=True)
        _gravar_seguro(caminho, doc, agora)
    return {"ok": True}


PAGINA = Path(__file__).resolve().parent / "pagina.html"


def criar_servidor(saida, esperar=False, publicar=None, publicar_cor=None):
    """publicar/publicar_cor vem de fora para os testes nunca publicarem de verdade."""
    saida = Path(saida)
    publicar = publicar or pub.publicar_anuncio
    publicar_cor = publicar_cor or pub.publicar_cor

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

        def _barrar(self):
            """Recusa pedido que nao veio desta tela. O Host fixo barra o truque de outro site
            apontar o proprio endereco pra 127.0.0.1 (DNS rebinding); a senha de uso unico,
            embutida na pagina, barra qualquer outro programa que ache a porta."""
            porta = srv.server_address[1]
            if (self.headers.get("Host") or "") not in (f"127.0.0.1:{porta}", f"localhost:{porta}"):
                self._responder(403, {"erro": "endereco nao permitido"})
                return True
            if self.path.startswith("/api/") and not hmac.compare_digest(
                    self.headers.get("X-Tela-Token") or "", srv.selo):
                self._responder(403, {"erro": "pedido sem a senha da tela"})
                return True
            return False

        def do_GET(self):
            if self._barrar():
                return
            if self.path == "/":
                html = PAGINA.read_bytes().replace(b"__TELA_TOKEN__", srv.selo.encode())
                return self._responder(200, html, "text/html; charset=utf-8")
            if self.path == "/api/pendentes":
                return self._responder(200, {"cartoes": listar_pendentes(saida)})
            self._responder(404, {"erro": "nao existe"})

        def do_POST(self):
            if self._barrar():
                return
            if not (self.headers.get("Content-Type") or "").startswith("application/json"):
                return self._responder(415, {"erro": "so JSON"})
            try:
                n = int(self.headers.get("Content-Length") or 0)
                corpo = json.loads(self.rfile.read(n) or b"{}")
                pai = corpo.get("pai")
                if self.path == "/api/conferir":
                    return self._responder(200, {"itens": conferir(saida, pai, corpo.get("edicao") or {})})
                if self.path == "/api/aprovar":
                    r = aprovar_e_publicar(saida, pai, corpo.get("edicao") or {}, vistos=corpo.get("vistos") or [],
                                           publicar=publicar)
                elif self.path == "/api/tentar":
                    r = tentar_cor(saida, pai, corpo.get("sku"), publicar_cor=publicar_cor)
                elif self.path == "/api/tirar":
                    r = tirar(saida, pai)
                elif self.path == "/api/reler-ean":
                    caminho_anuncio(saida, pai)  # valida o pai
                    r = reler_ean(saida, corpo.get("sku"))
                elif self.path == "/api/devolver":
                    with trava(pai):
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
                if esperar and not _pendentes_validos(saida):
                    threading.Thread(target=lambda: (srv.shutdown(), srv.encerrado.set()), daemon=True).start()
            self._responder(200, r)

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    srv.selo = secrets.token_urlsafe(32)
    srv.estado = {"devolvidos": 0, "acoes": 0}
    srv.encerrado = threading.Event()
    return srv


def main():
    p = argparse.ArgumentParser(description="Tela de aprovacao do anuncio.")
    p.add_argument("--saida", default=str(SAIDA_PADRAO), help="pasta de saida da esteira")
    p.add_argument("--esperar", action="store_true",
                   help="encerra quando nao sobrar pendente; sai 0 = todos aprovados, 3 = algum devolvido, 2 = pendente/defeito")
    p.add_argument("--sem-navegador", action="store_true")
    a = p.parse_args()
    if a.esperar and not tem_o_que_mostrar(a.saida):
        print("Nada esperando aprovacao.")
        sys.exit(situacao_lote(a.saida))
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
        sys.exit(situacao_lote(a.saida))


if __name__ == "__main__":
    main()