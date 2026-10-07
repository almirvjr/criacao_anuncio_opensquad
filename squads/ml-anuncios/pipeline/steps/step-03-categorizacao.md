---
execution: subagent
agent: cibele-categoria
inputFile: squads/ml-anuncios/output/anuncios-entrada.json
outputFile: squads/ml-anuncios/output/categorizacao/categorias.yaml
model_tier: powerful
---

# Step 03: Categorização ML e Benchmark Competitivo

## Context Loading

Load these files before executing:
- `squads/ml-anuncios/output/anuncios-entrada.json` — anúncios gerados no step 01 (pai_sku, nome_base, modo, variacoes[].cor)
- `squads/ml-anuncios/pipeline/data/ml-api-reference.md` — endpoints públicos do ML
- `squads/ml-anuncios/pipeline/data/domain-framework.md` — Fase 2 (Categorização)
- `squads/ml-anuncios/pipeline/data/quality-criteria.md` — critérios de categorização
- `squads/ml-anuncios/pipeline/data/anti-patterns.md` — erros comuns de categorização

## Instructions

### Process

1. Para cada anúncio em `anuncios-entrada.json`, extrair `pai_sku`, `nome_base`, `modo` e (se `modo: variacoes`) a lista de `variacoes[].cor`.
2. Chamar `GET https://api.mercadolibre.com/sites/MLB/domain_discovery/search?limit=3&q=<nome_base>` via WebFetch. A resposta é uma **lista**, do mais provável ao menos, **sem número de confiança**. Capturar de cada item `category_id`, `category_name`, `domain_id`. O item #1 é a aposta; guardar os demais como `categorias_alternativas`.
   - **2b.** Confirmar que o candidato #1 aceita anúncio: `GET https://api.mercadolibre.com/categories/{id}` e checar `children_categories` vazio (folha) **e** `settings.listing_allowed == true`. Se falhar, testar o próximo candidato da lista; capturar `path_from_root` para o breadcrumb.
3. Sinalizar `revisao_humana: true` (com 2 alternativas, tiradas da própria lista do predictor) quando: o predictor devolveu 2+ candidatos plausíveis **e** os concorrentes top (passo 6) se dividem entre eles sem maioria; OU menos de 2 dos 3 concorrentes estão na categoria #1; OU nenhum candidato da lista é folha que aceita anúncio. O `domain_discovery` não devolve confiança — o gatilho é a ambiguidade, não um número.
4. Carregar **todos** os atributos da categoria via `GET https://api.mercadolibre.com/categories/{id}/attributes` (sem filtro de required — precisamos dos atributos de variação também). Para `atributos_obrigatorios`, filtrar os que têm `tags.required == true`. Salvar nome, id, tipo e (quando existirem) `values` permitidos.
5. **[Somente modo: variacoes]** Validar suporte a variações e mapear COLOR:
   - a. Verificar se algum atributo tem `attribute_types` contendo `"variations"`. Se não, registrar `variacoes_suportadas: false` e `revisao_humana: true` — esta categoria não aceita anúncio com variações. Pular os subitens b e c.
   - b. Localizar o atributo `id: "COLOR"` com `tags.allow_variations: true`. Registrar `variation_attribute: { id: "COLOR", defines_picture: <bool> }` onde `defines_picture` vem de `tags.defines_picture` (false se ausente).
   - c. Montar `cor_value_map`: para cada `cor` da lista de variações do anúncio, buscar correspondência case-insensitive em `COLOR.values[]`. Se encontrar: `{ cor: "<cor>", value_id: "<id>", value_name: "<name>" }`. Se não encontrar: `{ cor: "<cor>", value_name_livre: true }`.
6. Buscar 3 concorrentes top com `GET https://api.mercadolibre.com/sites/MLB/search?category={id}&q=<keywords>&sort=sold_quantity_desc&limit=10`. Selecionar os 3 primeiros com `sold_quantity` mais alto. Capturar título, preço, MLB-id, vendedor, permalink.
7. Calcular range de preços do nicho (min, mediano, max) a partir dos resultados da busca.
8. Extrair top-5 palavras-chave que aparecem nos títulos dos concorrentes (tokenizar, remover stopwords, contar).
9. Escrever o YAML em `squads/ml-anuncios/output/categorizacao/categorias.yaml`.

## Output Format

```yaml
lote:
  total_categorizados: <int>
  revisao_humana_necessaria: <int>

categorias:
  - pai_sku: "<string>"
    modo: "variacoes|simples"
    category_id: "MLB<int>"
    category_name: "<string>"
    breadcrumb: ["<nivel1>", "<nivel2>", "<nivel3>"]
    domain_id: "<string>"
    aceita_anuncio: <bool>              # folha (children vazio) + listing_allowed
    validacao_cruzada: "<n>/3 concorrentes top na categoria"
    revisao_humana: <bool>
    motivo_revisao: "<string>"          # obrigatório quando revisao_humana: true — a frase que o humano lê pra saber por que caiu na revisão; omitir quando false
    categorias_alternativas:            # candidatos extras do predictor (já vêm na resposta)
      - { id: "MLB...", name: "..." }
    atributos_obrigatorios:
      - { id: "<string>", name: "<string>", tipo: "string|number|list", values_permitidos: ["..."]|null }
    # Campos exclusivos de modo: variacoes
    variacoes_suportadas: <bool>          # omitido em modo: simples
    variation_attribute:                  # omitido em modo: simples ou se variacoes_suportadas: false
      id: "COLOR"
      defines_picture: <bool>
    cor_value_map:                        # omitido em modo: simples ou se variacoes_suportadas: false
      - cor: "<string>"
        value_id: "<string>"              # presente quando a cor existe na lista ML
        value_name: "<string>"            # presente quando value_id encontrado
        value_name_livre: <bool>          # true quando a cor não existe na lista ML
    concorrentes_top:
      - { mlb_id: "MLB...", titulo: "...", preco: <num>, vendedor: "...", sold_quantity: <int>, permalink: "<url>" }
    range_precos:
      min: <num>
      mediano: <num>
      max: <num>
    top_keywords: ["<string>", ...]
```

## Output Example

```yaml
lote:
  total_categorizados: 2
  revisao_humana_necessaria: 0

categorias:
  - pai_sku: "VIE_1066-PAI"
    modo: "variacoes"
    category_id: "MLB33375"
    category_name: "Lixeiras"
    breadcrumb: ["Casa, Móveis e Decoração", "Cozinha", "Armazenamento e Organização", "Lixeiras"]
    domain_id: "MLB-WASTE_BASKETS"
    aceita_anuncio: true
    validacao_cruzada: "3/3 concorrentes top na categoria"
    revisao_humana: false
    categorias_alternativas: []
    atributos_obrigatorios:
      - { id: "BRAND", name: "Marca", tipo: "string", values_permitidos: null }
      - { id: "MODEL", name: "Modelo", tipo: "string", values_permitidos: null }
      - { id: "MAIN_MATERIAL", name: "Material principal", tipo: "list", values_permitidos: ["Aço inox", "Plástico", "Alumínio"] }
      - { id: "CAPACITY", name: "Capacidade", tipo: "number", values_permitidos: null }
      - { id: "COLOR", name: "Cor", tipo: "string", values_permitidos: null }
      - { id: "ACTUATION_TYPE", name: "Acionamento", tipo: "list", values_permitidos: ["Pedal", "Manual", "Sensor"] }
    variacoes_suportadas: true
    variation_attribute:
      id: "COLOR"
      defines_picture: true
    cor_value_map:
      - { cor: "Branco", value_id: "283155", value_name: "Branco" }
      - { cor: "Preto", value_id: "283164", value_name: "Preto" }
      - { cor: "Cinza", value_id: "283152", value_name: "Cinza" }
    concorrentes_top:
      - { mlb_id: "MLB1234567890", titulo: "Lixeira Inox 5L Pedal Antiodor Cozinha", preco: 99.90, vendedor: "TopHomeBR", sold_quantity: 5200, permalink: "https://produto.mercadolivre.com.br/MLB-1234567890" }
      - { mlb_id: "MLB1234567891", titulo: "Lixeira Aço Inox 5 Litros Tampa Pedal", preco: 119.00, vendedor: "CasaUtil", sold_quantity: 3800, permalink: "https://produto.mercadolivre.com.br/MLB-1234567891" }
      - { mlb_id: "MLB1234567892", titulo: "Lixeira Inox 5L Pedal Banheiro Cozinha", preco: 89.90, vendedor: "MegaCasa", sold_quantity: 2900, permalink: "https://produto.mercadolivre.com.br/MLB-1234567892" }
    range_precos: { min: 79.00, mediano: 99.90, max: 149.00 }
    top_keywords: ["lixeira", "inox", "pedal", "5l", "cozinha"]

  - pai_sku: "VIE_1067-PAI"
    modo: "variacoes"
    category_id: "MLB33375"
    category_name: "Lixeiras"
    breadcrumb: ["Casa, Móveis e Decoração", "Cozinha", "Armazenamento e Organização", "Lixeiras"]
    domain_id: "MLB-WASTE_BASKETS"
    aceita_anuncio: true
    validacao_cruzada: "3/3 concorrentes top na categoria"
    revisao_humana: false
    categorias_alternativas: []
    atributos_obrigatorios:
      - { id: "BRAND", name: "Marca", tipo: "string", values_permitidos: null }
      - { id: "MODEL", name: "Modelo", tipo: "string", values_permitidos: null }
      - { id: "MAIN_MATERIAL", name: "Material principal", tipo: "list", values_permitidos: ["Aço inox", "Plástico", "Alumínio"] }
      - { id: "CAPACITY", name: "Capacidade", tipo: "number", values_permitidos: null }
      - { id: "COLOR", name: "Cor", tipo: "string", values_permitidos: null }
      - { id: "ACTUATION_TYPE", name: "Acionamento", tipo: "list", values_permitidos: ["Pedal", "Manual", "Sensor"] }
    variacoes_suportadas: true
    variation_attribute:
      id: "COLOR"
      defines_picture: true
    cor_value_map:
      - { cor: "Branco", value_id: "283155", value_name: "Branco" }
      - { cor: "Preto", value_id: "283164", value_name: "Preto" }
      - { cor: "Cinza", value_id: "283152", value_name: "Cinza" }
    concorrentes_top:
      - { mlb_id: "MLB2345678901", titulo: "Lixeira Inox 8L Pedal Antiodor Cozinha", preco: 139.90, vendedor: "TopHomeBR", sold_quantity: 4100, permalink: "https://produto.mercadolivre.com.br/MLB-2345678901" }
      - { mlb_id: "MLB2345678902", titulo: "Lixeira Aço Inox 8 Litros Tampa Pedal", preco: 159.00, vendedor: "CasaUtil", sold_quantity: 3300, permalink: "https://produto.mercadolivre.com.br/MLB-2345678902" }
      - { mlb_id: "MLB2345678903", titulo: "Lixeira Inox 8L Pedal Banheiro Cozinha", preco: 129.00, vendedor: "MegaCasa", sold_quantity: 2700, permalink: "https://produto.mercadolivre.com.br/MLB-2345678903" }
    range_precos: { min: 119.00, mediano: 149.90, max: 199.00 }
    top_keywords: ["lixeira", "inox", "pedal", "8l", "cozinha"]
```

## Veto Conditions

Rejeitar e refazer se ALGUMA for verdadeira:
1. Algum anúncio ficou sem `category_id` válido (formato `MLB<digits>`).
2. Algum anúncio com `revisao_humana: true` não tem 2 `categorias_alternativas` propostas **ou** está sem `motivo_revisao` preenchido.
2b. Algum anúncio com `aceita_anuncio` diferente de `true` (categoria não é folha ou não aceita anúncio) sem estar marcado `revisao_humana: true`.
3. Lista `atributos_obrigatorios` vazia em qualquer anúncio (toda categoria ML tem ao menos BRAND).
4. Menos de 3 `concorrentes_top` para algum anúncio (a menos que a busca tenha retornado < 3 itens — neste caso documentar).
5. [modo: variacoes] `variacoes_suportadas` ausente (deve ser sempre registrado para anúncios com variações).
6. [modo: variacoes] `variacoes_suportadas: true` mas `cor_value_map` ausente ou incompleto (menos entradas que o número de cores declaradas no anúncio).

## Quality Criteria

- [ ] 100% dos anúncios do arquivo de entrada foram categorizados
- [ ] Toda categoria escolhida confirmada como folha + `listing_allowed` (`aceita_anuncio: true`); as que não passam viram `revisao_humana: true`
- [ ] Casos ambíguos (predictor com 2+ candidatos e concorrentes divididos, ou <2 dos 3 concorrentes na categoria) marcados `revisao_humana: true` com 2 alternativas
- [ ] Atributos obrigatórios completos para cada anúncio (nome, id, tipo)
- [ ] Range de preços calculado para cada anúncio
- [ ] Top-5 keywords extraídas dos títulos dos concorrentes
- [ ] [modo: variacoes] `variacoes_suportadas` registrado para todos os anúncios com variações
- [ ] [modo: variacoes] `variation_attribute` com `id: COLOR` e `defines_picture` quando `variacoes_suportadas: true`
- [ ] [modo: variacoes] `cor_value_map` com uma entrada por cor do anúncio quando `variacoes_suportadas: true`
- [ ] Arquivo salvo em `squads/ml-anuncios/output/categorizacao/categorias.yaml`
