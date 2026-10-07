# Quality Criteria — Squad ML Anúncios

Critérios objetivos e verificáveis para cada artefato produzido pela squad.

## Regra global de fotos (esteira sem fotos desde 07/10/2026)

A squad **não gera foto**. A capa de cada cor é subida pelo Almir no Cloudinary (etiquetas: SKU da cor + `capa-anuncio`) e chega ao ML pelo endereço 1200×1200 que o `capas.py` monta. Regras de geração antigas: `_arquivo-fotos/`.

## Dossiê de Produto (saída de Caio Curador)

- [ ] SKU, EAN, preço_custo, preço_venda preenchidos
- [ ] Nome completo do produto (não abreviado)
- [ ] Pelo menos 3 specs técnicas (material, dimensões, peso)
- [ ] Marca identificada

**Veto:** se faltar SKU OU preço_venda, o produto é marcado como `bloqueado` e fica fora do lote.

## Categorização (saída de Cibele Categoria)

- [ ] `category_id` ML válido (formato MLB1234)
- [ ] Breadcrumb completo da categoria (ex: Casa > Cozinha > Lixeiras)
- [ ] Lista de atributos obrigatórios com nome e tipo de cada
- [ ] 3 concorrentes top extraídos (título, preço, MLB-id, vendedor, **permalink** — necessário para Helena fazer scraping)
- [ ] Range de preços do nicho (min, mediano, max)
- [ ] Top-5 palavras-chave aparecendo nos títulos dos concorrentes

**Veto:** o `domain_discovery` não retorna confiança. Marcar para revisão humana (com 2 categorias alternativas, tiradas da própria lista de candidatos) quando o predictor devolver 2+ candidatos plausíveis com os concorrentes top divididos entre eles, quando menos de 2 dos 3 concorrentes estiverem na categoria escolhida, ou quando a categoria não for folha que aceita anúncio (`listing_allowed`).

## Inteligência de Conversão (saída de Helena Estrategista)

- [ ] Brief gerado para 100% dos SKUs com `status: ok` em categorização
- [ ] Diagnóstico tem `dor_interna_mais_forte`, `only_factor`, `ansiedades` e `linguagem_real_cliente`
- [ ] Cada item do diagnóstico tem trecho de review como evidência (ancoragem obrigatória)
- [ ] `linguagem_real_cliente` com 5-10 frases textuais extraídas dos reviews
- [ ] Escada "E Daí?" com 3-5 features (feature → benefício lógico → benefício emocional)
- [ ] `confianca` declarada coerente com volume de reviews (alta ≥100 / media 50-99 / baixa <50)
- [ ] Dados brutos de scraping preservados em `output/inteligencia/_raw/`

**Veto:** brief com afirmação no diagnóstico sem citação de review como evidência; brief sem `limitacoes[]` ou sem `keywords_busca`.

## Conteúdo Textual (saída de Renata Redatora)

### Títulos (3-5 alternativas com scoring)
- [ ] 3-5 títulos propostos por SKU (nunca apenas 1)
- [ ] Cada título com 50 ≤ caracteres ≤ 70
- [ ] Cada título com `score_busca` (0-10), `score_conversao` (0-10), `justificativa` e `recomendado` (bool)
- [ ] Exatamente UM título com `recomendado: true` (maior soma de scores)
- [ ] Padrão PMME (Produto + Marca + Modelo + Especificação)
- [ ] Cada título começa com tipo+material+capacidade
- [ ] Cada título contém pelo menos 1 feature mecânica
- [ ] Cada título cita ambientes de uso
- [ ] Sem emojis nem caracteres especiais proibidos
- [ ] Sem CAPS LOCK (exceto siglas)
- [ ] Pelo menos 1 título incorpora palavra da `linguagem_real_cliente` do brief (quando brief não é neutro)

### Descrição
- [ ] Tem 3 blocos claramente delimitados
- [ ] Bloco 1 (abertura): 3-5 linhas, ancorada na `dor_interna` do brief (exceto se `diagnostico_neutro: true`)
- [ ] Bloco 1 integra 1-2 frases da `linguagem_real_cliente` do brief
- [ ] Bloco 2: bullets de specs técnicas + `publico_genero`/`compatibilidade` quando preenchidos no dossiê
- [ ] Bloco 3: features no formato `Feature: Benefício emocional` (camada 3 da escada E daí do brief)
- [ ] 200-350 palavras totais
- [ ] Tom Terra Casa Decor (casual, acolhedor — verificável pela presença de "seu lar", "casa", "dia a dia" e ausência de "adquira", "produto premium")
- [ ] Sem promessas exageradas (nada de "melhor do mercado")
- [ ] **Plain text estrito** (regra do ML, valida com regex):
  - Sem HTML (`<br>`, `<b>`, `<p>`, etc.) — testar com `/<[^>]+>/`
  - Sem markdown de formatação (`**negrito**`, `# título`, `> citação`)
  - Sem emojis (range Unicode pictográfico)
  - Sem caracteres `<` ou `>` soltos
  - Quebras de linha apenas com `\n` (nunca `\r\n` literal nem `<br>`)
  - Se algum desses aparecer, **veto** ou sanitização automática no workflow (já implementada)

### Ficha técnica
- [ ] 100% dos atributos obrigatórios da categoria preenchidos
- [ ] Unidades padronizadas (cm para dimensões, kg para peso, L para capacidade)
- [ ] Valores consistentes com os do dossiê

**Veto:** título fora do range 50-60 chars; descrição sem os 3 blocos; ficha incompleta.

## Capas (step-07)

- [ ] Toda cor de `variacoes[]` tem ≥1 foto em `capas-{pai_sku}.yaml` (máximo 10)
- [ ] Endereço entregue ao ML abre em 1200×1200 (transformação do Cloudinary)
- [ ] A capa mostra **este** produto **nesta** cor
- [ ] Nenhuma foto com logo, nome de loja, slogan ou texto embutido (regra SEM MARCA)

**Veto:** cor sem capa; capa de outra cor/produto; capa com marca da loja.

## Revisão (saída de Vinicius Validador)

- [ ] Parecer para 100% dos SKUs do lote
- [ ] Cada parecer com status `aprovado` ou `reprovado` + justificativa
- [ ] Se reprovado, lista de correções específicas
- [ ] Campo `modo` declarado em cada parecer (`simples` ou `variacoes`)

### Critérios adicionais para `modo: variacoes`

Os itens abaixo são **vetos duros**: qualquer falha = reprovado automático, independente de score.

- [ ] **Preço uniforme**: `preco_venda` idêntico em todas as entradas de `variacoes[]`. O parecer deve listar os valores encontrados nas notas para rastreabilidade.
- [ ] **Foto por cor**: cada valor distinto de `cor` em `variacoes[]` tem ≥1 foto em `capas-{pai_sku}.yaml` (regra `defines_picture` do atributo COLOR no ML).
- [ ] **`attribute_combinations` consistente**: (a) conjunto de chaves idêntico em todas as variações; (b) nenhum par `{atributo: valor}` repetido entre variações distintas.
- [ ] **`SELLER_SKU` e `EAN` por variação**: campos `sku` e `ean` preenchidos e não nulos em cada item de `variacoes[]`.
- [ ] **Categoria aceita variações**: `aceita_variacoes: true` e `cor_value_map`/`value_id` presentes para cada cor em `variacoes[]` no arquivo da Cibele.
- [ ] **Descrição plain text**: sem HTML, markdown, emojis ou `<br>` — mesma regra do modo simples, válida também para anúncios com variações.

**Veto na revisão de variações:** qualquer falha nos seis critérios acima dispara reprovação e devolve o anúncio ao agente responsável (Renata para preço/descrição, o Almir para a capa da cor, Caio para SELLER_SKU/EAN, Cibele para categoria/cor_value_map).

## Publicação (saída de Paula Publicação)

- [ ] MLB-id retornado pelo ML para cada produto aprovado
- [ ] URL pública do anúncio acessível
- [ ] Vinculação no Tiny com SUCCESS
- [ ] Log no Supabase em `ml_tools.publicacoes`

**Veto na publicação:** se ML retornar erro 4xx, parar e reportar ao usuário; não publicar próximo SKU automaticamente até diagnóstico.
