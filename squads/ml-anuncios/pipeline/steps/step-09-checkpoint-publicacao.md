---
type: checkpoint
---

# Step 09: Checkpoint B — Aprovação Final do Lote para Publicação

## Apresentar ao usuário

Mostrar tabela consolidada cruzando `output/revisao/pareceres.yaml`, `output/copywriting/anuncios.yaml`, `output/categorizacao/categorias.yaml`, `output/capas/capas-{pai_sku}.yaml` e `output/anuncios-entrada.json`.

Se algum anúncio tiver `preco_provisorio: true` em `anuncios-entrada.json`, mostrar **antes da tabela**, em destaque:

> ⚠️ **PREÇO PROVISÓRIO: R$ X** — este preço foi colocado só para teste. Publicar com ele? (o anúncio fica à venda por esse valor)

Tabela:

```
| SKU       | Status revisor | Título final                                            | Preço    | Categoria               | Fotos por cor     | Marca / Modelo | Confiança | Correções pendentes                  |
|-----------|----------------|---------------------------------------------------------|----------|-------------------------|-------------------|----------------|-----------|--------------------------------------|
| TCD-LXI12 | aprovado       | Lixeira Inox 12L Pedal Antiodor Cozinha Banheiro Moderna| R$159,90 | Casa > Cozinha > Lixei. | BR 1 · PT 1       | Viel Higiênica / Lixo Quarto | alta      | —                                    |
| TCD-PNT80 | reprovado      | Panela Antiaderente 24cm Cabo Soft Touch Indução Cozinha| R$129,00 | Casa > Cozinha > Panel. | PT 1              | Tramontina Indução / Fogão | baixa     | Expandir descrição; incluir COLOR    |
```

Logo abaixo, indicar: total aprovado, total reprovado, total bloqueado desde o step 01, e o resumo financeiro do lote (soma de preço_venda dos aprovados).

Lembrar o usuário que o passo seguinte (step-10) publica no Mercado Livre via API REAL e sincroniza com Tiny — operação NÃO trivial de reverter. Lembrar também: o anúncio sai com **estoque 1** e precisa ser **ligado ao produto no Tiny à mão** depois.

## Decisão esperada

- **Publicar tudo aprovado** — pipeline segue para o step 10 com todos os SKUs em status `aprovado`. SKUs reprovados são ignorados.
- **Publicar apenas SKUs X, Y, Z** — usuário fornece lista explícita de SKUs a publicar (subconjunto dos aprovados). Os demais ficam pendentes para um próximo lote.
- **Cancelar lote** — pipeline para. Nada é publicado. Outputs intermediários permanecem para iteração futura.

## Veto Conditions

1. Algum SKU em status `aprovado` tem `confianca_publicacao: baixa`, ou com **preço provisório sem "sim" explícito do Almir para o preço** — pedir confirmação extra antes de prosseguir.
2. O bloco `lote` de `pareceres.yaml` tem zero aprovados — não apresentar a opção "Publicar tudo"; só permitir "Cancelar lote" ou voltar para o step 08.
