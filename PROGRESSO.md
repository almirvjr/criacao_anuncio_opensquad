# PROGRESSO

## Tarefas ativas

- Revisao da spec do workflow ML Publicar: pontos 1 (descricao plain_text) e 2 (shipping ME2 + fluxo Tiny ML PADRAO) ja resolvidos. Pendentes: ponto 3 (limite 1-12 fotos), ponto 4 (listing_type_id configuravel), ponto 5 (SELLER_SKU como attribute).

## Proximas tarefas

1. **Almir enviar link do MCP da Tiny** - necessario para validar payload do no "POST Tiny" do workflow (endpoint, nomes de campos, estrutura de resposta). Sem isso, o payload atual e "best guess" e so vai ser validado no primeiro teste real.
2. Atualizar agente Felipe Fotos para refletir upload para Supabase Storage bucket `tcd-produtos` (caminho `<sku>/foto-NN.jpg`) e gerar manifest.yaml com URLs publicas.
3. Continuar revisao da spec: pontos 3, 4 e 5 (limite 12 fotos, listing_type configuravel, SELLER_SKU como attribute).
4. Ativar workflow "ML Publicar" no n8n UI apos teste com webhook-test (payload dummy).
5. Rodar primeira execucao da squad com 1-3 SKUs reais (pipeline end-to-end). Aceitar que POST Tiny pode falhar e ajustar.
