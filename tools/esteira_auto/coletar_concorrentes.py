"""Coleta dos concorrentes do ML para a pesquisa (Helena), sem raspar pagina com navegador escondido (19/10/2026).

Por que: o navegador escondido e a API sem chave sao barrados pelo ML (lote da boleira, 09/10: caiu para a
Amazon, 32 opinioes, confianca baixa). Teste em `projects/rea_base/desenho/_teste_pesquisa_boleira/_RESULTADO.md`.

Caminho misto:
- API com o acesso da loja (o Claude sem conversa nao tem o acesso; quem roda e o maestro): ficha do MESMO
  produto no catalogo pelo codigo de barras, mais vendidos da categoria, busca de fichas, quem vende cada ficha
  e por quanto, atributos, descricao e perguntas.
- Opinioes: a API nao entrega de concorrente (403). Vem de um Chrome de verdade com perfil proprio
  (`_opensquad/_perfil_opinioes`), pela mesma lista que a janela "Mostrar todas as opinioes" do ML pede.

Grava `inteligencia/_coleta/coleta-{pai}.json` no lote. So le; nao mexe em anuncio. Falha de rede ou nenhuma
opiniao lida por falha do Chrome = pai devolvido em `falhou` (o maestro tenta de novo antes da pesquisa e, na 3a,
para o produto: sem opiniao o texto sai fraco, 22/10). Nao guarda dado de pessoa: opiniao do ML ja vem sem autor; da
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
LIMITE, RESERVA = 3, 3  # concorrentes que ficam; quantos a mais o Chrome abre para achar os que tem opiniao
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


# Grupos de material: concorrente de vidro nao ensina nada sobre prato de plastico (Prato Cozy, 22/10: vieram 3
# jogos de prato fundo de vidro porque o filtro era so a palavra "prato").
MATERIAIS = {"plastico": ("plastico", "polipropileno", "pp", "polietileno", "acrilico", "melamina", "policarbonato", "tritan"),
             "vidro": ("vidro", "opaline", "opalina", "opalino", "cristal", "borossilicato"),
             "descartavel": ("isopor", "descartavel", "papelao"),
             "ceramica": ("ceramica", "porcelana", "gres", "faianca", "stoneware"),
             "metal": ("inox", "aco", "metal", "aluminio", "ferro", "cobre"),
             "madeira": ("madeira", "bambu")}


def grupo_material(valor):
    palavras = _sem_acento(valor).replace("-", " ").split()
    palavras += [p[:-1] for p in palavras if p.endswith("s")]  # "Pratos Plásticos"
    return next((g for g, ps in MATERIAIS.items() if any(p in palavras for p in ps)), None)


def _atributos(x):
    """{ID: valor} da ficha do ML (a busca ja traz; o resto vem de /products/{id})."""
    return {a.get("id"): a.get("value_name") for a in (x or {}).get("attributes") or [] if a.get("id") and a.get("value_name")}


def perfil_de(atrs):
    """O que o concorrente precisa ter igual ao nosso: grupo do material e o 'tipo' da categoria (ex. prato Raso)."""
    return {"material": grupo_material(atrs.get("MATERIAL")),
            "tipos": {k: v for k, v in atrs.items() if k.endswith("_TYPE")},
            "unidades": atrs.get("UNITS_PER_PACK")}


def _raiz(v):
    return {p.rstrip("s") for p in _sem_acento(v).split()}


def parecenca(perfil, atrs, nome=None, exigir_material=False):
    """Quanto o concorrente se parece com o nosso produto; None = outro produto (material ou tipo diferente).
    Material vem da ficha ou, sem ela, do nome ("Prato Plástico ..."). Com `exigir_material`, material desconhecido
    tambem fica fora (Prato Cozy, 22/10: sem isso entraram um prato infantil e um descartavel de isopor)."""
    if not perfil:
        return 0
    pontos = 0
    mat = grupo_material(atrs.get("MATERIAL")) or grupo_material(nome)
    if perfil["material"]:
        if mat and mat != perfil["material"]:
            return None
        if not mat and exigir_material:
            return None
        pontos += 2 if mat else 0
    for k, v in perfil["tipos"].items():
        if atrs.get(k):
            if not _raiz(v) & _raiz(atrs[k]):
                return None
            pontos += 2
    if perfil["unidades"] and atrs.get("UNITS_PER_PACK") == perfil["unidades"]:
        pontos += 1
    return pontos


def escolher(mesma, candidatos, termo, limite=3, perfil=None, reserva=0):
    """Mesmo produto (se houver) + ate `limite` concorrentes (+ `reserva` a mais, para o Chrome ficar com os que
    tem opiniao). Candidato = {id, nome, vendedores, mais_vendido, atributos}.
    Sem `perfil` (mesmo produto fora do catalogo): o nome tem que ter a 1a palavra do termo e a ficha um vendedor
    (na boleira, 19/10, os mais vendidos traziam um suporte de fotografia).
    Com `perfil`: o nome tem que COMECAR pelo tipo ("Descanso de Prato" e "Kit 5 Prato" ficam fora) e o material
    tem que bater; ficha sem vendedor entra (no Prato Cozy, 22/10, quase todo prato de plastico do catalogo
    tinha 0 vendedor e a opiniao existe assim mesmo). Se o material conhecido nao fechar a conta, completa com
    quem so nao contradiz. Ordem: mais parecido, mais vendido da categoria, mais vendedores."""
    out, vistos = [], set()
    chave = (_sem_acento(termo).split() or [""])[0]
    if mesma and FICHA_OK.match(str(mesma.get("id") or "")):
        vistos.add(mesma["id"])
        out.append({"id": mesma["id"], "origem": "mesmo_produto"})
    validos = [c for c in candidatos or [] if FICHA_OK.match(str(c.get("id") or "")) and c["id"] not in vistos and chave]
    if perfil:
        validos = [c for c in validos if _sem_acento(c.get("nome")).split()[:1] == [chave]]
    else:
        validos = [c for c in validos if (c.get("vendedores") or 0) > 0 and chave in _sem_acento(c.get("nome")).split()]
    bons = []
    for exigir in ((True, False) if perfil else (False,)):
        nota = {c["id"]: parecenca(perfil, c.get("atributos") or {}, c.get("nome"), exigir) for c in validos}
        lista = sorted((c for c in validos if nota[c["id"]] is not None and c not in bons),
                       key=lambda c: (-nota[c["id"]], not c.get("mais_vendido"), -(c.get("vendedores") or 0)))
        bons += lista
        if len(bons) >= limite + reserva:
            break
    for c in bons:
        if c["id"] not in vistos and len(out) - (1 if mesma else 0) < limite + reserva:
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


def _ficha_da_busca(api, c):
    """Concorrente que veio da busca do Chrome. Ficha do catalogo (/p/) = ficha completa pela API; anuncio comum
    (MLB-123) = descricao e perguntas pela API (essas abrem para anuncio de terceiro); o resto, so titulo e pagina."""
    if "/p/" in c["url"] and FICHA_OK.match(c["id"]):
        f = _ficha(api, c["id"])
        return {**f, "nome": f.get("nome") or c["titulo"], "pagina": c["url"], "nota_na_busca": c.get("nota")}
    item = c["id"] if "/up/" not in c["url"] and FICHA_OK.match(c["id"]) else None
    q = (api(f"/questions/search?item={item}&api_version=4&limit=50") or {}) if item else {}
    return {"nome": c["titulo"], "pagina": c["url"], "nota_na_busca": c.get("nota"), "atributos": [], "destaques": [],
            "fotos": None, "vendedores": None, "preco_min": None, "preco_mediano": None,
            "descricao": (api(f"/items/{item}/description") or {}).get("plain_text") if item else None,
            "perguntas": [{"pergunta": x.get("text"), "resposta": (x.get("answer") or {}).get("text"), "data": x.get("date_created")}
                          for x in q.get("questions") or [] if x.get("text")][:MAX_PERGUNTAS]}


PAGINA_OK = re.compile(r"^https://(www|produto)\.mercadolivre\.com\.br/[^#?\s]+$")
ID_NA_PAGINA = re.compile(r"/(?:p|up)/(MLBU?\d+)|/(MLB)-(\d+)")


def _abrir_chrome():
    import subprocess
    import time
    PERFIL.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen([CHROME, f"--remote-debugging-port={PORTA}", "--remote-debugging-address=127.0.0.1",
                             f"--user-data-dir={PERFIL}", "--no-first-run", "--window-size=1300,900", "about:blank"])
    time.sleep(4)
    return proc


def id_da_pagina(url):
    """Endereco de anuncio/ficha do ML -> codigo (MLB123 da ficha, MLBU123 do produto do vendedor, MLB123 do anuncio)."""
    m = ID_NA_PAGINA.search(str(url or ""))
    return (m.group(1) or f"{m.group(2)}{m.group(3)}") if m else None


def _busca_chrome(termos):
    """Cartoes da busca do ML como o comprador ve (Chrome de verdade; a busca pela API da 403 e o catalogo da API
    so tem ficha sem venda e sem opiniao: Prato Cozy, 22/10). Anuncio pago (Ad) fica fora."""
    from playwright.sync_api import sync_playwright
    proc = _abrir_chrome()
    cartoes = []
    try:
        with sync_playwright() as pw:
            nav = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{PORTA}")
            pg = nav.contexts[0].new_page()
            for termo in termos:
                slug = "-".join(_sem_acento(termo).split())
                if not re.fullmatch(r"[a-z0-9-]+", slug):
                    continue
                try:
                    pg.goto(f"https://lista.mercadolivre.com.br/{slug}", wait_until="domcontentloaded", timeout=60000)
                    pg.wait_for_timeout(4000)
                    lidos = pg.evaluate(r"""() => [...document.querySelectorAll('li.ui-search-layout__item')].map(li => {
                        const a = [...li.querySelectorAll('a[href]')].map(x => x.href);
                        return {titulo: (li.querySelector('h3, .poly-component__title') || {}).innerText || '',
                                url: a.find(h => !h.includes('click1.')) || null, ad: a.some(h => h.includes('click1.')),
                                nota: (li.querySelector('.poly-component__review-compacted, [class*=reviews__rating]') || {}).innerText || '',
                                preco: (li.querySelector('.andes-money-amount__fraction') || {}).innerText || ''}; })""")
                except Exception:  # noqa: BLE001
                    continue
                for c in lidos:
                    url = str(c.get("url") or "").split("#")[0].split("?")[0]
                    if c.get("ad") or not PAGINA_OK.match(url) or not id_da_pagina(url):
                        continue
                    cartoes.append({"id": id_da_pagina(url), "url": url, "titulo": " ".join(c["titulo"].split()),
                                    "nota": c["nota"].strip(), "preco": c["preco"].strip(), "termo": termo})
            pg.close()
    finally:
        proc.terminate()
    return cartoes


def escolher_busca(cartoes, termo, perfil, ja, n):
    """Dos cartoes da busca: o tipo no titulo (palavra, plural vale), com nota (tem opiniao), sem contradizer o
    material. Mais parecido primeiro (material e tipo no titulo); empate = ordem do ML (relevancia/venda)."""
    chave = (_sem_acento(termo).split() or [""])[0].rstrip("s")
    tipos = set().union(*[_raiz(v) for v in (perfil or {}).get("tipos", {}).values()]) if perfil else set()
    mat_nosso = (perfil or {}).get("material")
    bons, vistos = [], set(ja)
    for pos, c in enumerate(cartoes):
        if c["id"] in vistos or not c.get("nota"):
            continue
        palavras = _raiz(c["titulo"])
        if not chave or chave not in palavras:
            continue
        mat = grupo_material(c["titulo"])
        if mat_nosso and mat and mat != mat_nosso:
            continue
        vistos.add(c["id"])
        pontos = (2 if mat_nosso and mat == mat_nosso else 0) + (2 if tipos & palavras else 0)
        bons.append((-pontos, pos, c))
    return [c for _, _, c in sorted(bons, key=lambda x: (x[0], x[1]))][:n]


def _opinioes_chrome(ids, paginas=None):
    """{ficha: {"media_texto", "lidas": [...]}} abrindo cada ficha num Chrome de verdade (perfil proprio).
    `paginas` = endereco de quem nao e ficha do catalogo (veio da busca)."""
    from playwright.sync_api import sync_playwright
    proc = _abrir_chrome()
    out = {}
    try:
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
                    url = (paginas or {}).get(cid) or f"https://www.mercadolivre.com.br/p/{cid}"
                    if not PAGINA_OK.match(url):
                        raise ValueError("endereco estranho")
                    pg.goto(url, wait_until="domcontentloaded", timeout=60000)
                    pg.wait_for_timeout(3000)
                    pg.mouse.wheel(0, 6000)
                    pg.wait_for_timeout(2500)
                    resumo = pg.evaluate("() => (document.querySelector(\"[class*='ui-review-capability__rating']\")||{}).innerText||''")
                    botao = pg.get_by_text("Mostrar todas as opiniões")
                    if not botao.count() and resumo.strip():
                        # ficha com poucas notas e nenhum comentario (o proprio Prato Cozy, 22/10): nao e falha.
                        # Sem o bloco de notas na pagina (nao carregou) segue para o clique, que falha como erro.
                        out[cid] = {"media_texto": " ".join(resumo.split())[:200], "lidas": [], "sem_comentarios": True}
                        pg.remove_listener("response", pegar)
                        continue
                    botao.first.click(timeout=10000)
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


def coletar(lote, api=_api_real, opinioes=_opinioes_chrome, buscar=_busca_chrome):
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
            perfil = None
            if mesma and FICHA_OK.match(str(mesma.get("id") or "")):
                perfil = perfil_de(_atributos(mesma) or _atributos(api(f"/products/{mesma['id']}")))
            destaques = (api(f"/highlights/MLB/category/{cat}") or {}).get("content") or []
            termo = termo_busca(a.get("nome_base"))
            # 2a busca pelo que o produto E (tipo + material), nao pelo nome: "prato raso plastico"
            termos = [termo]
            if perfil and termo:
                tipo = termo.split()[0]
                termos.append(" ".join([tipo, *perfil["tipos"].values(), perfil["material"] or ""]).strip())
                if perfil["material"]:
                    termos.append(f"{tipo} {perfil['material']}")
            busca = []
            for t in dict.fromkeys(x for x in termos if x):
                busca += ((api(f"/products/search?status=active&site_id=MLB&q={urllib.parse.quote(t)}") or {}).get("results") or [])[:10]
            candidatos, ja = [], set()
            for c, mv in [(x, True) for x in destaques if x.get("type", "PRODUCT") == "PRODUCT"][:10] + [(x, False) for x in busca]:
                cid = str(c.get("id") or "")
                if not FICHA_OK.match(cid) or cid in ja:
                    continue
                ja.add(cid)
                atrs = _atributos(c)
                if not c.get("name") or (perfil and not atrs):
                    ficha = api(f"/products/{cid}") or {}
                    c = {**ficha, **{k: v for k, v in c.items() if v}}
                    atrs = atrs or _atributos(ficha)
                vend = len((api(f"/products/{cid}/items") or {}).get("results") or [])
                candidatos.append({"id": cid, "nome": c.get("name"), "vendedores": vend, "mais_vendido": mv, "atributos": atrs})
            escolhidos = escolher(mesma, candidatos, termo, perfil=perfil, reserva=RESERVA if perfil else 0)
            # quem vende de verdade (e tem opiniao) vem da busca do ML no Chrome; o catalogo da API so completa
            try:
                cartoes = buscar(list(dict.fromkeys(t for t in reversed(termos) if t)))  # o descritivo primeiro
            except Exception:  # noqa: BLE001
                cartoes = []
            mesmos = [e for e in escolhidos if e["origem"] == "mesmo_produto"]
            da_busca = escolher_busca(cartoes, termo, perfil, {e["id"] for e in mesmos}, LIMITE + RESERVA)
            ids_busca = {c["id"] for c in da_busca}
            do_catalogo = [e for e in escolhidos if e["origem"] != "mesmo_produto" and e["id"] not in ids_busca]
            concorrentes = ([{**e, **_ficha(api, e["id"])} for e in mesmos]
                            + [{"id": c["id"], "origem": "busca_ml", **_ficha_da_busca(api, c)} for c in da_busca]
                            + [{**e, **_ficha(api, e["id"])} for e in do_catalogo[:max(0, LIMITE + RESERVA - len(da_busca))]])
            paginas = {c["id"]: c["url"] for c in da_busca}
        except Exception:  # noqa: BLE001
            falhou.append(pai)
            continue
        try:
            ops = opinioes([e["id"] for e in concorrentes], paginas)
            status = "ok"
        except Exception as e:  # noqa: BLE001
            ops, status = {}, f"falhou: {type(e).__name__} (a Helena usa o caminho antigo para as opinioes)"
        for k in concorrentes:
            o = ops.get(k["id"]) or {}
            lidas = o.get("lidas") or []
            k["opinioes"] = {"media_texto": o.get("media_texto"), "lidas": len(lidas), "por_nota": por_nota(lidas),
                             "erro": o.get("erro"), "sem_comentarios": bool(o.get("sem_comentarios")), "itens": lidas}
        # dos concorrentes lidos, ficam os 3 primeiros que tem opiniao (a reserva so serve para isso)
        # A mesma opiniao em dois concorrentes = mesmo produto em outra cor (Prato Cozy, 22/10: Bege e Preto com as
        # mesmas 120 opinioes); fica so o primeiro.
        outros = [k for k in concorrentes if k["origem"] != "mesmo_produto"]
        com, ja_lidas = [], set()
        for k in outros:
            ids = {o["id"] for o in k["opinioes"]["itens"]}
            if ids and len(ids & ja_lidas) * 2 <= len(ids) and len(com) < LIMITE:
                com.append(k)
                ja_lidas |= ids
        fica = {k["id"] for k in com + [k for k in outros if k not in com][:LIMITE - len(com)]}
        concorrentes = [k for k in concorrentes if k["origem"] == "mesmo_produto" or k["id"] in fica]
        # nenhuma opiniao lida por falha (Chrome caiu, PC dormiu: pedido 9, 22/10) = falhou; o maestro tenta de novo
        # antes de pagar o texto. Ficha sem comentario nenhum nao e falha.
        if concorrentes and (status != "ok" or all(k["opinioes"]["erro"] for k in concorrentes)):
            falhou.append(pai)
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
