#!/usr/bin/env python3
"""
prompt_lint.py — TRAVA das boas praticas do Nano Banana (anti-amnesia de prompt).

Roda em TODA geracao (chamado de dentro do generate.py) pra garantir, de forma
infalivel, que o prompt segue as praticas que a pesquisa oficial + benchmark
provaram funcionar (ver SKILL.md / [[nano_banana_prompt_engineering]]):

  - ESCALA por RAZAO em texto NAO funciona ("1/3 da bancada") -> o modelo ignora
    e orbita ~metade. Na 1a geracao isso BLOQUEIA (usar framing de fotografo).
    Em modo EDICAO (--edit) e so AVISO (ali "deixe ~1/4 menor" é direcao relativa).
  - JSON cru no prompt atrapalha a compreensao espacial -> BLOQUEIA (usar prosa).
  - Termos de camera que INCHAM o produto (close-up/low-angle/macro/f1.8) -> AVISO.

Uso como modulo: lint_prompt(text, edit=False) -> [(nivel, code, msg)]
  nivel: "BLOCK" | "WARN".
"""

import json
import re

# --- razao de tamanho em texto (o anti-padrao nº1) -------------------------
_RATIO_PATS = [
    r"\b[1-3]\s*/\s*[2-4]\b",                       # 1/3, 1/4, 2/3, 3/4
    r"\bone[\s-]?(third|quarter|half)\b",
    r"\bum[\s-]?(terço|terco|quarto)\b",
    r"\bmetade\s+(da|do)\b",
    r"\bhalf\s+(the|of)\b",
    r"\d{1,3}\s*%\s*(of|da|do|de)\b",               # "28% da bancada"
    r"\b0[.,]\d+\s*(da|do|of)\b",                    # "0,28 da bancada"
    r"\b(one[\s-]?third|1/3|um[\s-]?terço)\s+(the|da|do|of)\b",
]
# so conta como "escala" se aparecer perto de palavra de tamanho
_SCALE_CTX = re.compile(
    r"(height|altura|vanity|bancada|tall|size|escala|proporç|proporc|larg|width)", re.I)

# --- termos de camera que incham o produto ---------------------------------
_INFLA_PATS = [
    r"\bclose[\s-]?ups?\b", r"\blow[\s-]?angle\b", r"\bmacro\b",
    r"\bf\s*/?\s*1\.?8\b", r"\bworm'?s[\s-]?eye\b", r"\bextreme close\b",
]


def _norm(s):
    return s if isinstance(s, str) else str(s)


def parece_json(text):
    t = text.strip()
    if t.startswith("{") and t.endswith("}"):
        try:
            json.loads(t)
            return True
        except Exception:
            # JSON malformado mas claramente um dump (chaves "x": )
            return bool(re.search(r'"\s*\w+\s*"\s*:', t))
    return False


def lint_prompt(text, edit=False):
    """Retorna lista de (nivel, code, msg). Vazia = limpo."""
    text = _norm(text)
    out = []

    # 1) JSON cru -> sempre BLOCK
    if parece_json(text):
        out.append(("BLOCK", "JSON_CRU",
                    "prompt parece JSON cru — o Nano Banana entende melhor PROSA "
                    "(ordem 6-fatores: sujeito→ação→cenário→estilo→composição/luz→proporção). "
                    "Reescreva em linguagem natural."))

    # 2) razao de tamanho em texto
    if _SCALE_CTX.search(text):
        for pat in _RATIO_PATS:
            if re.search(pat, text, re.I):
                if edit:
                    out.append(("WARN", "RATIO_ESCALA_EDIT",
                                "razão de tamanho no prompt de edição é OK como direção relativa "
                                "('deixe ~1/4 menor'), mas o que pega é o verbo relativo ('menor/maior'), "
                                "não a fração."))
                else:
                    out.append(("BLOCK", "RATIO_ESCALA",
                                "razão de tamanho em texto ('1/3 da bancada' etc.) NÃO funciona na 1ª "
                                "geração — o modelo ignora e orbita ~metade. Use framing de fotógrafo "
                                "(wide shot, altura dos olhos, ~2m, grande-angular), gabinete cortado, ou "
                                "marcos ('chega na gaveta de baixo'); ajuste fino de escala via --edit."))
                break

    # 3) termos de camera que incham o produto
    for pat in _INFLA_PATS:
        if re.search(pat, text, re.I):
            out.append(("WARN", "CAMERA_INFLA",
                        f"termo de câmera que INCHA o produto detectado (close-up/low-angle/macro/f1.8). "
                        f"Pra produto pequeno em escala correta, preferir 'wide shot, altura dos olhos, ~2m'."))
            break

    return out


def formatar(issues):
    """String legivel pros avisos/bloqueios."""
    linhas = []
    for nivel, code, msg in issues:
        marca = "BLOQUEIO" if nivel == "BLOCK" else "aviso"
        linhas.append(f"  [{marca}] {code}: {msg}")
    return "\n".join(linhas)
