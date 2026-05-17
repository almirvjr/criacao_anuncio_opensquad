# PROGRESSO

## Tarefas ativas

- Squad `ml-anuncios` reformulada com método StorySelling (GPT Himmel) — todos os 11 steps + 6 agentes + skill `image-overlay` prontos. Falta validar em produção (teste E2E).
- Workflow `ML Publicar` no n8n: dry-run parcial OK (execution 118607). Pronto para teste end-to-end com SKU real.

## Proximas tarefas

1. **Teste E2E com lixeira inox 12L** (mesma do exemplo Himmel) — rodar pipeline completa, validar Helena scraping ML, validar Nano Banana preservando produto, comparar 10 fotos finais com output do GPT Himmel.
2. **Criar templates HTML do `image-overlay`** sob demanda na primeira execução (skill define posicionamento por slot mas não tem os 10 HTMLs ainda).
3. **Configurar Gemini 2.5 Flash Image (Nano Banana)** na skill `image-ai-generator` — model id, créditos, validar custo por foto (~$0.04 estimado).
4. Apos cada publicacao no ML, vincular SKU→MLB manualmente no painel Tiny (Integracoes > ML PADRAO > Relacionar Anuncios).
