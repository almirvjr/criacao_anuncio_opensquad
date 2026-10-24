"""Lote que veio da fila do hub: a entrada sai da leitura do Olist que o hub guardou no pedido (no lugar da
planilha exportada) e, no fim, o resultado vai para o banco (no lugar da tela; aprovar e publicar e no site).
Mesmo formato de anuncios-entrada.json do caminho da planilha (normalizer + cubagem), entao as etapas nao mudam.
Preco do Olist nunca entra (o R$ 10 e so para nao ficar zerado)."""
import json
import os
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
import sys  # noqa: E402
sys.path.insert(0, str(RAIZ / "tools"))
from esteira.normalizer import normalize  # noqa: E402
import tiny_to_esteira as tte  # noqa: E402
from esteira_auto import precheck  # noqa: E402
from esteira_auto import precos as precos_mod  # noqa: E402


def _cor(grade):
    """{"cor": "Azul", ...} -> "Cor:Azul" (o formato da coluna Variacoes da planilha)."""
    if not grade:
        return None
    k = "cor" if "cor" in grade else next(iter(grade))
    return f"{k.capitalize()}:{grade[k]}"


def _registro(f, cod_pai=None, grade=None):
    return {"sku": f.get("sku"), "nome": f.get("descricao"), "preco_venda": None, "preco_custo": None,
            "ean": f.get("gtin"), "descricao_complementar": f.get("descricao_complementar"),
            "cod_pai": cod_pai, "variacoes_raw": _cor(grade), "tipo": None, "marca": f.get("marca"),
            "fornecedor": f.get("fornecedor"), "peso_bruto": f.get("peso_bruto_kg"),
            "dim_cm": dict(f.get("dim_embalagem_cm") or {}), "fotos": list(f.get("fotos") or [])}


def registros(pedido):
    """Leitura do Olist (pedido['olist']) -> linhas no formato que o tiny_to_esteira tira da planilha."""
    lido = pedido.get("olist") or {}
    pai, filhos = lido.get("pai") or {}, lido.get("variacoes") or []
    if not pai.get("sku") or not filhos:
        raise ValueError("o pedido veio sem a leitura do Olist")
    if not pedido["produto"].get("com_variacao"):
        return [_registro(filhos[0])]
    return [_registro(pai)] + [_registro(f, cod_pai=pai["sku"], grade=f.get("grade")) for f in filhos]


def montar_entrada(lote, cubagem=precheck.CUBAGEM, ler_cubagem=tte.carregar_cubagem):
    """Escreve anuncios-entrada.json do lote. Devolve a lista de problemas que param o lote (vazia = segue)."""
    pedido = json.loads((Path(lote) / "pedido.json").read_text(encoding="utf-8"))
    try:
        recs = registros(pedido)
    except ValueError as e:
        return [str(e)]
    try:
        tte.aplicar_cubagem(recs, ler_cubagem(cubagem))
    except Exception:  # noqa: BLE001
        return ["nao consegui abrir a planilha de cubagem (peso e medida) no Drive"]
    out = normalize(recs)
    # Decisoes do Almir gravadas no hub (ficha tecnica manual ou conferida) valem sobre qualquer fonte [P27]
    decisoes = [{"campo": d.get("atributo_ml") or d.get("atributo"), "valor": d.get("valor"), "sku": d.get("sku")}
                for d in pedido.get("decisoes") or []]
    # Recado do Almir ao pedir ("Refazer do zero" no app: o que estava errado) vale para todas as etapas
    recado = str(pedido.get("recado") or "").strip()
    # Magalu (hub, 24/10/2026): categorias candidatas que o hub achou no Magalu (com TODOS os campos de cada uma) e as
    # decisoes do Almir nesses campos. A etapa do texto escolhe a categoria e responde todos os campos (ficha_magalu).
    magalu = None
    if "magalu" in (pedido.get("canais") or []):
        lido = pedido.get("magalu") or {}
        magalu = {"candidatas": lido.get("candidatas") or [], "fixa": bool(lido.get("fixa")),
                  "decisoes": pedido.get("decisoes_magalu") or []}
    for a in out["anuncios"]:
        a["preco_provisorio"] = False
        a["decisoes_almir"] = decisoes
        a["recado_almir"] = recado
        if magalu is not None:
            a["magalu"] = magalu
    out["origem"] = f"pedido {pedido['pedido_id']} do hub"
    saida = Path(lote) / "anuncios-entrada.json"
    tmp = saida.with_name(saida.name + ".novo")
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, saida)
    if not out.get("anuncios"):
        return ["a leitura do Olist nao tem nenhum produto"]
    return precheck.faltas_de_caixa(out)


def _yaml(p):
    p = Path(p)
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}) if p.is_file() else None


def resultado(lote, ler_precos=precos_mod.ler_para_lote):
    """O que a esteira produziu, por produto (cru; o hub espalha para a ficha mestra). Preco do Olist nunca;
    `precos` = proposta da planilha de precificacao do hub por canal e SKU (o Almir confere na aprovacao)."""
    lote = Path(lote)
    tabela = ler_precos(lote)
    d = json.loads((lote / "andamento.json").read_text(encoding="utf-8"))
    entrada = json.loads((lote / "anuncios-entrada.json").read_text(encoding="utf-8"))
    cats = {c.get("pai_sku"): c for c in (_yaml(lote / "categorizacao" / "categorias.yaml") or {}).get("categorias", [])}
    produtos = []
    for a in entrada.get("anuncios", []):
        pai = a["pai_sku"]
        if pai in d.get("parados", {}):
            continue
        anuncio = _yaml(lote / "copywriting" / f"anuncio-{pai}.yaml") or {}
        anuncio.pop("preco", None)
        canais = {}
        if a.get("magalu") is not None and isinstance(anuncio.get("ficha_magalu"), dict):
            canais["magalu"] = anuncio.pop("ficha_magalu")  # {categoria_id, campos: [{nome, valor|motivo}]}
        produtos.append({"pai_sku": pai, "categoria": cats.get(pai), "anuncio": anuncio, "canais": canais,
                         "parecer": _yaml(lote / "revisao" / f"parecer-{pai}.yaml"),
                         "capas": _yaml(lote / "capas" / f"capas-{pai}.yaml"),
                         "precos": precos_mod.do_produto(tabela, [v.get("sku") for v in a.get("variacoes", [])]),
                         # o que a publicacao do hub precisa e so existe aqui: caixa ja com a cubagem (maior entre as
                         # cores) e cada cor com o codigo de barras
                         "pacote": {"peso_bruto_kg": a.get("peso_bruto_kg"), "dim_embalagem_cm": a.get("dim_embalagem_cm")},
                         "variacoes": [{"sku": v.get("sku"), "cor": v.get("cor"), "ean": v.get("ean")}
                                       for v in a.get("variacoes", [])]})
    return {"lote": lote.name, "produtos": produtos, "parados": d.get("parados", {})}
