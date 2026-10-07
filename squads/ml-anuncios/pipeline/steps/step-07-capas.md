---
execution: inline
inputFile: squads/ml-anuncios/output/anuncios-entrada.json
outputFile: squads/ml-anuncios/output/capas/
---

# Step 07: Buscar as capas no Cloudinary

Desde 07/10/2026 a squad **não gera foto**. O Almir sobe a capa de cada cor no Cloudinary
(pasta do fornecedor) com duas etiquetas: o **SKU da cor** exatamente como no Tiny e `capa-anuncio`.

## Instructions

1. Buscar com a ferramenta `search-assets` do MCP Cloudinary:
   `expression: "tags=capa-anuncio"`, `fields: "tags,secure_url,created_at,width,height"`, `max_results: 500`.
2. Gravar a resposta **inteira e sem editar** em `squads/ml-anuncios/output/capas/_busca.json`.
3. Rodar:
   ```
   python squads/ml-anuncios/pipeline/validators/capas.py squads/ml-anuncios/output/capas/_busca.json squads/ml-anuncios/output/anuncios-entrada.json squads/ml-anuncios/output/capas/
   ```
4. Código 0 → seguir. Código 1 → **parar** e mostrar ao Almir, em português simples, qual cor de qual
   produto está sem capa e o que conferir (etiqueta com o SKU da cor, `-` e não `_`, e `capa-anuncio`).
   Nunca completar com foto de outra cor.

## Veto Conditions

1. `capas.py` saiu com código diferente de 0.
2. `_busca.json` foi escrito à mão ou resumido (tem que ser a resposta da ferramenta).
