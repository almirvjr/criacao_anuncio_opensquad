#!/usr/bin/env python3
"""
aprovacao.py — tela de aprovacao do anuncio (Almir, 08/10/2026).

Le os anuncios parados no step-06, confere com as MESMAS travas da esteira e grava
a escolha do Almir no anuncio-{pai}.yaml. Spec:
docs/superpowers/specs/2026-10-08-tela-aprovacao-design.md

Uso:  python aprovacao.py [--saida PASTA] [--esperar] [--sem-navegador]
"""
import copy
import json
import os
import re
import shutil
import sys
from datetime import datetime
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
