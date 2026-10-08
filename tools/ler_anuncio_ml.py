"""So le anuncios do ML e imprime o essencial (nunca o token). Uso: python tools/ler_anuncio_ml.py MLB1 [MLB2 ...]"""
import json, sys, urllib.request, urllib.error
sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from conferir_no_ml import token, UA

tk = token()
if not tk:
    print("nao consegui o acesso ao ML"); sys.exit(2)
for mlb in sys.argv[1:]:
    req = urllib.request.Request(f"https://api.mercadolibre.com/items/{mlb}",
                                 headers={"Authorization": "Bearer " + tk, "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(mlb, "HTTP", e.code); continue
    at = {a["id"]: a.get("value_name") for a in d.get("attributes", [])}
    print(json.dumps({"id": d["id"], "status": d.get("status"), "sub_status": d.get("sub_status"),
                      "title": d.get("title"), "family_name": d.get("family_name"),
                      "user_product_id": d.get("user_product_id"), "price": d.get("price"),
                      "estoque": d.get("available_quantity"), "tipo": d.get("listing_type_id"),
                      "frete_gratis": (d.get("shipping") or {}).get("free_shipping"),
                      "fotos": len(d.get("pictures") or []),
                      "BRAND": at.get("BRAND"), "MODEL": at.get("MODEL"), "COLOR": at.get("COLOR"),
                      "GTIN": at.get("GTIN"), "SELLER_SKU": at.get("SELLER_SKU"),
                      "caixa": [at.get(k) for k in ("SELLER_PACKAGE_HEIGHT", "SELLER_PACKAGE_WIDTH",
                                                    "SELLER_PACKAGE_LENGTH", "SELLER_PACKAGE_WEIGHT")],
                      "permalink": d.get("permalink")}, ensure_ascii=False, indent=1))
