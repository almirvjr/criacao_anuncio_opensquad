FOTOS_MIN, FOTOS_MAX = 1, 10   # esteira sem fotos (07/10/2026): capa do Almir, ate 10 por cor


def _mapa_de_cores(cor_value_map):
    """Aceita o formato REAL da Cibele (lista de objetos) e o dict plano legado.

    A Cibele entrega uma linha por cor — `{cor, value_id?, value_name, value_name_livre?}` —
    porque a lista carrega o aviso de "esta cor nao tem codigo no ML", que o dict plano
    nao consegue expressar. Cor sem `value_id` fica FORA do mapa de proposito: vai ao ML
    so como `value_name` livre. (Decisao do Almir, 2026-07-22.)
    """
    if isinstance(cor_value_map, dict):
        return {k: v for k, v in cor_value_map.items() if v}
    return {e["cor"]: e["value_id"] for e in (cor_value_map or []) if e.get("value_id")}


def _fotos_por_sku(picture_ids_por_variacao):
    """Lista pronta do Felipe: `[{sku_variacao, picture_ids[10]}]`, capa na 1a posicao.

    O builder NAO remonta essa lista somando fotos da cor + compartilhadas — era essa
    conta que gerava 11 picture_ids (o bug das duas capas). Quem monta e o Felipe, que
    tem o brief; aqui so se le. (Decisao do Almir, 2026-07-22.)
    """
    return {e["sku_variacao"]: e.get("picture_ids") or []
            for e in (picture_ids_por_variacao or [])}


def _fotos_da_variacao(mapa, sku):
    fotos = mapa.get(sku)
    if not fotos:
        raise ValueError(
            f"Sem foto para a variacao {sku}: falta a capa dessa cor no Cloudinary "
            f"(etiquetas 'capa-anuncio' + '{sku}'). Anuncio nao vai ao ar sem foto.")
    if not (FOTOS_MIN <= len(fotos) <= FOTOS_MAX):
        raise ValueError(f"Variacao {sku} veio com {len(fotos)} fotos; o ML aceita de "
                         f"{FOTOS_MIN} a {FOTOS_MAX}.")
    return fotos


def validate_anuncio(anuncio):
    erros = []
    vs = anuncio.get("variacoes", [])
    if anuncio["modo"] == "variacoes":
        precos = {v.get("preco_venda") for v in vs}
        if len(precos) > 1:
            erros.append(f"Preço não uniforme entre variações: {sorted(precos)} (ML exige igual)")
        for v in vs:
            if not v.get("cor"):
                erros.append(f"Variação {v['sku']} sem cor")
            if not v.get("ean"):
                erros.append(f"Variação {v['sku']} sem EAN")
    return erros

def atributos_embalagem(anuncio):
    """Medida da CAIXA (cubagem) — e a que manda no frete do ML. Sem medida: nao inventa."""
    peso = anuncio.get("peso_bruto_kg")
    dim = anuncio.get("dim_embalagem_cm") or {}
    try:
        peso = float(peso or 0)
        l, a, c = (float(dim.get(k) or 0) for k in ("largura", "altura", "comprimento"))
    except (TypeError, ValueError):
        return []
    if not (peso and l and a and c):
        return []
    fmt = lambda x: f"{int(x)}" if float(x).is_integer() else f"{x}"  # noqa: E731
    return [{"id": "SELLER_PACKAGE_HEIGHT", "value_name": f"{fmt(a)} cm"},
            {"id": "SELLER_PACKAGE_WIDTH", "value_name": f"{fmt(l)} cm"},
            {"id": "SELLER_PACKAGE_LENGTH", "value_name": f"{fmt(c)} cm"},
            {"id": "SELLER_PACKAGE_WEIGHT", "value_name": f"{int(round(peso * 1000))} g"}]


def build_payload(anuncio, *, title, category_id, description_plain,
                  picture_ids_por_variacao, cor_value_map, item_attributes,
                  listing_type_id="gold_special"):
    item_attributes = list(item_attributes) + atributos_embalagem(anuncio)
    cores = _mapa_de_cores(cor_value_map)
    fotos = _fotos_por_sku(picture_ids_por_variacao)

    base = {"modo": anuncio["modo"], "pai_sku": anuncio["pai_sku"], "title": title,
            "category_id": category_id, "listing_type_id": listing_type_id,
            "condition": "new", "currency_id": "BRL",
            "description_plain": description_plain, "brand": anuncio.get("marca"),
            "attributes": item_attributes}

    if anuncio["modo"] == "simples":
        v = anuncio["variacoes"][0]
        base["price"] = v["preco_venda"]
        base["available_quantity"] = 1
        base["pictures"] = _fotos_da_variacao(fotos, v["sku"])
        base["sku"] = v["sku"]
        base["attributes"] = item_attributes + [{"id": "SELLER_SKU", "value_name": v["sku"]}]
        if v.get("ean"):
            base["attributes"].append({"id": "EAN", "value_name": v["ean"]})
        return base

    base["variation_attribute"] = {"id": "COLOR", "defines_picture": True}
    base["variacoes"] = []
    for v in anuncio["variacoes"]:
        comb = {"id": "COLOR", "value_name": v["cor"]}
        if cores.get(v["cor"]):
            comb = {"id": "COLOR", "value_id": cores[v["cor"]], "value_name": v["cor"]}
        attrs = [{"id": "SELLER_SKU", "value_name": v["sku"]}]
        if v.get("ean"):
            attrs.append({"id": "EAN", "value_name": v["ean"]})
        base["variacoes"].append({
            "sku": v["sku"], "cor_value_name": v["cor"],
            "attribute_combinations": [comb],
            "price": v["preco_venda"], "available_quantity": 1,
            "attributes": attrs,
            "fotos_cor": v.get("fotos_cor", []),
            "picture_ids": _fotos_da_variacao(fotos, v["sku"]),
        })
    return base


# Regras do Almir para TODO anuncio novo (09/10/2026): dentro da loja oficial da Terra, garantia do
# vendedor de 30 dias e anuncio Classico (gold_special no ML Brasil; gold_pro = Premium).
LOJA_OFICIAL = 458566
GARANTIA = [{"id": "WARRANTY_TYPE", "value_name": "Garantia do vendedor"},
            {"id": "WARRANTY_TIME", "value_name": "30 dias"}]

TETO_FAMILIA = 60  # family_name <= max_title_length do dominio (MLB33375 = 60)


def build_payloads_familia(anuncio, *, family_name, category_id, description_plain,
                           picture_ids_por_variacao, cor_value_map, item_attributes,
                           listing_type_id="gold_special"):
    """Modelo novo do ML (User Products, conta com a tag user_product_seller, 08/10/2026).

    O ML nao aceita mais `variations` nem `title`: cada cor e um anuncio proprio, e os
    anuncios da mesma familia levam o mesmo `family_name` (o ML monta o titulo e junta as
    cores na mesma pagina). Devolve um pacote por cor, no contrato `modo: simples` do
    webhook ML Publicar.
    """
    family_name = (family_name or "").strip()
    if not family_name or len(family_name) > TETO_FAMILIA:
        raise ValueError(f"Nome da familia com {len(family_name)} caracteres; o ML aceita de 1 a {TETO_FAMILIA}.")
    base_attrs = list(item_attributes) + atributos_embalagem(anuncio)
    cores = _mapa_de_cores(cor_value_map)
    fotos = _fotos_por_sku(picture_ids_por_variacao)
    pacotes = []
    # Almir 08/10/2026: a preta e sempre a cor principal -> criada primeiro na familia
    # (a familia guarda as cores na ordem de criacao). Sem preta, mantem a ordem.
    variacoes = sorted(anuncio["variacoes"], key=lambda v: str(v.get("cor") or "").strip().lower() != "preto")
    for v in variacoes:
        attrs = list(base_attrs)
        if v.get("cor"):
            cor = {"id": "COLOR", "value_name": v["cor"]}
            if cores.get(v["cor"]):
                cor = {"id": "COLOR", "value_id": cores[v["cor"]], "value_name": v["cor"]}
            attrs.append(cor)
        attrs.append({"id": "SELLER_SKU", "value_name": v["sku"]})
        if v.get("ean"):
            attrs.append({"id": "GTIN", "value_name": v["ean"]})
        pacotes.append({
            "modo": "simples", "pai_sku": anuncio["pai_sku"], "sku": v["sku"],
            "family_name": family_name, "category_id": category_id,
            "listing_type_id": listing_type_id, "condition": "new", "currency_id": "BRL",
            "official_store_id": LOJA_OFICIAL, "sale_terms": [dict(g) for g in GARANTIA],
            "description_plain": description_plain, "attributes": attrs,
            "price": v["preco_venda"], "available_quantity": 1,
            "pictures": _fotos_da_variacao(fotos, v["sku"]),
        })
    return pacotes
