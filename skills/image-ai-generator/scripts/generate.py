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
}

API_URL = "https://openrouter.ai/api/v1/chat/completions"

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


def generate_image(prompt, output_path, mode, api_key, reference_image=None, faithful=False, edit=False):
    """Generate a single image and save to output_path.

    edit=True: MODO EDIÇÃO ITERATIVA (Nano Banana). `reference_image` e a imagem
    ATUAL (geralmente a gerada na rodada anterior); `prompt` descreve UMA mudança
    isolada. O modelo muda SO isso e mantem o resto IDENTICO (composicao, camera,
    fundo, luz, props, produto). E a forma confiavel de ajustar escala/centro/cor
    sem a "amnesia" de regerar a cena do zero. Requer reference_image.

    faithful=True: reproduce the reference photo IDENTICALLY (same angle, framing,
    background, lighting) and apply ONLY the edits described in `prompt`. Use for
    faithful recolors/variations of a real product photo. Default (False) keeps the
    old behavior: re-stage the product in a new scene/angle.
    """
    model = MODELS.get(mode, MODELS["test"])

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    if reference_image and os.path.exists(reference_image):
        # Multimodal: send reference image + text prompt
        ext = os.path.splitext(reference_image)[1].lower()
        mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}
        mime = mime_map.get(ext, "image/png")
        with open(reference_image, "rb") as img_f:
            img_b64 = base64.b64encode(img_f.read()).decode("utf-8")
        if edit:
            # MODO EDICAO ITERATIVA: muda SO o que o prompt pede, preserva o resto.
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
            instr = (f"The reference image above IS the exact product to depict. Faithfully reproduce that same product — "
                     f"its exact shape, proportions, parts and finish — but you MAY place it at a different, more flattering "
                     f"camera angle and inside a new scene as described. Do NOT redesign the product, do NOT copy the "
                     f"reference's framing/background. {prompt}.{SCENE_COHERENCE} Only output the image, no extra text rendered in the image.")
        content = [
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}},
            {"type": "text", "text": instr}
        ]
    else:
        content = f"Generate an image: {prompt}. Only output the image, no text."

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
    parser.add_argument("--mode", choices=["test", "production", "pro"], default="test",
                        help="Generation mode: test (cheap), production (Nano Banana Flash) or pro (Gemini 3 Pro Image, mais fiel)")
    parser.add_argument("--reference", help="Path to reference image to include in the prompt")
    parser.add_argument("--faithful", action="store_true",
                        help="Reproduce the reference photo identically and apply only the prompt's edits (faithful recolor/variation)")
    parser.add_argument("--edit", action="store_true",
                        help="MODO EDICAO: --reference e a imagem atual; --prompt e UMA mudanca isolada; muda so isso e preserva o resto (iteracao Nano Banana)")
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
    print(f"Image Generator — Mode: {args.mode} | Model: {model}")

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
            if generate_image(prompt, output, args.mode, api_key, reference_image=ref, faithful=faithful, edit=edit):
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
        ok = generate_image(args.prompt, args.output, args.mode, api_key, reference_image=args.reference, faithful=args.faithful, edit=args.edit)
        if ok:
            gate_fidelidade(args.output, args.lock, args.no_qa)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
