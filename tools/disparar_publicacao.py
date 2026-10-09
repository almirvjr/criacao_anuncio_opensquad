"""Envia payload-{pai}.json ao webhook ML Publicar (step-10). Le o endereco do .env e nunca o imprime.
Uso: python tools/disparar_publicacao.py <payload.json> <resultado.yaml>"""
import json, sys, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]


def endereco():
    for linha in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if linha.startswith("N8N_WEBHOOK_ML_PUBLICAR="):
            return linha.split("=", 1)[1].strip().strip('"')
    return None


UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) terra-esteira/1.0"


def enviar(corpo, timeout=120):
    """POST de um pacote (dict) ao ML Publicar. Devolve {'http', 'resposta'}; nunca o endereco."""
    url = endereco()
    if not url:
        return {"http": None, "resposta": {"texto_cru": "N8N_WEBHOOK_ML_PUBLICAR ausente no .env"}}
    # o Cloudflare da frente do n8n barra o agente padrao do urllib (erro 1010)
    req = urllib.request.Request(url, data=json.dumps(corpo, ensure_ascii=False).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            http, txt = r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        http, txt = e.code, e.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        http, txt = None, f"falha de conexao ({type(e).__name__})"
    try:
        resp = json.loads(txt)
    except Exception:  # noqa: BLE001
        resp = {"texto_cru": txt[:2000]}
    return {"http": http, "resposta": resp if isinstance(resp, dict) else {"texto_cru": str(resp)[:2000]}}


def main():
    payload, saida = Path(sys.argv[1]), Path(sys.argv[2])
    corpo = json.loads(payload.read_text(encoding="utf-8"))
    envio = datetime.now().isoformat(timespec="seconds")
    r = enviar(corpo)
    if r["http"] is None and "ausente" in str(r["resposta"].get("texto_cru")):
        print("N8N_WEBHOOK_ML_PUBLICAR ausente no .env"); sys.exit(2)
    resp = r["resposta"]
    doc = {"pai_sku": corpo["pai_sku"], "http_webhook": r["http"], "hora_envio": envio,
           "hora_resposta": datetime.now().isoformat(timespec="seconds"), "n8n_response": resp}
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(json.dumps({"http": r["http"], "status": resp.get("status"), "mlb_id": resp.get("mlb_id"),
                      "permalink": resp.get("permalink"), "stage": resp.get("stage"),
                      "error_code": resp.get("error_code"), "error_message": resp.get("error_message"),
                      "tiny_sync": resp.get("tiny_sync")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
