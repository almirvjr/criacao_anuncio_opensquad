# Quality Criteria — Squad ML Anúncios

Critérios objetivos e verificáveis para cada artefato produzido pela squad.

## Regra global de fotos

**TODA foto entregue pela squad tem exatamente 1200×1200 pixels.** Não é mínimo, não é "a partir de" — é o padrão fixo do projeto. Foto com qualquer outra dimensão (maior ou menor) é veto automático, mesmo que tenha qualidade visual boa. Aplica-se a:

- 10 fotos finais de cada SKU (`output/fotos/{sku}/foto-01.jpg` a `foto-10.jpg`)
- Imagens geradas pelo `image-ai-generator` (saída do Gemini Nano Banana)
- Imagens com overlay aplicadas pela skill `image-overlay`
- Qualquer foto intermediária baixada do fornecedor que vá entrar no pacote final (precisa ser redimensionada/recortada para 1200×1200 antes de ir para o anúncio)

Motivo: padronização visual no marketplace, previsibilidade de overlay (templates assumem 1200×1200), conformidade com o tamanho recomendado pelo Mercado Livre.

## Dossiê de Produto (saída de Caio Curador)

- [ ] SKU, EAN, preço_custo, preço_venda preenchidos
- [ ] Nome completo do produto (não abreviado)
- [ ] Pelo menos 3 specs técnicas (material, dimensões, peso)
- [ ] Marca identificada
- [ ] URL de foto base válida (responde HTTP 200)
- [ ] URL do fornecedor (quando disponível) para Felipe usar

**Veto:** se faltar SKU OU preço_venda, o produto é marcado como `bloqueado` e fica fora do lote.

## Categorização (saída de Cibele Categoria)

- [ ] `category_id` ML válido (formato MLB1234)
- [ ] Breadcrumb completo da categoria (ex: Casa > Cozinha > Lixeiras)
- [ ] Lista de atributos obrigatórios com nome e tipo de cada
- [ ] 3 concorrentes top extraídos (título, preço, MLB-id, vendedor, **permalink** — necessário para Helena fazer scraping)
- [ ] Range de preços do nicho (min, mediano, max)
- [ ] Top-5 palavras-chave aparecendo nos títulos dos concorrentes

**Veto:** se `category_predictor` retornar confiança < 70%, marcar para revisão humana e propor 2 categorias alternativas.

## Inteligência de Conversão (saída de Helena Estrategista)

- [ ] Brief gerado para 100% dos SKUs com `status: ok` em categorização
- [ ] Diagnóstico tem `dor_interna_mais_forte`, `only_factor`, `ansiedades` e `linguagem_real_cliente`
- [ ] Cada item do diagnóstico tem trecho de review como evidência (ancoragem obrigatória)
- [ ] `linguagem_real_cliente` com 5-10 frases textuais extraídas dos reviews
- [ ] Escada "E Daí?" com 3-5 features (feature → benefício lógico → benefício emocional)
- [ ] Briefing das 10 fotos completo, todos os slots preenchidos com nome canônico (`CAPA_PURPLE_COW` a `MACRO_YES_CTA_FINAL`)
- [ ] Cada foto tem `objetivo_meclabs` válido (códigos `+m`, `-a-f`, `+i+v`, etc.)
- [ ] Headlines ≤ 8 palavras; subheadlines ≤ 14
- [ ] Slot 9 (`SOBRECORRECAO_ANSIEDADE`) com 4-6 selos visuais e objetivo psicológico declarado em cada
- [ ] Slot 10 (`MACRO_YES_CTA_FINAL`) com `cta` preenchido
- [ ] `confianca` declarada coerente com volume de reviews (alta ≥100 / media 50-99 / baixa <50)
- [ ] Dados brutos de scraping preservados em `output/inteligencia/_raw/`

**Veto:** brief com afirmação no diagnóstico sem citação de review como evidência; briefing com menos de 10 slots; slot 9 sem selos.

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

**Veto:** título fora do range 50-70 chars; descrição sem os 3 blocos; ficha incompleta.

## Mídia Visual StorySelling (saída de Felipe Fotos)

- [ ] Exatamente 10 fotos por SKU em hierarquia psicológica fixa
- [ ] **Toda foto com dimensão EXATA 1200×1200 px** (regra global do projeto — não aceitar maior nem menor)
- [ ] Slot 1 (`CAPA_PURPLE_COW`) — produto preservado da `foto_base_url` via image-to-image; headline aplicada via overlay
- [ ] Slot 2 (`ANTES_DEPOIS`) — composição split-screen ou comparação visível
- [ ] Slot 3 (`BADGE_TAMANHO`) — objeto de referência cotidiano ao lado do produto
- [ ] Slot 4 (`ANTI_ANSIEDADE_MATERIAL`) — close macro do material
- [ ] Slot 5 (`CLAREZA_ABSOLUTA`) — esclarece objeção declarada no `objecao_alvo`
- [ ] Slots 6-7 (`DETALHE_TECNICO_*`) — closes de features
- [ ] Slot 8 (`LIFESTYLE_USO_REAL`) — produto em ambiente brasileiro contemporâneo
- [ ] Slot 9 (`SOBRECORRECAO_ANSIEDADE`) — 4-6 selos visuais aplicados via overlay
- [ ] Slot 10 (`MACRO_YES_CTA_FINAL`) — CTA aplicado (SEM brand_signature/logo/slogan — regra SEM MARCA, Almir 19/06)
- [ ] Nenhuma foto com logo/slogan/brand_signature ou cores da marca aplicados (regra SEM MARCA)
- [ ] Dimensão **exata 1200×1200 px** em todas (não mínimo — padrão fixo)
- [ ] Toda foto preserva o produto da `foto_base_url` (image-to-image)
- [ ] Texto (headline, subheadline, badge, selos, CTA) aplicado via overlay pós-produção (não embutido pela IA)
- [ ] Cada foto tem JSON correspondente em `output/fotos/{sku}/prompts/foto-NN.json`
- [ ] Cada foto tem `funcao`, `objetivo_meclabs`, `objecao_alvo`, `headline_aplicada` no `metadata.yaml`
- [ ] Custo total do lote reportado em `metadata-fotos.yaml`

**Veto:** menos de 10 fotos; foto que distorceu o produto da base; slot 9 sem selos; slot 10 sem CTA; **qualquer foto com logo/slogan/brand_signature ou cores da marca** (viola a regra SEM MARCA, Almir 19/06); texto embutido na imagem AI em vez de overlay.

## Revisão (saída de Vinicius Validador)

- [ ] Parecer para 100% dos SKUs do lote
- [ ] Cada parecer com status `aprovado` ou `reprovado` + justificativa
- [ ] Se reprovado, lista de correções específicas
- [ ] Campo `modo` declarado em cada parecer (`simples` ou `variacoes`)

### Critérios adicionais para `modo: variacoes`

Os itens abaixo são **vetos duros**: qualquer falha = reprovado automático, independente de score.

- [ ] **Preço uniforme**: `preco_venda` idêntico em todas as entradas de `variacoes[]`. O parecer deve listar os valores encontrados nas notas para rastreabilidade.
- [ ] **Foto por cor**: cada valor distinto de `cor` em `variacoes[]` possui ≥1 entrada em `fotos_cor[]` dessa variação. Imagem ambientalizada distinta por cor — regra `defines_picture` do atributo COLOR no ML.
- [ ] **`attribute_combinations` consistente**: (a) conjunto de chaves idêntico em todas as variações; (b) nenhum par `{atributo: valor}` repetido entre variações distintas.
- [ ] **`SELLER_SKU` e `EAN` por variação**: campos `sku` e `ean` preenchidos e não nulos em cada item de `variacoes[]`.
- [ ] **Categoria aceita variações**: `aceita_variacoes: true` e `cor_value_map`/`value_id` presentes para cada cor em `variacoes[]` no arquivo da Cibele.
- [ ] **Descrição plain text**: sem HTML, markdown, emojis ou `<br>` — mesma regra do modo simples, válida também para anúncios com variações.

**Veto na revisão de variações:** qualquer falha nos seis critérios acima dispara reprovação e devolve o anúncio ao agente responsável (Renata para preço/descrição, Felipe para fotos_cor, Caio para SELLER_SKU/EAN, Cibele para categoria/cor_value_map).

## Publicação (saída de Paula Publicação)

- [ ] MLB-id retornado pelo ML para cada produto aprovado
- [ ] URL pública do anúncio acessível
- [ ] Vinculação no Tiny com SUCCESS
- [ ] Log no Supabase em `ml_tools.publicacoes`

**Veto na publicação:** se ML retornar erro 4xx, parar e reportar ao usuário; não publicar próximo SKU automaticamente até diagnóstico.
