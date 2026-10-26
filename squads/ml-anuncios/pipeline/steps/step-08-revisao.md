---
execution: subagent
agent: vinicius-validador
inputFile: squads/ml-anuncios/output/copywriting/anuncios.yaml
outputFile: squads/ml-anuncios/output/revisao/pareceres.yaml
model_tier: powerful
---

# Step 08: Revisão Final (QA + Compliance ML + StorySelling)

## Context Loading

Load these files before executing:
- `squads/ml-anuncios/output/copywriting/anuncios.yaml` — copy a auditar (com 3-5 títulos e `recomendado`/`titulo_final`)
- `squads/ml-anuncios/output/inteligencia/briefs.yaml` — brief estratégico para validar coerência (Helena)
- `squads/ml-anuncios/output/categorizacao/categorias.yaml` — atributos obrigatórios da categoria
- `squads/ml-anuncios/output/curadoria/dossies.json` — verificar consistência técnica entre copy e dossiê
- `squads/ml-anuncios/output/capas/capas-{pai_sku}.yaml` — capas de cada cor (endereço 1200×1200 do Cloudinary), montadas no step-07
- `squads/ml-anuncios/pipeline/data/quality-criteria.md` — checklist completo
- `squads/ml-anuncios/pipeline/data/anti-patterns.md` — termos proibidos e CAPS LOCK
- `squads/ml-anuncios/pipeline/data/storyselling-framework.md` — códigos MECLABS e escada E daí
- `squads/ml-anuncios/pipeline/data/ml-api-reference.md` — campos exigidos pelo ML

## Instructions

### Process

1. Para cada SKU, identificar o `modo` do anúncio (`simples` ou `variacoes`) no arquivo `anuncios.yaml`. O modo determina quais blocos executar.
2. **Rodar checklist base (todos os modos)** — 7 blocos: Título, Descrição, Ficha Técnica, Mídia Visual, Tom Marca, Compliance ML, **StorySelling**.
   - **Validar título escolhido**: `titulo_final` está entre as 3-5 alternativas propostas, e seu `length` está entre 50-60. Se `titulo_final` é resultado de edição livre, validar contagem.
   - **Cruzar dossiê x copy**: capacidade na descrição = capacidade na ficha = capacidade no dossiê; cor, material idem.
   - **Compliance ML**: caracteres proibidos no título (`!`, `?`, `*`, emojis), CAPS LOCK fora de siglas, atributos obrigatórios todos preenchidos.
   - **Tom Terra Casa Decor**: presença de pelo menos uma das palavras-âncora (`casa`, `lar`, `dia a dia`); "Terra Casa Decor" só aparece em produto Mundiart (`MDA`) e nunca no título; ausência de termos proibidos (`melhor do mercado`, `imbatível`, `adquira`, `produto premium`).
   - **Capas (bloqueante quando há foto; cor sem foto não é veto, só nota — Almir 26/10/2026, a trava é na publicação):** para cada cor com foto, abrir o endereço de `picture_ids[0]` em `capas-{pai_sku}.yaml` (Chrome ou download) e confirmar: abre, é 1200×1200, é **este** produto **nesta** cor, sem logo/nome de loja/texto. Rodar `python squads/ml-anuncios/pipeline/validators/validar_ficha_seo.py squads/ml-anuncios/output/copywriting/anuncio-{pai_sku}.yaml` e `python squads/ml-anuncios/pipeline/validators/validar_claims.py squads/ml-anuncios/output/inteligencia/brief-{pai_sku}.yaml --copy squads/ml-anuncios/output/copywriting/anuncio-{pai_sku}.yaml --sem-fotos` — os dois com código 0. Qualquer falha = `midia_visual: ok: false` com a cor e o motivo. **Não aprovar capa sem abrir.**
   - **StorySelling**: Bloco 1 da descrição ancora na `dor_interna` do brief (a menos que `diagnostico_neutro: true`). Pelo menos 2 frases da `linguagem_real_cliente` do brief aparecem na descrição. Bloco 3 segue a `escada_e_dai` do brief (cada bullet tem benefício emocional, não só técnico). `titulo_final` do SKU é coerente com o `only_factor` do brief.
3. **[Modo variacoes] Rodar bloco 8 — Variações ML** (veto duro em cada critério):
   - **Preço uniforme**: comparar `preco_venda` de todas as entradas de `variacoes[]`. Qualquer divergência — mesmo de centavos — é veto. Registrar os valores encontrados e indicar qual é o correto.
   - **Foto por cor**: cada cor de `variacoes[]` tem ≥1 endereço em `capas-{pai_sku}.yaml` (e no máximo 10). Cor sem foto não é veto: só registrar em `notas` (a publicação no canal trava sem foto; Almir 26/10/2026).
   - **`attribute_combinations` consistente**: (a) todas as variações devem ter o mesmo conjunto de chaves em `attribute_combinations`; (b) nenhum par `{atributo: valor}` deve se repetir entre variações distintas. Violação de (a) ou (b) é veto.
   - **`SELLER_SKU` e `EAN` por variação**: varrer cada item de `variacoes[]` e confirmar que os campos `sku` e `ean` estão preenchidos e não nulos. Campo vazio ou ausente é veto.
   - **Categoria aceita variações**: no `categorias.yaml` da Cibele, o produto deve ter `variacoes_suportadas: true` e `cor_value_map` preenchido para cada cor presente em `variacoes[]`. `value_id` ausente para qualquer cor é veto — devolver à Cibele.
   - **Descrição plain text**: confirmar ausência de HTML, markdown, emojis e `<br>` na descrição (mesma regra do modo simples). Regex: `/<[^>]+>/` e `\*\*|__|\#{1,}|>[ ]+`.
4. Atribuir status: `aprovado` se zero veto e score >= 80; `reprovado` se algum veto ou score < 80, com lista de correções específicas por bloco.
5. Escrever **dois** arquivos, sem duplicar verdade: um parecer por SKU em `output/revisao/parecer-{pai_sku}.yaml` (é esse que a Paula lê no step-10) e o consolidado do lote em `output/revisao/pareceres.yaml` (o `lote:` + a lista, para leitura humana). Mesmo conteúdo de `checks`, `score_total` e `breakdown` nos dois.

## Output Format

```yaml
lote:
  total_skus: <int>
  aprovados: <int>
  reprovados: <int>
  data_revisao: "<ISO-8601>"

pareceres:
  - sku: "<string>"
    modo: "simples|variacoes"          # reflete o campo modo do anúncio
    status: "aprovado|reprovado"
    score_total: <int>                 # 0-100; aprovado exige >= 80 E zero veto
    breakdown:                         # tabela fixa, IGUAL nos dois modos, soma 100
      titulo: <int>                    # teto 15
      descricao: <int>                 # teto 20
      ficha_tecnica: <int>             # teto 15
      midia_visual: <int>              # teto 20
      storyselling: <int>              # teto 15
      compliance_ml: <int>             # teto 10
      tom_marca: <int>                 # teto 5
    titulo_final_validado: "<string>"
    checks:
      titulo:        { ok: <bool>, notas: ["<string>", ...] }
      descricao:     { ok: <bool>, notas: ["<string>", ...] }
      ficha_tecnica: { ok: <bool>, notas: ["<string>", ...] }
      midia_visual:  { ok: <bool>, notas: ["<string>", ...] }
      tom_marca:     { ok: <bool>, notas: ["<string>", ...] }
      compliance_ml: { ok: <bool>, notas: ["<string>", ...] }
      storyselling:  { ok: <bool>, notas: ["<string>", ...] }
      # bloco abaixo presente apenas para modo: variacoes — é PORTÃO, não pontua:
      # não entra no breakdown, e qualquer ok:false reprova independente do score
      variacoes_ml:
        ok: <bool>
        preco_uniforme:             { ok: <bool>, notas: ["<string>", ...] }
        fotos_por_cor:              { ok: <bool>, notas: ["<string>", ...] }
        attribute_combinations:     { ok: <bool>, notas: ["<string>", ...] }
        seller_sku_ean_por_variacao: { ok: <bool>, notas: ["<string>", ...] }
        categoria_aceita_variacoes:  { ok: <bool>, notas: ["<string>", ...] }
        descricao_plain_text:        { ok: <bool>, notas: ["<string>", ...] }
    correcoes_necessarias: ["<string>", ...]
    confianca_publicacao: "alta|media|baixa"
```

## Output Example

```yaml
lote:
  total_skus: 1
  aprovados: 1
  reprovados: 0
  data_revisao: "2026-05-17T15:18:00-03:00"

pareceres:
  - sku: "TCD-LXI12"
    status: "aprovado"
    score_total: 100
    breakdown:
      titulo: 15
      descricao: 20
      ficha_tecnica: 15
      midia_visual: 20
      storyselling: 15
      compliance_ml: 10
      tom_marca: 5
    titulo_final_validado: "Lixeira Inox 12L Pedal Antiodor Cozinha Banheiro Moderna"
    checks:
      titulo:        { ok: true, notas: ["56 chars", "padrão PMME OK", "escolha entre as alternativas válida"] }
      descricao:     { ok: true, notas: ["3 blocos identificados", "224 palavras (range 200-350)", "ancora dor interna do brief"] }
      ficha_tecnica: { ok: true, notas: ["10/10 atributos obrigatórios preenchidos"] }
      midia_visual:  { ok: true, notas: ["3 cores, 1 capa cada, 1200x1200", "cor da capa = cor do SKU", "sem marca nas fotos (OK)"] }
      tom_marca:     { ok: true, notas: ["presença de 'casa', 'dia a dia'", "sem termos proibidos"] }
      compliance_ml: { ok: true, notas: ["sem caracteres proibidos", "sem CAPS indevido"] }
      storyselling:  { ok: true, notas: ["dor interna ancorada", "3 frases linguagem real aplicadas", "escada E daí seguida no bloco 3"] }
    correcoes_necessarias: []
    confianca_publicacao: "alta"
```

## Veto Conditions

Rejeitar e refazer se ALGUMA for verdadeira:
1. Algum SKU sem parecer.
2. Algum parecer `aprovado` com pelo menos um `checks.<bloco>.ok == false`.
3. Algum parecer `reprovado` sem lista de `correcoes_necessarias` populada.
4. Mídia visual `ok: true` sem ter aberto a capa de cada cor, ou com cor faltando em `capas-{pai_sku}.yaml`.
4b. `validar_ficha_seo.py` ou `validar_claims.py --sem-fotos` com código != 0 e parecer `aprovado`.
5. Bloco StorySelling `ok: true` para SKU cujo bloco 1 da descrição não ancora na dor_interna (quando brief não é neutro).
6. Capa com logo, nome de loja ou texto embutido aprovada.
7. **[Modo variacoes]** Parecer sem bloco `variacoes_ml` em anúncio com `modo: variacoes`.
8. **[Modo variacoes]** Qualquer sub-check de `variacoes_ml` com `ok: false` E parecer com status `aprovado` — cada falha em variações é veto duro.
9. **[Modo variacoes]** `variacoes_ml.preco_uniforme.ok: true` sem listar os valores de `preco_venda` verificados nas notas.

## Quality Criteria

- [ ] 100% dos SKUs do step 07 receberam parecer
- [ ] Campo `modo` presente em cada parecer
- [ ] Cada parecer no modo simples contém os 7 blocos de check (incluindo StorySelling)
- [ ] Cada parecer no modo variacoes contém os 7 blocos base + bloco `variacoes_ml` com os 6 sub-checks
- [ ] Status `aprovado` só quando todos os blocos têm `ok: true`
- [ ] Reprovados têm correções acionáveis (não genéricas)
- [ ] Totais agregados batem com a contagem real
- [ ] Arquivo salvo em `squads/ml-anuncios/output/revisao/pareceres.yaml`
