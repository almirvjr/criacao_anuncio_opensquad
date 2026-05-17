# DECISOES

<!-- Decisoes tecnicas importantes. Formato: data - contexto - decisao - motivo. -->

## 2026-05-16

### Workflow "ML Publicar" hospedado em n8n cloud - estrategia de fotos
**Contexto:** spec original previa que Paula enviaria caminhos locais de fotos (`pictures_local_paths`) no payload do webhook. Mas o n8n esta em cloud (`dryboxjellyfish-n8n.cloudfy.live`), nao acessa o disco local.

**Decisao:** opcao A - fotos sao salvas previamente pelo Felipe no bucket publico `tcd-produtos` do Supabase Storage. Paula envia apenas as URLs publicas. ML baixa server-side via `pictures: [{source: "https://..."}]` no POST /items.

**Motivo:** workflow fica mais simples (~6 nos a menos, sem upload de fotos). ML aceita URLs publicas no payload. As fotos vao ficar publicas no anuncio publicado de qualquer jeito, entao expor no Storage publico nao adiciona risco.

### Tabela ml_tools.publicacoes sem RLS
**Contexto:** Supabase alertou que RLS esta desabilitado na tabela `ml_tools.publicacoes`.

**Decisao:** manter sem RLS.

**Motivo:** tabela e usada apenas pelo workflow n8n via service_role. Nao contem dados sensiveis (so log de publicacoes proprias). Se a chave anon nao vazar, esta seguro. Adicionar RLS exigiria criar policies para cada cliente futuro.

### Available_quantity inicial fixo em 1 no POST /items ML
**Contexto:** Tiny ERP detecta anuncios na conta "ML PADRAO" e sobrescreve o estoque com o valor real do ERP. Workflow nao precisa enviar estoque correto.

**Decisao:** workflow forca `available_quantity: 1` no payload ML, ignorando o que Paula enviar.

**Motivo:** garante consistencia (Tiny e a fonte da verdade do estoque). Evita descompasso entre planilha e ERP. ML aceita anuncio com qualquer estoque > 0.

### No "POST Tiny" mantido no workflow (substitui varredura manual) — **REVOGADA em 2026-05-17**
**Contexto:** descoberta - hoje Almir varre manualmente o painel Tiny para importar cada anuncio ML novo. A integracao nativa Tiny<->ML nao importa sozinha.

**Decisao:** manter o no "POST Tiny" no workflow chamando `POST https://api.tiny.com.br/public-api/v3/anuncios` (com `conta: "ML PADRAO"`).

**Motivo:** automatiza a varredura manual. Reduz tempo manual do Almir. Endpoint exato e estrutura do payload sao "best guess" ate validar com MCP da Tiny (pendencia).

**REVOGADA:** endpoint `/anuncios` nao existe na API v3 do Tiny (verificado via swagger.json oficial em 17/05). Ver decisao "Vinculo SKU↔MLB manual no painel Tiny" abaixo.

### Sanitizacao defensiva de description no workflow
**Contexto:** ML rejeita `description.plain_text` com HTML/emojis/`<` `>` (erro `item.description.type.invalid`). Renata pode produzir texto com formatacao inadvertidamente.

**Decisao:** defesa em 3 camadas - (1) Renata escreve plain text por instrucao, (2) Vinicius valida via quality-criteria com regex, (3) workflow Code "Montar Payload" sanitiza por seguranca.

**Motivo:** redundancia previne falha total. Se Renata erra ou Vinicius nao pega, workflow ainda salva o anuncio.

### Bucket publico vs privado no Supabase Storage
**Contexto:** fotos dos produtos precisam ser acessadas pelo ML para download server-side.

**Decisao:** bucket `tcd-produtos` configurado como publico.

**Motivo:** as fotos viram publicas no anuncio do ML de qualquer jeito - o bucket publico e apenas o intermediario. Alternativa privada (signed URLs com expiracao) foi considerada mas adicionaria complexidade no Felipe sem ganho de seguranca real.

## 2026-05-17

### Vinculo SKU↔MLB manual no painel Tiny (substitui "POST Tiny mantido")
**Contexto:** investigacao do MCP Tiny revelou que a API v3 NAO tem endpoint para criar mapeamento Tiny↔MLB (busca em paths/summaries/schemas: zero hits para `anuncio/marketplace/mlb/mercado/mapeamento`). API v2 documentada tambem nao tem. Doc oficial e fontes terceiras (Arcos Scale, Marketfacil, suporte Olist) confirmam: integracao nativa Tiny↔ML nao detecta MLBs novos criados via API externa nem cria anuncios novos no ML.

**Decisao:** apos cada publicacao bem-sucedida no ML, o operador faz o vinculo SKU↔MLB **manualmente** no painel Tiny (Integracoes > ML PADRAO > Relacionar Anuncios). Workflow responde com `tiny_sync: { status: "manual_pending", instrucao: "..." }` para sinalizar a pendencia.

**Motivo:** unico caminho documentado e estavel hoje. API v2 legacy (`incluir-mapeamento-anuncio.php`, folclore de forum) foi considerada mas sem doc oficial - apostaria no escuro. Custo operacional baixo no volume atual (esperado 1-5 publicacoes/dia).

### Query do "Buscar Publicacao Existente" com COALESCE para sempre retornar 1 linha
**Contexto:** n8n Postgres node nao propaga downstream quando query retorna 0 linhas. Query antiga `SELECT mlb_id FROM publicacoes WHERE sku = X AND mlb_id IS NOT NULL LIMIT 1` retornava 0 linhas para SKU novo, matando o workflow silenciosamente.

**Decisao:** envolver a query em `SELECT COALESCE((subquery), '') AS mlb_id` que sempre retorna 1 linha (string vazia ou MLB-id). IF `notEmpty` continua roteando certo (vazio -> publica; nao-vazio -> already_published).

**Motivo:** corrige bug estrutural sem mudar a logica do IF. Padrao aplicavel a outros nos Postgres do projeto que fazem lookup de chave estrangeira opcional.

### SELLER_SKU em attributes complementa seller_custom_field
**Contexto:** workflow originalmente enviava SKU apenas em `seller_custom_field` (campo legado do ML).

**Decisao:** `Montar Payload` injeta automaticamente `{ id: 'SELLER_SKU', value_name: sku }` em `attributes` (se nao vier no input). Mantem `seller_custom_field` tambem.

**Motivo:** SELLER_SKU em attributes e o padrao ML moderno e a forma que a integracao nativa Tiny lê o SKU para tentar fazer matching. Manter ambos (atributos + seller_custom_field) e redundancia barata sem conflito.

### listing_type_id validado contra lista
**Contexto:** fallback antigo `input.listing_type_id || 'gold_special'` aceitava qualquer string vinda do webhook.

**Decisao:** validar contra `['gold_special', 'gold_pro']`; valor invalido (ou vazio) cai em `gold_special`.

**Motivo:** previne erro 400 do ML caso a planilha tenha typo ou valor inesperado. Lista pode crescer se outros tipos forem usados (ex: `free`).

### MCP olist-docs apenas como referencia de documentacao
**Contexto:** MCP em `api-docs.erp.olist.com/mcp` foi identificado como **MCP de documentacao** (Mintlify), nao executor.

**Decisao:** adicionado ao `.mcp.json` como `olist-docs`. Para consulta de doc da API v3 Tiny (substitui ter que baixar swagger.json toda vez). NAO substitui chamada HTTP real ao Tiny - operacao real continua via HTTP Request node no n8n com OAuth2.

**Motivo:** util como "enciclopedia" durante desenvolvimento. Nao existe MCP oficial executor da Olist publicado.

### Metodo StorySelling absorvido na squad — fonte de reviews = concorrentes ML
**Contexto:** absorvido conceito do GPT externo "Cientific Selling: O anuncio bionico da Himmel" — fotos baseadas em quebra de objecao a partir de reviews + FAQ. Squad ml-anuncios e para produtos NOVOS sem reviews proprios.

**Decisao:** Helena Estrategista usa Playwright para scrapear reviews + FAQ dos 3 `concorrentes_top` (com `permalink`) que Cibele ja coleta no step-03. Amostra agregada (~50-100 reviews + 10-30 perguntas por SKU) alimenta diagnostico psicologico que vai gerar tanto a copy (Renata) quanto as fotos (Felipe).

**Motivo:** concorrentes ML capturam linguagem real do mesmo publico-alvo brasileiro. Reaproveita estrutura existente (Cibele ja tem permalinks). Alternativas (reviews multi-marketplace, manual, hibrido) descartadas por complexidade vs ganho.

### Helena Estrategista como agente novo separado (nao ampliar Felipe)
**Contexto:** metodo StorySelling tem duas camadas — diagnostico psicologico e execucao do prompt cinematografico.

**Decisao:** criar agente novo `helena-estrategista` (icone 🎯) para diagnostico; Felipe Fotos vira executor puro (consome brief, nao decide).

**Motivo:** separacao de responsabilidade (preserva principio da squad). Brief da Helena tambem alimenta Renata (copy), entao precisa ser produto compartilhavel, nao logica interna do Felipe.

### Texto em overlay pos-producao, nao embutido na imagem AI
**Contexto:** metodo Himmel poe headline, badge, selos visualmente dentro da imagem. Modelos de IA renderizam texto inconsistente (fontes variam, letras erram).

**Decisao:** modelo de IA (Gemini Nano Banana) gera imagem LIMPA. Skill nova `image-overlay` aplica todo o texto via HTML/CSS renderizado por Playwright (depende de `image-creator`).

**Motivo:** tipografia consistente, edicao posterior facil, fonte controlada (Inter), zero risco de letra errada. Tradeoff aceito: 1 passo a mais no pipeline.

### Image-to-image obrigatorio (foto base do dossie sagrada)
**Contexto:** GPT Himmel insiste "USE A IMAGEM ANEXADA — NAO ALTERE O PRODUTO". Comprador recebe o produto real, nao versao reimaginada pela IA.

**Decisao:** toda foto gerada e image-to-image sobre `foto_base_url` do dossie (capturada por Caio). Modelo so altera cenario e iluminacao. Se modelo distorce produto, retry 1 vez; ainda distorceu = veto.

**Motivo:** fidelidade visual reduz devolucao. Text-to-image puro foi descartado (alto risco de produto entregue diferente da foto).

### Modelo de IA = Gemini 2.5 Flash Image (Nano Banana)
**Contexto:** GPT Himmel recomenda Gemini Pro. Skill `image-ai-generator` precisa de modelo image-to-image bom, barato, com API estavel.

**Decisao:** padronizar em `gemini-2.5-flash-image` (Nano Banana) via Google AI Studio para todas as 10 fotos. Custo estimado ~$0.04/imagem ($0.40 por SKU).

**Motivo:** image-to-image nativo bom, custo baixo, API estavel, aceita prompt JSON estruturado. GPT Image 1 (OpenAI) considerado mas image-to-image fraco e mais caro ($0.19).

### Inteligencia de Conversao alimenta copy E fotos (step entre categorizacao e copywriting)
**Contexto:** diagnostico psicologico das reviews tambem serve para Renata escrever titulo/descricao, nao so para Felipe gerar fotos.

**Decisao:** novo step-04 (Inteligencia de Conversao) entre Cibele (step-03) e Renata (step-05). Brief estrategico compartilhado: Renata usa para copy, Felipe usa para fotos.

**Motivo:** maxima sinergia — copy e fotos contam a mesma historia. Custo de scraping pago 1 vez por SKU, beneficio em 2 entregaveis. Pipeline cresceu de 10 para 11 steps.

### Renata gera 3-5 titulos com scoring (D7 absorvido do GPT "Gerador de Titulos ML")
**Contexto:** GPT publico "Gerador de Titulos ML" entrega 3-5 opcoes com explicacao de potencial. Versao anterior da Renata entregava 1 titulo.

**Decisao:** Renata propõe 3-5 alternativas, cada uma com `score_busca` (0-10), `score_conversao` (0-10), `justificativa` e `recomendado` (1 por SKU). Checkpoint humano (step-06) escolhe.

**Motivo:** reduz risco de "titulo unico ruim". Cria log de alternativas para iteracao. Casa com Himmel (que tambem gera 3 titulos SEO).

### Caio Curador formaliza campos canonicos (D8)
**Contexto:** Renata precisa de inputs estruturados previsiveis (produto, marca, modelo, categoria, especificacoes, publico, compatibilidade).

**Decisao:** dossie do Caio sempre carrega `tipo`, `marca`, `modelo`, `categoria_sugerida_livre`, `publico_genero` e `compatibilidade` (mesmo que `null` para a maior parte do catalogo).

**Motivo:** padroniza vocabulario downstream. `null` explicito > campo ausente. Inferir agora evita refator depois quando entrar categoria com gênero (roupas) ou compatibilidade (panela inducao).

### Tamanho de foto 1200x1200 px e PADRAO FIXO (nao minimo)
**Contexto:** versao anterior dizia "resolucao minima 1200x1200", o que permitia fotos maiores (ex: 1500x1500).

**Decisao:** toda foto entregue tem dimensao EXATA 1200x1200. Maior OU menor e veto automatico. Felipe redimensiona se Nano Banana retornar diferente.

**Motivo:** templates de overlay (image-overlay) assumem canvas 1200x1200 fixo — outras dimensoes quebram posicionamento de selos/headlines. Padronizacao visual no marketplace. Conformidade com tamanho recomendado pelo ML.
