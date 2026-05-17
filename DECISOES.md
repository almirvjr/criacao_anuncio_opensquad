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
