# PROGRESSO

## Estado atual — Fase 5 (fotos): conjunto do 5L (VIE_1066) quase fechado
**Run ID:** `2026-05-26-091553`. Lote: lixeiras Viel **5L** (VIE_1066, R$150) e **8L** (VIE_1067, R$200), 3 cores. Cor-herói = Branco. Dims reais: 5L 18×25, 8L 18×34.

### Conjunto 5L em `VIE_1066-PAI/_final/` (TODAS sem marca)
- **Capas** branco/preto/cinza ✅ (aberta hero, "gabinete cortado" p/ escala).
- Foto **2** antes/depois ✅ · **3** cotas ✅ · **4** macro inox ✅ · **5** embalagem ✅ · **6** pedal ✅ · **7** macro dobradiça ✅ · **8** lifestyle banheiro ✅ · **9** selos ✅.
- **Falta: foto 10 (CTA)** — regerar com Gemini Pro (cena aspiracional + selo + botão, sem marca).

### Ferramentas/método (ver DECISOES 18-19/06)
- **Gemini 3 Pro Image** (`generate.py --mode pro`) = fiel, acerta de 1ª. Cenas/lifestyle/antes-depois = **1 geração via JSON** (NÃO compor recorte = vira "figurinha").
- **Heros fiéis** (refs mestras): `_redesign-overlay/branco-studio-fiel.jpg` (aberto) e `branco-studio-fiel-fechada.jpg` (fechado, recolor da foto real). Macro de detalhe = recorte da foto real + `faithful`.
- `generate.py`: modos `faithful` (recolor idêntico) e `pro`; cláusula **`SCENE_COHERENCE`** anexada auto em toda cena (props no lugar certo).
- Overlay = Pillow (`render_faixa.py`: faixa-clara + `layout:"scrim"`). **Sem logo/slogan por padrão** (gate `show_brand`, off).

## Próximas tarefas
1. **Foto 10 (CTA)** com Pro (sem marca, coerência, escala medida) + overlay selo/botão.
2. Replicar as 9 + capa pro **8L (VIE_1067)**. `picture_ids` = 1 capa + 9 = 10. Subir ao bucket `tcd-produtos` (precisa SERVICE_ROLE).
3. Step-08 Vinícius → Step-09 dry-run → Step-10 publicar. Depois vincular SKU→MLB no Tiny.
4. **Validar briefing da Helena vs agente-referência** (Almir manda as respostas aos poucos; corrigir a Helena se divergir). Ver memória `criacao_anuncio_validar_helena_vs_referencia`.
5. (Opcional) Regerar capas/6/7 (eram Flash) com Gemini Pro p/ mais fidelidade.

### ⚠️ Regras de trabalho (Almir)
- **CHECKLIST medido ANTES de pedir aprovação** (`_memory/memories.md`): materiais (tampa/aro/pedal=plástico branco, só corpo=inox) · aba alinhada ao pedal · inox neutro (`inox_cast`) · **escala medida lixeira÷bancada ≈1/3** (não % do frame) · coerência dos props · sem marca · sem texto embutido.
- **SEM MARCA em todo o anúncio** (Almir 19/06) — nome "Terra Casa Decor" e slogan "O seu melhor lugar é a sua casa" NÃO entram em foto, título nem descrição (não prender a um rebrand). Só o tom/voz acolhedor permanece.

## Pendências
- **Commitar 18 arquivos da squad** (renata/vinicius/steps/data) com a regra SEM MARCA — o `/save` só commita os 5 docs raiz.
- **SUPABASE_SERVICE_ROLE** (`sb_secret_...`): re-fornecer ao retomar.
- **Publicação (step-10):** `N8N_WEBHOOK_ML_PUBLICAR` ausente; workflow "ML Publicar" (`0rzNJ7RLqLzMbKnf`) INATIVO de propósito.
- `generate.py` devolve 1024² → normalizar 1200² (PIL LANCZOS). `OPENROUTER_API_KEY` no `.env`.
