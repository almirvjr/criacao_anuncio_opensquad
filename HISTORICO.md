# HISTORICO

<!-- Tarefas concluidas (arquivo morto). Formato: data - resumo. -->

## 2026-05-16 - Sessao: setup infra + revisao spec do workflow ML Publicar

### Infraestrutura criada
- Schema `ml_tools` + tabela `ml_tools.publicacoes` no Supabase (log de publicacoes ML; sem RLS, decisao consciente em DECISOES.md).
- Bucket publico `tcd-produtos` no Supabase Storage (Felipe Fotos vai salvar fotos aqui; ML baixa via URL).
- Workflow n8n "ML Publicar" criado (ID `0rzNJ7RLqLzMbKnf`), 13 nos, validado sem erros, inativo no n8n.
- Variavel `N8N_WEBHOOK_ML_PUBLICAR` adicionada ao `.env`.
- Variavel `OPENROUTER_API_KEY` adicionada ao `.env` (chave correta `sk-or-v1-...`).
- Credencial `openrouter_cloudfy` do n8n corrigida (antes estava com chave Supabase por engano).

### Skills verificadas
- `image-fetcher` (hybrid, MCP playwright): OK.
- `image-creator` (mcp, playwright): OK.
- `image-ai-generator` (script Python, env `OPENROUTER_API_KEY`): OK (chave configurada).

### Revisao da spec - ponto 1 (description plain_text)
- Confirmado via doc ML: `description.plain_text` e estrito - sem HTML, sem emojis, sem `<` `>`, quebra so com `\n`.
- Workflow n8n nó "Montar Payload" agora sanitiza defensivamente (regex remove HTML/markdown/emojis/`< >`, normaliza `\r\n` -> `\n`).
- Agente Renata atualizado: novo principio (#4), 4 novos anti-patterns, 2 novos quality criteria.
- `quality-criteria.md` e `anti-patterns.md` da squad atualizados com regras plain text.

### Revisao da spec - ponto 2 (shipping ME2 + fluxo Tiny)
- Verificado via API ML: conta TERRACASADECOR e Platinum 5_green (34k+ vendas), usa ME2 com `logistic_type: "fulfillment"`. Workflow estava com config correta.
- Esclarecido fluxo Tiny: integracao ML-Tiny NAO importa anuncios sozinha; Almir varre manualmente o painel Tiny hoje. O no "POST Tiny" do workflow SUBSTITUI essa varredura manual.
- Decisao: `available_quantity: 1` fixo no payload ML (Tiny corrige depois com estoque real do ERP).
- Workflow nó "POST Tiny" atualizado: `conta: "ML PADRAO"` (era "Mercado Livre" - errado).
- Agente Paula atualizado: payload sem `available_quantity`, fotos via URLs Supabase Storage (nao mais paths locais), novos anti-patterns, timeout 60s.

### Outros
- Tabela `ml_tools.publicacoes` criada sem RLS - decisao consciente (uso interno, service_role only).

## 2026-05-17 - Sessao: validacao do MCP Tiny + dry-run do workflow ML Publicar

### MCP olist-docs adicionado
- Novo MCP `olist-docs` (HTTP, https://api-docs.erp.olist.com/mcp) adicionado ao `.mcp.json`. E **MCP de documentacao** (Mintlify), nao executor. Expoe 2 tools: `search_olist_erp_api_v3` e `query_docs_filesystem_olist_erp_api_v3` (shell read-only com rg/grep/cat/jq no filesystem virtual da doc). Carrega apos reiniciar Claude Code.

### Mapeamento da API v3 Tiny
- Baixado swagger.json (~1MB) de `erp.tiny.com.br/public-api/v3/swagger/swagger.json`.
- Total: 177 endpoints em 26 areas. Distribuicao: GET 72, POST 50, PUT 37, DELETE 18.
- **Achado critico:** API v3 NAO tem endpoint para mapear anuncio Tiny↔MLB. Busca por "anuncio/marketplace/mlb/mercado/mapeamento" retorna ZERO em paths, summaries e schemas. API v2 documentada tambem nao tem endpoint publico para isso (`incluir-mapeamento-anuncio.php` e folclore de forum, sem doc oficial).
- Confirmado via doc oficial e fontes terceiras (Arcos Scale, Marketfacil, suporte Olist): integracao nativa Tiny↔ML **nao cria anuncios novos** nem detecta MLBs criados via API externa. So gerencia anuncios ja existentes.
- Memoria criada: `reference_olist_tiny_api_v3.md` com mapa completo (evita re-baixar swagger em sessoes futuras).

### Workflow ML Publicar ajustado
- **No `POST Tiny` removido.** Revoga decisao anterior (DECISOES.md 2026-05-16) - endpoint que ela assumia nao existe.
- `Publicacao OK?` (branch true) agora liga direto em `Log Sucesso`.
- `Log Sucesso` simplificado: status='success' fixo (so roda no branch ML 201).
- `Respond Sucesso` agora retorna `tiny_sync: { status: "manual_pending", instrucao: "vincular SKU ao MLB no painel Tiny: Integracoes > ML PADRAO > Relacionar Anuncios" }`.
- Workflow agora tem 12 nos (era 13), validacao OK 0 erros.

### Montar Payload reforcado (pontos 4 e 5 da spec)
- Ponto 5: injeta `{ id: 'SELLER_SKU', value_name: sku }` em `attributes` se nao vier (padrao ML moderno, complementa `seller_custom_field` legado).
- Ponto 4: `listing_type_id` validado contra `['gold_special','gold_pro']` com fallback `gold_special` (antes era `||` cego que aceitaria qualquer string).

### Bug estrutural corrigido em Buscar Publicacao Existente
- Query antiga `SELECT mlb_id ... LIMIT 1` retornava 0 linhas quando SKU era novo. n8n descarta downstream nesses casos -> toda primeira publicacao morria silenciosamente.
- Trocado por `SELECT COALESCE((subquery), '') AS mlb_id` que sempre retorna 1 linha (string vazia se SKU novo, MLB-id se existente). IF `notEmpty` continua roteando certo.

### Dry-run parcial executado com sucesso
- 6 nos pos-`Montar Payload` desabilitados temporariamente para zero-risco (evita criar anuncio real no ML).
- Webhook-test acionado via curl com payload dummy (SKU `TEST-DRY-RUN-001`).
- Execution 118607: webhook -> Buscar Publicacao -> Ja Publicado? (false, mlb_id='') -> Buscar Token -> Montar Payload. Payload final validado: SELLER_SKU injetado, listing_type validado, description sanitizada, pictures shape correto, shipping ME2 default.
- 6 nos reabilitados ao final; workflow no mesmo estado funcional de antes (mais correto).

### Memoria
- `reference_olist_tiny_api_v3.md` criada (mapa API v3 + status do MCP olist-docs).
- Plugin `github@claude-plugins-official` desabilitado (conta GitHub gratuita do Almir nao tem Copilot ativo; plugin nao essencial para o projeto).
