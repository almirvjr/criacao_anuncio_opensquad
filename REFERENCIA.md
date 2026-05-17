# REFERENCIA

Detalhes tecnicos de infraestrutura, MCPs, tabelas, RLS, skills, workflows.

## MCPs

### mercadolibre
- URL: `https://mcp.mercadolibre.com/mcp`
- Auth: `Bearer <access_token>` (atualizado automaticamente pelo plugin `ml-kit`)
- Token expira em ~6h. Tabela fonte: `public.access_token_ML` no Supabase.

### supabase (opcional)
- MCP oficial via `claude.ai` connector ou config manual.

### n8n (opcional)
- Instancia: ver `.env` -> `N8N_URL`
- Auth: `X-N8N-API-KEY` header com `.env` -> `N8N_API_KEY`

### olist-docs (documentacao API Tiny v3)
- URL: `https://api-docs.erp.olist.com/mcp`
- Tipo: MCP de documentacao (Mintlify), nao executor. Carrega apos restart do Claude Code.
- Tools: `search_olist_erp_api_v3`, `query_docs_filesystem_olist_erp_api_v3` (shell read-only com rg/grep/cat/jq no filesystem virtual da doc).
- API v3 Tiny: 177 endpoints em 26 areas (mapeado em memoria `reference_olist_tiny_api_v3.md`). Auth: OAuth2.
- **Importante:** API v3 NAO tem endpoint para mapeamento Tiny↔MLB. Vinculo SKU↔MLB e manual no painel Tiny.

## Supabase

- Project ID: ver `.env` -> `SUPABASE_PROJECT_ID`
- Schemas: `public` (legado), `ml_tools`, `tiny`, `integracao`
- Tabela critica: `public.access_token_ML` (id, access_token, refresh_token, expires_at)
- Tabela: `ml_tools.publicacoes` (log de publicacoes ML feitas pelo workflow ML Publicar)
  - Campos: id (BIGSERIAL), sku, mlb_id, category_id, price, status ('success'|'failed'|'partial'), error_message, payload_request (JSONB), payload_response (JSONB), created_at
  - Indices: sku, status, created_at DESC
  - RLS: desabilitado (acesso so via service_role)

## Supabase Storage

- Bucket `tcd-produtos` (publico): fotos dos produtos para publicacao no ML
  - Estrutura: `<sku>/foto-NN.jpg`
  - URL base: `https://<project>.supabase.co/storage/v1/object/public/tcd-produtos/`

## Skills e Plugins

- **ml-kit** (local): hook SessionStart refresh token ML + `/ml-kit:refresh-ml`
- **superpowers** (opcional): brainstorming, planning, TDD, debugging helpers

## Workflows n8n

### ML Publicar
- **ID:** `0rzNJ7RLqLzMbKnf`
- **Webhook:** `https://dryboxjellyfish-n8n.cloudfy.live/webhook/ml-publicar` (var `.env` -> `N8N_WEBHOOK_ML_PUBLICAR`)
- **Proposito:** receber payload da Paula (squad ml-anuncios), criar anuncio no ML via `POST /items`, logar resultado em `ml_tools.publicacoes`. Vinculo Tiny↔MLB e MANUAL no painel Tiny (Integracoes > ML PADRAO > Relacionar Anuncios) - feito apos cada execucao bem-sucedida.
- **Nos:** 12 (Webhook -> Postgres SELECT COALESCE idempotencia -> IF -> Postgres SELECT token -> Code montar payload -> HTTP POST ML -> IF -> Postgres INSERT log -> Respond)
- **Credenciais usadas:** `supabase - postgres`, token ML via SELECT no Postgres. (Credencial `Tiny OAuth ERP` deixou de ser usada.)
- **Status atual:** INATIVO (aguarda primeiro teste end-to-end com SKU real antes de ativar). Dry-run parcial validado em 17/05 (execution 118607).
- **Idempotencia:** SELECT em `ml_tools.publicacoes` por SKU antes de publicar; se ja tem mlb_id com status 'success', retorna `already_published`. Query usa `COALESCE((subquery), '') AS mlb_id` para sempre retornar 1 linha (evita 0-rows que matariam o flow).
- **Resposta:** `tiny_sync.status: "manual_pending"` no JSON de retorno, sinalizando ao operador a pendencia de vinculo manual.

## Skills da squad ml-anuncios

- `image-fetcher` (hybrid, usa MCP playwright): busca/screenshot de fotos na web
- `image-creator` (mcp playwright): renderiza HTML/CSS em imagem
- `image-ai-generator` (script Python): gera imagens via OpenRouter (env `OPENROUTER_API_KEY`)
