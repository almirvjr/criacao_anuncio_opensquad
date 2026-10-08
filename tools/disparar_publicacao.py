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


def main():
    payload, saida = Path(sys.argv[1]), Path(sys.argv[2])
    url = endereco()
    if not url:
        print("N8N_WEBHOOK_ML_PUBLICAR ausente no .env"); sys.exit(2)
    corpo = payload.read_bytes()
    envio = datetime.now().isoformat(timespec="seconds")
    req = urllib.request.Request(url, data=corpo, method="POST", headers={"Content-Type": "application/json",
                                 # o Cloudflare da frente do n8n barra o agente padrao do urllib (erro 1010)
                                 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) terra-esteira/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            http, txt = r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        http, txt = e.code, e.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        http, txt = None, f"falha de conexao ({type(e).__name__})"
    try:
        resp = json.loads(txt)
    except Exception:  # noqa: BLE001
        resp = {"texto_cru": txt[:2000]}
    doc = {"pai_sku": json.loads(corpo)["pai_sku"], "http_webhook": http, "hora_envio": envio,
           "hora_resposta": datetime.now().isoformat(timespec="seconds"), "n8n_response": resp}
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
    r = resp if isinstance(resp, dict) else {}
    print(json.dumps({"http": http, "status": r.get("status"), "mlb_id": r.get("mlb_id"), "permalink": r.get("permalink"),
                      "stage": r.get("stage"), "error_code": r.get("error_code"), "error_message": r.get("error_message"),
                      "tiny_sync": r.get("tiny_sync")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
