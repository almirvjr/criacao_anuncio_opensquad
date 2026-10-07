---
execution: subagent
agent: paula-publicacao
inputFile: squads/ml-anuncios/output/revisao/pareceres.yaml
outputFile: squads/ml-anuncios/output/publicacao/resultados.yaml
model_tier: powerful
# Unidade de trabalho: 1 anúncio (pai_sku). modo:variacoes = N cores; modo:simples = N=1.
---

# Step 10: Disparo de Publicação via Webhook n8n

## Context Loading

Load these files before executing:
- `squads/ml-anuncios/output/revisao/pareceres.yaml` — filtrar apenas anúncios com `status: aprovado`
- `squads/ml-anuncios/output/copywriting/anuncios.yaml` — `titulo_final`, `description.plain_text` (Renata — mapear para `description_plain` no payload)
- `squads/ml-anuncios/output/categorizacao/categorias.yaml` — `category_id`, `cor_value_map`, `variation_attribute` por pai_sku (Cibele)
- `squads/ml-anuncios/output/capas/capas-{pai_sku}.yaml` — fotos de cada cor (1 a 10, endereço 1200×1200 do Cloudinary), montadas no step-07
- `squads/ml-anuncios/output/curadoria/dossies.json` — `brand`, `price`, atributos de nível item (Caio)
- `.env` — variável `N8N_WEBHOOK_ML_PUBLICAR`

## Instructions

### Process

1. **Validar pré-requisitos do step**: confirmar que `N8N_WEBHOOK_ML_PUBLICAR` está definido em `.env`. Se ausente, parar e instruir o usuário.
2. **Filtrar anúncios aprovados**: ler `pareceres.yaml` e selecionar apenas os com `status: aprovado` (ou subconjunto que o usuário escolheu no checkpoint do step 09).
3. **Montar o pacote com o comando (não à mão):** para cada anúncio aprovado
   ```
   python tools/montar_payload.py --entrada squads/ml-anuncios/output/anuncios-entrada.json --categorias squads/ml-anuncios/output/categorizacao/categorias.yaml --copy squads/ml-anuncios/output/copywriting/anuncio-{pai_sku}.yaml --capas squads/ml-anuncios/output/capas/capas-{pai_sku}.yaml --pai {pai_sku} --saida squads/ml-anuncios/output/publicacao/payload-{pai_sku}.json
   ```
   O comando aplica o contrato do webhook (modo variações/simples, preço igual entre cores, 1 a 10 fotos por cor, `SELLER_SKU`/`EAN` por cor, medida da caixa em `SELLER_PACKAGE_*`, `COLOR` só na variação). Erro do comando = parar o anúncio e reportar a mensagem (ela diz qual cor/campo). **Nunca editar o JSON gerado.**
4. **POST para o webhook n8n** com o conteúdo de `payload-{pai_sku}.json`, header `Content-Type: application/json` e timeout de 60 segundos. Capturar HTTP code e corpo da resposta.
5. **Interpretar a resposta** segundo o contrato do n8n:
   - HTTP webhook != 200 OR timeout → falha de infra; marcar anúncio como `infra_failure` e PAUSAR o lote.
   - HTTP webhook 200 e `status: "success"` → registrar `mlb_id`, `permalink`, `tiny_sync` (espera-se `status: "manual_pending"`), `supabase_log_id`, `timestamps`.
   - HTTP webhook 200 e `status: "failed"` → registrar `stage`, `error_code`, `error_message`; CONTINUAR.
   - HTTP webhook 200 e `status: "partial"` → registrar mlb_id válido + warning; CONTINUAR.
6. **Gravar resultado por anúncio** em `output/{run_id}/publicacao/resultado-{pai_sku}.yaml` com a resposta crua do n8n + timestamps + http_webhook code.
7. **Consolidar `resultados.yaml`** com bloco `lote` e lista `resultados`.
8. **Apendar linha** em `squads/ml-anuncios/_memory/runs.md` com data, run_id, qtd_tentadas, sucessos, falhas.

## Output Format

```yaml
lote:
  data_execucao: "<ISO-8601>"
  run_id: "<string>"
  webhook_n8n: "<url do .env, mascarada>"
  total_tentativas: <int>
  sucessos: <int>
  falhas_ml: <int>
  falhas_tiny: <int>
  falhas_infra: <int>
  lote_pausado: <bool>
  faturamento_potencial: <num>

resultados:
  - pai_sku: "<string>"
    modo: "variacoes|simples"
    status: "success|failed|partial|infra_failure"
    mlb_id: "MLB<int>|null"
    permalink: "<url|null>"
    disparo_paula:
      hora_envio: "<ISO-8601>"
      hora_resposta: "<ISO-8601|null>"
      http_webhook: <int>
    n8n_response:
      status: "<string>"
      stage: "<string|null>"
      error_code: "<string|null>"
      error_message: "<string|null>"
      tiny_sync:
        status: "manual_pending|not_attempted|<erro>"
      supabase_log_id: <int|null>
      timestamps: {...}
    acao_recomendada: "<string|null>"
```

## Output Example

```yaml
lote:
  data_execucao: "2026-05-25T12:45:00-03:00"
  run_id: "2026-05-25-1200"
  webhook_n8n: "https://n8n.terracasadecor.com.br/webhook/ml-publicar-***"
  total_tentativas: 2
  sucessos: 1
  falhas_ml: 0
  falhas_tiny: 0
  falhas_infra: 1
  lote_pausado: true
  faturamento_potencial: 150.00

resultados:
  - pai_sku: "VIE_1066-PAI"
    modo: "variacoes"
    status: "success"
    mlb_id: "MLB5087654321"
    permalink: "https://produto.mercadolivre.com.br/MLB-5087654321-lixeira-pedal-5l-tampa-vai-e-vem-viel"
    disparo_paula:
      hora_envio: "2026-05-25T12:01:05-03:00"
      hora_resposta: "2026-05-25T12:02:41-03:00"
      http_webhook: 200
    n8n_response:
      status: "success"
      tiny_sync:
        status: "manual_pending"
      supabase_log_id: 1560
    acao_recomendada: null
```

## Veto Conditions

Rejeitar e refazer se ALGUMA for verdadeira:
1. Tentativa de disparar webhook para anúncio que não está em status `aprovado` no parecer.
2. Algum anúncio com `status: success` retornado pelo n8n mas sem `mlb_id` no corpo da resposta.
3. Falha de infra (timeout/5xx do webhook) NÃO pausou o lote.
4. Variável `N8N_WEBHOOK_ML_PUBLICAR` ausente no `.env` e o step tentou disparar mesmo assim.
5. Payload `modo: variacoes` enviado com `price`/`available_quantity` no nível raiz (violação de contrato).
6. Payload `modo: simples` enviado com bloco `variacoes` ou `variation_attribute` (violação de contrato).

## Quality Criteria

- [ ] Webhook n8n disparado uma vez por anúncio aprovado (1 anúncio = 1 chamada)
- [ ] Payload gerado no contrato correto para o modo (`variacoes` ou `simples`)
- [ ] Resposta crua do n8n preservada no resultado por anúncio
- [ ] 100% das `status: success` têm `mlb_id` e `permalink`
- [ ] `tiny_sync.status: "manual_pending"` presente em todas as respostas `success`
- [ ] `supabase_log_id` presente em respostas success/failed
- [ ] `lote_pausado: true` quando houve `infra_failure`
- [ ] Arquivo `resultados.yaml` consolidado no caminho correto
