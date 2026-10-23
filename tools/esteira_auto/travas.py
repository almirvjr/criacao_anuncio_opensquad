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
                motivo = _titulos_longos(anuncio) or _decisoes_almir(lote, p, anuncio, campos)
                if motivo:
                    ruins[p] = motivo
        elif etapa == "revisao":
            if not (lote / "revisao" / f"parecer-{p}.yaml").is_file():
                ruins[p] = "a revisao deste produto nao foi gravada"
    return ruins
