---
execution: inline
agent: paula-publicacao
inputFile: squads/ml-anuncios/output/publicacao/resultados.yaml
outputFile: squads/ml-anuncios/output/relatorio-final.md
---

# Step 11: Relatório Final do Lote

## Context Loading

Load these files before executing:
- `squads/ml-anuncios/output/publicacao/resultados.yaml` — resultado canônico da publicação
- `squads/ml-anuncios/output/revisao/pareceres.yaml` — para listar reprovados/não publicados
- `squads/ml-anuncios/output/curadoria/skus-listados.yaml` — SKUs bloqueados desde a entrada
- `squads/ml-anuncios/output/copywriting/anuncios.yaml` — preço e título final para cruzamento
- `squads/ml-anuncios/pipeline/data/research-brief.md` — tom do relatório

## Instructions

### Process

1. Ler os 4 inputs e classificar cada SKU do lote original em um destes baldes:
   - `publicado` (success no step 10 com MLB-id)
   - `falha_publicacao` (failed no step 10, com mensagem do ML)
   - `nao_publicado_revisao` (reprovado no step 08)
   - `bloqueado_entrada` (status bloqueado já no step 01)
   - `ja_publicado` (duplicidade no step 10)
2. Gerar relatório em Markdown com seções: Cabeçalho, Resumo Executivo, Tabela de Anúncios Publicados (link público), Tabela de Pendências, Próximos Passos.
3. Calcular faturamento potencial = soma dos `preco_venda` dos publicados. Calcular taxa de sucesso.
4. Para cada SKU não publicado, dar recomendação concreta (ex: "Refazer step 05 para TCD-PNT80 — incluir COLOR na ficha").
5. Salvar markdown em `output/relatorio-final.md`. Sem emojis em excesso.

## Output Format

```
# Relatório Final — Lote ML Anúncios

**Data:** <ISO-8601 local>
**Lote:** <total inicial> SKUs

## Resumo Executivo
- Publicados: <int>
- Falhas: <int>
- Reprovados na revisão: <int>
- Bloqueados na entrada: <int>
- Já publicados (duplicados): <int>
- Faturamento potencial publicado: R$ <num>
- Taxa de sucesso: <pct>%

## Anúncios Publicados

| SKU | Título | MLB-id | Preço | URL pública | Tiny |
|-----|--------|--------|-------|-------------|------|
| ... | ...    | ...    | ...   | ...         | ...  |

## Pendências e Recomendações

| SKU | Status | Motivo | Próximo passo |
|-----|--------|--------|---------------|
| ... | ...    | ...    | ...           |

## Próximos Passos
- <ação 1>
- <ação 2>
```

## Veto Conditions

Rejeitar e refazer se ALGUMA for verdadeira:
1. Relatório omite qualquer SKU presente no lote original.
2. Tabela "Anúncios Publicados" lista SKU sem MLB-id ou sem URL pública.
3. Seção "Próximos Passos" vazia quando existem pendências.

## Quality Criteria

- [ ] Cada SKU do lote inicial aparece em exatamente um balde
- [ ] Tabela de publicados tem URL clicável para cada anúncio
- [ ] Pendências têm próximo passo acionável e específico
- [ ] Taxa de sucesso calculada corretamente
- [ ] Faturamento potencial bate com a soma dos preços dos publicados
- [ ] Arquivo salvo em `squads/ml-anuncios/output/relatorio-final.md`
