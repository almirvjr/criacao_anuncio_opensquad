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
