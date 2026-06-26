#!/usr/bin/env python3
"""
validar_brief.py — TRAVA DE ENTRADA do método StorySelling (Fase 1).

Valida o brief estrategico da Helena de forma DETERMINISTICA. Se o brief nao
cumpre o contrato, o script sai com codigo != 0 e o pipeline NAO avanca para
geracao de fotos. Isso transforma "a Helena deve lembrar" em "o sistema obriga".

O que ele exige (resumo):
  1. Os 10 slots de foto preenchidos, cada um com a funcao canonica correta,
     objetivo MECLABS valido, headline, e objecao_alvo onde aplicavel.
  2. Campo `limitacoes` presente. Se vazio, exige `limitacoes_nota` justificando
     (forca uma decisao consciente sobre pontos fracos / ausencia de balde etc).
  3. Diagnostico com dor interna, only_factor, ansiedades e escada "E dai?".
  4. Toda evidencia citada (dor interna, ansiedades) tem que EXISTIR de fato no
     texto bruto dos concorrentes (`_raw/{mlb_id}.json`) — mata review inventada.

Uso:
  python validar_brief.py <brief.yaml> [--raw-dir <pasta _raw>]
  python validar_brief.py <brief.yaml>            # sem --raw-dir: ancora vira WARN

Saida: codigo 0 = BRIEF OK | codigo 1 = BRIEF REJEITADO (lista de erros).

A AUTORIDADE da validacao e este script. O arquivo brief.schema.json ao lado e
apenas o contrato legivel (documentacao); quem bloqueia e o .py.
"""

import argparse
import glob
import json
import os
import re
import sys
import unicodedata

# ---------------------------------------------------------------------------
# CONTRATO: hierarquia canonica (Equilibrado, escolhido pelo Almir 2026-06-21).
# Ritmo emocional: lifestyle no slot 5 (respiro) + slot 8; detalhes tecnicos
# fundidos no slot 7. ESTE e o unico lugar a mudar a hierarquia.
# numero -> (funcao canonica, exige_objecao_alvo)
# ---------------------------------------------------------------------------
SLOTS_CANONICOS = {
    1: ("CAPA_PURPLE_COW", False),
    2: ("ANTES_DEPOIS", False),
    3: ("BADGE_TAMANHO", True),
    4: ("ANTI_ANSIEDADE_MATERIAL", True),      # material + durabilidade
    5: ("LIFESTYLE_EMOCIONAL", False),         # respiro emocional (novo)
    6: ("CLAREZA_ABSOLUTA", True),
    7: ("DETALHE_TECNICO", False),             # funde det1+det2 (pedal/mecanismo)
    8: ("LIFESTYLE_USO_REAL", False),
    9: ("SOBRECORRECAO_ANSIEDADE", False),
    10: ("MACRO_YES_CTA_FINAL", False),
}
# Slot OPCIONAL e DORMENTE: so entra quando ha review REAL nosso (anuncio novo
# nao tem). Se presente, exige a flag reviews_proprios_confirmados=true no brief
# (impede prova social fabricada/de concorrente).
SLOTS_OPCIONAIS = {
    11: ("PROVA_SOCIAL", False),
}
SLOT_COM_SELOS = {9, 10}          # slots que exigem selos_visuais
SELOS_MIN, SELOS_MAX = 4, 6       # foto 9: 4 a 6 selos

# Tokens MECLABS validos. Proibido: +f, +a, -m, -v, -i (nunca queremos isso).
MECLABS_TOKENS_VALIDOS = {"+m", "+v", "+i", "-f", "-a"}
MECLABS_TOKENS_PROIBIDOS = {"+f", "+a", "-m", "-v", "-i"}

EVIDENCIA_MIN_CHARS = 12          # citacao curta demais = ancora fraca


def norm(s):
    """lowercase + remove acento + colapsa tudo que nao for alfanumerico em espaco."""
    if not isinstance(s, str):
        s = str(s)
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()


def parse_meclabs(code):
    """Quebra '+v-a' em ['+v','-a']. Retorna [] se malformado."""
    if not isinstance(code, str):
        return None
    toks = re.findall(r"[+-][mvifa]", code.replace(" ", ""))
    # reconstroi e compara pra detectar lixo no meio
    if "".join(toks) != code.replace(" ", ""):
        return None
    return toks


def _strings_do_json(x):
    """Itera todos os valores string de uma estrutura JSON (recursivo)."""
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from _strings_do_json(v)
    elif isinstance(x, (list, tuple)):
        for v in x:
            yield from _strings_do_json(v)


def load_raw_blob(raw_dir):
    """Concatena o texto normalizado dos _raw/*.json para busca de ancora.
    Parseia o JSON e extrai os VALORES de texto (reviews/qa/descricao) — ler os
    bytes crus poluiria o blob com escapes (\\n vira token 'n' e quebra a frase)."""
    files = glob.glob(os.path.join(raw_dir, "*.json"))
    partes = []
    for f in files:
        try:
            partes.extend(_strings_do_json(json.load(open(f, encoding="utf-8"))))
        except Exception:
            partes.append(open(f, encoding="utf-8").read())  # fallback defensivo
    return norm(" ".join(partes)), len(files)


def evidencia_ancorada(quote, raw_blob):
    """True se a citacao existe no texto bruto. Aceita '...' como separador de
    trechos (cada pedaco precisa existir, contiguo)."""
    pedacos = [p for p in re.split(r"\.{2,}|…", quote) if norm(p)]
    if not pedacos:
        return False
    return all(norm(p) in raw_blob for p in pedacos)


def validate_brief(brief, raw_dir=None):
    """Retorna lista de erros (code, msg). Lista vazia = brief valido.
    Avisos de ancora (raw_dir ausente) entram como ('WARN:...')."""
    err = []

    def E(code, msg):
        err.append((code, msg))

    if not isinstance(brief, dict):
        return [("BRIEF_INVALIDO", "Brief nao e um mapa YAML valido.")]

    # --- campos de topo obrigatorios ------------------------------------
    for campo in ("pai_sku", "nome_base", "confianca", "cor_heroi",
                  "dados_produto", "diagnostico", "escada_e_dai",
                  "briefing_fotos", "limitacoes"):
        if campo not in brief or brief[campo] in (None, "", []):
            if campo == "limitacoes" and "limitacoes" in brief:
                continue  # lista vazia tratada abaixo
            E("FALTA_CAMPO", f"Campo de topo obrigatorio ausente/vazio: '{campo}'.")

    # --- limitacoes: presente; se vazia, exige nota justificando ---------
    if "limitacoes" in brief:
        lims = brief["limitacoes"]
        if not isinstance(lims, list):
            E("LIMITACOES_TIPO", "'limitacoes' tem que ser uma lista.")
        elif len(lims) == 0:
            if not brief.get("limitacoes_nota"):
                E("LIMITACOES_VAZIA",
                  "'limitacoes' vazia exige 'limitacoes_nota' justificando por que "
                  "nenhuma limitacao foi identificada (forca decisao consciente).")
        else:
            for i, lim in enumerate(lims):
                if not isinstance(lim, dict) or not lim.get("texto"):
                    E("LIMITACAO_TEXTO", f"limitacoes[{i}] precisa de 'texto'.")

    # --- diagnostico -----------------------------------------------------
    diag = brief.get("diagnostico") or {}
    evidencias_para_ancora = []
    if isinstance(diag, dict):
        dor = diag.get("dor_interna_mais_forte") or {}
        if not dor.get("texto"):
            E("DOR_INTERNA", "diagnostico.dor_interna_mais_forte.texto ausente.")
        evs = dor.get("evidencias") or []
        if not evs:
            E("DOR_SEM_EVIDENCIA",
              "dor_interna_mais_forte precisa de pelo menos 1 evidencia (review).")
        evidencias_para_ancora += [(("dor_interna"), e) for e in evs]

        of = diag.get("only_factor") or {}
        if not of.get("texto"):
            E("ONLY_FACTOR", "diagnostico.only_factor.texto ausente.")

        ansi = diag.get("ansiedades") or []
        if not ansi:
            E("SEM_ANSIEDADES", "diagnostico.ansiedades vazio.")
        for i, a in enumerate(ansi):
            if not isinstance(a, dict):
                E("ANSIEDADE_TIPO", f"ansiedades[{i}] malformada.")
                continue
            if not a.get("texto"):
                E("ANSIEDADE_TEXTO", f"ansiedades[{i}].texto ausente.")
            ev = a.get("evidencia")
            if not ev:
                E("ANSIEDADE_SEM_EVIDENCIA",
                  f"ansiedades[{i}] ('{a.get('texto','?')[:40]}') sem evidencia de review.")
            else:
                evidencias_para_ancora.append((f"ansiedade[{i}]", ev))
    else:
        E("DIAGNOSTICO_TIPO", "diagnostico tem que ser um mapa.")

    # --- escada "E dai?" -------------------------------------------------
    escada = brief.get("escada_e_dai") or []
    if not escada:
        E("SEM_ESCADA", "escada_e_dai vazia.")
    for i, deg in enumerate(escada):
        if not all(isinstance(deg, dict) and deg.get(k) for k in ("feature", "logico", "emocional")):
            E("ESCADA_INCOMPLETA",
              f"escada_e_dai[{i}] precisa de feature + logico + emocional.")

    # --- briefing_fotos: 10 slots, funcao certa, meclabs valido ----------
    fotos = brief.get("briefing_fotos") or []
    por_numero = {}
    for f in fotos:
        if isinstance(f, dict) and isinstance(f.get("numero"), int):
            por_numero[f["numero"]] = f

    for numero, (funcao_ok, exige_obj) in SLOTS_CANONICOS.items():
        f = por_numero.get(numero)
        if f is None:
            E("SLOT_FALTANDO", f"Foto slot {numero} ({funcao_ok}) ausente.")
            continue
        if f.get("funcao") != funcao_ok:
            E("SLOT_FUNCAO_ERRADA",
              f"Foto {numero}: funcao '{f.get('funcao')}' != esperada '{funcao_ok}'.")
        if not f.get("headline"):
            E("SLOT_SEM_HEADLINE", f"Foto {numero} sem headline.")
        toks = parse_meclabs(f.get("objetivo_meclabs"))
        if toks is None or not toks:
            E("MECLABS_INVALIDO",
              f"Foto {numero}: objetivo_meclabs '{f.get('objetivo_meclabs')}' invalido.")
        else:
            for t in toks:
                if t in MECLABS_TOKENS_PROIBIDOS:
                    E("MECLABS_PROIBIDO",
                      f"Foto {numero}: token MECLABS proibido '{t}' (nunca amplificar f/a nem reduzir m/v/i).")
                elif t not in MECLABS_TOKENS_VALIDOS:
                    E("MECLABS_DESCONHECIDO", f"Foto {numero}: token '{t}' desconhecido.")
        if exige_obj and not f.get("objecao_alvo"):
            E("SLOT_SEM_OBJECAO",
              f"Foto {numero} ({funcao_ok}) exige objecao_alvo ancorada.")
        if numero in SLOT_COM_SELOS:
            selos = f.get("selos_visuais") or []
            if numero == 9 and not (SELOS_MIN <= len(selos) <= SELOS_MAX):
                E("SELOS_QTD",
                  f"Foto 9 precisa de {SELOS_MIN}-{SELOS_MAX} selos_visuais (tem {len(selos)}).")
            if numero == 10 and len(selos) < 1:
                E("SELOS_QTD", "Foto 10 precisa de pelo menos 1 selo_visual.")

    # slots OPCIONAIS (ex.: 11 PROVA_SOCIAL): validados so se presentes
    for numero, (funcao_ok, _) in SLOTS_OPCIONAIS.items():
        f = por_numero.get(numero)
        if f is None:
            continue
        if f.get("funcao") != funcao_ok:
            E("SLOT_FUNCAO_ERRADA",
              f"Foto {numero}: funcao '{f.get('funcao')}' != esperada '{funcao_ok}'.")
        # PROVA_SOCIAL so vale com review REAL nosso (anti prova social fabricada)
        if funcao_ok == "PROVA_SOCIAL" and not brief.get("reviews_proprios_confirmados"):
            E("PROVA_SOCIAL_SEM_REVIEW",
              "Foto 11 (PROVA_SOCIAL) exige 'reviews_proprios_confirmados: true' no brief "
              "(prova social so com review REAL nosso — nunca de concorrente nem inventado). "
              "Anuncio novo sem review: omitir a foto 11.")

    permitidos = set(SLOTS_CANONICOS) | set(SLOTS_OPCIONAIS)
    extras = set(por_numero) - permitidos
    if extras:
        E("SLOT_EXTRA", f"Slots fora da hierarquia 1-10 (+11 opcional): {sorted(extras)}.")

    # --- ANCORA: evidencias tem que existir no _raw ----------------------
    if raw_dir and os.path.isdir(raw_dir):
        raw_blob, n = load_raw_blob(raw_dir)
        if n == 0:
            E("RAW_VAZIO", f"Pasta _raw '{raw_dir}' sem arquivos .json.")
        else:
            for origem, quote in evidencias_para_ancora:
                if not isinstance(quote, str) or len(quote.strip()) < EVIDENCIA_MIN_CHARS:
                    E("EVIDENCIA_CURTA",
                      f"{origem}: evidencia curta/invalida ('{quote}').")
                elif not evidencia_ancorada(quote, raw_blob):
                    E("EVIDENCIA_INVENTADA",
                      f"{origem}: citacao NAO encontrada no texto bruto dos concorrentes "
                      f"(parafrase ou inventada): '{quote}'.")
    else:
        err.append(("WARN_SEM_RAW",
                    "Pasta _raw nao informada (--raw-dir): verificacao de ancora PULADA. "
                    "Rode com --raw-dir para travar reviews inventadas."))

    return err


def carregar_yaml(caminho):
    import yaml
    with open(caminho, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def main():
    ap = argparse.ArgumentParser(description="Trava de validacao do brief StorySelling.")
    ap.add_argument("brief", help="Caminho do brief .yaml")
    ap.add_argument("--raw-dir", help="Pasta _raw com os JSON brutos dos concorrentes")
    args = ap.parse_args()

    if not os.path.isfile(args.brief):
        print(f"ERRO: brief nao encontrado: {args.brief}", file=sys.stderr)
        sys.exit(2)

    # auto-descoberta do _raw se nao passado: irmao 'inteligencia/_raw'
    raw_dir = args.raw_dir
    if not raw_dir:
        cand = os.path.join(os.path.dirname(args.brief), "_raw")
        if os.path.isdir(cand):
            raw_dir = cand

    brief = carregar_yaml(args.brief)
    erros = validate_brief(brief, raw_dir=raw_dir)

    hard = [e for e in erros if not e[0].startswith("WARN")]
    warns = [e for e in erros if e[0].startswith("WARN")]

    for code, msg in warns:
        print(f"  [aviso] {code}: {msg}")

    if hard:
        print(f"\nBRIEF REJEITADO - {len(hard)} erro(s):")
        for code, msg in hard:
            print(f"  [{code}] {msg}")
        sys.exit(1)

    print(f"BRIEF OK — {os.path.basename(args.brief)} passou na trava StorySelling.")
    sys.exit(0)


if __name__ == "__main__":
    main()
