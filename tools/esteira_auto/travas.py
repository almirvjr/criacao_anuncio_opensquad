"""Conferencia depois de cada etapa, por anuncio. Devolve so os reprovados: {pai: motivo}."""
import json
import subprocess
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
VAL = RAIZ / "squads" / "ml-anuncios" / "pipeline" / "validators"


def _py(script, *args, rodar):
    r = rodar([sys.executable, str(VAL / script), *map(str, args)], capture_output=True, text=True,
              encoding="utf-8", errors="replace", cwd=str(RAIZ))
    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()[-800:]


def _titulos_longos(anuncio):
    """Titulos de 85-100 letras para os outros canais (hub, Fase 1; teto 100 = Magalu, Portal 23/10/2026). Conta o texto, nunca o `length` declarado."""
    if not anuncio.is_file():
        return None  # sem o arquivo as outras travas ja reprovam
    a = yaml.safe_load(anuncio.read_text(encoding="utf-8")) or {}
    if a.get("status_copy") in ("aprovado", "tirado"):
        return None
    longos = a.get("titulos_longos")
    if not isinstance(longos, list) or not longos:
        return "faltam os titulos longos (titulos_longos, 85-100 letras, para os outros canais)"
    if not 2 <= len(longos) <= 3:
        return f"titulos longos: sao {len(longos)}, tem que ser de 2 a 3"
    fora = [len(t.get("texto") or "") for t in longos if not 85 <= len(t.get("texto") or "") <= 100]
    if fora:
        return f"titulos longos com {', '.join(map(str, fora))} letras (tem que ser 85-100)"
    if sum(1 for t in longos if t.get("recomendado") is True) != 1:
        return "titulos longos: marque exatamente 1 como recomendado"
    return None


def _decisoes_almir(lote, pai, anuncio, campos):
    """Campo da ficha que o Almir decidiu no hub (decisoes_almir da entrada) tem o valor dele e nao fica pendente.
    So cobra campo da familia (sem sku) que existe na categoria ou que o texto preencheu."""
    entrada = lote / "anuncios-entrada.json"
    if not (anuncio.is_file() and entrada.is_file()):
        return None
    ent = json.loads(entrada.read_text(encoding="utf-8"))
    decisoes = next((x.get("decisoes_almir") or [] for x in ent.get("anuncios", []) if x.get("pai_sku") == pai), [])
    if not decisoes:
        return None
    a = yaml.safe_load(anuncio.read_text(encoding="utf-8")) or {}
    if a.get("status_copy") in ("aprovado", "tirado"):
        return None
    attrs = a.get("attributes") or {}
    pendentes = set(a.get("campos_pendentes") or [])
    na_categoria = {c.get("id") for c in json.loads(campos.read_text(encoding="utf-8"))} if campos.is_file() else set()
    norm = lambda v: str(v).strip().casefold()
    erros = []
    for d in decisoes:
        k = d.get("campo")
        if d.get("sku") or not k or (k not in na_categoria and k not in attrs):
            continue
        if k in pendentes or norm(attrs.get(k, "")) != norm(d.get("valor")):
            erros.append(f"{k} = {d.get('valor')} (no texto: {attrs.get(k, 'pendente')})")
    if erros:
        return "ficha tecnica contra a decisao do Almir (decisoes_almir na entrada): " + "; ".join(erros)
    return None


ENCHIMENTO = {"n/a", "na", "-", "nenhum", "nao informado", "não informado", "sem informacao", "sem informação", "?"}


def _ficha_magalu(lote, pai, anuncio):
    """Magalu (hub, regra do Almir 24/10/2026): categoria = uma das candidatas que o hub leu no Magalu; TODO campo
    dela com `valor` real OU `motivo` de ficar em branco (nunca os dois, nunca nenhum); obrigatorio nunca em branco;
    decisao do Almir (magalu.decisoes da entrada) vale sobre tudo. Sem Magalu no pedido: nao cobra."""
    entrada = lote / "anuncios-entrada.json"
    if not (anuncio.is_file() and entrada.is_file()):
        return None
    ent = json.loads(entrada.read_text(encoding="utf-8"))
    mg = next((x.get("magalu") for x in ent.get("anuncios", []) if x.get("pai_sku") == pai), None)
    if not mg or not mg.get("candidatas"):
        return None
    a = yaml.safe_load(anuncio.read_text(encoding="utf-8")) or {}
    if a.get("status_copy") in ("aprovado", "tirado"):
        return None
    f = a.get("ficha_magalu")
    if not isinstance(f, dict):
        return "falta a ficha do Magalu (ficha_magalu: categoria_id + todos os campos da categoria escolhida)"
    cands = {str(c.get("id")): c for c in mg["candidatas"]}
    cat = cands.get(str(f.get("categoria_id")))
    if not cat:
        return "ficha_magalu: categoria_id tem que ser uma das candidatas (" + ", ".join(
            f"{c.get('nome')} = {i}" for i, c in cands.items()) + ")"
    norm = lambda v: " ".join(str(v or "").split()).casefold()
    dados, erros = {}, []
    for x in f.get("campos") or []:
        k = norm((x or {}).get("nome"))
        if k in dados:
            erros.append(f"{x.get('nome')}: repetido")
        dados[k] = x or {}
    da_categoria = {norm(c.get("nome")) for c in cat.get("campos") or []}
    for c in cat.get("campos") or []:
        x = dados.get(norm(c.get("nome")))
        valor, motivo = str((x or {}).get("valor") or "").strip(), str((x or {}).get("motivo") or "").strip()
        if x is None:
            erros.append(f"{c.get('nome')}: sem resposta")
        elif bool(valor) == bool(motivo):
            erros.append(f"{c.get('nome')}: precisa de valor OU de motivo (nunca os dois, nunca nenhum)")
        elif not valor and c.get("obrigatorio"):
            erros.append(f"{c.get('nome')}: obrigatorio no Magalu, nao pode ficar em branco")
        elif valor and norm(valor) in ENCHIMENTO:
            erros.append(f"{c.get('nome')}: valor de enchimento ({valor})")
    erros += [f"{x.get('nome')}: nao existe na categoria" for k, x in dados.items() if k not in da_categoria]
    for d in mg.get("decisoes") or []:
        if str(d.get("categoria_id")) != str(f.get("categoria_id")):
            continue
        x = dados.get(norm(d.get("campo"))) or {}
        if norm(x.get("valor")) != norm(d.get("valor")) or (not d.get("valor") and not x.get("motivo")):
            erros.append(f"{d.get('campo')}: contra a decisao do Almir ({d.get('valor') or 'em branco: ' + str(d.get('motivo'))})")
    if erros:
        return f"ficha do Magalu ({cat.get('nome')}): " + "; ".join(erros[:15]) + (f" (+{len(erros) - 15})" if len(erros) > 15 else "")
    return None


BUSCA = ("MODEL", "LINE", "MATERIAL", "MAIN_MATERIAL")  # campos que no ML levam palavra de busca (step-05, passo 5)


def _atributos_reais(anuncio):
    """Hub (Almir 23-24/10/2026): a ficha guarda a informacao real; a palavra de busca em Modelo/Linha/Material e so
    do ML. Todo campo desses preenchido em `attributes` tem o valor real em `atributos_reais` (ex.: Modelo
    "Cozy 10570", Material "Polipropileno"), mesmo quando igual."""
    if not anuncio.is_file():
        return None
    a = yaml.safe_load(anuncio.read_text(encoding="utf-8")) or {}
    if a.get("status_copy") in ("aprovado", "tirado"):
        return None
    attrs, reais = a.get("attributes") or {}, a.get("atributos_reais") or {}
    if not isinstance(reais, dict):
        return "atributos_reais tem que ser um bloco campo: valor real"
    norm = lambda v: " ".join(str(v or "").split()).casefold()
    erros = [f"{k}: so Modelo, Linha e Material levam valor real separado" for k in reais if k not in BUSCA]
    for k in BUSCA:
        v = norm(attrs.get(k))
        if not v or v in ("não se aplica", "nao se aplica"):
            continue
        r = norm(reais.get(k))
        if not r:
            erros.append(f"{k}: falta o valor real (atributos_reais)")
        elif r in ENCHIMENTO:
            erros.append(f"{k}: valor de enchimento no valor real ({reais.get(k)})")
    return ("valor real de Modelo/Linha/Material: " + "; ".join(erros)) if erros else None


def conferir(etapa, lote, pais, rodar=subprocess.run):
    lote = Path(lote)
    ruins = {}
    if etapa == "capas":
        busca = lote / "capas" / "_busca.json"
        if not busca.is_file():
            return {p: "a busca das capas no Cloudinary nao foi gravada" for p in pais}
        cod, saida = _py("capas.py", busca, lote / "anuncios-entrada.json", lote / "capas", rodar=rodar)
        if cod != 0:
            for p in pais:
                linhas = [l.strip(" -") for l in saida.splitlines() if l.strip(" -").startswith(p + ":")]
                if linhas:
                    ruins[p] = " | ".join(linhas)
            if not ruins:
                ruins = {p: saida or "a conferencia das capas falhou" for p in pais}
        return ruins
    if etapa == "curadoria":
        f = lote / "curadoria" / "dossies.json"
        tem = json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}
        achados = {d.get("pai_sku") or d.get("sku") for d in tem.get("dossies") or []}
        return {p: "o dossie deste produto nao foi gravado" for p in pais if p not in achados}
    if etapa == "categoria":
        f = lote / "categorizacao" / "categorias.yaml"
        cats = (yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("categorias") if f.is_file() else []
        ok = {c.get("pai_sku") for c in cats or [] if c.get("category_id")}
        return {p: "nao foi escolhida a categoria do ML" for p in pais if p not in ok}
    for p in pais:
        brief = lote / "inteligencia" / f"brief-{p}.yaml"
        anuncio = lote / "copywriting" / f"anuncio-{p}.yaml"
        if etapa == "pesquisa":
            cod, s = _py("validar_brief.py", brief, "--sem-fotos", rodar=rodar)
            if cod != 0:
                ruins[p] = s or "a pesquisa foi reprovada"
        elif etapa == "texto":
            campos = lote / "categorizacao" / f"campos-{p}.json"
            for script, args in (("validar_claims.py", (brief, "--copy", anuncio, "--sem-fotos")),
                                 ("validar_ficha_seo.py", (anuncio,)),
                                 ("validar_ficha_nsa.py", (anuncio, campos) if campos.is_file() else (anuncio,))):
                cod, s = _py(script, *args, rodar=rodar)
                if cod != 0:
                    ruins[p] = s or f"{script} reprovou"
                    break
            else:
                motivo = (_titulos_longos(anuncio) or _decisoes_almir(lote, p, anuncio, campos)
                          or _ficha_magalu(lote, p, anuncio) or _atributos_reais(anuncio))
                if motivo:
                    ruins[p] = motivo
        elif etapa == "revisao":
            if not (lote / "revisao" / f"parecer-{p}.yaml").is_file():
                ruins[p] = "a revisao deste produto nao foi gravada"
    return ruins
