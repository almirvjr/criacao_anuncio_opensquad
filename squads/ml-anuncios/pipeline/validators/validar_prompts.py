#!/usr/bin/env python3
"""
validar_prompts.py — PRENDE O PROMPT DO FELIPE AO TEMPLATE (Fase 3 da blindagem).

O Felipe gera um JSON de prompt por slot (prompts/foto-NN.json) preenchendo o
template parametrizado de photo-templates.md. Esta trava garante que ele nao
improvisou: cada prompt tem que (1) nao ter placeholder {{...}} sobrando,
(2) ter `nome` = funcao canonica do slot, e (3) cobrir os 10 slots fixos.

Reusa a hierarquia canonica de validar_brief.py (fonte unica da verdade).

Uso:
  python validar_prompts.py <pasta_prompts>
Saida: codigo 0 = PROMPTS OK | codigo 1 = REPROVADO.
"""

import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from validar_brief import SLOTS_CANONICOS, SLOTS_OPCIONAIS  # noqa: E402

NOME_AUXILIAR = {"FICHA_TECNICA_DIMENSOES"}  # foto tecnica, fora da hierarquia de slots
RE_PLACEHOLDER = re.compile(r"\{\{[^}]*\}\}")


def numero_do_prompt(d, fname):
    """Numero do slot: campo 'imagem' ou 'numero' do JSON, ou do nome do arquivo."""
    for k in ("imagem", "numero"):
        if isinstance(d.get(k), int):
            return d[k]
    m = re.search(r"foto-?(\d+)", os.path.basename(fname))
    return int(m.group(1)) if m else None


def validar_prompts(pasta):
    """Retorna lista de erros (code,msg). Vazia = ok."""
    err = []
    arquivos = sorted(glob.glob(os.path.join(pasta, "foto-*.json")))
    # tambem aceitar um prompt da ficha tecnica auxiliar, se existir
    arquivos += sorted(glob.glob(os.path.join(pasta, "*ficha*.json")))
    if not arquivos:
        return [("SEM_PROMPTS", f"nenhum prompt foto-*.json em {pasta}")]

    vistos = {}
    for f in arquivos:
        nome_arq = os.path.basename(f)
        raw = open(f, encoding="utf-8").read()
        # 1) placeholder nao preenchido
        sobrando = RE_PLACEHOLDER.findall(raw)
        if sobrando:
            err.append(("PLACEHOLDER_NAO_PREENCHIDO",
                        f"{nome_arq}: placeholders sem preencher: {sorted(set(sobrando))[:5]}"))
        # 2) JSON valido
        try:
            d = json.loads(raw)
        except Exception as e:
            err.append(("JSON_INVALIDO", f"{nome_arq}: {e}"))
            continue
        nome = d.get("nome")
        numero = numero_do_prompt(d, f)

        # 3) nome bate com a funcao canonica do slot
        if nome in NOME_AUXILIAR:
            continue  # foto tecnica auxiliar, nao e slot
        if numero in SLOTS_CANONICOS:
            esperado = SLOTS_CANONICOS[numero][0]
            vistos[numero] = nome
        elif numero in SLOTS_OPCIONAIS:
            esperado = SLOTS_OPCIONAIS[numero][0]
        else:
            err.append(("SLOT_DESCONHECIDO",
                        f"{nome_arq}: slot {numero} fora da hierarquia (1-10 +11 opcional)"))
            continue
        if nome != esperado:
            err.append(("PROMPT_FUNCAO_ERRADA",
                        f"{nome_arq}: nome '{nome}' != funcao canonica do slot {numero} ('{esperado}')"))

    # 4) cobertura dos slots fixos
    faltando = [n for n in SLOTS_CANONICOS if n not in vistos]
    if faltando:
        err.append(("PROMPT_SLOT_FALTANDO",
                    f"sem prompt para slot(s) fixo(s): {faltando}"))
    return err


def main():
    ap = argparse.ArgumentParser(description="Trava: prompt do Felipe preso ao template.")
    ap.add_argument("pasta", help="Pasta prompts/ do anuncio")
    args = ap.parse_args()
    if not os.path.isdir(args.pasta):
        print(f"ERRO: pasta nao encontrada: {args.pasta}", file=sys.stderr)
        sys.exit(2)

    erros = validar_prompts(args.pasta)
    if erros:
        print(f"\nPROMPTS REJEITADOS - {len(erros)} erro(s):")
        for code, msg in erros:
            print(f"  [{code}] {msg}")
        sys.exit(1)
    print(f"PROMPTS OK - {os.path.basename(os.path.dirname(args.pasta.rstrip(os.sep)))}: "
          f"templates preenchidos, funcoes batem com a hierarquia.")
    sys.exit(0)


if __name__ == "__main__":
    main()
