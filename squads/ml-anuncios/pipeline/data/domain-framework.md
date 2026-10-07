# Domain Framework — Anúncios Mercado Livre

> ⚠️ **Esteira sem fotos desde 07/10/2026:** os trechos deste arquivo sobre geração de fotos (Felipe, 10 fotos, slots, overlay, bucket) **não se aplicam** — a capa vem do Almir pelo Cloudinary. Regras de foto guardadas em `_arquivo-fotos/`.

## Metodologia Operacional da Squad

Esta squad executa um pipeline de 10 etapas para transformar uma linha de planilha em um anúncio publicado no Mercado Livre. O framework abaixo descreve cada fase, seu objetivo e os critérios de transição.

## Fase 1 — Ingestão (Etapas 1-2)

**Objetivo:** transformar planilha bruta em dossiês estruturados por SKU.

1. **Leitura:** abrir Excel/Google Sheets, validar headers obrigatórios (SKU, EAN, nome, preço_custo, preço_venda, foto_base_url, marca, material).
2. **Enriquecimento:** para cada SKU, buscar na web o nome completo do produto (se vier abreviado), specs faltantes do site do fornecedor, peso e dimensões caso ausentes.

**Saída:** `output/curadoria/dossie-{sku}.yaml` para cada produto.

## Fase 2 — Categorização (Etapa 3)

**Objetivo:** descobrir a categoria ML correta e o benchmark competitivo.

1. Chamar `GET /sites/MLB/domain_discovery/search?limit=3&q={nome_simples}` (lista de candidatos, sem número de confiança). Confirmar que o candidato #1 é folha que aceita anúncio via `GET /categories/{id}` (`children_categories` vazio + `settings.listing_allowed`).
2. Buscar concorrentes top-3 com `GET /sites/MLB/search?category={id}&q={keywords}&sort=sold_quantity_desc`.
3. Carregar atributos obrigatórios da categoria via `GET /categories/{id}/attributes`.

**Saída:** `output/categorizacao/categoria-{sku}.yaml` com category_id, breadcrumb, atributos obrigatórios, e os 3 concorrentes top.

## Fase 3 — Criação de Conteúdo (Etapa 4)

**Objetivo:** gerar texto de anúncio (título + descrição + ficha técnica).

1. Título: aplicar padrão `[Tipo] + [Material] + [Capacidade] + [Features] + [Ambientes] + [Marca]` (50-60 chars).
2. Descrição: estrutura de 3 blocos (lifestyle / specs / features-benefícios).
3. Ficha técnica: preencher TODOS os atributos obrigatórios da categoria + opcionais relevantes.

**Saída:** `output/copywriting/anuncio-{sku}.yaml` com title, description, attributes.

## Checkpoint A (Etapa 5)

Usuário aprova o conteúdo textual antes de gerar fotos (passo caro). Apresentação em formato de tabela com SKU, título proposto, categoria, e link para descrição completa.

## Fase 4 — Mídia Visual (Etapa 6)

**Objetivo:** entregar 10 fotos por produto, padronizadas para ML.

1. `image-fetcher` extrai fotos do site do fornecedor (URL na planilha).
2. Se menos de 10, `image-ai-generator` complementa.
3. Saída em 1200×1200 exatos — o `render_faixa.py` normaliza a base no overlay; o Felipe confere antes.
4. Hierarquia: a **Equilibrado** da seção 6 do `storyselling-framework.md` (fonte única). A ordem antiga "2-5 ângulos / 6-8 detalhes" foi substituída em 21/06.

**Saída:** `output/fotos/{sku}/foto-{01..10}.jpg`.

## Fase 5 — Revisão (Etapa 7)

**Objetivo:** auditoria final antes de publicar.

Vinicius Validador checa:
- [ ] Título tem 50-60 chars e segue padrão
- [ ] Descrição tem 3 blocos
- [ ] Ficha técnica cobre 100% dos atributos obrigatórios
- [ ] Tom da copy é Terra Casa Decor (casual, acolhedor — não formal/frio)
- [ ] 10 fotos existem e estão acima de 1200x1200
- [ ] Categoria escolhida combina com o produto
- [ ] Preço de venda > preço de custo

**Saída:** `output/revisao/parecer-{sku}.yaml` com status `aprovado` ou `reprovado` + lista de correções.

## Checkpoint B (Etapa 8)

Usuário aprova o lote inteiro. Visualização em tabela com todos SKUs, status do revisor, e botões/respostas para aprovar, rejeitar, ou aprovar apenas alguns.

## Fase 6 — Publicação (Etapa 9)

**Objetivo:** colocar o anúncio no ar e sincronizar com Tiny.

1. Para cada SKU aprovado, fazer upload das 10 fotos via `POST /pictures/items/upload` → recebe picture_ids.
2. Montar payload do anúncio (title, category_id, price, available_quantity, listing_type_id, description, pictures, attributes).
3. `POST /items` autenticado → recebe MLB-id.
4. `POST` na API Tiny com SKU + MLB-id para vincular o anúncio ao produto.
5. Log em Supabase: tabela `ml_tools.publicacoes` (sku, mlb_id, status, timestamp).

**Saída:** `output/publicacao/resultado-{sku}.yaml` com MLB-id ou erro.

## Fase 7 — Relatório (Etapa 10)

Tabela final consolidada: SKU | Título | MLB-id | URL pública | Status Tiny | Erros.

## Critérios de Transição

- Cada fase só avança quando 100% dos SKUs tiverem seu artefato gerado.
- Erros não bloqueiam o lote — produtos com erro são marcados e seguem; revisor decide se publica ou não.
- Checkpoints PARAM o pipeline; pipeline só retoma com resposta humana.
