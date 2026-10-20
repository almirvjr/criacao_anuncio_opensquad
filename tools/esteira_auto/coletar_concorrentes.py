"""Coleta dos concorrentes do ML para a pesquisa (Helena), sem raspar pagina com navegador escondido (19/10/2026).

Por que: o navegador escondido e a API sem chave sao barrados pelo ML (lote da boleira, 09/10: caiu para a
Amazon, 32 opinioes, confianca baixa). Teste em `projects/rea_base/desenho/_teste_pesquisa_boleira/_RESULTADO.md`.

Caminho misto:
- API com o acesso da loja (o Claude sem conversa nao tem o acesso; quem roda e o maestro): ficha do MESMO
  produto no catalogo pelo codigo de barras, mais vendidos da categoria, busca de fichas, quem vende cada ficha
  e por quanto, atributos, descricao e perguntas.
- Opinioes: a API nao entrega de concorrente (403). Vem de um Chrome de verdade com perfil proprio
  (`_opensquad/_perfil_opinioes`), pela mesma lista que a janela "Mostrar todas as opinioes" do ML pede.

Grava `inteligencia/_coleta/coleta-{pai}.json` no lote. So le; nao mexe em anuncio. Falha de rede ou do Chrome
so anota (a Helena cai no caminho antigo). Nao guarda dado de pessoa: opiniao do ML ja vem sem autor; da
pergunta fica so texto, resposta e data."""
import json
import re
import sys
import urllib.parse
from pathlib import Path

import yaml

TOOLS = Path(__file__).resolve().parents[1]
RAIZ = TOOLS.parent
PERFIL = RAIZ / "_opensquad" / "_perfil_opinioes"
PORTA = 9336
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
# o que vem do ML ou do Claude so vira endereco se tiver o formato esperado
FICHA_OK = re.compile(r"^MLB\d+$")
CATEGORIA_OK = re.compile(r"^MLB\d+$")
PAI_OK = re.compile(r"^[A-Za-z0-9_-]+$")
EAN_OK = re.compile(r"^\d{8,14}$")
MAX_PERGUNTAS = 50
# por concorrente: as mais relevantes (o ML poe as boas na frente) + as ruins e medias, que mostram o medo do
# comprador (parametro `rating` da lista, achado em 19/10). Sem repetir opiniao.
COTAS = [({}, 90), ({"rating": "1"}, 30), ({"rating": "2"}, 30), ({"rating": "3"}, 30)]


def _api_real(caminho):
    import urllib.error
    import urllib.request
    sys.path.insert(0, str(TOOLS))
    from conferir_no_ml import UA, token
    if not hasattr(_api_real, "tk"):
        _api_real.tk = token()
    if not _api_real.tk:
        raise OSError("sem acesso ao ML")
    req = urllib.request.Request("https://api.mercadolibre.com" + caminho,
                                 headers={"Authorization": "Bearer " + _api_real.tk, "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError:
        return None


def _sem_acento(s):
    import unicodedata
    return "".join(ch for ch in unicodedata.normalize("NFD", str(s or "").lower()) if unicodedata.category(ch) != "Mn")


def escolher(mesma, candidatos, termo, limite=3):
    """Mesmo produto (se houver) + ate `limite` concorrentes.
    Candidato = {id, nome, vendedores, mais_vendido}. So entra quem tem no nome a 1a palavra do termo (o tipo do
    produto: na boleira, 19/10, os mais vendidos da categoria traziam um suporte de fotografia). Ordem: mais
    vendido da categoria primeiro, depois quem tem mais vendedores (ficha sem vendedor nao tem opiniao)."""
    out, vistos = [], set()
    chave = (_sem_acento(termo).split() or [""])[0]
    if mesma and FICHA_OK.match(str(mesma.get("id") or "")):
        vistos.add(mesma["id"])
        out.append({"id": mesma["id"], "origem": "mesmo_produto"})
    bons = [c for c in candidatos or [] if FICHA_OK.match(str(c.get("id") or "")) and c["id"] not in vistos
            and (c.get("vendedores") or 0) > 0 and chave and chave in _sem_acento(c.get("nome")).split()]
    bons.sort(key=lambda c: (not c.get("mais_vendido"), -(c.get("vendedores") or 0)))
    for c in bons:
        if c["id"] not in vistos and len(out) - (1 if mesma else 0) < limite:
            vistos.add(c["id"])
            out.append({"id": c["id"], "origem": "mais_vendidos" if c.get("mais_vendido") else "busca"})
    return out


def termo_busca(nome, palavras=4):
    """Nome do Tiny vira busca: so palavras (sem medida, numero, simbolo), minusculas, as primeiras N.
    'BOLEIRA PRATO COM CÚPULA BRISA Ø26,5 cm' deu 0 fichas; 'boleira prato com cúpula' acha."""
    so = [p for p in re.findall(r"[^\W\d_]+", str(nome or "").lower()) if len(p) > 1 and p not in {"cm", "mm", "ml", "kg", "un"}]
    return " ".join(so[:palavras])


def limpar_opiniao(r):
    texto = (((r or {}).get("comment") or {}).get("content") or {}).get("text")
    if not texto:
        return None
    return {"id": r.get("id"), "nota": r.get("rating"), "texto": texto, "quando": (r.get("comment") or {}).get("date")}


def por_nota(ops):
    out = {str(n): 0 for n in range(1, 6)}
    for o in ops:
        if str(o.get("nota")) in out:
            out[str(o["nota"])] += 1
    return out


def _ficha(api, cid):
    p = api(f"/products/{cid}") or {}
    vend = (api(f"/products/{cid}/items") or {}).get("results") or []
    precos = sorted(v.get("price") for v in vend if isinstance(v.get("price"), (int, float)))
    item = next((v.get("item_id") for v in vend if v.get("item_id")), None)
    desc = (api(f"/items/{item}/description") or {}).get("plain_text") if item else None
    perguntas = []
    for v in vend[:3]:
        if len(perguntas) >= MAX_PERGUNTAS or not v.get("item_id"):
            continue
        q = api(f"/questions/search?item={v['item_id']}&api_version=4&limit=50") or {}
        perguntas += [{"pergunta": x.get("text"), "resposta": (x.get("answer") or {}).get("text"), "data": x.get("date_created")}
                      for x in q.get("questions") or [] if x.get("text")]
    return {
        "nome": p.get("name"),
        "pagina": f"https://www.mercadolivre.com.br/p/{cid}",
        "atributos": [{"id": a.get("id"), "nome": a.get("name"), "valor": a.get("value_name")}
                      for a in p.get("attributes") or [] if a.get("value_name")],
        "destaques": [f.get("text") for f in p.get("main_features") or [] if f.get("text")],
        "fotos": len(p.get("pictures") or []),
        "vendedores": len(vend),
        "preco_min": precos[0] if precos else None,
        "preco_mediano": precos[len(precos) // 2] if precos else None,
        "descricao": desc,
        "perguntas": perguntas[:MAX_PERGUNTAS],
    }


def _opinioes_chrome(ids):
    """{ficha: {"media_texto", "lidas": [...]}} abrindo cada ficha num Chrome de verdade (perfil proprio)."""
    import subprocess
    import time
    from playwright.sync_api import sync_playwright
    PERFIL.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen([CHROME, f"--remote-debugging-port={PORTA}", "--remote-debugging-address=127.0.0.1",
                             f"--user-data-dir={PERFIL}", "--no-first-run", "--window-size=1300,900", "about:blank"])
    out = {}
    try:
        time.sleep(4)
        with sync_playwright() as pw:
            nav = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{PORTA}")
            pg = nav.contexts[0].new_page()
            for cid in ids:
                lista = {}

                def pegar(r, lista=lista):
                    if "/noindex/catalog/reviews/" in r.url and r.url.split("?")[0].endswith("/search") and "url" not in lista:
                        lista["url"] = r.url
                pg.on("response", pegar)
                try:
                    pg.goto(f"https://www.mercadolivre.com.br/p/{cid}", wait_until="domcontentloaded", timeout=60000)
                    pg.wait_for_timeout(3000)
                    pg.mouse.wheel(0, 6000)
                    pg.wait_for_timeout(2500)
                    resumo = pg.evaluate("() => (document.querySelector(\"[class*='ui-review-capability__rating']\")||{}).innerText||''")
                    pg.get_by_text("Mostrar todas as opiniões").first.click(timeout=10000)
                    pg.wait_for_timeout(4000)
                    fr = next(f for f in pg.frames if "/noindex/catalog/reviews/" in f.url)
                    for _ in range(4):  # rolar a janela faz a pagina pedir a lista; dela se tira o endereco
                        if "url" in lista:
                            break
                        fr.evaluate("() => { const e=[...document.querySelectorAll('*')].find(x=>x.scrollHeight>x.clientHeight+50 && getComputedStyle(x).overflowY!='visible'); (e||document.scrollingElement).scrollTop += 4000; }")
                        pg.wait_for_timeout(1500)
                    lidas, vistas = [], set()
                    if "url" in lista:
                        partes = urllib.parse.urlsplit(lista["url"])
                        base_q = dict(urllib.parse.parse_qsl(partes.query))
                        for extra, cota in COTAS:
                            offset, pegas = 0, 0
                            while pegas < cota:
                                q = {**base_q, **extra, "offset": str(offset), "limit": "15"}
                                u = urllib.parse.urlunsplit((partes.scheme, partes.netloc, partes.path, urllib.parse.urlencode(q), ""))
                                d = fr.evaluate("async (u) => { const r = await fetch(u, {credentials: 'include'}); return r.ok ? await r.json() : null; }", u)
                                brutas = (d or {}).get("reviews") or []
                                if not brutas:
                                    break
                                for o in (limpar_opiniao(x) for x in brutas):
                                    if o and o["id"] not in vistas and pegas < cota:
                                        vistas.add(o["id"])
                                        lidas.append(o)
                                        pegas += 1
                                offset += len(brutas)
                                pg.wait_for_timeout(700)
                    out[cid] = {"media_texto": " ".join(resumo.split())[:200], "lidas": lidas}
                except Exception as e:  # noqa: BLE001
                    out[cid] = {"erro": type(e).__name__, "lidas": []}
                pg.remove_listener("response", pegar)
            pg.close()
    finally:
        proc.terminate()
    return out


def coletar(lote, api=_api_real, opinioes=_opinioes_chrome):
    """Grava coleta-{pai}.json para cada produto do lote. Devolve os pais que falharam."""
    lote = Path(lote)
    try:
        cats = (yaml.safe_load((lote / "categorizacao" / "categorias.yaml").read_text(encoding="utf-8")) or {}).get("categorias") or []
        entrada = json.loads((lote / "anuncios-entrada.json").read_text(encoding="utf-8")).get("anuncios") or []
    except Exception:  # noqa: BLE001
        return ["(categorias ou entrada do lote)"]
    por_pai = {a.get("pai_sku"): a for a in entrada}
    falhou = []
    for c in cats:
        pai, cat = str(c.get("pai_sku") or ""), str(c.get("category_id") or "")
        if not PAI_OK.match(pai) or not CATEGORIA_OK.match(cat):
            falhou.append(pai or "(sem nome)")
            continue
        a = por_pai.get(pai) or {}
        eans = [str(v.get("ean") or "") for v in a.get("variacoes") or []]
        ean = next((e for e in eans if EAN_OK.match(e)), None)
        try:
            mesma = None
            if ean:
                r = (api(f"/products/search?status=active&site_id=MLB&product_identifier={ean}") or {}).get("results") or []
                mesma = r[0] if r else None
            destaques = (api(f"/highlights/MLB/category/{cat}") or {}).get("content") or []
            termo = termo_busca(a.get("nome_base"))
            busca = ((api(f"/products/search?status=active&site_id=MLB&q={urllib.parse.quote(termo)}") or {}).get("results") or []) if termo else []
            candidatos, ja = [], set()
            for c, mv in [(x, True) for x in destaques if x.get("type", "PRODUCT") == "PRODUCT"][:10] + [(x, False) for x in busca[:10]]:
                cid = str(c.get("id") or "")
                if not FICHA_OK.match(cid) or cid in ja:
                    continue
                ja.add(cid)
                nome = c.get("name") or (api(f"/products/{cid}") or {}).get("name")
                vend = len((api(f"/products/{cid}/items") or {}).get("results") or [])
                candidatos.append({"id": cid, "nome": nome, "vendedores": vend, "mais_vendido": mv})
            escolhidos = escolher(mesma, candidatos, termo)
            concorrentes = [{**e, **_ficha(api, e["id"])} for e in escolhidos]
        except Exception:  # noqa: BLE001
            falhou.append(pai)
            continue
        try:
            ops = opinioes([e["id"] for e in concorrentes])
            status = "ok"
        except Exception as e:  # noqa: BLE001
            ops, status = {}, f"falhou: {type(e).__name__} (a Helena usa o caminho antigo para as opinioes)"
        for k in concorrentes:
            o = ops.get(k["id"]) or {}
            lidas = o.get("lidas") or []
            k["opinioes"] = {"media_texto": o.get("media_texto"), "lidas": len(lidas), "por_nota": por_nota(lidas),
                             "erro": o.get("erro"), "itens": lidas}
        saida = {
            "pai_sku": pai, "category_id": cat, "ean": ean,
            "mesmo_produto": ({"id": mesma.get("id"), "nome": mesma.get("name")} if mesma else None),
            "opinioes_status": status,
            "resumo": {"concorrentes": len(concorrentes),
                       "opinioes": sum(k["opinioes"]["lidas"] for k in concorrentes),
                       "perguntas": sum(len(k["perguntas"]) for k in concorrentes),
                       "atributos_mesmo_produto": len(concorrentes[0]["atributos"]) if mesma and concorrentes else 0},
            "concorrentes": concorrentes,
        }
        pasta = lote / "inteligencia" / "_coleta"
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / f"coleta-{pai}.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
        # cada concorrente tambem no _raw: e onde a trava (validar_brief) confere que a opiniao citada existe
        raw = lote / "inteligencia" / "_raw"
        raw.mkdir(parents=True, exist_ok=True)
        for k in concorrentes:
            (raw / f"{k['id']}.json").write_text(json.dumps(k, ensure_ascii=False, indent=1), encoding="utf-8")
    return falhou


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    f = coletar(sys.argv[1])
    print("falhou: " + ", ".join(f) if f else "coleta pronta")
