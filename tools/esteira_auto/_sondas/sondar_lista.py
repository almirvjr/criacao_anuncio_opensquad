"""Sonda 2: abre direto a pagina de opinioes do ML no Chrome de verdade, conta as opinioes e as chamadas ao rolar."""
import subprocess, sys, time, urllib.parse, json, re
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
PERFIL = RAIZ / "_opensquad" / "_perfil_opinioes"; PORTA = 9336
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
pid = sys.argv[1]
p = subprocess.Popen([CHROME, f"--remote-debugging-port={PORTA}", "--remote-debugging-address=127.0.0.1",
                      f"--user-data-dir={PERFIL}", "--no-first-run", "--window-size=1300,900", "about:blank"])
time.sleep(4)
with sync_playwright() as pw:
    b = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{PORTA}"); pg = b.contexts[0].new_page()
    vistos = []
    def resp(r):
        u = urllib.parse.urlparse(r.url)
        if "review" in u.path.lower():
            try: corpo = r.body(); tam = len(corpo)
            except Exception: corpo = b""; tam = -1
            vistos.append((r.status, u.netloc + u.path, sorted(urllib.parse.parse_qs(u.query).keys()), tam, r.headers.get("content-type","")[:25], corpo[:300].decode("utf-8","replace") if "json" in r.headers.get("content-type","") else ""))
    pg.on("response", resp)
    pg.goto(f"https://www.mercadolivre.com.br/noindex/catalog/reviews/{pid}?noIndex=true&modal=true&access=view_all", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(4000)
    n0 = pg.evaluate("() => document.querySelectorAll('article').length")
    for _ in range(6):
        pg.mouse.wheel(0, 5000); pg.wait_for_timeout(1500)
    n1 = pg.evaluate("() => document.querySelectorAll('article').length")
    est = pg.evaluate("() => [...document.scripts].map(s=>s.textContent).filter(t=>/reviews/.test(t)).map(t=>t.length).slice(0,5)")
    print("titulo:", pg.title()[:60], "| artigos antes/depois de rolar:", n0, n1, "| scripts com reviews (tamanho):", est)
    print("amostra:", pg.evaluate("() => [...document.querySelectorAll('article')].slice(0,2).map(a=>a.innerText.replace(/\s+/g,' ').slice(0,150))"))
    for v in vistos: print(v)
    pg.close()
p.terminate()
