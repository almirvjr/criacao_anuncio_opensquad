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

### playwright (navegacao headless)
- MCP oficial Playwright para automacao de browser headless.
- Tools usadas: `browser_navigate`, `browser_resize`, `browser_take_screenshot`, `browser_evaluate`, `browser_snapshot`.
- Usado em producao por:
  - **Helena Estrategista** (squad ml-anuncios, step-04): scraping de reviews + FAQ + descricao dos 3 concorrentes top no Mercado Livre.
  - **image-creator** (skill): renderiza HTML/CSS em PNG via headless browser.
  - **image-overlay** (skill): aplica texto sobre imagem via HTML/CSS renderizado.

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
- `image-creator` (mcp playwright): renderiza HTML/CSS em imagem (motor generico)
- `image-ai-generator` (script Python): gera imagens AI **via OpenRouter** (`OPENROUTER_API_KEY`). **Modelo de producao: `google/gemini-3.1-flash-image-preview` (Nano Banana 2)** em modo image-to-image, com a `foto_base_url` do dossie como referencia. Modo `test`: `sourceful/riverflow-v2-fast`. Custo producao ~R$0,07-0,10/imagem. (NAO usa Google AI Studio direto — decisao 25/05.)
- `image-overlay` (mcp playwright, depende de `image-creator`): aplica overlay de texto (headline, subheadline, badge, selos, CTA) sobre imagem gerada. Especializado nos 10 slots da hierarquia StorySelling. **Toda saida e 1200x1200 px exatos** (input tambem precisa ser 1200x1200; falha rapido se vier diferente).

## Squad ml-anuncios — agentes e pipeline (11 steps)

Agentes (em `squads/ml-anuncios/agents/`):

| Agente | Papel | Skills |
|---|---|---|
| Caio Curador 📥 | Le planilha, enriquece dossie do produto | WebFetch, WebSearch |
| Cibele Categoria 🗂️ | Descobre categoria ML + 3 concorrentes top com `permalink` | API ML publica |
| Helena Estrategista 🎯 | Scrapea reviews+FAQ dos concorrentes, gera diagnostico StorySelling + briefing das 10 fotos | playwright |
| Renata Redatora ✍️ | Gera 3-5 titulos com scoring + descricao + ficha tecnica, ancorada no brief da Helena | — |
| Felipe Fotos 📸 | Executa as 10 fotos a partir do briefing da Helena (image-to-image + overlay) | image-ai-generator, image-overlay, image-creator |
| Vinicius Validador ✅ | QA + compliance ML + bloco StorySelling | — |
| Paula Publicacao 🚀 | Dispara webhook n8n "ML Publicar" + log no Supabase | — |

Pipeline (11 steps, 2 checkpoints):
1. step-01-leitura-planilha
2. step-02-curadoria-produtos (Caio)
3. step-03-categorizacao (Cibele)
4. step-04-inteligencia-conversao (Helena) ← NOVO
5. step-05-copywriting (Renata)
6. step-06-checkpoint-copy (humano) ← apresenta 3-5 titulos com scoring
7. step-07-fotos (Felipe)
8. step-08-revisao (Vinicius)
9. step-09-checkpoint-publicacao (humano)
10. step-10-publicacao (Paula)
11. step-11-relatorio-final

Frameworks de referencia (em `squads/ml-anuncios/pipeline/data/`):
- `storyselling-framework.md` — MECLABS (equacao C = 4m + 3v + 2(i-f) - 2a), codigos psicologicos (`+m`, `-a-f`, `+i+v`...), escada "E Dai?", StoryBrand adaptado, hierarquia das 10 fotos.
- `objection-patterns.md` — 10 familias de objecao tipicas (F1-F10) com gatilhos e templates.
- `photo-templates.md` — 10 templates JSON cinematograficos parametrizados (CAPA_PURPLE_COW -> MACRO_YES_CTA_FINAL).

## Regra global de fotos da squad

**1200x1200 px exatos.** Maior ou menor e veto automatico. Aplicado em todos os pontos da pipeline (Felipe, image-overlay, quality-criteria, anti-patterns). Motivo: templates de overlay assumem canvas 1200x1200 fixo; outras dimensoes quebram posicionamento de selos/headlines.
