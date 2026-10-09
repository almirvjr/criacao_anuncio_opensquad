"""Publica um anuncio aprovado na tela: uma cor por vez, preta primeiro, pelo ML Publicar
(n8n, sem mudanca) e, logo depois, descricao + Flex (completar_anuncio). Cor ja publicada
(com mlb gravado) e pulada: clicar duas vezes nao duplica. Spec:
docs/superpowers/specs/2026-10-09-botao-criar-anuncios-design.md"""
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import montar_payload  # noqa: E402


def _caminho(saida, pai):
    return Path(saida) / "copywriting" / f"anuncio-{pai}.yaml"


def _ler(p):
    with open(p, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _gravar(p, doc):
    tmp = p.with_name(p.name + ".novo")
    with open(tmp, "w", encoding="utf-8") as fh:
        yaml.safe_dump(doc, fh, allow_unicode=True, sort_keys=False, width=100000)
    os.replace(tmp, p)


def _padrao_enviar(corpo):
    from disparar_publicacao import enviar
    return enviar(corpo)


def _padrao_completar(payload, mlb, tk):
    from completar_anuncio import completar
    return completar(payload, mlb, tk)


def _padrao_token():
    from conferir_no_ml import token
    return token()


def pacotes(saida, pai):
    saida = Path(saida)
    doc = _ler(_caminho(saida, pai))
    if not doc.get("preco"):
        raise ValueError("Anuncio sem preco: digite o preco na tela antes de publicar.")
    return montar_payload.montar(saida / "anuncios-entrada.json", saida / "categorizacao" / "categorias.yaml",
                                 _caminho(saida, pai), saida / "capas" / f"capas-{pai}.yaml", pai,
                                 preco=doc["preco"])


def _uma(pacote, enviar, completar, token):
    cor = next((a.get("value_name") for a in pacote["attributes"] if a["id"] == "COLOR"), None)
    item = {"sku": pacote["sku"], "cor": cor, "ok": False, "mlb": None, "link": None,
            "descricao": False, "flex": False, "erro": None, "em": datetime.now().strftime("%Y-%m-%d %H:%M")}
    r = enviar(pacote)
    resp = r.get("resposta") or {}
    if r.get("http") is None or r.get("http") >= 500:
        item["erro"] = "o sistema de publicacao nao respondeu; nada foi publicado nesta cor"
        return item
    if resp.get("status") not in ("success", "partial") or not resp.get("mlb_id"):
        item["erro"] = f"o Mercado Livre recusou: {resp.get('error_message') or resp.get('error_code') or 'sem motivo'}"
        return item
    item.update(ok=True, mlb=resp["mlb_id"], link=resp.get("permalink"))
    tk = token()
    if not tk:
        item["erro"] = "publicado, mas nao consegui o acesso ao ML para gravar descricao e Flex"
        return item
    c = completar(pacote, item["mlb"], tk)
    item.update(descricao=bool(c.get("descricao")), flex=bool(c.get("flex")))
    return item


def publicar_anuncio(saida, pai, enviar=_padrao_enviar, completar=_padrao_completar, token=_padrao_token):
    caminho = _caminho(saida, pai)
    lista = pacotes(saida, pai)
    feitos = []
    for pacote in lista:
        doc = _ler(caminho)
        doc["_total_cores"] = len(lista)
        anterior = (doc.get("publicacao") or {}).get(pacote["sku"]) or {}
        if anterior.get("mlb"):
            feitos.append(anterior)
            continue
        item = _uma(pacote, enviar, completar, token)
        doc.setdefault("publicacao", {})[pacote["sku"]] = item
        _gravar(caminho, doc)
        feitos.append(item)
    return feitos


def publicar_cor(saida, pai, sku, enviar=_padrao_enviar, completar=_padrao_completar, token=_padrao_token):
    caminho = _caminho(saida, pai)
    pacote = next((p for p in pacotes(saida, pai) if p["sku"] == sku), None)
    if pacote is None:
        raise ValueError(f"Cor {sku} nao e deste anuncio.")
    doc = _ler(caminho)
    anterior = (doc.get("publicacao") or {}).get(sku) or {}
    if anterior.get("mlb"):
        return anterior
    item = _uma(pacote, enviar, completar, token)
    doc.setdefault("publicacao", {})[sku] = item
    _gravar(caminho, doc)
    return item


def situacao(doc):
    pub = doc.get("publicacao") or {}
    if not pub:
        return "nao_publicado"
    oks = [bool(v.get("mlb")) for v in pub.values()]
    return "publicado" if all(oks) and len(oks) == doc.get("_total_cores", len(oks)) else "em_parte"
