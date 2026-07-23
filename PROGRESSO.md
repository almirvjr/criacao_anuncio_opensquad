# PROGRESSO

> Atualizado 2026-07-22. **8L (VIE_1067) EM ANDAMENTO.** 5L fechado/aprovado (ver HISTORICO 2026-06-24/26). Rodada 8L em `output/2026-06-26-conforme-8L/`. **RETOMAR EM: aprovar a capa v8 (capa-v8.jpg) → gerar as 9 StorySelling.**
> **Plano paralelo (estratégico):** fechar o loop do pipeline — ver `PLANO-LOOP-JUIZ-VISUAL.md` (seção 4 abaixo).

## 0. Estado do 8L (VIE_1067)
- **Cor-herói = PRETO** (escolha explícita do Almir; ele quer definir a herói por anúncio, sempre). As 9 StorySelling sairão em preto.
- **Produto-travado PRETO** em `pipeline/data/produtos-travados/VIE_1067-PAI.json` (+ `_aberto.png`/`_fechado.png`). Travado DIRETO das fotos reais pretas (`output/2026-05-26-091553/fotos/VIE_1067-PAI/_base/WhatsApp ...16.46.47/16.47.56`) → fidelidade máxima, sem recolor de IA.
- **Master branco** (recolor fiel) guardado em `.../_master/master-branco-*.jpg` — só p/ futura capa da variação Branco (não-herói).
- **Brief conformado** em `output/2026-06-26-conforme-8L/inteligencia/brief-VIE_1067-PAI.yaml`: hierarquia aprovada do 5L, SEM marca, **cozinha-líder** (only_factor 8L = tamanho útil + cabe a sacola de mercado), dims REAIS 18Ø×34cm, foto 6 = sem balde interno.
- **Capa v8** (`.../VIE_1067-PAI/_redesign/capa-v8.jpg`) — AGUARDANDO APROVAÇÃO DO ALMIR. Escala MEDIDA razão 0,32 (≤1/3, exigência do Almir) + realista (não-adesivo). Método novo (ver DECISOES 2026-06-26).

## 1. Próximas tarefas (ordem)
1. **Aprovar a capa v8** no Chrome (pendente). Se reprovar, iterar a posição/sombra/cena mantendo o método.
2. **Gerar as 9 StorySelling (fotos 2–10)** do 8L em PRETO, reusando a receita: studio compose (3,4,9,10) + lifestyle pelo método render-in-scene→recorta→encolhe→recompõe (capa,2,5,8) + ação no pedal (7). Texto NEUTRO de cor. Medir escala ≤1/3 (contexto) antes de apresentar cada uma.
3. Validar regras de imagem do ML (capa exige fundo branco?) antes de publicar.
4. Subir ao bucket `tcd-produtos` (precisa SERVICE_ROLE) → Step-08 → publicar.

## 2. Regras de trabalho (Almir) — INFALÍVEIS
- **CONFERIR medindo (não afirmar) + rodar checklist COMPLETO ANTES de apresentar** + aprovar SEMPRE no Chrome dedicado.
- **Escala em ambientada = 1/3 ou menos da bancada** (8L 34cm ÷ bancada 90cm). MEDIR (razão = alt. lixeira ÷ alt. chão→tampo). O Gemini fotorrealista orbita ~metade e NÃO desce a 1/3 — usar o método de compor a lixeira-já-renderizada-na-cena encolhida (DECISOES 26/06).
- **Pedal = tamanho FIXO** (igual no 5L e 8L). Numa lixeira mais alta o pedal deve parecer proporcionalmente menor — é a régua real do tamanho. Vem fiel no produto-travado.
- **SEM MARCA** em todo o anúncio. Cor-herói definida pelo Almir por anúncio.

## 3. Pendências
- **SUPABASE_SERVICE_ROLE** (a chave service_role do Supabase): re-fornecer p/ subir ao bucket.
- **step-10:** `N8N_WEBHOOK_ML_PUBLICAR` ausente; workflow "ML Publicar" (`0rzNJ7RLqLzMbKnf`) INATIVO de propósito.
- Custo da sessão 8L (OpenRouter Pro): ~$1,9 (master + cena + iterações de capa). Saldo OpenRouter ~$4,5.
- **⚠️ Arquivos da squad editados 20-22/07 NÃO commitados** (o /save só commita os 5 docs raiz): agentes (cibele, vinicius, felipe, paula, caio), steps (02,03,07,08,10), data (storyselling, photo-templates, research-brief, domain-framework, ml-api-reference), `generate.py`, `prompt_lint.py`, `render_faixa.py`, `payload_builder.py`, ambos SKILL.md + testes novos. Decidir quando commitar em bloco.
- **Quando for LIGAR o `ML Publicar`:** tirar do nó `Montar Payload` a união de `pictures_compartilhadas` — campo que não existe mais no contrato (não quebra hoje; o nó também une todos os `picture_ids`).
- Higiene de prompts: **as 4 decisões de contrato foram fechadas em 22/07** e aplicadas; fila ALTA e onda MÉDIA zeradas. Ver HISTORICO/DECISOES 2026-07-22 e `.claude-hub/plans/2026-07-20-diagnostico-onda-media.md`. **118 testes verdes.**

## 4. Plano paralelo — Juiz Visual (fechar o loop)
Detalhe completo em `PLANO-LOOP-JUIZ-VISUAL.md`. Ordem: **Peça A primeiro** (Juiz Visual = camada 1 estende `qa_imagens.py`, camada 2 `juiz_visual.py` por modelo de visão; **calibrar contra o 5L FECHADO antes de plugar**); B (heartbeat/fila) e C (checkpoints condicionais) só depois de A confiável. Não reconstruir o Opensquad — ele já é ~85% loop.

## 5. Higiene de prompts (19-22/07) — só o que afeta o 8L em andamento
- **`picture_ids` = 10, não 11** — no `modo: variacoes` publica ambientalizada + slots 2-10; o slot 1 é gerado e guardado, mas **não publicado**. A Paula agora **copia** essa lista do Felipe; não monta mais.
- **Overlay nos slots 5 e 6:** faixa clara é do 6 (Clareza), scrim é do 5 (Lifestyle).
- **Template 1 (CAPA):** escala saiu de "ATE 1/3" para framing + marco físico. **O método de compor-e-encolher da capa v8 continua valendo** — mudou só a forma de pedir à IA, que nunca obedeceu razão em texto. O gerador também não escolhe mais ângulo "mais bonito" por conta própria.
- **`cor_heroi` nunca vem vazia**; cor diferente da 1ª variação faz o step-04b parar e pedir sua confirmação.
- **Travas ligadas:** `validar_claims.py --copy` cobre título e descrição; `--lock` do `qa_imagens.py` confere o sha256 do produto-travado (vale pro 8L, que é travado PRETO).
- **Revisão do Vinícius agora tem 7 blocos com nota** e audita **StorySelling** contra o brief — o 8L vai ser cobrado nisso.
- **Foto técnica:** ganhou a 3ª cota (profundidade). ⚠️ **Deixar folga no enquadramento** (~80px à esquerda, ~110px abaixo do produto) — sem isso as cotas são desenhadas fora da imagem; o renderer avisa no log, mas não conserta.
- **Categoria REAL = `MLB33375`** (os antigos `MLB263532`/`MLB264586` eram RAIZ e não publicavam). Predictor: `category_predictor` morreu (404) → `domain_discovery/search`.
