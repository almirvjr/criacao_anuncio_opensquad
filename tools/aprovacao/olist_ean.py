"""Rele o codigo de barras de um SKU no Olist (depois de gerado pelo botao da GS1) e grava
na entrada do lote, sem recomecar a esteira. Token so do cofre do Windows: a tela nao
tem terminal para pedir senha. Nunca imprime token nem texto cru de erro."""
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

SCRIPTS_TINY = Path(__file__).resolve().parents[3] / "cadastro_tiny" / "scripts"
BASE = "https://api.tiny.com.br/public-api/v3"


def _token_do_cofre():
    try:
        import keyring
        sys.path.insert(0, str(SCRIPTS_TINY))
        import senha_banco
        senha = keyring.get_password(senha_banco.SERVICO, senha_banco.USUARIO)
        return senha_banco._token(senha) if senha else None
    except Exception:  # noqa: BLE001
        return None


def _buscar_no_olist(sku):
    tk = _token_do_cofre()
    if not tk:
        return None, "sem acesso ao Olist (rode uma vez o botao '1 - Conferir EANs' para guardar a senha)"
    url = f"{BASE}/produtos?codigo={urllib.parse.quote(sku)}"
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + tk, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            itens = json.loads(r.read()).get("itens") or []
    except Exception as e:  # noqa: BLE001
        return None, f"o Olist nao respondeu ({type(e).__name__})"
    item = next((i for i in itens if str(i.get("sku") or i.get("codigo")) == sku), None)
    return ((item or {}).get("gtin") or None), None


def reler_ean(saida, sku, buscar=_buscar_no_olist):
    p = Path(saida) / "anuncios-entrada.json"
    entrada = json.loads(p.read_text(encoding="utf-8"))
    alvo = next((v for a in entrada.get("anuncios", []) for v in a.get("variacoes", []) if v.get("sku") == sku), None)
    if alvo is None:
        return {"ok": False, "ean": None, "motivo": f"{sku} nao e deste lote"}
    ean, erro = buscar(sku)
    if erro:
        return {"ok": False, "ean": None, "motivo": erro}
    if not ean:
        return {"ok": False, "ean": None, "motivo": "o Olist ainda nao tem codigo de barras para este SKU"}
    alvo["ean"] = str(ean)
    tmp = p.with_name(p.name + ".novo")
    tmp.write_text(json.dumps(entrada, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)
    return {"ok": True, "ean": str(ean), "motivo": None}
