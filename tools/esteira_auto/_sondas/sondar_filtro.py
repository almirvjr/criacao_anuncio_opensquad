"""Sonda 4: descobre o parametro de filtro por nota na lista de opinioes (so leitura)."""
import subprocess, sys, time, urllib.parse
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
PERFIL = RAIZ / "_opensquad" / "_perfil_opinioes"; PORTA = 9336
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
p = subprocess.Popen([CHROME, f"--remote-debugging-port={PORTA}", "--remote-debugging-address=127.0.0.1", f"--user-data-dir={PERFIL}", "--no-first-run", "about:blank"])
time.sleep(4)
with sync_playwright() as pw:
    pg = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{PORTA}").contexts[0].new_page()
    urls = []
    pg.on("response", lambda r: urls.append(r.url) if "/noindex/catalog/reviews/" in r.url and "/search" in r.url else None)
    pg.goto("https://www.mercadolivre.com.br/p/MLB34852629", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(3000); pg.mouse.wheel(0, 6000); pg.wait_for_timeout(2500)
    pg.get_by_text("Mostrar todas as opiniões").first.click(timeout=10000); pg.wait_for_timeout(4000)
    fr = next(f for f in pg.frames if "/noindex/catalog/reviews/" in f.url)
    # botoes/filtros da janela
    print("controles:", fr.evaluate("() => [...document.querySelectorAll('button,[role=button],select,label,a')].map(e=>(e.innerText||e.getAttribute('aria-label')||'').replace(/\s+/g,' ').trim()).filter(x=>x && x.length<40).slice(0,40)"))
    fr.evaluate("() => { const e=[...document.querySelectorAll('*')].find(x=>x.scrollHeight>x.clientHeight+50 && getComputedStyle(x).overflowY!='visible'); (e||document.scrollingElement).scrollTop += 4000; }")
    pg.wait_for_timeout(2500)
    base = urls[0]
    s = urllib.parse.urlsplit(base); q = dict(urllib.parse.parse_qsl(s.query)); q.update({"offset": "0", "limit": "15"})
    print("parametros da lista:", sorted(q))
    for extra in [{}, {"rating": "1"}, {"rating": "2"}, {"stars": "1"}, {"filters": "rating:1"}, {"rating_filter": "1"}, {"sort": "rating_asc"}, {"order": "asc"}]:
        qq = dict(q); qq.update(extra)
        u = urllib.parse.urlunsplit((s.scheme, s.netloc, s.path, urllib.parse.urlencode(qq), ""))
        d = fr.evaluate("async (u) => { const r = await fetch(u, {credentials:'include'}); return r.ok ? await r.json() : {erro: r.status}; }", u)
        notas = [x.get("rating") for x in (d or {}).get("reviews") or []]
        print(extra, "->", notas[:15], (d or {}).get("erro"), [k for k in (d or {}).keys()][:8])
    pg.close()
p.terminate()
