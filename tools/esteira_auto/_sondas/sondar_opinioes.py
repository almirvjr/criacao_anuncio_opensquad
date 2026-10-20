"""Sonda (19/10/2026): abre Chrome de verdade com perfil proprio, abre um anuncio e lista as chamadas de opinioes.
Imprime so caminho + nomes de parametros + tamanho (nunca cookie nem cabecalho)."""
import subprocess, sys, time, urllib.parse
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
PERFIL = RAIZ / "_opensquad" / "_perfil_opinioes"
PORTA = 9336
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
url = sys.argv[1]
p = subprocess.Popen([CHROME, f"--remote-debugging-port={PORTA}", "--remote-debugging-address=127.0.0.1",
                      f"--user-data-dir={PERFIL}", "--no-first-run", "--window-size=1300,900", "about:blank"])
time.sleep(4)
with sync_playwright() as pw:
    b = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{PORTA}")
    ctx = b.contexts[0]
    pg = ctx.new_page()
    vistos = []
    def resp(r):
        u = urllib.parse.urlparse(r.url)
        ct = r.headers.get("content-type", "")
        if ("mercadolivre" in u.netloc or "mercadolibre" in u.netloc) and ("json" in ct or "html" in ct) and not u.path.endswith((".js",".css")):
            try: tam = len(r.body())
            except Exception: tam = -1
            vistos.append((r.status, u.netloc + u.path, sorted(urllib.parse.parse_qs(u.query).keys()), tam, r.headers.get("content-type", "")[:30]))
    pg.on("response", resp)
    pg.goto(url, wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(3000)
    pg.mouse.wheel(0, 6000); pg.wait_for_timeout(3000)
    print("titulo:", pg.title()[:70])
    try:
        pg.get_by_text("Mostrar todas as opiniões").first.click(timeout=8000)
        pg.wait_for_timeout(5000)
        print("--- depois do clique ---"); vistos.append(("---",))
        pg.mouse.wheel(0, 3000); pg.wait_for_timeout(3000)
    except Exception as e:
        print("nao achei o botao:", type(e).__name__)
    for f in pg.frames:
        if "review" in f.url.lower():
            u = urllib.parse.urlparse(f.url); print("FRAME", u.netloc + u.path, sorted(urllib.parse.parse_qs(u.query).keys()))
    for v in vistos: print(v)
    pg.close()
p.terminate()
