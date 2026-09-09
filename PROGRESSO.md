# PROGRESSO

> Atualizado 2026-09-09. **Três frentes:** (1) **8L (VIE_1067) EM ANDAMENTO** — 5L fechado/aprovado (HISTORICO 2026-06-24/26), rodada em `output/2026-06-26-conforme-8L/`, **RETOMAR EM: aprovar a capa v8 → gerar as 9 StorySelling**; (2) **ficha técnica dos anúncios no ar** (seção 6), parada esperando 4 decisões suas; (3) **Raio-X do anúncio** (seção 7), pronto e em uso.
> **Plano paralelo (estratégico):** fechar o loop do pipeline — ver `PLANO-LOOP-JUIZ-VISUAL.md` (seção 4 abaixo).

## 0. Estado do 8L (VIE_1067)
- **Cor-herói = PRETO** (escolha explícita do Almir; ele quer definir a herói por anúncio, sempre). As 9 StorySelling sairão em preto.
- **Produto-travado PRETO** em `pipeline/data/produtos-travados/VIE_1067-PAI.json` (+ `_aberto.png`/`_fechado.png`), travado DIRETO das fotos reais pretas → fidelidade máxima, sem recolor de IA. **Master branco** (recolor fiel) em `.../_master/` só p/ futura capa da variação Branco.
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
- **⚠️ Código da squad editado 20-22/07 segue NÃO commitado** (o /save só commita os 5 docs raiz): agentes, steps 02/03/07/08/10, `data/`, `generate.py`, `prompt_lint.py`, `render_faixa.py`, `payload_builder.py`, os 2 SKILL.md e os testes. Decidir quando commitar em bloco. **Somam agora `tools/auditoria_ficha/` e `userscripts/`.** ⚠️ Este repo é PÚBLICO — conferir antes de commitar.
- **Quando for LIGAR o `ML Publicar`:** tirar do nó `Montar Payload` a união de `pictures_compartilhadas` — campo que não existe mais no contrato (não quebra hoje; o nó também une todos os `picture_ids`).

## 4. Plano paralelo — Juiz Visual (fechar o loop)
Detalhe completo em `PLANO-LOOP-JUIZ-VISUAL.md`. Ordem: **Peça A primeiro** (Juiz Visual = camada 1 estende `qa_imagens.py`, camada 2 `juiz_visual.py` por modelo de visão; **calibrar contra o 5L FECHADO antes de plugar**); B (heartbeat/fila) e C (checkpoints condicionais) só depois de A confiável. Não reconstruir o Opensquad — ele já é ~85% loop.

## 5. Higiene de prompts (19-22/07) — o que ainda pega no 8L
- **`picture_ids` = 10** (capa + slots 2-10; o slot 1 não é publicado) e a Paula **copia** a lista do Felipe. Overlay: faixa é do slot 6, scrim do 5. `cor_heroi` nunca vem vazia. Travas ligadas: `validar_claims.py --copy` e `qa_imagens.py --lock`. Revisão do Vinícius = 7 blocos com nota, auditando StorySelling.
- **Categoria REAL = `MLB33375`**; predictor via `domain_discovery/search` (o `category_predictor` morreu, 404). Detalhe de tudo em HISTORICO/DECISOES 2026-07-22.

## 6. Ficha técnica dos anúncios NO AR (frente nova, 06-10/08) — `tools/auditoria_ficha/`
Feito: 371 campos preenchidos em 146 anúncios, 36 "não se aplica", 8 erros de unidade, piloto MLB1254314177. Detalhe em HISTORICO/DECISOES 06-10/08. **Nenhuma gravação alterou preço/fotos/estoque/variações** (conferido contra backup em `backups_*/`).

**Esperando decisão do Almir (não avançar sem ela):**
1. **6 anúncios com litros divergentes** entre título e ficha (o maior tem 2.635 vendas): decidir qual número vale — corrijo a ficha OU o título.
2. **5 anúncios travados no catálogo** (peso 1 g, comprimento 15,7 m, altura 0,3 cm): só via "Sugerir correções" no painel, um a um, se autorizar.
3. **41 campos de vela**: escolher 1 cor por anúncio ou deixar vazio (cada variação tem uma cor e o campo é do anúncio).
4. **112 suspeitas**: 63 de caixa menor/mais leve que o produto (mexe em frete) + 49 de "Kit N unidades" com a ficha dizendo 1.

⚠️ **Antes de qualquer lote novo:** filtrar `catalog_listing=false` (catálogo responde 200 e ignora), rodar `validar_sugestoes.ps1` e comparar título antes/depois.

## 7. Raio-X do anúncio (frente nova, 09/09) — `userscripts/raio-x-anuncio.user.js`
**PRONTO e em uso.** Userscript Tampermonkey: cola a URL de qualquer anúncio do ML e devolve **só o que não está na tela** — código universal (EAN13), catálogo vs lista, marca+modelo, visitas 30d, quanto sobra pro vendedor, e quem disputa a ficha. Manual em `README-raio-x.md`, detalhe em HISTORICO/DECISOES 09/09.
🔑 **Régua do Almir, vale pra qualquer painel:** se ele vê o dado abrindo o anúncio, o dado NÃO entra.
- **Próximo passo opcional (não iniciado):** medidor de posição na busca. Já provado viável (achou um anúncio na posição 34 de 937), mas exige ABRIR a página de busca — o servidor manda ela sem os anúncios. Só fazer se o Almir pedir.
