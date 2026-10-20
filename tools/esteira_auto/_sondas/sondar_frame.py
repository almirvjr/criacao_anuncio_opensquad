"""Sonda 3: produto -> 'Mostrar todas as opinioes' -> conta opinioes dentro da janela e chamadas ao rolar."""
import subprocess, sys, time, urllib.parse
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
PERFIL = RAIZ / "_opensquad" / "_perfil_opinioes"; PORTA = 9336
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SEL = "[class*='ui-review-capability-comments__comment']:not([class*='__comment__'])"
p = subprocess.Popen([CHROME, f"--remote-debugging-port={PORTA}", "--remote-debugging-address=127.0.0.1",
                      f"--user-data-dir={PERFIL}", "--no-first-run", "--window-size=1300,900", "about:blank"])
time.sleep(4)
with sync_playwright() as pw:
    b = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{PORTA}"); pg = b.contexts[0].new_page()
    vistos = []
    def resp(r):
        u = urllib.parse.urlparse(r.url)
        if "review" in u.path.lower() and not u.netloc.startswith("http2"):
            ct = r.headers.get("content-type","")
            try: corpo = r.body()
            except Exception: corpo = b""
            vistos.append((r.status, u.path, sorted(urllib.parse.parse_qs(u.query).keys()), len(corpo), ct[:20], corpo[:400].decode("utf-8","replace") if "json" in ct else ""))
    pg.on("response", resp)
    pg.goto(sys.argv[1], wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(3000); pg.mouse.wheel(0, 6000); pg.wait_for_timeout(2500)
    pg.get_by_text("Mostrar todas as opiniões").first.click(timeout=10000); pg.wait_for_timeout(5000)
    fr = next(f for f in pg.frames if "/noindex/catalog/reviews/" in f.url)
    n0 = fr.evaluate(f"() => document.querySelectorAll(\"{SEL}\").length")
    for _ in range(8):
        fr.evaluate("() => { const el=[...document.querySelectorAll('*')].find(e=>e.scrollHeight>e.clientHeight+50 && getComputedStyle(e).overflowY!='visible'); (el||document.scrollingElement).scrollTop += 4000; }")
        pg.wait_for_timeout(1500)
    n1 = fr.evaluate(f"() => document.querySelectorAll(\"{SEL}\").length")
    print("opinioes na janela antes/depois de rolar:", n0, n1)
    print("amostra:", fr.evaluate(f"() => [...document.querySelectorAll(\"{SEL}\")].slice(0,2).map(a=>a.innerText.replace(/\s+/g,' ').slice(0,160))"))
    for v in vistos: print(v)
    pg.close()
p.terminate()
