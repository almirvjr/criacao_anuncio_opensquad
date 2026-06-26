#!/usr/bin/env python3
"""
validar_prompt_nano.py — GATE das boas praticas do prompt Nano Banana (pipeline).

Wrapper de CLI sobre o linter co-localizado com o generate.py
(`skills/image-ai-generator/scripts/prompt_lint.py`). O `generate.py` ja roda o
linter em TODA geracao; este gate existe pra rodar a checagem isolada no pipeline
(step-07) e em testes, com codigo de saida bloqueante.

Uso:
  python validar_prompt_nano.py --prompt "<texto>" [--edit]
Saida: 0 = OK | 1 = BLOQUEADO.
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..",
                                      "skills", "image-ai-generator", "scripts"))
if SKILLS not in sys.path:
    sys.path.insert(0, SKILLS)
import prompt_lint  # noqa: E402

# reexporta pra testes
lint_prompt = prompt_lint.lint_prompt


def main():
    ap = argparse.ArgumentParser(description="Gate das boas praticas do prompt Nano Banana.")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--edit", action="store_true")
    args = ap.parse_args()

    issues = prompt_lint.lint_prompt(args.prompt, edit=args.edit)
    if not issues:
        print("PROMPT OK - boas praticas Nano Banana respeitadas.")
        sys.exit(0)
    print(prompt_lint.formatar(issues))
    if any(n == "BLOCK" for n, _, _ in issues):
        print("\nPROMPT REJEITADO - reescreva conforme as boas praticas (ou --no-lint no generate.py).")
        sys.exit(1)
    sys.exit(0)  # so avisos


if __name__ == "__main__":
    main()
