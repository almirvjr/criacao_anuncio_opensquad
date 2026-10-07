#!/usr/bin/env python3
"""
Image Generator — Opensquad Skill
Generates images via Openrouter API using AI image models.

Usage:
  # Single image
  python3 generate.py --prompt "description" --output "path/to/image.jpg" --mode test

  # Single image with reference (logo/mascot)
  python3 generate.py --prompt "description" --output "path/to/image.jpg" --reference "path/to/logo.png" --mode production

  # Batch (JSON file with list of {prompt, output} objects)
  python3 generate.py --batch "path/to/batch.json" --mode production
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.request
import urllib.error

# Linter das boas praticas do Nano Banana (co-localizado). Roda em toda geracao.
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import prompt_lint
except Exception:
    prompt_lint = None

# Gate de fidelidade do produto (co-localizado). Roda apos gravar quando --lock e dado.
try:
    import fidelity
except Exception:
    fidelity = None

# Model configuration per mode
MODELS = {
    "test": "sourceful/riverflow-v2-fast",
    "production": "google/gemini-3.1-flash-image-preview",
    "pro": "google/gemini-3-pro-image",
    # 2026-09-17: GPT Image 2. Mediu MELHOR escala que os Gemini no bake-off do 8L
    # (erro medio +0,08 contra +0,23 do pro). So existe na API de imagem
    # (/images/generations), nao no /chat/completions.
    "gpt": "openai/gpt-image-2",
}

API_URL = "https://openrouter.ai/api/v1/chat/completions"
# API propria de imagem: aceita tamanho e devolve 2048x2048. O /chat/completions
# IGNORA pedido de tamanho e hoje entrega 1024 (em junho/2026 entregava 1200).
IMAGES_API_URL = "https://openrouter.ai/api/v1/images/generations"
TAMANHO_PADRAO = "2048x2048"
# Contrato da squad (REFERENCIA.md): 1200x1200 EXATOS, senao o qa_imagens veta e os
# moldes do overlay saem fora de lugar. Geramos GRANDE e reduzimos — reduzir de 2048
# preserva nitidez; o caminho antigo AMPLIAVA de 1024, que borra.
NORMALIZAR_PARA = (1200, 1200)
# So estes rodam na API de imagem (conferido em 17/09/2026).
MODELOS_API_IMAGEM = {"google/gemini-3-pro-image", "google/gemini-3.1-flash-image",
                      "google/gemini-3.1-flash-image-preview", "google/gemini-3.1-flash-lite-image",
                      "google/gemini-2.5-flash-image", "openai/gpt-image-2"}
# ARMADILHA REAL (17/09/2026): com o nome de parametro errado (image/image_urls) a API
# aceita, COBRA e IGNORA a referencia em silencio — devolveu outro produto. O nome certo
# e input_references. Uma referencia custa centenas de tokens de entrada; sem ela o
# prompt_tokens fica rasteiro (~10). Este piso transforma o erro mudo em erro barulhento.
MIN_TOKENS_COM_REFERENCIA = 200

# Coerencia de cena: anexado automaticamente a TODA geracao com cena (modo nao-faithful),
# pra o Gemini nao por objetos em lugares sem sentido (ex.: toalha no chao). Regra do Almir.
SCENE_COHERENCE = (
    " SCENE COHERENCE (mandatory): every prop must be where it realistically belongs in the room. "
    "Towels go on a towel rail/ring or folded on the counter/shelf — NEVER on the floor. "
    "Soap, plants (small), toothbrush holders, decor go on the counter/shelf — NOT on the floor. "
    "On the FLOOR only put things that really live on the floor: a rug/bath mat, a large floor plant in a pot, or a laundry basket. "
    "No object floating or placed unnaturally; everything consistent with this room type. "
    "Do NOT put towels, soap or counter items on the floor."
)


def load_api_key():
    """Load OPENROUTER_API_KEY from environment."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        # Try loading from .env in project root
        env_candidates = [
            os.path.join(os.getcwd(), ".env"),
            os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"),
        ]
        for env_path in env_candidates:
            env_path = os.path.abspath(env_path)
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("OPENROUTER_API_KEY=") and not line.startswith("#"):
                            key = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break
                if key:
                    break
    if not key:
        print("ERROR: OPENROUTER_API_KEY not found in environment or .env file", file=sys.stderr)
        sys.exit(1)
    return key


def _instrucao_com_referencia(prompt, edit=False, faithful=False):
    """Texto que acompanha a foto de referencia. Identico nos dois caminhos de API."""
    if edit:
        return (f"The attached image is the CURRENT version. Change ONLY the following, and keep "
                f"EVERYTHING ELSE in the image EXACTLY THE SAME - same composition, same framing and crop, "
                f"same camera angle, same background and scene, same lighting and reflections, same props, "
                f"and the product's exact shape, proportions, parts and finish: {prompt}. "
                f"Do not regenerate or re-stage the scene from scratch; this is a local edit on top of the "
                f"attached image. Output the full edited image, no extra text rendered in the image.")
    if faithful:
        return (f"The reference image above IS the exact product AND the exact photograph to reproduce. "
                f"Reproduce this photo with MAXIMUM FIDELITY: keep the SAME camera angle, SAME framing and composition, "
                f"SAME background, SAME lighting and reflections, and the product's EXACT shape, proportions, parts and finish. "
                f"Apply ONLY the following change and NOTHING else: {prompt}. "
                f"Do NOT redesign the product, do NOT move the camera, do NOT change the scene or background. "
                f"Only output the image, no extra text rendered in the image.")
    return (f"The reference image above IS the exact product to depict. Faithfully reproduce that same product - "
            f"its exact shape, proportions, parts, materials and finish - and place it inside the new scene "
            f"described below. The camera framing and the product's viewing angle are dictated by that description: "
            f"do NOT pick a more 'flattering' or heroic angle on your own, and do NOT tilt the camera up at the "
            f"product - that inflates it and breaks its real-world scale. Do NOT redesign the product, do NOT copy "
            f"the reference's framing/background. {prompt}.{SCENE_COHERENCE} Only output the image, no extra text rendered in the image.")


def normalizar_1200(output_path, normalizar=True):
    """Reduz/ajusta a imagem gravada pro canvas exigido pela pipeline (1200x1200)."""
    if not normalizar:
        return None
    try:
        from PIL import Image
    except ImportError:
        print("  [aviso] Pillow ausente: nao deu pra normalizar pra 1200x1200.", file=sys.stderr)
        return None
    try:
        with Image.open(output_path) as im:
            nativo = im.size
            if tuple(nativo) == NORMALIZAR_PARA:
                return nativo
            im = im.convert("RGB").resize(NORMALIZAR_PARA, Image.LANCZOS)
        im.save(output_path, quality=95)
        return nativo
    except Exception as e:
        print(f"  [aviso] falhou ao normalizar ({type(e).__name__}); arquivo mantido como veio.",
              file=sys.stderr)
        return None


def _b64_referencia(reference_image):
    ext = os.path.splitext(reference_image)[1].lower()
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".webp": "image/webp", ".gif": "image/gif"}.get(ext, "image/png")
    with open(reference_image, "rb") as fh:
        return "data:%s;base64,%s" % (mime, base64.b64encode(fh.read()).decode("utf-8"))


def gerar_pela_api_de_imagem(prompt, output_path, model, api_key, reference_image=None,
                             faithful=False, tamanho=TAMANHO_PADRAO, normalizar=True):
    """Caminho NOVO (17/09/2026): /images/generations. Aceita tamanho (2048x2048) e
    recebe a referencia por `input_references`. Devolve True/False."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    tem_ref = bool(reference_image and os.path.exists(reference_image))
    corpo = {"model": model, "aspect_ratio": "1:1", "size": tamanho,
             "prompt": (_instrucao_com_referencia(prompt, edit=False, faithful=faithful) if tem_ref
                        else f"Generate an image: {prompt}.{SCENE_COHERENCE} Only output the image, no text.")}
    if tem_ref:
        corpo["input_references"] = [{"type": "image_url",
                                      "image_url": {"url": _b64_referencia(reference_image)}}]
    req = urllib.request.Request(IMAGES_API_URL, data=json.dumps(corpo).encode("utf-8"),
                                 headers={"Authorization": f"Bearer {api_key}",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=420) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"  API error [{e.code}]: {e.read().decode('utf-8', errors='replace')[:200]}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  Request error: {e}", file=sys.stderr)
        return False

    usage = data.get("usage") or {}
    if tem_ref and (usage.get("prompt_tokens") or 0) < MIN_TOKENS_COM_REFERENCIA:
        print(f"  ABORTADO: mandei a referencia e a API cobrou sem recebe-la "
              f"(prompt_tokens={usage.get('prompt_tokens')}, minimo {MIN_TOKENS_COM_REFERENCIA}). "
              f"A imagem sairia com OUTRO produto. Nada foi gravado.", file=sys.stderr)
        return False

    item = (data.get("data") or [{}])[0]
    b64 = item.get("b64_json") or (item.get("image_url") or {}).get("url") or ""
    if not b64:
        print(f"  No image returned by model {model}", file=sys.stderr)
        return False
    with open(output_path, "wb") as fh:
        fh.write(base64.b64decode(b64.split(",", 1)[1] if "," in b64 else b64))

    nativo = normalizar_1200(output_path, normalizar)
    custo = registrar_custo(output_path, data, model)
    extra = f" | custo ${custo:.4f}" if custo is not None else " | custo n/d"
    onde = (f"{NORMALIZAR_PARA[0]}x{NORMALIZAR_PARA[1]} reduzido de {nativo[0]}x{nativo[1]}"
            if nativo else tamanho)
    print(f"  OK: {output_path} ({os.path.getsize(output_path)/1024:.0f} KB, {onde}){extra}")
    return True


def generate_image(prompt, output_path, mode, api_key, reference_image=None, faithful=False, edit=False,
                   api="images", tamanho=TAMANHO_PADRAO, normalizar=True):
    """Generate a single image and save to output_path.

    edit=True: MODO EDIÇÃO SO DE FUNDO/CENARIO (Nano Banana). `reference_image` e a
    imagem ATUAL; `prompt` descreve UMA mudança isolada que NAO toca o produto — troca
    de fundo, luz do ambiente, um prop do cenario. PROIBIDO usar --edit pra corrigir o
    PRODUTO (escala, centro, cor, forma, partes, acabamento): --edit re-renderiza a
    cena TODA e regride detalhes ja aprovados do produto (edit-drift; arquitetura
    produto-travado, CLAUDE.md 2026-06-23). Correcao de escala/centro/cor/forma do
    produto NAO se faz aqui: e composicao (compose.py + PNG travado) ou one-shot
    regenerado, conforme a politica por slot do CLAUDE.md. Requer reference_image.

    faithful=True: reproduce the reference photo IDENTICALLY (same angle, framing,
    background, lighting) and apply ONLY the edits described in `prompt`. Use for
    faithful recolors/variations of a real product photo. Default (False) re-stages
    the product in a new scene — o angulo vem do prompt/template, nao da escolha do
    modelo (angulo "lisonjeiro" incha o produto e quebra a escala).
    """
    model = MODELS.get(mode, MODELS["test"])

    # 2026-09-17: por padrao vai pela API de imagem — e a unica que aceita tamanho
    # (2048x2048) e a unica que o modelo "gpt" atende. O /chat/completions fica para
    # --edit (nao testado na API de imagem) e para --api chat (escotilha de volta).
    if (not edit) and api == "images" and model in MODELOS_API_IMAGEM:
        return gerar_pela_api_de_imagem(prompt, output_path, model, api_key,
                                        reference_image=reference_image,
                                        faithful=faithful, tamanho=tamanho,
                                        normalizar=normalizar)
    if api == "images" and model not in MODELOS_API_IMAGEM and not edit:
        print(f"  [aviso] {model} nao existe na API de imagem; indo pelo caminho antigo "
              f"(sai 1024x1024).", file=sys.stderr)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    if reference_image and os.path.exists(reference_image):
        # Multimodal: send reference image + text prompt
        ext = os.path.splitext(reference_image)[1].lower()
        mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}
        mime = mime_map.get(ext, "image/png")
        with open(reference_image, "rb") as img_f:
            img_b64 = base64.b64encode(img_f.read()).decode("utf-8")
        if edit:
            # MODO EDICAO SO DE FUNDO/CENARIO: muda SO o fundo/luz/prop pedido, preserva o resto (inclusive o produto).
            instr = (f"The attached image is the CURRENT version. Change ONLY the following, and keep "
                     f"EVERYTHING ELSE in the image EXACTLY THE SAME — same composition, same framing and crop, "
                     f"same camera angle, same background and scene, same lighting and reflections, same props, "
                     f"and the product's exact shape, proportions, parts and finish: {prompt}. "
                     f"Do not regenerate or re-stage the scene from scratch; this is a local edit on top of the "
                     f"attached image. Output the full edited image, no extra text rendered in the image.")
        elif faithful:
            instr = (f"The reference image above IS the exact product AND the exact photograph to reproduce. "
                     f"Reproduce this photo with MAXIMUM FIDELITY: keep the SAME camera angle, SAME framing and composition, "
                     f"SAME background, SAME lighting and reflections, and the product's EXACT shape, proportions, parts and finish. "
                     f"Apply ONLY the following change and NOTHING else: {prompt}. "
                     f"Do NOT redesign the product, do NOT move the camera, do NOT change the scene or background. "
                     f"Only output the image, no extra text rendered in the image.")
        else:
            # O angulo vem do TEMPLATE (campo "angulo" de cada slot no photo-templates.md),
            # nunca do gosto do modelo: "mais lisonjeiro" e sinonimo de heroico/contra-plongee,
            # que INCHA o produto e quebra a escala real medida (CLAUDE.md / prompt_lint CAMERA_INFLA).
            instr = (f"The reference image above IS the exact product to depict. Faithfully reproduce that same product — "
                     f"its exact shape, proportions, parts, materials and finish — and place it inside the new scene "
                     f"described below. The camera framing and the product's viewing angle are dictated by that description: "
                     f"do NOT pick a more 'flattering' or heroic angle on your own, and do NOT tilt the camera up at the "
                     f"product — that inflates it and breaks its real-world scale. Do NOT redesign the product, do NOT copy "
                     f"the reference's framing/background. {prompt}.{SCENE_COHERENCE} Only output the image, no extra text rendered in the image.")
        content = [
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}},
            {"type": "text", "text": instr}
        ]
    else:
        # Sem referencia = geracao pura de cena a partir do texto (nao ha produto a
        # preservar; --edit e barrado pelo argparse sem --reference, e --faithful nao
        # faz sentido sem foto pra reproduzir). Logo e SEMPRE cena -> anexa SCENE_COHERENCE.
        content = f"Generate an image: {prompt}.{SCENE_COHERENCE} Only output the image, no text."

    payload = json.dumps({
        "model": model,
        "messages": [{
            "role": "user",
            "content": content
        }],
        "usage": {"include": True}   # pede o custo real (USD) na resposta do OpenRouter
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        print(f"  API error [{e.code}]: {error_body[:200]}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  Request error: {e}", file=sys.stderr)
        return False

    images = data.get("choices", [{}])[0].get("message", {}).get("images", [])
    if not images:
        # Some models return image in content as base64
        content_resp = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if content_resp and isinstance(content_resp, str) and content_resp.startswith("data:image"):
            img_data = content_resp.split(",", 1)[1] if "," in content_resp else content_resp
        else:
            print(f"  No image returned by model {model}", file=sys.stderr)
            return False
    else:
        img_data = images[0].get("image_url", {}).get("url", "")
        if img_data.startswith("data:"):
            img_data = img_data.split(",", 1)[1]

    with open(output_path, "wb") as f:
        f.write(base64.b64decode(img_data))

    size_kb = os.path.getsize(output_path) / 1024
    custo = registrar_custo(output_path, data, model)
    extra = f" | custo ${custo:.4f}" if custo is not None else " | custo n/d"
    print(f"  OK: {output_path} ({size_kb:.0f} KB){extra}")
    return True


def registrar_custo(output_path, data, model):
    """Extrai o custo real (USD) do usage do OpenRouter e acumula num CSV na pasta
    de saida (_custos.csv). Retorna o custo desta chamada (ou None se indisponivel)."""
    usage = data.get("usage") or {}
    custo = usage.get("cost")
    if custo is None:
        # alguns retornos aninham em cost_details/total_cost
        custo = (usage.get("cost_details") or {}).get("upstream_inference_cost") or usage.get("total_cost")
    try:
        custo = float(custo) if custo is not None else None
    except (TypeError, ValueError):
        custo = None
    try:
        pasta = os.path.dirname(os.path.abspath(output_path)) or "."
        csv = os.path.join(pasta, "_custos.csv")
        novo = not os.path.exists(csv)
        with open(csv, "a", encoding="utf-8") as fh:
            if novo:
                fh.write("arquivo,modelo,prompt_tokens,completion_tokens,custo_usd\n")
            fh.write(f"{os.path.basename(output_path)},{model},"
                     f"{usage.get('prompt_tokens','')},{usage.get('completion_tokens','')},"
                     f"{('%.6f' % custo) if custo is not None else ''}\n")
        # total acumulado da pasta (so quando ha custo)
        if custo is not None:
            total = 0.0
            for ln in open(csv, encoding="utf-8").read().splitlines()[1:]:
                parts = ln.rsplit(",", 1)
                if len(parts) == 2 and parts[1]:
                    try:
                        total += float(parts[1])
                    except ValueError:
                        pass
            print(f"  [custo] acumulado nesta pasta: ${total:.4f}", file=sys.stderr)
    except Exception:
        pass
    return custo


def checar_prompt(prompt, edit, no_lint):
    """Roda a trava de boas praticas do Nano Banana. Sai (exit 2) num BLOQUEIO,
    a menos de --no-lint. Avisos so imprimem."""
    if not prompt or prompt_lint is None or no_lint:
        return
    issues = prompt_lint.lint_prompt(prompt, edit=edit)
    if not issues:
        return
    print("Boas praticas do prompt (Nano Banana):", file=sys.stderr)
    print(prompt_lint.formatar(issues), file=sys.stderr)
    if any(n == "BLOCK" for n, _, _ in issues):
        print("  -> BLOQUEADO. Reescreva o prompt (ou use --no-lint pra forcar).", file=sys.stderr)
        sys.exit(2)


def gate_fidelidade(output_path, lock_manifest, no_qa):
    """Gate de fidelidade do produto (rota ONE-SHOT). Roda APOS gravar a imagem.
    So pega DESASTRE (produto ausente/area absurda) — fidelidade fina e olho humano +
    inox_cast (a rota composicao usa proveniencia, nao este gate). Reprova -> move o
    arquivo pra _rejeitado/ e sai com exit 3. Override consciente: --no-qa."""
    if not lock_manifest or no_qa or fidelity is None:
        return
    r = fidelity.disaster_check(output_path)
    tag = "OK" if r["ok"] else "REPROVA"
    print(f"  [gate produto:{r['rota']}] {tag} | {r['motivo']}", file=sys.stderr)
    if not r["ok"]:
        quaran = os.path.join(os.path.dirname(output_path) or ".", "_rejeitado")
        os.makedirs(quaran, exist_ok=True)
        dest = os.path.join(quaran, os.path.basename(output_path))
        try:
            os.replace(output_path, dest)
        except OSError:
            dest = output_path
        print(f"  -> REPROVADO pelo gate de produto. Movido pra {dest}. (override: --no-qa)", file=sys.stderr)
        sys.exit(3)


def main():
    parser = argparse.ArgumentParser(description="Generate images via Openrouter API")
    parser.add_argument("--prompt", help="Text prompt for single image generation")
    parser.add_argument("--output", help="Output file path for single image")
    parser.add_argument("--batch", help="Path to JSON batch file")
    parser.add_argument("--mode", choices=["test", "production", "pro", "gpt"], default="gpt",
                        help="Motor: test (barato), production (Nano Banana 2 Flash), pro (Nano Banana Pro) ou gpt (GPT Image 2 - melhor escala medida no bake-off de 17/09/2026)")
    parser.add_argument("--api", choices=["images", "chat"], default="images",
                        help="images (padrao): /images/generations, aceita --size e devolve 2048x2048. chat: caminho antigo /chat/completions, sai 1024x1024 e ignora --size. --edit usa chat sempre.")
    parser.add_argument("--size", default=TAMANHO_PADRAO,
                        help=f"tamanho que a IA gera na API de imagem (padrao {TAMANHO_PADRAO}); ignorado com --api chat")
    parser.add_argument("--nativo", action="store_true",
                        help=f"NAO reduzir pra {NORMALIZAR_PARA[0]}x{NORMALIZAR_PARA[1]}; grava do tamanho que a IA devolveu. A pipeline VETA dimensao diferente — use so fora dela")
    parser.add_argument("--reference", help="Path to reference image to include in the prompt")
    parser.add_argument("--faithful", action="store_true",
                        help="Reproduce the reference photo identically and apply only the prompt's edits (faithful recolor/variation)")
    parser.add_argument("--edit", action="store_true",
                        help="MODO EDICAO SO DE FUNDO/CENARIO: --reference e a imagem atual; --prompt e UMA mudanca no fundo/luz/prop que NAO toca o produto. PROIBIDO pra corrigir o produto (escala/centro/cor/forma) — isso e edit-drift; usar composicao ou one-shot")
    parser.add_argument("--no-lint", action="store_true",
                        help="pula a trava de boas praticas do prompt (use so se souber o que esta fazendo)")
    parser.add_argument("--lock", help="manifesto do produto travado (produtos-travados/SKU.json): ativa o gate de fidelidade do produto APOS gravar; produto ausente -> reprova e move pra _rejeitado/")
    parser.add_argument("--no-qa", action="store_true",
                        help="pula o gate de fidelidade do produto (override consciente)")
    args = parser.parse_args()

    if args.edit and not (args.reference or args.batch):
        parser.error("--edit requer --reference (a imagem atual a ser editada)")

    if not args.prompt and not args.batch:
        parser.error("Either --prompt or --batch is required")

    api_key = load_api_key()
    model = MODELS[args.mode]
    print(f"Image Generator — Mode: {args.mode} | Model: {model} | API: {args.api}" + (f" | {args.size}" if args.api == "images" else ""))

    if args.batch:
        # Batch mode
        with open(args.batch, "r") as f:
            items = json.load(f)
        print(f"Generating {len(items)} images...\n")
        success = 0
        for i, item in enumerate(items, 1):
            prompt = item["prompt"]
            output = item["output"]
            ref = item.get("reference")
            faithful = item.get("faithful", args.faithful)
            edit = item.get("edit", args.edit)
            checar_prompt(prompt, edit, args.no_lint)
            print(f"[{i}/{len(items)}] {os.path.basename(output)}...")
            if generate_image(prompt, output, args.mode, api_key, reference_image=ref, faithful=faithful, edit=edit,
                              api=args.api, tamanho=args.size, normalizar=not args.nativo):
                gate_fidelidade(output, item.get("lock", args.lock), args.no_qa)
                success += 1
            if i < len(items):
                time.sleep(1)  # Rate limiting
        print(f"\nDone: {success}/{len(items)} images generated.")
        sys.exit(0 if success == len(items) else 1)
    else:
        # Single mode
        if not args.output:
            parser.error("--output is required for single image generation")
        checar_prompt(args.prompt, args.edit, args.no_lint)
        print(f"Generating: {os.path.basename(args.output)}...")
        ok = generate_image(args.prompt, args.output, args.mode, api_key, reference_image=args.reference,
                            faithful=args.faithful, edit=args.edit, api=args.api, tamanho=args.size,
                            normalizar=not args.nativo)
        if ok:
            gate_fidelidade(args.output, args.lock, args.no_qa)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
