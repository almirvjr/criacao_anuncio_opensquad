---
execution: inline
inputFile: squads/ml-anuncios/output/anuncios-entrada.json
outputFile: squads/ml-anuncios/output/capas/
---

# Step 07: Buscar as capas no Cloudinary

Desde 07/10/2026 a squad **não gera foto**. O Almir sobe a capa de cada cor no Cloudinary
(pasta do fornecedor) com duas etiquetas: o **SKU da cor** exatamente como no Tiny e `capa-anuncio`.
Sem `capa-anuncio`, a foto de cadastro do SKU (`foto-cadastro`) vira a capa (Almir 26/10/2026).

## Instructions

1. Buscar com a ferramenta `search-assets` do MCP Cloudinary:
   pelas etiquetas dos SKUs de cor do lote (traz capa, foto de cadastro e as outras), ex.
   `expression: "tags=\"SKU-1\" OR tags=\"SKU-2\""`, `fields: "tags,secure_url,created_at,width,height"`, `max_results: 500`.
   Nunca só `tags=capa-anuncio`: a foto de cadastro ficaria de fora.
2. Gravar a resposta **inteira e sem editar** em `squads/ml-anuncios/output/capas/_busca.json`.
3. Rodar:
   ```
   python squads/ml-anuncios/pipeline/validators/capas.py squads/ml-anuncios/output/capas/_busca.json squads/ml-anuncios/output/anuncios-entrada.json squads/ml-anuncios/output/capas/
   ```
4. Código 0 → seguir. Código 1 (cor sem foto) → **seguir sem a foto** e avisar qual cor de qual produto está
   sem foto (Almir 26/10/2026: a falta de foto trava só a publicação no canal; o Almir sobe a foto e usa
   "Atualizar fotos" no hub). Nunca completar com foto de outra cor.

## Veto Conditions

1. `capas.py` quebrou (erro do programa, não "CAPAS INCOMPLETAS").
2. `_busca.json` foi escrito à mão ou resumido (tem que ser a resposta da ferramenta).
