#!/usr/bin/env python3
"""peneirar.py — escolhe a melhor tentativa de cada foto e so mostra as finalistas.

Nasceu do fato medido em 22/09/2026: a forma do produto VARIA de rodada pra rodada
com o mesmo pedido (1,86 a 2,13; ~45% caem dentro da tolerancia). Nao adianta caçar
a frase perfeita — adianta gerar N tentativas e deixar a maquina peneirar.

Junta os dois portoes que ja existem:
  - juiz_escala.py  -> forma do produto e escala contra o movel
  - inox_cast.py    -> inox dourado

Agrupa por SLOT pelo nome do arquivo (`<slot>-t<N>.jpg`) e, em cada slot, escolhe a
tentativa APROVADA com a forma mais proxima do alvo. Slot sem nenhuma aprovada e
reportado como tal — nao promove a "menos pior" caladinho.

O que ele NAO faz: alinhamento dobradica-pedal (nao deu pra automatizar de forma
confiavel em 22/09 — e relacao 3D que uma silhueta achatada nao resolve) e gosto.
Essas duas ficam com o olho humano, mas so sobre as finalistas.

Uso:
  python peneirar.py PASTA --altura-cm 34 --diametro-cm 18
"""
import argparse
import glob
import os
import re
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import juiz_escala as J  # noqa: E402

INOX = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..",
                                    "skills", "image-overlay", "scripts", "inox_cast.py"))


def slot_de(caminho):
    nome = os.path.basename(caminho)
    m = re.match(r"^(.*)-t\d+\.(jpg|jpeg|png)$", nome, re.I)
    return m.group(1) if m else os.path.splitext(nome)[0]


def dourado(caminho):
    """Devolve (veredito, w_med) do gate de inox. None se nao deu pra rodar."""
    try:
        r = subprocess.run([sys.executable, INOX, caminho], capture_output=True,
                           text=True, timeout=300)
    except Exception:
        return None, None
    saida = (r.stdout or "").strip().splitlines()
    if not saida:
        return None, None
    linha = saida[-1]
    v = linha.rsplit("->", 1)[-1].strip() if "->" in linha else "?"
    m = re.search(r"w_med=\s*([+-]?\d+(?:\.\d+)?)", linha)
    return v, (float(m.group(1)) if m else None)


def main():
    ap = argparse.ArgumentParser(description="Peneira as tentativas e mostra so as finalistas.")
    ap.add_argument("pasta")
    ap.add_argument("--altura-cm", type=float, required=True)
    ap.add_argument("--diametro-cm", type=float, required=True)
    ap.add_argument("--bancada-cm", type=float, default=J.BANCADA_CM)
    ap.add_argument("--apenas", help="roda so os slots cujo nome comeca com isto "
                                     "(lista separada por virgula) — util p/ rodar em blocos "
                                     "e nao pesar a maquina")
    a = ap.parse_args()

    fotos = sorted(f for f in glob.glob(os.path.join(a.pasta, "*.jpg"))
                   if not os.path.basename(f).startswith("_"))
    if a.apenas:
        pref = tuple(x.strip() for x in a.apenas.split(",") if x.strip())
        fotos = [f for f in fotos if os.path.basename(f).startswith(pref)]
    if not fotos:
        print("nenhuma foto na pasta"); sys.exit(1)

    por_slot = {}
    for f in fotos:
        r = J.julgar(f, a.altura_cm, a.diametro_cm, a.bancada_cm)
        v_inox, w = dourado(f)
        r["inox"] = v_inox
        r["inox_w"] = w
        r["caminho"] = f
        # CRITERIO (revisto em 22/09/2026, com o Almir avisado):
        # Barra pelo que se mede BEM: forma do produto e inox dourado.
        # A escala e so INFORMADA. Motivo: em cena cheia (prateleira, gaveta, faixa de
        # parede) o detector acha 7 candidatos a linha da bancada em vez de 2, e o juiz
        # se recusa a cravar — bloqueando fotos boas. E o Almir ja aceitou a faixa larga
        # (~0,45) olhando a imagem. Escala com MEDIDA CONFIAVEL e FORA da faixa continua
        # barrando; escala que nao deu pra medir passa e vai pro olho humano.
        forma = r.get("forma") or {}
        forma_ok = forma.get("ok") is True
        escala = r.get("escala") or {}
        escala_barra = (escala.get("confianca") == "alta" and escala.get("ok") is False)
        r["finalista"] = forma_ok and v_inox in ("OK", "NEUTRO") and not escala_barra
        por_slot.setdefault(slot_de(f), []).append(r)

    alvo = a.altura_cm / a.diametro_cm
    finalistas, sem_saida = [], []
    for slot in sorted(por_slot):
        tentativas = por_slot[slot]
        bons = [t for t in tentativas if t["finalista"]]
        print(f"\n=== {slot} ({len(tentativas)} tentativas) ===")
        for t in tentativas:
            f = t.get("forma", {})
            marca = "  <== ESCOLHIDA" if False else ""
            e = t.get("escala") or {}
            esc = f"{e.get('medida','-')}{'' if e.get('confianca')=='alta' else '?'}"
            print(f"  {os.path.basename(t['caminho']):<34} forma {f.get('medida','?'):<5} "
                  f"escala {esc:<6} inox {(t['inox'] or '?'):<8} "
                  f"{'FINALISTA' if t['finalista'] else t['veredito']}{marca}")
        if bons:
            melhor = min(bons, key=lambda t: abs(t["forma"]["medida"] - alvo))
            finalistas.append(melhor)
            e = melhor.get("escala") or {}
            print(f"  -> ESCOLHIDA: {os.path.basename(melhor['caminho'])} "
                  f"(forma {melhor['forma']['medida']}, escala {e.get('medida','nao medida')}"
                  f"{'' if e.get('confianca')=='alta' else ' — sem confianca, conferir a olho'})")
        else:
            sem_saida.append(slot)
            print("  -> NENHUMA passou nos dois portoes")

    print("\n" + "=" * 60)
    print(f"FINALISTAS: {len(finalistas)} de {len(por_slot)} fotos")
    for t in finalistas:
        print(f"  {os.path.basename(t['caminho'])}")
    if sem_saida:
        print(f"SEM SAIDA (decidir com o Almir): {', '.join(sem_saida)}")
    print("\nFalta conferir a OLHO nas finalistas: alinhamento dobradica-pedal e gosto.")
    sys.exit(0 if not sem_saida else 4)


if __name__ == "__main__":
    main()
