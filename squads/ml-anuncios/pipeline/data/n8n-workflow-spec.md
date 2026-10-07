# Workflow n8n — "ML Publicar" (especificação)

> ⚠️ **Esteira sem fotos desde 07/10/2026:** os trechos deste arquivo sobre geração de fotos (Felipe, 10 fotos, slots, overlay, bucket) **não se aplicam** — a capa vem do Almir pelo Cloudinary. Regras de foto guardadas em `_arquivo-fotos/`.

Este documento descreve o workflow n8n que a squad `ml-anuncios` chama via webhook. Use como referência para criar o workflow no n8n (manualmente ou via MCP n8n quando configurado).

## Variável de ambiente

Adicionar ao `.env` do projeto:

```
N8N_WEBHOOK_ML_PUBLICAR=https://<seu-n8n>/webhook/ml-publicar
```

A URL exata é gerada pelo n8n ao criar o nó Webhook do workflow.

## Contrato do webhook

### Entrada — JSON recebido de Paula

```json
{
  "run_id": "2026-05-16-1430",
  "sku": "TCD-LXI15",
  "tiny_sku": "TCD-LXI15",
  "title": "Lixeira Inox 15L Pedal Tampa Antiodor Cozinha Banheiro",
  "category_id": "MLB33375",
  "price": 159.90,
  "currency_id": "BRL",
  "available_quantity": 50,
  "buying_mode": "buy_it_now",
  "listing_type_id": "gold_special",
  "condition": "new",
  "description_plain_text": "...",
  "pictures_urls": [
    "https://<project>.supabase.co/storage/v1/object/public/tcd-produtos/TCD-LXI15/foto-01.jpg",
    "..."
  ],
  "attributes": [
    {"id": "BRAND", "value_name": "Terra Casa Decor"},
    {"id": "MODEL", "value_name": "TCD-LXI15"}
  ],
  "shipping": {"mode": "me2", "free_shipping": false}
}
```

**Nota:** Fotos são publicadas previamente por Felipe Fotos no bucket público `tcd-produtos` do Supabase Storage (caminho: `<sku>/foto-NN.jpg`). O ML baixa as imagens diretamente a partir das URLs — não há upload prévio ao endpoint `/pictures/items/upload`.

### Saída — JSON que o n8n responde para Paula

**Sucesso:**
```json
{
  "status": "success",
  "sku": "TCD-LXI15",
  "mlb_id": "MLB5012345678",
  "permalink": "https://produto.mercadolivre.com.br/MLB-...",
  "pictures_count": 10,
  "tiny_sync": {"status": "success", "id_anuncio_tiny": "998877"},
  "supabase_log_id": 1542,
  "timestamps": {
    "n8n_inicio": "...",
    "post_items_fim": "...",
    "tiny_sync_fim": "...",
    "n8n_fim": "..."
  }
}
```

**Falha do ML (publicação não foi):**
```json
{
  "status": "failed",
  "sku": "TCD-VAS22",
  "stage": "ml_post_items",
  "http_status_ml": 400,
  "error_code": "validation.required_attribute_missing",
  "error_message": "attribute COLOR is required for category MLB438471",
  "supabase_log_id": 1543,
  "tiny_sync": {"status": "not_attempted", "motivo": "publicação ML falhou"}
}
```

**Falha parcial (ML OK, Tiny falhou):**
```json
{
  "status": "partial",
  "sku": "TCD-LXI15",
  "mlb_id": "MLB5012345678",
  "permalink": "https://...",
  "tiny_sync": {"status": "failed", "error_message": "API Tiny indisponível"},
  "supabase_log_id": 1544
}
```

## Estrutura do workflow

```
[1] Webhook (POST)
       ↓
[2] Set: extrair vars + montar pictures payload no formato ML
       (transforma pictures_urls em [{source: "..."}])
       ↓
[3] Supabase: SELECT em ml_tools.publicacoes WHERE sku=$sku → idempotência
       ↓
[4] IF: já existe mlb_id? → retornar "already_published" e ENCERRAR
       ↓ (não existe)
[5] Supabase: SELECT em access_token_ML WHERE app_name='pre-venda' → token
       ↓
[6] Function: montar payload final do item (com pictures: [{source: ...}])
       ↓
[7] HTTP Request: POST https://api.mercadolibre.com/items
       Headers: Authorization: Bearer {{$node["TokenML"].json.access_token}}
       Body: JSON do payload (nó 6)
       Retry: 2 tentativas, 10s entre
       Continue On Fail: true
       ↓
[8] IF: HTTP 201?
       │   sim → caminho de sucesso
       │   não → caminho de falha
       │
       ├─ SUCESSO:
       │   [9]  HTTP Request: POST https://api.tiny.com.br/api2/anuncio.incluir.alterar.php
       │       Body (form-urlencoded): token={{$env.TINY_TOKEN}}&formato=json&anuncio={"sku":"...","conta":"Mercado Livre","id_anuncio":"MLB..."}
       │       Continue On Fail: true
       │       ↓
       │   [10] Set: montar tiny_sync result
       │       ↓
       │   [11] HTTP Request: INSERT em ml_tools.publicacoes via PostgREST
       │       (status=success ou partial; payload_request/response em JSONB)
       │       ↓
       │   [12] Respond to Webhook: JSON de sucesso/parcial
       │
       └─ FALHA (HTTP != 201):
           [13] Set: montar error_code, error_message
               ↓
           [14] HTTP Request: INSERT em ml_tools.publicacoes (status=failed)
               ↓
           [15] Respond to Webhook: JSON de falha
```

**Por que HTTP Request para INSERT (e não nó Supabase nativo):** Conforme CLAUDE.md, o nó nativo `n8n-nodes-base.supabase` não suporta campos do tipo array/JSONB com payload complexo. Usamos PostgREST direto.

## Configuração crítica de cada nó

### Nó 6 — Montar payload do item (Function/Code)
Transforma `pictures_urls` em `pictures: [{source: "https://..."}]` e monta o JSON completo do POST /items.

### Nó 7 — Criar anúncio
- **HTTP Method:** POST
- **URL:** `https://api.mercadolibre.com/items`
- **Authentication:** Header Auth → Bearer token (nó 5)
- **Body Content Type:** JSON
- **Body:** expressão do nó 6 (payload pronto)
- **Retry on Fail:** Sim (max 2 tentativas, 10000ms entre)
- **Continue on Fail:** Sim (precisa continuar para registrar a falha no log)

### Nó 9 — Sync Tiny
- **HTTP Method:** POST
- **URL:** `https://api.tiny.com.br/api2/anuncio.incluir.alterar.php`
- **Body Content Type:** x-www-form-urlencoded
- **Body:**
  - `token`: `{{$env.TINY_TOKEN}}`
  - `formato`: `json`
  - `anuncio`: `{{$json.anuncio_payload}}` (JSON serializado)
- **Continue on Fail:** Sim

### Nó 11/14 — Insert Supabase (via HTTP/PostgREST)
- **URL:** `https://<project>.supabase.co/rest/v1/publicacoes?schema=ml_tools` (ou via header `Content-Profile: ml_tools`)
- **Headers:** `apikey`, `Authorization: Bearer <service_role>`, `Content-Type: application/json`, `Prefer: return=representation`
- **Body:** `{ "sku": "...", "mlb_id": "...", "category_id": "...", "price": ..., "status": "...", "error_message": null, "payload_request": {...}, "payload_response": {...} }`

⚠️ **Lembrete do CLAUDE.md:** Nó nativo `n8n-nodes-base.supabase` não suporta arrays/JSONB complexo. Use **HTTP Request** para PostgREST direto.

## Regras de retry/error handling

| Onde | Retry | Quando desistir |
|------|-------|----------------|
| POST /items | 2x com 10s | Após 2 falhas, registrar e responder failed |
| POST Tiny | 1x | Registrar partial e responder com mlb_id válido |
| INSERT Supabase | 2x | Logar warning e responder mesmo assim |

**Sobre fotos:** Como Paula envia URLs públicas, o ML faz o download server-side durante o POST /items. Se uma URL estiver quebrada, o ML retorna 400 com erro `pictures.invalid_url` — tratado como falha do SKU inteiro.

## Códigos de erro tratados explicitamente

| HTTP ML | Code n8n | status enviado a Paula |
|---------|----------|------------------------|
| 201 | sucesso | success |
| 400 (validação) | erro_payload | failed (stage: ml_post_items) |
| 401 | token_invalido | failed (stage: auth) — Paula vai pausar lote |
| 403 | sem_permissao | failed (stage: auth) |
| 409 | duplicado | already_published |
| 5xx | servidor_ml | failed (stage: ml_post_items, retry esgotado) |

## Pré-requisitos antes de ativar o workflow

1. ✅ Tabela `ml_tools.publicacoes` criada no Supabase
2. Bucket público `tcd-produtos` no Supabase Storage (para Felipe publicar fotos)
3. Credencial Tiny configurada no `.env` do n8n como `TINY_TOKEN`
4. Acesso à tabela `access_token_ML` via service role ou anon key
5. Webhook ativado e URL adicionada no `.env` do projeto Claude como `N8N_WEBHOOK_ML_PUBLICAR`

## Validação antes de subir

Antes de ativar o workflow no n8n:
1. Usar `validate_workflow` (MCP n8n-mcp) — obrigatório conforme regras do projeto
2. Testar com payload de SKU dummy + categoria pública conhecida
3. Verificar idempotência: rodar 2x o mesmo SKU, segundo deve responder `already_published`

## Status atual

- [ ] Workflow criado no n8n
- [ ] Webhook URL adicionada ao `.env`
- [ ] Tabela `ml_tools.publicacoes` criada no Supabase
- [ ] Testado em sandbox com SKU dummy
- [ ] Ativado em produção
