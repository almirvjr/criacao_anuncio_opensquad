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

## Supabase

- Project ID: ver `.env` -> `SUPABASE_PROJECT_ID`
- Schemas: `public` (legado), `ml_tools`, `tiny`, `integracao`
- Tabela critica: `public.access_token_ML` (id, access_token, refresh_token, expires_at)

## Skills e Plugins

- **ml-kit** (local): hook SessionStart refresh token ML + `/ml-kit:refresh-ml`
- **superpowers** (opcional): brainstorming, planning, TDD, debugging helpers

## Workflows n8n

<!-- Listar workflows principais: nome, ID, proposito, tags. -->
