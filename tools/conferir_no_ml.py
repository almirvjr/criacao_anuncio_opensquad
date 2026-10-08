"""Pede ao ML para CONFERIR um anuncio (POST /items/validate) - nao cria nada.
Le o acesso pelo .env (funcao get-ml-token) e nunca imprime o token.
Uso: python tools/conferir_no_ml.py <corpo.json>"""
import json, sys, urllib.request, urllib.error
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) terra-esteira/1.0"


def _env():
    out = {}
    for linha in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in linha and not linha.lstrip().startswith("#"):
            k, v = linha.split("=", 1)
            out[k.strip()] = v.strip().strip('"')
    return out


def token():
    e = _env()
    req = urllib.request.Request(e["ML_TOKEN_FUNCTION_URL"], method="POST", data=b"{}",
                                 headers={"x-shared-secret": e["ML_TOKEN_SHARED_SECRET"],
                                          "Content-Type": "application/json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["access_token"]
    except Exception:  # noqa: BLE001
        return None


def conferir(corpo, tk):
    req = urllib.request.Request("https://api.mercadolibre.com/items/validate", method="POST",
                                 data=json.dumps(corpo).encode("utf-8"),
                                 headers={"Authorization": "Bearer " + tk, "Content-Type": "application/json",
                                          "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


if __name__ == "__main__":
    tk = token()
    if not tk:
        print("nao consegui o acesso ao ML"); sys.exit(2)
    corpo = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    st, txt = conferir(corpo, tk)
    print("HTTP", st)
    try:
        d = json.loads(txt)
        print("mensagem:", d.get("message"), "|", d.get("error"))
        for c in d.get("cause") or []:
            print(" -", json.dumps(c, ensure_ascii=False))
    except Exception:  # noqa: BLE001
        print(txt[:500] if txt else "(sem corpo = conferido OK)")
