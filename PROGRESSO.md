# PROGRESSO

> Atualizado 2026-06-26. **5L (VIE_1066) FECHADO E APROVADO** — 10 fotos sem marca em `output/2026-06-21-conforme-5L/fotos/VIE_1066-PAI/` (incl. foto-08 local). Detalhe da sessão em HISTORICO (2026-06-24). **RETOMAR EM: replicar as 10 pro 8L (VIE_1067) + publicação.**

## 0. ARQUITETURA PRODUTO-TRAVADO (2026-06-23) — em uso
O produto NÃO é re-renderizado, é composição (mata edit-drift). Detalhe em HISTORICO/DECISOES + plano `~/.claude/plans/bubbly-sleeping-ember.md`.
- Studio/neutro (3,4,9,10) = `compose.py` (produto travado + fundo por código; fidelidade por hash).
- Lifestyle (capa,2,5,7,8) = híbrido / one-shot do hero fiel com `--lock`; **`--edit` PROIBIDO** p/ corrigir produto.
- Produtos travados em `pipeline/data/produtos-travados/`.

## 0b. Overlay (3 arquétipos, `render_faixa.py`) — bake-ins desta rodada
- `faixa-clara` (studio) com **framing_gate** (autofit + gate inpulável: produto nunca cortado pela faixa).
- `scrim` (lifestyle escuro). · `plate` (lifestyle com parede/área clara: texto tinta escura, sem faixa/scrim).
- Regras duras: inox natural em lifestyle (inox_cast só studio) · proporção ≤0,33 medida (exceção foto de ação ~0,4) · sem saco no interior · tampa BRANCA (não inox) · prompt_lint barra ratio/half em texto.

## 1. Próximas tarefas (ordem)
1. **Replicar as 10 fotos pro 8L (VIE_1067)** (mesmo diâmetro, mais alto — 18×34). Brief `.../inteligencia/brief-VIE_1067-PAI.yaml`. Reusar pipeline/regras do 5L.
2. Validar **regras de imagem do ML** (capa exige fundo branco?) num anúncio E2E antes de publicar.
3. Subir fotos ao bucket `tcd-produtos` (precisa SERVICE_ROLE) → Step-08 Vinícius → Step-09 → Step-10 publicar.

## 2. Regras de trabalho (Almir) — INFALÍVEIS
- **CONFERIR medindo (não afirmar) ANTES de apresentar** + **aprovar SEMPRE no Chrome dedicado**.
- **SEM MARCA em todo o anúncio** (sem logo/slogan E sem verde-marca; referência = método, não fonte de feature).

## 3. Pendências
- **SUPABASE_SERVICE_ROLE** (`sb_secret_...`): re-fornecer p/ subir ao bucket.
- **step-10:** `N8N_WEBHOOK_ML_PUBLICAR` ausente; workflow "ML Publicar" (`0rzNJ7RLqLzMbKnf`) INATIVO de propósito.
- `qa_imagens.py` pesado (BiRefNet) — rodar lote num processo só (evita OOM).
- Hook `check-write-path.ps1` não registrado no settings.json global — confirmar c/ Almir.
