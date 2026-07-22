# PROGRESSO

> Atualizado 2026-07-12. **8L (VIE_1067) EM ANDAMENTO.** 5L fechado/aprovado (ver HISTORICO 2026-06-24/26). Rodada 8L em `output/2026-06-26-conforme-8L/`. **RETOMAR EM: aprovar a capa v8 (capa-v8.jpg) → gerar as 9 StorySelling.**
> **Plano paralelo (estratégico):** fechar o loop do pipeline — ver `PLANO-LOOP-JUIZ-VISUAL.md` (seção 4 abaixo).

## 0. Estado do 8L (VIE_1067) — feito nesta sessão
- **Cor-herói = PRETO** (escolha explícita do Almir; ele quer definir a herói por anúncio, sempre). As 9 StorySelling sairão em preto.
- **Produto-travado PRETO** em `pipeline/data/produtos-travados/VIE_1067-PAI.json` (+ `_aberto.png`/`_fechado.png`). Travado DIRETO das fotos reais pretas (`output/2026-05-26-091553/fotos/VIE_1067-PAI/_base/WhatsApp ...16.46.47/16.47.56`) → fidelidade máxima, sem recolor de IA. (Nota antiga "base 8L = squat do 5L" estava desatualizada; as fotos do WhatsApp 15/06 são o 8L alto real.)
- **Master branco** (recolor fiel) guardado em `.../_master/master-branco-*.jpg` — só p/ futura capa da variação Branco (não-herói).
- **Brief conformado** em `output/2026-06-26-conforme-8L/inteligencia/brief-VIE_1067-PAI.yaml`: hierarquia aprovada do 5L, SEM marca, **cozinha-líder** (only_factor 8L = tamanho útil + cabe a sacola de mercado), dims REAIS 18Ø×34cm, foto 6 = sem balde interno.
- **Capa v8** (`.../VIE_1067-PAI/_redesign/capa-v8.jpg`) — AGUARDANDO APROVAÇÃO DO ALMIR. Escala MEDIDA razão 0,32 (≤1/3, exigência do Almir) + realista (não-adesivo). Método novo (ver DECISOES 2026-06-26).

## 1. Próximas tarefas (ordem)
1. **Aprovar a capa v8** no Chrome (pendente). Se reprovar, iterar a posição/sombra/cena mantendo o método.
2. **Gerar as 9 StorySelling (fotos 2–10)** do 8L em PRETO, reusando a receita: studio compose (3,4,9,10) + lifestyle pelo método render-in-scene→recorta→encolhe→recompõe (capa,2,5,8) + ação no pedal (7). Texto NEUTRO de cor. Medir escala ≤1/3 (contexto) antes de apresentar cada uma.
3. Validar regras de imagem do ML (capa exige fundo branco?) antes de publicar.
4. Subir ao bucket `tcd-produtos` (precisa SERVICE_ROLE) → Step-08 → publicar.

## 2. Regras de trabalho (Almir) — INFALÍVEIS
- **CONFERIR medindo (não afirmar) + rodar checklist COMPLETO ANTES de apresentar** + aprovar SEMPRE no Chrome dedicado. (Furei isto na v4/v5 nesta sessão — Almir cobrou; não repetir.)
- **Escala em ambientada = 1/3 ou menos da bancada** (8L 34cm ÷ bancada 90cm). MEDIR (razão = alt. lixeira ÷ alt. chão→tampo). O Gemini fotorrealista orbita ~metade e NÃO desce a 1/3 — usar o método de compor a lixeira-já-renderizada-na-cena encolhida (DECISOES 26/06).
- **Pedal = tamanho FIXO** (igual no 5L e 8L). Numa lixeira mais alta o pedal deve parecer proporcionalmente menor — é a régua real do tamanho. Vem fiel no produto-travado.
- **SEM MARCA** em todo o anúncio. Cor-herói definida pelo Almir por anúncio.

## 3. Pendências
- **SUPABASE_SERVICE_ROLE** (a chave service_role do Supabase): re-fornecer p/ subir ao bucket.
- **step-10:** `N8N_WEBHOOK_ML_PUBLICAR` ausente; workflow "ML Publicar" (`0rzNJ7RLqLzMbKnf`) INATIVO de propósito.
- Custo da sessão 8L (OpenRouter Pro): ~$1,9 (master + cena + iterações de capa). Saldo OpenRouter ~$4,5.
- **⚠️ Arquivos da squad editados 20-22/07 NÃO commitados** (o /save só commita os 5 docs raiz): cibele, step-03, vinicius, felipe, step-02, storyselling, generate.py, SKILL.md, ml-api-reference, +data. Decidir quando commitar em bloco.
- **3 decisões de contrato abertas (diagnóstico 20/07):** (a) auditoria do Vinícius = 4 blocos ou os 7 do step-08 (sem StorySelling hoje); (b) `pictures_compartilhadas` — Paula remonta por fórmula bugável vs. ler `picture_ids_por_variacao` já pronto do Felipe (payload_builder é órfão); (c) `cor_value_map` lista vs dict; e `publico_alvo`/`ambientes_uso` cortar ou manter.

## 4. Plano paralelo — Juiz Visual (fechar o loop)
Detalhe completo em `PLANO-LOOP-JUIZ-VISUAL.md`. Ordem: **Peça A primeiro** (Juiz Visual = camada 1 estende `qa_imagens.py`, camada 2 `juiz_visual.py` por modelo de visão; **calibrar contra o 5L FECHADO antes de plugar**); B (heartbeat/fila) e C (checkpoints condicionais) só depois de A confiável. Não reconstruir o Opensquad — ele já é ~85% loop.

## 5. Prompts da squad foram higienizados em 19-22/07 — o que mudou pro 8L
Helena, Felipe, Renata e `photo-templates` foram limpos (detalhe em HISTORICO/DECISOES 19-20/07). O que afeta o trabalho em andamento:
- **`picture_ids` agora é 10, não 11** — no `modo: variacoes` publica ambientalizada + slots 2-10; o slot 1 é gerado e guardado, mas **não publicado**. (O DECISOES já mandava isso; os prompts é que estavam errados.)
- **Overlay trocou nos slots 5 e 6:** faixa clara agora é do slot 6 (Clareza), scrim é do 5 (Lifestyle).
- **Template 1 (CAPA):** a instrução de escala saiu de "ATE 1/3" para framing + marco físico. **O método de compor-e-encolher da capa v8 continua valendo** — a mudança é só na forma de pedir à IA, que nunca obedeceu a razão em texto.
- **`cor_heroi` nunca mais vem vazia** e, quando a Helena escolher uma cor diferente da 1ª variação, o step-04b para e pede sua confirmação.
- **Nova trava:** `validar_claims.py --copy` agora cobre também título e descrição, não só as fotos.
- **`--lock` LIGADO (22/07):** o gate `qa_imagens.py` do Vinícius/step-08 agora confere o sha256 da camada do produto (`produtos-travados/{pai_sku}.json`) — a prova de proveniência do produto-travado, que estava desligada, agora roda de verdade. Vale pro 8L (é produto-travado PRETO).
- **Categoria REAL = `MLB33375`** (22/07). Os IDs antigos `MLB263532`/`MLB264586` eram categorias RAIZ e não publicavam. Predictor mudou: `category_predictor` morreu (404) → usar `domain_discovery/search` (sem token, sem número de confiança).
