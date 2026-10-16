#!/usr/bin/env python3
"""
validar_ficha_nsa.py — ficha tecnica sem valor inventado e sem campo esquecido (Almir 16/10/2026).

Regra: cada campo que a categoria mostra ao comprador tem um destino:
  - o valor real;
  - "não se aplica" quando o campo nao faz sentido para o produto (vai ao ML com value_id -1);
  - em branco SO quando faz sentido e ninguem achou o dado — e entao o campo fica listado em
    `campos_pendentes` do anuncio, para o Almir decidir no quadro da tela.
Valor de enchimento ("N/A", "-", "nenhum", "não informado"...) e proibido: ou e "não se aplica", ou e o valor.

Uso:  python validar_ficha_nsa.py <anuncio-{pai}.yaml> [campos-{pai}.json]
Saida: 0 = ok | 1 = problema (lista) | 2 = arquivo nao abriu
"""
import json
import re
import sys
import unicodedata

ENCHIMENTO = {"n/a", "na", "n.a.", "n/d", "nd", "-", "--", "---", ".", "?", "nenhum", "nenhuma", "sem",
              "nao informado", "nao informada", "nao possui", "nao tem", "nao ha", "indefinido",
              "desconhecido", "nao disponivel", "null", "none", "vazio"}


def _norm(v):
    s = unicodedata.normalize("NFKD", str(v or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


def valores_inventados(attrs):
    """[(campo, valor)] com valor de enchimento no lugar de 'não se aplica' ou do valor real."""
    return [(k, v) for k, v in (attrs or {}).items() if _norm(v) in ENCHIMENTO]


def campos_sem_destino(attrs, campos, pendentes=()):
    """Campos da categoria que nao tem valor, nem 'não se aplica', nem estao pendentes para o Almir."""
    tem = {k for k, v in (attrs or {}).items() if str(v or "").strip()}
    pend = set(pendentes or [])
    return [c["id"] for c in campos or [] if c.get("id") not in tem and c.get("id") not in pend]


def main():
    import yaml
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # mensagem com acento nao quebra no Windows
    except Exception:  # noqa: BLE001
        pass
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    try:
        with open(sys.argv[1], encoding="utf-8") as fh:
            doc = yaml.safe_load(fh) or {}
        campos = []
        if len(sys.argv) > 2:
            with open(sys.argv[2], encoding="utf-8") as fh:
                campos = json.load(fh)
    except Exception as e:  # noqa: BLE001
        print(f"nao abriu ({type(e).__name__})")
        sys.exit(2)
    attrs = doc.get("attributes") or {}
    problemas = [f"VALOR_INVENTADO {c}: '{v}' — use 'não se aplica' ou o valor real" for c, v in valores_inventados(attrs)]
    problemas += [f"CAMPO_SEM_DESTINO {c}: preencha, marque 'não se aplica' ou liste em campos_pendentes"
                  for c in campos_sem_destino(attrs, campos, doc.get("campos_pendentes"))]
    if problemas:
        print(f"FICHA COM PROBLEMA - {len(problemas)}:")
        for p in problemas:
            print(f"  - {p}")
        sys.exit(1)
    print("FICHA OK (sem valor inventado, todo campo com destino)")
    sys.exit(0)


if __name__ == "__main__":
    main()
