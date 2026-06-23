# PROGRESSO

> Atualizado 2026-06-23 (ARQUITETURA PRODUTO-TRAVADO construída/testada + slots 6 e 7 aprovados).
> **RETOMAR EM: slot 9 (sobrecorreção) do ciclo conforme 5L — pelo PIPELINE PRODUTO-TRAVADO.**

## 0. ARQUITETURA PRODUTO-TRAVADO (2026-06-23) — base pronta
Resolveu o edit-drift do Nano Banana: **o produto não é re-renderizado, é composição.** Detalhe completo em HISTORICO.md (2026-06-23), DECISOES.md e plano `~/.claude/plans/bubbly-sleeping-ember.md`. Em uso:
- Studio/neutro (3,4,9,10) = `compose.py` (produto travado + fundo por código, custo IA 0, fidelidade por hash).
- Lifestyle (capa,2,5,8) = híbrido (compor+harmonizar; fallback one-shot do hero sem `--edit`).
- Slot 7 (pedal c/ pé) = one-shot com `generate.py --lock` (gate de produto após gravar).
- **`--edit` PROIBIDO p/ corrigir produto.** Produtos travados em `pipeline/data/produtos-travados/`.

## 1. Ciclo conforme 5L (VIE_1066) — EM ANDAMENTO
Pasta: `output/2026-06-21-conforme-5L/fotos/VIE_1066-PAI/`. Brief: `.../inteligencia/brief-VIE_1066-PAI.yaml` (cor-herói Branco; sem balde→disclosure foto 6). NÃO mexer no `_final` (run 2026-05-26).

| Slot | Status |
|---|---|
| 1 Capa (3 cores) · 2 A/D · 3 Tamanho · 4 Material | ✅ (capa warm; 2/3/4 reuso `_final`) |
| 5 Lifestyle Emocional | ✅ gerado (SEM texto) |
| 6 Clareza · 7 Pedal | ✅ APROVADOS (SEM texto) — ver HISTORICO |
| 8 Lifestyle Uso Real | reuso `_final` foto-08 ($0) |
| **9 Sobrecorreção** | **RETOMAR** — composição studio + selos transparência "sem balde/saco comum" no overlay |
| 10 Macro-Yes+CTA | gerar (não existia no `_final`; SEM MARCA) |

**Overlays de texto pendentes** (slots 5,6,7,9,10) via `render_faixa.py` num bloco no fim. 6/9/10 = infográficos pesados de texto.

## 2. Próximas tarefas (ordem)
1. **Slot 9 → 10** pelo pipeline produto-travado (composição; conferir no Chrome dedicado).
2. **Overlays** (render_faixa) nos slots gerados.
3. Replicar 10 fotos pro **8L (VIE_1067)** (18×34). Subir ao bucket `tcd-produtos` (precisa SERVICE_ROLE).
4. Step-08 Vinícius → Step-09 → Step-10 publicar.

## 3. Regras de trabalho (Almir) — INFALÍVEIS
- **CHECKLIST + CONFERÊNCIA (medir, não afirmar) ANTES de apresentar** (`feedback_checklist_imagem_antes_de_apresentar`).
- **Aprovação SEMPRE abrindo no Chrome dedicado** (chrome-devtools-mcp).
- **SEM MARCA em todo o anúncio** (19/06). Referência = método, não fonte de feature.

## 4. Pendências
- **Regras de imagem do ML** antes de publicar (capa exige fundo branco? validar 1 anúncio E2E).
- Hook PostToolUse opcional (defesa extra); `check-write-path.ps1` não registrado no settings.json global — confirmar c/ Almir.
- **SUPABASE_SERVICE_ROLE** (`sb_secret_...`): re-fornecer p/ subir ao bucket.
- **step-10:** `N8N_WEBHOOK_ML_PUBLICAR` ausente; workflow "ML Publicar" (`0rzNJ7RLqLzMbKnf`) INATIVO de propósito.
- `qa_imagens.py` pesado (BiRefNet) — rodar lote num processo só (cutout cacheia); evita OOM.
