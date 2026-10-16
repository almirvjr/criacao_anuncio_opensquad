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
        elif etapa == "revisao":
            if not (lote / "revisao" / f"parecer-{p}.yaml").is_file():
                ruins[p] = "a revisao deste produto nao foi gravada"
    return ruins
