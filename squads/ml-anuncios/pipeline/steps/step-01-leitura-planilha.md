---
execution: inline
agent: caio-curador
inputFile: squads/ml-anuncios/output/planilha-entrada.xlsx
outputFile: squads/ml-anuncios/output/anuncios-entrada.json
---

# Step 01: Leitura e Detecção de Modo (Simples vs Variações)

## Context Loading

Load these files before executing:
- `squads/ml-anuncios/pipeline/data/research-brief.md` — contexto do negócio Terra Casa Decor
- `squads/ml-anuncios/pipeline/data/quality-criteria.md` — critérios mínimos por anúncio
- `squads/ml-anuncios/pipeline/data/domain-framework.md` — Fase 1 (Ingestão)

## Instructions

### Process

O operador apenas entrega a planilha; o step detecta o modo automaticamente a partir do conteúdo do arquivo.

1. **Detectar o formato.** Se a planilha tem a coluna `Código do pai` (export padrão Tiny), ela traz produtos pai (agrupamento) + filhos (variações de cor). Se for planilha simples (1 SKU por linha, sem coluna pai), idem — o tradutor lida com os dois casos.

2. **Rodar o tradutor:**
   ```
   # Windows (PowerShell) — definir UTF-8 antes se o caminho tiver acentos:
   $env:PYTHONUTF8=1
   python tools/tiny_to_esteira.py "<caminho/planilha.xlsx>" squads/ml-anuncios/output/anuncios-entrada.json
   ```
   O tradutor usa `tools/esteira/normalizer.py`, que:
   - Agrupa linhas filhas pelo campo `cod_pai` (= `Código do pai`) de cada linha pai.
   - Marca cada anúncio com `modo: variacoes` (pai com pelo menos 1 filho) ou `modo: simples` (SKU avulso, sem vínculo de pai/filho).
   - Extrai a cor de cada variação a partir do campo `Variações` da planilha Tiny (ex.: `"Cor: Branco | Tamanho: ..."` → `"Branco"`).
   - Para SKUs simples, cria uma única variação com `cor: null`.
   - Campos de foto (`fotos_origem`) são populados com as URLs da planilha; `fotos_bucket` começa vazio e é preenchido pelo step de re-hosting.

3. **Confirmar a saída.** O arquivo `squads/ml-anuncios/output/anuncios-entrada.json` deve existir, não estar vazio e ter ao menos 1 anúncio na lista `anuncios`.

## Output Format

O arquivo gerado é `squads/ml-anuncios/output/anuncios-entrada.json`:

```json
{
  "origem": "<caminho absoluto da planilha>",
  "total_anuncios": <int>,
  "total_variacoes": <int — soma de todas as variações de todos os anúncios>,
  "anuncios": [
    {
      "modo": "variacoes | simples",
      "pai_sku": "<SKU da linha pai (agrupador) ou SKU único>",
      "nome_base": "<nome do produto>",
      "marca": "<marca>",
      "peso_bruto_kg": <number | null>,
      "dim_embalagem_cm": { "largura": <int>, "altura": <int>, "comprimento": <int> },
      "atributos_pendentes": ["material", "tamanho_produto", "caracteristicas"],
      "total_variacoes": <int>,
      "variacoes": [
        {
          "sku": "<SKU filho>",
          "cor": "<string | null — null quando modo: simples>",
          "nome": "<nome completo da variação>",
          "ean": "<EAN ou null>",
          "preco_venda": <number>,
          "preco_custo": <number>,
          "fotos_origem": ["<url drive ou planilha>"],
          "fotos_bucket": ["<url bucket — vazio neste step>"],
          "fotos_cor": []
        }
      ]
    }
  ]
}
```

## Output Example

### Exemplo 1 — `modo: variacoes` (produto com cores)

```json
{
  "origem": "g:\\Meu Drive\\TERRA CASA DECOR\\MERCADORIA\\PLANILHA CRIAÇÃO ANÚNCIO ML.xlsx",
  "total_anuncios": 2,
  "total_variacoes": 6,
  "anuncios": [
    {
      "modo": "variacoes",
      "pai_sku": "VIE_1066-PAI",
      "nome_base": "LIXEIRA 5L INOX TAMPA PEDAL PP",
      "marca": "Viel",
      "peso_bruto_kg": 1.1,
      "dim_embalagem_cm": { "largura": 33, "altura": 26, "comprimento": 26 },
      "atributos_pendentes": ["material", "tamanho_produto", "caracteristicas"],
      "total_variacoes": 3,
      "variacoes": [
        {
          "sku": "VIE_1066_3402_BR",
          "cor": "Branco",
          "nome": "LIXEIRA 5L INOX TAMPA PEDAL PP BRANCO",
          "ean": "7893633908576",
          "preco_venda": 150.0,
          "preco_custo": 35.04,
          "fotos_origem": ["https://drive.google.com/open?id=17h3DFSW-1GYRAt5N3-nNuZlYAnccXSMc&usp=drive_fs"],
          "fotos_bucket": [],
          "fotos_cor": []
        }
      ]
    }
  ]
}
```

### Exemplo 2 — `modo: simples` (SKU avulso, sem variação de cor)

```json
{
  "origem": "planilha-simples.xlsx",
  "total_anuncios": 1,
  "total_variacoes": 1,
  "anuncios": [
    {
      "modo": "simples",
      "pai_sku": "TCD-LXI15",
      "nome_base": "Lixeira Inox 15 Litros com Pedal",
      "marca": "Terra Casa Decor",
      "peso_bruto_kg": 2.3,
      "dim_embalagem_cm": { "largura": 30, "altura": 40, "comprimento": 30 },
      "atributos_pendentes": ["material", "tamanho_produto", "caracteristicas"],
      "total_variacoes": 1,
      "variacoes": [
        {
          "sku": "TCD-LXI15",
          "cor": null,
          "nome": "Lixeira Inox 15 Litros com Pedal",
          "ean": "7891234567890",
          "preco_venda": 159.90,
          "preco_custo": 89.90,
          "fotos_origem": ["https://drive.google.com/file/d/xxx/view"],
          "fotos_bucket": [],
          "fotos_cor": []
        }
      ]
    }
  ]
}
```

**Descrição dos campos principais:**
- `origem` — caminho absoluto da planilha usada como entrada.
- `total_anuncios` / `total_variacoes` — contadores de checagem; devem bater com os tamanhos das listas.
- `modo` — `"variacoes"` quando o produto tem linhas filhas agrupadas por cor; `"simples"` quando é um SKU único sem cor.
- `pai_sku` — para `variacoes`, é o SKU da linha pai (agrupador, sem preço/foto próprios); para `simples`, é o próprio SKU do produto.
- `atributos_pendentes` — campos que ainda precisam ser preenchidos nos steps seguintes (pesquisa de categoria ML).
- `fotos_bucket` — começa vazio; preenchido pelo step de re-hosting de fotos.
- `fotos_cor` — reservado para fotos agrupadas por cor (preenchido em step posterior).

## Veto Conditions

Rejeitar e refazer se ALGUMA for verdadeira:

1. O arquivo de entrada não pôde ser aberto ou está vazio (zero linhas de dados após o cabeçalho).
2. Nenhum anúncio foi gerado (`total_anuncios == 0` ou lista `anuncios` vazia).
3. Um anúncio com `modo: variacoes` tem preços **não uniformes** entre as variações — o ML rejeita publicações com preços diferentes por cor na mesma listagem. Verificar se todos os `preco_venda` dentro do mesmo anúncio são iguais.
4. Alguma variação está sem `sku` (campo `null` ou string vazia).

## Quality Criteria

- [ ] Todo anúncio tem campo `modo` explícito (`"variacoes"` ou `"simples"`)
- [ ] Toda variação de um anúncio `modo: variacoes` tem `cor` preenchida (não `null`) e `preco_venda > 0`
- [ ] Toda variação de um anúncio `modo: simples` tem `cor: null` e `preco_venda > 0`
- [ ] Os contadores `total_anuncios` e `total_variacoes` batem com o tamanho real das listas (`anuncios` e `variacoes` de cada anúncio)
- [ ] O arquivo foi salvo em `squads/ml-anuncios/output/anuncios-entrada.json`
