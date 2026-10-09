"""Quadro 'Faltou ou divergiu': cada dado do brief (step-04) com status pendente ou divergente,
com o que cada fonte disse, para o Almir decidir na tela."""

# campo da ficha por dado do brief, em ordem de preferencia (o nome muda conforme a categoria)
SUGESTAO_DE_CAMPO = {"material": ["MATERIAL", "STRUCTURE_MATERIALS", "MAIN_MATERIAL"], "altura_cm": ["HEIGHT"],
                     "largura_cm": ["WIDTH"], "profundidade_cm": ["LENGTH", "DEPTH"], "diametro_cm": ["DIAMETER"],
                     "capacidade": ["VOLUME_CAPACITY", "CAPACITY"]}
ROTULOS = {"material": "Material", "altura_cm": "Altura (cm)", "largura_cm": "Largura (cm)",
           "profundidade_cm": "Profundidade (cm)", "diametro_cm": "Diâmetro (cm)",
           "capacidade": "Capacidade", "caracteristicas": "Características"}


def _folhas(d, prefixo=""):
    for k, v in (d or {}).items():
        if isinstance(v, dict) and "status" in v:
            yield (prefixo + k, k, v)
        elif isinstance(v, dict):
            yield from _folhas(v, prefixo + k + ".")


def _link(u):
    """So http(s): o brief vem de pagina de concorrente; 'javascript:' rodaria na tela de publicar."""
    u = str(u or "").strip()
    return u if u.lower().startswith(("https://", "http://")) else None


def _txt(v):
    return ", ".join(map(str, v)) if isinstance(v, list) else str(v)


def montar(brief, ficha):
    itens = []
    for chave, nome, v in _folhas((brief or {}).get("dados_produto")):
        if v.get("status") not in ("pendente", "divergente"):
            continue
        fontes = []
        if v.get("valor") not in (None, "", []):
            fontes.append({"origem": v.get("fonte") or "planilha", "valor": _txt(v["valor"]), "link": _link(v.get("permalink"))})
        for d in v.get("valores_divergentes") or []:
            fontes.append({"origem": d.get("fonte") or "concorrente", "valor": _txt(d.get("valor")), "link": _link(d.get("permalink"))})
        campo = next((c for c in SUGESTAO_DE_CAMPO.get(nome, []) if c in (ficha or {})), None)
        itens.append({"chave": chave, "rotulo": ROTULOS.get(nome, nome), "status": v["status"], "fontes": fontes,
                      "campo_ficha": campo,
                      "unidade": "cm" if nome.endswith("_cm") else None})
    return itens
