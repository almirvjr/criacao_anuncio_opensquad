"""Campos da ficha que o comprador ve, por categoria (regra do "não se aplica", Almir 16/10/2026).

O maestro busca no ML (so leitura, com o acesso da loja — o Claude sem conversa nao tem o acesso)
e grava `categorizacao/campos-{pai}.json` no lote. A redacao usa a lista para dar destino a cada
campo, e a conferencia (`validar_ficha_nsa.py`) cobra. Falha de rede nao para a esteira.
Campos OCULTOS (tag hidden) tambem entram, marcados `oculto` (Almir, 23-24/10/2026: todos os campos de ficha): o
comprador nao ve, mas o ML usa na busca e nos filtros (ex.: e apto para lava-loucas, e kit). Ficam fora so os que
o vendedor nao escreve (so-leitura, fixo, inferido) e os de controle do proprio ML (SISTEMA)."""
import json
import re
import sys
from pathlib import Path

import yaml

TOOLS = Path(__file__).resolve().parents[1]
ESCONDIDO = ("read_only", "fixed", "others", "inferred")  # o vendedor nao escreve
SISTEMA = {"APGID", "AGID", "PRODUCT_DATA_SOURCE", "ITEM_CONDITION"}  # ocultos de controle do ML (condicao = a publicacao)
A_ESTEIRA_POE = {"GTIN", "SELLER_SKU", "EMPTY_GTIN_REASON",  # vem da planilha, nao da redacao
                 # caixa (oculto): a publicacao poe a da planilha de cubagem
                 "SELLER_PACKAGE_HEIGHT", "SELLER_PACKAGE_WIDTH", "SELLER_PACKAGE_LENGTH", "SELLER_PACKAGE_WEIGHT"}
DA_VARIACAO = {"COLOR", "MAIN_COLOR"}  # com cores, vem de cada cor
# categorias.yaml vem do Claude sem conversa: so aceita o formato esperado, senao o codigo viraria
# outro endereco do ML lido com o acesso da loja, e o SKU viraria caminho fora do lote
CATEGORIA_OK = re.compile(r"^MLB\d+$")
PAI_OK = re.compile(r"^[A-Za-z0-9_-]+$")


def _ler_api(category_id):
    import urllib.request
    sys.path.insert(0, str(TOOLS))
    from conferir_no_ml import UA, token
    tk = token()
    if not tk:
        raise OSError("sem acesso ao ML")
    req = urllib.request.Request(f"https://api.mercadolibre.com/categories/{category_id}/attributes",
                                 headers={"Authorization": "Bearer " + tk, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def visiveis(atributos, modo):
    fora = A_ESTEIRA_POE | SISTEMA | (DA_VARIACAO if modo == "variacoes" else set())
    out = []
    for a in atributos or []:
        tags = a.get("tags") or {}
        if a.get("id") in fora or any(tags.get(t) for t in ESCONDIDO):
            continue
        c = {"id": a["id"], "nome": a.get("name"), "tipo": a.get("value_type"),
             "values": [v.get("name") for v in a.get("values") or [] if v.get("name")]}
        if tags.get("hidden"):
            c["oculto"] = True
        out.append(c)
    return out


def buscar_campos(lote, ler=_ler_api):
    """Grava campos-{pai}.json para cada produto do lote. Devolve os pais que falharam."""
    lote = Path(lote)
    try:
        cats = (yaml.safe_load((lote / "categorizacao" / "categorias.yaml").read_text(encoding="utf-8")) or {}).get("categorias") or []
    except Exception:  # noqa: BLE001
        return ["(lista de categorias)"]
    falhou = []
    for c in cats:
        if not CATEGORIA_OK.match(str(c.get("category_id") or "")) or not PAI_OK.match(str(c.get("pai_sku") or "")):
            falhou.append(c.get("pai_sku"))
            continue
        try:
            lista = visiveis(ler(c["category_id"]), c.get("modo"))
        except Exception:  # noqa: BLE001
            falhou.append(c.get("pai_sku"))
            continue
        (lote / "categorizacao" / f"campos-{c['pai_sku']}.json").write_text(
            json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")
    return falhou
