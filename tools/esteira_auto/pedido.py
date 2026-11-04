"""Lote que veio da fila do hub: a entrada sai da leitura do Olist que o hub guardou no pedido (no lugar da
planilha exportada) e, no fim, o resultado vai para o banco (no lugar da tela; aprovar e publicar e no site).
Mesmo formato de anuncios-entrada.json do caminho da planilha (normalizer + cubagem), entao as etapas nao mudam.
Preco do Olist nunca entra (o R$ 10 e so para nao ficar zerado)."""
import json
import os
import re
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
import sys  # noqa: E402
sys.path.insert(0, str(RAIZ / "tools"))
from esteira.normalizer import normalize  # noqa: E402
import tiny_to_esteira as tte  # noqa: E402
from esteira_auto import precheck  # noqa: E402
from esteira_auto import precos as precos_mod  # noqa: E402
from esteira_auto import variacoes as variacoes_mod  # noqa: E402
from esteira_auto.travas import PENDENTE_MAGALU, pendentes_magalu  # noqa: E402


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
    # grade do Olist de cada SKU (cor, tamanho...) e por onde a familia varia (hub, 25/10/2026): variacao que nao e
    # de cor pede titulo do ML por variacao e o campo de variacao certo no Magalu
    grades = {f.get("sku"): dict(f.get("grade") or {}) for f in (pedido.get("olist") or {}).get("variacoes") or []}
    # kit cujos itens TODOS tem ficha aprovada no hub (mig 231, Almir 26/10/2026): medidas, capacidade, material e
    # titulo de cada item vem de la. Sem as fotos dos itens.
    kits = {k.get("sku_kit"): k.get("itens") for k in pedido.get("itens_kit") or [] if k.get("completo") and k.get("itens")}
    for a in out["anuncios"]:
        for v in a.get("variacoes") or []:
            v["grade"] = grades.get(v.get("sku"), {})
            if v.get("sku") in kits:
                v["itens_kit"] = kits[v["sku"]]
        a["eixo_variacao"] = variacoes_mod.eixo([v["grade"] for v in a.get("variacoes") or []])
        a["preco_provisorio"] = False
        a["decisoes_almir"] = decisoes
        # regra da marca (hub, Almir 02/11/2026): null, ou {"marca": "Terra Casa Decor", "motivo", "proibidas": [...]}
        a["marca_regra"] = pedido.get("marca_regra")
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


LIMITE_RESULTADO = 512 * 1024  # esteira.gravar_resultado recusa acima disso
_URL = re.compile(r"https?://\S+")


def _txt(v, teto=1000):
    """So texto, sem endereco (permalink de concorrente nao vai para o hub)."""
    if isinstance(v, dict):
        v = v.get("texto") or v.get("frase") or v.get("campo") or v.get("descricao") or ""
    t = " ".join(_URL.sub("", str(v or "")).split())
    return t[:teto]


def _lista(xs, teto=20):
    return [t for t in (_txt(x) for x in (xs or [])[:teto] if x is not None) if t] if isinstance(xs, list) else []


def brief_resumo(lote, pai):
    """Diagnostico do brief (inteligencia/brief-<pai>.yaml) para o hub montar o resumo do ChatGPT (peca 5, 04/11/2026).
    Sem evidencias nem enderecos de concorrente. Sem brief = None."""
    b = _yaml(Path(lote) / "inteligencia" / f"brief-{pai}.yaml")
    if not isinstance(b, dict):
        return None
    dg = b.get("diagnostico") if isinstance(b.get("diagnostico"), dict) else {}
    ans = []
    for x in (dg.get("ansiedades") or [])[:20]:
        if isinstance(x, dict):
            # o step-04 ja chamou a resposta de resposta_na_copy, como_responder e como_combater
            resp = x.get("resposta_na_copy") or x.get("como_responder") or x.get("como_combater")
            ans.append({"texto": _txt(x.get("texto")), "resposta_na_copy": _txt(resp) or None})
        elif x:
            ans.append({"texto": _txt(x), "resposta_na_copy": None})
    escada = [{k: _txt(x.get(k)) for k in ("feature", "logico", "emocional")}
              for x in (b.get("escada_e_dai") or [])[:20] if isinstance(x, dict)]
    return {"diagnostico": {"dor_interna_mais_forte": _txt(dg.get("dor_interna_mais_forte")) or None,
                            "only_factor": _txt(dg.get("only_factor")) or None,
                            "ansiedades": ans,
                            "linguagem_real_cliente": _lista(dg.get("linguagem_real_cliente"), 40),
                            "persona": _txt(dg.get("persona")) or None},
            "escada_e_dai": escada,
            "limitacoes": _lista(b.get("limitacoes")),
            "limitacoes_pesquisa": _lista(b.get("limitacoes_pesquisa")),
            "pendencias": _lista(b.get("pendencias"))}


SEM_OPINIOES = "sem opiniões de concorrentes: o texto saiu sem a linguagem real do comprador (peça de novo mais tarde se quiser)"


def _avisar_sem_opinioes(brief):
    """Produto que seguiu sem as opinioes dos concorrentes: o aviso vai nas pendencias do brief para o Almir ver no hub,
    mesmo que o brief tenha esquecido de declarar (a trava ja reprova isso; aqui e a garantia)."""
    brief = dict(brief or {})
    pend = list(brief.get("pendencias") or [])
    if not any("sem opini" in str(x).casefold() for x in pend):
        pend.insert(0, SEM_OPINIOES)
    brief["pendencias"] = pend
    brief.setdefault("limitacoes_pesquisa", [])
    return brief


def _marcar_pendentes(ficha, pendentes):
    """{categoria_id, campos: [{nome, valor|motivo}]}: obrigatorio sem valor em nivel nenhum sai com o motivo
    "PENDENTE: ..." (o hub mostra em vermelho e nao aprova o Magalu com ele vazio). Campo que nem veio entra."""
    if not pendentes:
        return ficha
    norm = lambda v: " ".join(str(v or "").split()).casefold()
    campos = [dict(x) for x in ficha.get("campos") or [] if isinstance(x, dict)]
    for nome in pendentes:
        x = next((c for c in campos if norm(c.get("nome")) == norm(nome)), None)
        if x is None:
            campos.append({"nome": nome, "motivo": PENDENTE_MAGALU})
            continue
        antes = str(x.get("motivo") or "").strip()
        x.pop("valor", None)
        if not antes.startswith("PENDENTE:"):
            x["motivo"] = PENDENTE_MAGALU + (f" ({antes})" if antes else "")
    return {**ficha, "campos": campos}


def resultado(lote, ler_precos=precos_mod.ler_para_lote):
    """O que a esteira produziu, por produto (cru; o hub espalha para a ficha mestra). Preco do Olist nunca;
    `precos` = proposta da planilha de precificacao do hub por canal e SKU (o Almir confere na aprovacao)."""
    lote = Path(lote)
    tabela = ler_precos(lote)
    d = json.loads((lote / "andamento.json").read_text(encoding="utf-8"))
    sem_opinioes = set(d.get("sem_opinioes") or [])
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
            canais["magalu"] = _marcar_pendentes(anuncio.pop("ficha_magalu"), pendentes_magalu(lote, pai))
        cat = cats.get(pai)
        lista = lote / "categorizacao" / f"campos-{pai}.json"
        if cat is not None and lista.is_file():  # campos da categoria do ML (com os ocultos) para a tela do hub
            cat = {**cat, "campos": [{"id": c.get("id"), "nome": c.get("nome"), "oculto": bool(c.get("oculto")),
                                      "variacao": bool(c.get("variacao"))}
                                     for c in json.loads(lista.read_text(encoding="utf-8"))]}
        brief = brief_resumo(lote, pai)
        if pai in sem_opinioes:
            brief = _avisar_sem_opinioes(brief)
        produtos.append({"pai_sku": pai, "categoria": cat, "anuncio": anuncio, "canais": canais,
                         **({"brief": brief} if brief is not None else {}),
                         "parecer": _yaml(lote / "revisao" / f"parecer-{pai}.yaml"),
                         "capas": _yaml(lote / "capas" / f"capas-{pai}.yaml"),
                         "precos": precos_mod.do_produto(tabela, [v.get("sku") for v in a.get("variacoes", [])]),
                         # o que a publicacao do hub precisa e so existe aqui: caixa ja com a cubagem (maior entre as
                         # cores) e cada cor com o codigo de barras
                         "pacote": {"peso_bruto_kg": a.get("peso_bruto_kg"), "dim_embalagem_cm": a.get("dim_embalagem_cm")},
                         "variacoes": [{"sku": v.get("sku"), "cor": v.get("cor"), "ean": v.get("ean")}
                                       for v in a.get("variacoes", [])]})
    out = {"lote": lote.name, "produtos": produtos, "parados": d.get("parados", {})}
    if len(json.dumps(out, ensure_ascii=False).encode("utf-8")) > LIMITE_RESULTADO:
        for pr in produtos:  # o brief e o que sobra: nunca deixar ele derrubar a entrega
            pr.pop("brief", None)  # o aviso do "sem opinioes" segue no caderno espelhado no hub
    return out
