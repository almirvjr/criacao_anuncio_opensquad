"""Completa o anuncio DEPOIS de publicado (modelo novo do ML, 08/10/2026).

No modelo User Products o ML ignora a descricao mandada junto com o anuncio: ela
precisa de um segundo envio. E o Flex e ligado de proposito em todo anuncio novo
(nao depender da configuracao da conta). Le o acesso pelo .env, nunca imprime o token.

Uso: python tools/completar_anuncio.py <payload-{sku}.json> <MLB...>
"""
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from esteira.payload_builder import GARANTIA, LOJA_OFICIAL  # noqa: E402

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿\U0001F000-\U0001F2FF︀-️]")


def texto_descricao(payload):
    t = str(payload.get("description_plain") or "")
    t = re.sub(r"<[^>]*>", "", t).replace("<", "").replace(">", "")
    t = EMOJI.sub("", t).replace("\r\n", "\n").replace("\r", "\n")
    t = "\n".join(linha.strip() for linha in t.split("\n"))
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    if not t:
        raise ValueError("Pacote sem descricao: nada para gravar.")
    return t


def _chamar(metodo, caminho, tk, corpo=None):
    from conferir_no_ml import UA
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request("https://api.mercadolibre.com" + caminho, data=dados, method=metodo,
                                 headers={"Authorization": "Bearer " + tk, "User-Agent": UA,
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            txt = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(txt) if txt else {})
    except urllib.error.HTTPError as e:
        txt = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(txt)
        except Exception:  # noqa: BLE001
            return e.code, {"texto": txt[:300]}


def _garantia_e_loja(mlb, tk, res):
    """Garantia do vendedor de 30 dias (regravada aqui porque o ML Publicar do n8n pode nao repassar
    sale_terms) e conferencia de que o anuncio caiu na loja oficial da Terra (Almir 09/10/2026)."""
    st, d = _chamar("GET", f"/items/{mlb}", tk)
    if st != 200:
        print(f"{mlb} garantia/loja: FALHOU HTTP {st}")
        return
    res["loja_oficial"] = d.get("official_store_id") == LOJA_OFICIAL
    print(f"{mlb} loja oficial: {'sim' if res['loja_oficial'] else 'NAO - confira no ML'}")
    termos = {t.get("id"): t.get("value_name") for t in d.get("sale_terms") or []}
    if all(termos.get(g["id"]) == g["value_name"] for g in GARANTIA):
        res["garantia"] = True
        print(f"{mlb} garantia: ja estava")
        return
    st, d = _chamar("PUT", f"/items/{mlb}", tk, {"sale_terms": GARANTIA})
    res["garantia"] = st in (200, 201)
    print(f"{mlb} garantia: {'gravada' if res['garantia'] else 'FALHOU HTTP %s %s' % (st, d.get('message'))}")


def completar(payload, mlb, tk):
    res = {"descricao": False, "flex": False, "garantia": False, "loja_oficial": False}
    st, d = _chamar("GET", f"/items/{mlb}/description", tk)
    if st == 200 and (d.get("plain_text") or "").strip():
        res["descricao"] = True
        print(f"{mlb} descricao: ja existe")
    else:
        st, d = _chamar("POST", f"/items/{mlb}/description", tk, {"plain_text": texto_descricao(payload)})
        res["descricao"] = st in (200, 201)
        print(f"{mlb} descricao: {'gravada' if res['descricao'] else 'FALHOU HTTP %s %s' % (st, d.get('message'))}")
    st, d = _chamar("GET", f"/flex/sites/MLB/items/{mlb}/v2", tk)
    if st == 200 and d.get("has_flex"):
        res["flex"] = True
        print(f"{mlb} flex: ja ligado")
    else:
        st, d = _chamar("POST", f"/flex/sites/MLB/items/{mlb}/v2", tk)
        res["flex"] = st in (200, 201, 204)
        print(f"{mlb} flex: {'ligado' if res['flex'] else 'FALHOU HTTP %s %s' % (st, d.get('message'))}")
    _garantia_e_loja(mlb, tk, res)
    return res


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from conferir_no_ml import token
    tk = token()
    if not tk:
        print("nao consegui o acesso ao ML"); sys.exit(2)
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    r = completar(payload, sys.argv[2], tk)
    sys.exit(0 if all(r.values()) else 1)
