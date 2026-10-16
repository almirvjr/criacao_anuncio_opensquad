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


def _enviar(pacote, enviar):
    """1a metade: manda ao ML Publicar. O resultado e gravado ANTES de qualquer outra coisa,
    para um erro depois nao perder o numero do anuncio (e o clique seguinte nao publicar de novo)."""
    cor = next((a.get("value_name") for a in pacote["attributes"] if a["id"] == "COLOR"), None)
    item = {"sku": pacote["sku"], "cor": cor, "ok": False, "mlb": None, "link": None, "incerto": False,
            "descricao": False, "flex": False, "garantia": False, "loja_oficial": False, "erro": None, "em": datetime.now().strftime("%Y-%m-%d %H:%M")}
    try:
        r = enviar(pacote)
    except Exception:  # noqa: BLE001
        r = {"http": None, "resposta": {}}
    resp = r.get("resposta") or {}
    if r.get("http") is None or r.get("http") >= 500:
        # sem resposta nao quer dizer que nao publicou: o ML pode ter criado e a resposta se perdido
        item.update(incerto=True, erro="o sistema de publicacao nao respondeu: nao sei se publicou. "
                                       "confira no ML antes de tentar de novo")
        return item
    if r.get("http") == 404:
        # n8n responde 404 quando o workflow esta desligado: o pedido nem chegou ao ML
        item["erro"] = ("o sistema de publicacao (ML Publicar, no n8n) esta desligado: nada foi publicado. "
                        "Ligue o workflow e clique em Tentar de novo")
        return item
    if resp.get("status") not in ("success", "partial") or not resp.get("mlb_id"):
        item["erro"] = f"o Mercado Livre recusou: {resp.get('error_message') or resp.get('error_code') or 'sem motivo'}"
        return item
    item.update(ok=True, mlb=resp["mlb_id"], link=resp.get("permalink"))
    return item


def _completar(item, pacote, completar, token):
    """2a metade: descricao + Flex. Qualquer falha vira frase fixa; o anuncio ja existe."""
    try:
        tk = token()
        if not tk:
            item["erro"] = "publicado, mas nao consegui o acesso ao ML para gravar descricao e Flex"
            return item
        c = completar(pacote, item["mlb"], tk)
        item.update(descricao=bool(c.get("descricao")), flex=bool(c.get("flex")),
                    garantia=bool(c.get("garantia")), loja_oficial=bool(c.get("loja_oficial")))
        if not item["loja_oficial"]:
            item["erro"] = "publicado FORA da loja oficial da Terra: confira no ML"
    except Exception:  # noqa: BLE001
        item["erro"] = "publicado, mas a descricao e o Flex nao foram gravados (falha de rede); chame o Claude"
    return item


def _uma(caminho, pacote, enviar, completar, token):
    item = _enviar(pacote, enviar)
    _guardar(caminho, item)
    if item["ok"]:
        _guardar(caminho, _completar(item, pacote, completar, token))
    return item


def _guardar(caminho, item):
    doc = _ler(caminho)  # rele sempre: nunca grava por cima do que outra acao acabou de gravar
    doc.setdefault("publicacao", {})[item["sku"]] = item
    _gravar(caminho, doc)


def publicar_anuncio(saida, pai, enviar=_padrao_enviar, completar=_padrao_completar, token=_padrao_token):
    caminho = _caminho(saida, pai)
    lista = pacotes(saida, pai)
    doc = _ler(caminho)
    doc["_total_cores"] = len(lista)
    _gravar(caminho, doc)
    feitos = []
    for pacote in lista:
        anterior = (_ler(caminho).get("publicacao") or {}).get(pacote["sku"]) or {}
        if anterior.get("mlb"):
            feitos.append(anterior)
            continue
        feitos.append(_uma(caminho, pacote, enviar, completar, token))
    return feitos


def publicar_cor(saida, pai, sku, enviar=_padrao_enviar, completar=_padrao_completar, token=_padrao_token):
    caminho = _caminho(saida, pai)
    if _ler(caminho).get("status_copy") != "aprovado":
        raise ValueError("Este anuncio nao esta aprovado.")
    pacote = next((p for p in pacotes(saida, pai) if p["sku"] == sku), None)
    if pacote is None:
        raise ValueError(f"Cor {sku} nao e deste anuncio.")
    anterior = (_ler(caminho).get("publicacao") or {}).get(sku) or {}
    if anterior.get("mlb"):
        return anterior
    return _uma(caminho, pacote, enviar, completar, token)


def situacao(doc):
    pub = doc.get("publicacao") or {}
    if not pub:
        return "nao_publicado"
    oks = [bool(v.get("mlb")) for v in pub.values()]
    return "publicado" if all(oks) and len(oks) == doc.get("_total_cores", len(oks)) else "em_parte"
