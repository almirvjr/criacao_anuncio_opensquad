import re


def parse_color(variacoes_raw):
    if not variacoes_raw:
        return None
    m = re.match(r"\s*[^:]+:([^|]+)", variacoes_raw)
    return m.group(1).strip() if m else None


def normalize(records):
    """records: list de dicts já lidos do xlsx (sku, cod_pai, variacoes_raw, preco_venda,
    preco_custo, ean, tipo, marca, peso_bruto, dim_cm, fotos). Retorna anúncios com modo."""
    records = [r for r in records if r.get("sku")]
    parent_skus = {r["cod_pai"] for r in records if r.get("cod_pai")}
    pais = {r["sku"]: r for r in records if r["sku"] in parent_skus}
    anuncios = []
    consumidos = set()

    for rec in records:
        if rec["sku"] in pais:  # linha pai -> anúncio com variações
            filhos = [c for c in records if c.get("cod_pai") == rec["sku"]]
            anuncios.append(_anuncio(rec, filhos, "variacoes"))
            consumidos.update(f["sku"] for f in filhos)
            consumidos.add(rec["sku"])

    for rec in records:  # SKUs avulsos (sem pai e que não são filhos) -> simples
        if rec["sku"] in consumidos or rec.get("cod_pai"):
            continue
        anuncios.append(_anuncio(rec, [rec], "simples"))

    return {"total_anuncios": len(anuncios),
            "total_variacoes": sum(a["total_variacoes"] for a in anuncios),
            "anuncios": anuncios}


def _num(x):
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


def _medidas(base, filhos):
    """Pai costuma vir zerado no Tiny e fora da cubagem: usa a maior medida entre as cores."""
    fontes = [base] + list(filhos)
    peso = max(_num(f.get("peso_bruto")) for f in fontes)
    dim = {k: max(_num((f.get("dim_cm") or {}).get(k)) for f in fontes)
           for k in ("largura", "altura", "comprimento")}
    dim = {k: (int(v) if float(v).is_integer() else v) for k, v in dim.items()}
    return (peso or None), dim


def _variacao(f):
    return {"sku": f["sku"], "cor": parse_color(f.get("variacoes_raw")), "nome": f.get("nome"),
            "ean": f.get("ean"), "preco_venda": f.get("preco_venda"),
            "preco_custo": f.get("preco_custo"),
            "peso_bruto_kg": f.get("peso_bruto"), "dim_embalagem_cm": f.get("dim_cm", {}),
            "fotos_origem": f.get("fotos", []), "fotos_bucket": [], "fotos_cor": []}


def _anuncio(base, filhos, modo):
    variacoes = [_variacao(f) for f in filhos]
    peso, dim = _medidas(base, filhos)
    return {"modo": modo, "pai_sku": base["sku"], "nome_base": base.get("nome"),
            "marca": base.get("marca") or next((f.get("marca") for f in filhos if f.get("marca")), None),
            "descricao_complementar": base.get("descricao_complementar")
            or next((f.get("descricao_complementar") for f in filhos if f.get("descricao_complementar")), None),
            "fornecedor": base.get("fornecedor")
            or next((f.get("fornecedor") for f in filhos if f.get("fornecedor")), None),
            "peso_bruto_kg": peso, "dim_embalagem_cm": dim,
            "atributos_pendentes": ["material", "tamanho_produto", "caracteristicas"],
            "total_variacoes": len(variacoes), "variacoes": variacoes}
