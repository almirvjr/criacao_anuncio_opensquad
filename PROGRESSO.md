# PROGRESSO

## Estado atual — Fase 5 (fotos): CAPAS ok + BLOCO 1 (faixa-clara) do 5L feito

**Run ID:** `2026-05-26-091553` — `squads/ml-anuncios/output/2026-05-26-091553/`
**Lote:** lixeiras Viel 5L (VIE_1066-PAI, R$150) e 8L (VIE_1067-PAI, R$200), 3 cores (Branco/Preto/Cinza), modo `variacoes`. Cor-herói = Branco. Dims reais: 5L 18×25, 8L 18×34.

Steps 02-06 concluídos (dossiê, categorização MLB33375, brief Helena, copy Renata). Capas 6/6 aprovadas (15/06). Títulos: **5L** "Lixeira Inox 5L Pedal Tampa Banheiro Cozinha Escritório" / **8L** "Lixeira Inox 8L Pedal Tampa Cozinha Banheiro Sofisticada".

### Sistema de overlay (TRAVADO) — detalhe em HISTORICO 16/17-06 e memória
- **Identidade da marca** em `_memory/brand-identity.md`: Montserrat + marrom #541D03 / terracota #EBB28A / verde #228D40 / creme. Logo real em `_memory/brand-recon/terra-logo-clean.png`.
- **Render = Python/Pillow** (NÃO browser): `skills/image-overlay/scripts/render_faixa.py` (config JSON, `dim_style`, badge, selos, `band_h`, logo, modo técnico) + `fit_scale.py` + `compose_two.py`.
- **Detecção de produto = BiRefNet** (`cutout.py`, rembg, offline R$0) nos 3 scripts; fallback p/ heurística se faltar (`CUTOUT_DISABLE=1`). Deps: `pip install rembg onnxruntime`.
- **Gate de cor do inox** (`inox_cast.py`): reprova "dourado" (`w_med>=14`) → pedir retry. Rodar antes de aprovar foto de inox.
- **Receita base (v9):** esbelta (~1,4-1,5×, nunca squat) + reflexo inox estilo CAPA (espelhado vidrado quente) + prata neutro.

### BLOCO 1 (faixa-clara) — `VIE_1066-PAI/_final/`
- `foto-09-sobrecorrecao.jpg` ✅ · `foto-05-clareza.jpg` ✅ (lixeira + caixa kraft em pé) · `foto-03-tamanho.jpg` ✅ (FOTO TÉCNICA: cota engenharia + 5 Litros). Capa esbelta = `_redesign/capa-branco-slim.jpg` (pendente substituir). Configs em `_redesign-overlay/cfg-foto{3,5,9}.json`.

## Próximas tarefas (retomar daqui)
0. **Substituir capa:** `cp _redesign/capa-branco-slim.jpg _final/capa-5L-branco.jpg` (após OK).
1. **BLOCO 2 — construir arquétipos scrim no render_faixa.py:** scrim-minimal (slots 6 pedal, 7 durabilidade), scrim imersivo (8 lifestyle), scrim+CTA (10 macro-yes), antes/depois (2). Cada: base Nano Banana (receita v9) + overlay. **Rodar `inox_cast.py` em cada base nova** (retry se dourado). Conteúdo em `inteligencia/brief-VIE_1066-PAI.yaml`.
2. Replicar as 9 pro **8L (VIE_1067)** (brief próprio). `picture_ids` = 1 capa + 9 StorySelling = 10. Subir ao bucket `tcd-produtos` (precisa SERVICE_ROLE).
3. Step-08 Vinícius → Step-09 Checkpoint B (dry-run) → Step-10 publicar com OK.
4. Após publicar: vincular SKU→MLB manual no Tiny.

### ⚠️ Regra de trabalho (Almir exigiu)
Antes de mandar imagem pra validação, **rodar o checklist de TODAS as orientações** dele e reportar o status real (medido, não no olho). Se consertar um lado e quebrar outro, AVISAR. Ver DECISOES 16/17-06.

## Pendências
- **SUPABASE_SERVICE_ROLE** (`sb_secret_...`): re-fornecer ao retomar: `! $env:SUPABASE_SERVICE_ROLE='<chave>'`.
- **Publicação (step-10):** `N8N_WEBHOOK_ML_PUBLICAR` ausente do `.env`; workflow "ML Publicar" (`0rzNJ7RLqLzMbKnf`) INATIVO de propósito.
- `generate.py` devolve 1024×1024 → normalizar pra 1200×1200 (PIL LANCZOS). `OPENROUTER_API_KEY` no `.env`.
