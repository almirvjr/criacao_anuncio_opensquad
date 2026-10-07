---
execution: subagent
agent: caio-curador
inputFile: squads/ml-anuncios/output/anuncios-entrada.json
outputFile: squads/ml-anuncios/output/curadoria/dossies.json
model_tier: powerful
---

# Step 02: Curadoria e Enriquecimento dos Anúncios

## Context Loading

Load these files before executing:
- `squads/ml-anuncios/output/anuncios-entrada.json` — lista de anúncios gerada no step-01 (cada item: `pai_sku`, `modo`, `nome_base`, `marca`, `peso_bruto_kg`, `dim_embalagem_cm`, `descricao_complementar`, `variacoes[]`)
- `squads/ml-anuncios/pipeline/data/research-brief.md` — contexto Terra Casa Decor
- `squads/ml-anuncios/pipeline/data/domain-framework.md` — Fase 1 (Ingestão), seção Enriquecimento
- `squads/ml-anuncios/pipeline/data/quality-criteria.md` — critérios do dossiê
- `squads/ml-anuncios/pipeline/data/anti-patterns.md` — armadilhas comuns a evitar

## Instructions

### Unidade de trabalho: o ANÚNCIO

A unidade de trabalho é o **anúncio** (`pai_sku`), não o SKU individual. Um anúncio no modo `simples` tem exatamente 1 variação; um anúncio no modo `variacoes` tem N variações de cor/tamanho. O dossiê tem a mesma estrutura em ambos os casos.

### Process

1. Filtrar os anúncios com `status` em [`pronto`, `incompleto`] do `anuncios-entrada.json`. Anúncios `bloqueado` são copiados para o output com `dossie: null` e seguem ignorados pelos próximos steps.
2. **Parsear `descricao_complementar`** de cada anúncio (campo string livre do Tiny, pode estar vazio). Extrair atributos canônicos presentes: `material`, `dimensoes_produto` (altura e largura do produto — obrigatórias; profundidade — opcional), `caracteristicas` (lista), e outros atributos relevantes identificáveis no texto. Para cada atributo extraído: registrar `fonte: "descricao_complementar"`, `status: "ok"`. Atributos canônicos ausentes na `descricao_complementar` ficam com `valor: null`, `fonte: null`, `status: "pendente"`. Exceção: `profundidade` ausente deve ser marcada `status: "nao_aplicavel"` (não `pendente`) quando o produto não possui essa dimensão (ex: produto redondo com apenas Altura × Diâmetro). `nao_aplicavel` não gera pendência bloqueante. Nunca inventar valor.
3. **Enriquecer via web** os atributos ainda com `status: "pendente"`, na seguinte ordem:
   - (a) **WebFetch** na página do fornecedor/fabricante quando houver URL disponível nas variações ou no anúncio.
   - (b) **WebSearch** com combinações `"<EAN da variação principal>"`, `"<marca> <nome_base>"` — até 2 resultados relevantes.
   - (c) Se nenhuma fonte resolver: manter `status: "pendente"` com nota explícita. Nunca deixar o campo ausente do mapa `dados_produto`.
4. Para cada anúncio elegível, montar dossiê com: `pai_sku`, `nome_base`, `marca`, `modo`, `peso_bruto_kg`, `dim_embalagem_cm`, o mapa `dados_produto` (construído nos passos 2-3), flags `sem_concorrente`, listas `pendencias` e `divergencias`, a lista de `variacoes` e as specs do produto base.
5. **Enriquecer specs do produto base**: extrair descrição oficial, features mecânicas/funcionais (ao menos 3 quando possível), garantia. Normalizar unidades: dimensões em `cm`, peso em `kg`, capacidade em `L`. Documentar conversão.
6. **Validar URLs de fotos por variação**: HEAD request em cada URL de `fotos_bucket` de cada variação; registrar status `200_ok` ou `invalida`.
7. **Preencher campos canônicos opcionais** (mesmo que `null`):
   - `modelo`: código/nome do modelo (geralmente igual ao `pai_sku` ou vindo da entrada).
   - `publico_genero`: `null` para a maior parte do catálogo Terra Casa Decor; preencher quando explicitamente direcionado (ex: "feminino", "infantil").
   - `compatibilidade`: `null` para a maioria; preencher quando há requisito técnico (ex: "Compatível com fogão a indução"). Texto livre, curto.
8. Marcar `confianca` do dossiê: `alta` (todos os campos vieram de fonte oficial), `media` (parte inferida ou pendente parcial), `baixa` (muita coisa pendente/inferida — sinalizar para revisor).
9. Escrever o JSON consolidado em `squads/ml-anuncios/output/curadoria/dossies.json`, incluindo `dados_produto` com proveniência por atributo.

## Output Format

```json
{
  "lote": {
    "total_dossies": "<int>",
    "confianca_alta": "<int>",
    "confianca_media": "<int>",
    "confianca_baixa": "<int>"
  },
  "dossies": [
    {
      "pai_sku": "<string>",
      "nome_base": "<string>",
      "marca": "<string>",
      "modo": "simples|variacoes",
      "confianca": "alta|media|baixa",
      "tipo": "<string>",
      "modelo": "<string|null>",
      "categoria_sugerida_livre": "<string>",
      "publico_genero": "<string|null>",
      "compatibilidade": "<string|null>",
      "descricao_fornecedor": "<string>",
      "dados_produto": {
        "material": {
          "valor": "<string|null>",
          "fonte": "descricao_complementar|site_fornecedor|concorrente|almir|null",
          "permalink": "<url|null>",
          "status": "ok|pendente|divergente",
          "valores_divergentes": []
        },
        "dimensoes_produto": {
          "valor": { "largura": "<num|null>", "altura": "<num|null>", "profundidade": "<num|null>" },
          "fonte": "descricao_complementar|site_fornecedor|concorrente|almir|null",
          "permalink": "<url|null>",
          "status": "ok|pendente|divergente",
          "valores_divergentes": []
        },
        "caracteristicas": {
          "valor": ["<string>"],
          "fonte": "descricao_complementar|site_fornecedor|concorrente|almir|null",
          "permalink": "<url|null>",
          "status": "ok|pendente|divergente",
          "valores_divergentes": []
        }
      },
      "sem_concorrente": "<bool>",
      "pendencias": ["<chave_dados_produto_com_status_pendente>"],
      "divergencias": ["<chave_dados_produto_com_status_divergente>"],
      "specs": {
        "capacidade_l": "<{valor:<num>, fonte:<string>}|null>",
        "peso_kg": "<{valor:<num>, fonte:<string>}|null>",
        "voltagem": "<{valor:<string>, fonte:<string>}|null>"
      },
      "features": ["<string>"],
      "garantia": "<string|null>",
      "publico_alvo": "<string>",
      "ambientes_uso": ["<string>"],
      "fontes_enriquecimento": [
        { "url": "<url>", "tipo": "fornecedor|fabricante|marketplace|outro" }
      ],
      "variacoes": [
        {
          "sku": "<string>",
          "cor": "<string>",
          "ean": "<string>",
          "preco_venda": "<num>",
          "preco_custo": "<num>",
          "fotos_bucket": ["<url>"],
          "fotos_bucket_status": ["200_ok|invalida"]
        }
      ],
      "status": "ok|warning|bloqueado",
      "warnings": ["<string>"]
    }
  ]
}
```

## Output Example

```json
{
  "lote": {
    "total_dossies": 2,
    "confianca_alta": 1,
    "confianca_media": 1,
    "confianca_baixa": 0
  },
  "dossies": [
    {
      "pai_sku": "LHP-LX15-INOX",
      "nome_base": "Lixeira Inox 15 Litros com Pedal e Tampa Antiodor",
      "marca": "LHP",
      "modo": "variacoes",
      "confianca": "alta",
      "tipo": "Lixeira",
      "modelo": "LX15",
      "categoria_sugerida_livre": "Lixeiras de Cozinha",
      "publico_genero": null,
      "compatibilidade": null,
      "descricao_fornecedor": "Lixeira em aco inox com pedal silencioso, balde interno removivel e tampa antiodor.",
      "dados_produto": {
        "material": {
          "valor": "Aco inox AISI 430",
          "fonte": "descricao_complementar",
          "permalink": null,
          "status": "ok",
          "valores_divergentes": []
        },
        "dimensoes_produto": {
          "valor": { "largura": 28, "altura": 43, "profundidade": 28 },
          "fonte": "descricao_complementar",
          "permalink": null,
          "status": "ok",
          "valores_divergentes": []
        },
        "caracteristicas": {
          "valor": ["Pedal silencioso", "Tampa antiodor", "Balde removivel", "Base antiderrapante"],
          "fonte": "site_fornecedor",
          "permalink": "https://fornecedor-lhp.com.br/produto/LX15",
          "status": "ok",
          "valores_divergentes": []
        }
      },
      "sem_concorrente": false,
      "pendencias": [],
      "divergencias": [],
      "specs": {
        "capacidade_l": { "valor": 15, "fonte": "anuncios-entrada.json" },
        "peso_kg": { "valor": 2.1, "fonte": "site_fornecedor" },
        "voltagem": null
      },
      "features": [
        "Pedal com acionamento suave",
        "Tampa com sistema antiodor",
        "Balde interno removivel",
        "Base antiderrapante"
      ],
      "garantia": "12 meses",
      "publico_alvo": "Familias que valorizam cozinha organizada e higienica",
      "ambientes_uso": ["Cozinha", "Banheiro", "Escritorio"],
      "fontes_enriquecimento": [
        { "url": "https://fornecedor-lhp.com.br/produto/LX15", "tipo": "fornecedor" }
      ],
      "variacoes": [
        {
          "sku": "LHP-LX15-INOX-ESCOVADO",
          "cor": "Inox escovado",
          "ean": "7898555012345",
          "preco_venda": 179.90,
          "preco_custo": 89.90,
          "fotos_bucket": ["gs://bucket/lhp-lx15/escovado-01.jpg"],
          "fotos_bucket_status": ["200_ok"]
        },
        {
          "sku": "LHP-LX15-INOX-PRETO",
          "cor": "Preto fosco",
          "ean": "7898555012346",
          "preco_venda": 179.90,
          "preco_custo": 89.90,
          "fotos_bucket": ["gs://bucket/lhp-lx15/preto-01.jpg"],
          "fotos_bucket_status": ["200_ok"]
        }
      ],
      "status": "ok",
      "warnings": []
    },
    {
      "pai_sku": "TCD-VS22-CER",
      "nome_base": "Vaso Decorativo de Ceramica 22cm Bege Fosco",
      "marca": "Terra Casa Decor",
      "modo": "simples",
      "confianca": "media",
      "tipo": "Vaso decorativo",
      "modelo": null,
      "categoria_sugerida_livre": "Vasos Decorativos",
      "publico_genero": null,
      "compatibilidade": null,
      "descricao_fornecedor": "Vaso em ceramica esmaltada com acabamento fosco e pintura artesanal.",
      "dados_produto": {
        "material": {
          "valor": "Ceramica esmaltada",
          "fonte": "site_fornecedor",
          "permalink": "https://terracasadecor.com.br/vs22",
          "status": "ok",
          "valores_divergentes": []
        },
        "dimensoes_produto": {
          "valor": { "largura": 12, "altura": 22, "profundidade": 12 },
          "fonte": "anuncios-entrada.json",
          "permalink": null,
          "status": "ok",
          "valores_divergentes": []
        },
        "caracteristicas": {
          "valor": null,
          "fonte": null,
          "permalink": null,
          "status": "pendente",
          "valores_divergentes": []
        }
      },
      "sem_concorrente": false,
      "pendencias": ["caracteristicas"],
      "divergencias": [],
      "specs": {
        "capacidade_l": null,
        "peso_kg": null,
        "voltagem": null
      },
      "features": [
        "Acabamento fosco",
        "Pintura artesanal"
      ],
      "garantia": null,
      "publico_alvo": "Amantes de decoracao artesanal",
      "ambientes_uso": ["Sala", "Quarto", "Varanda"],
      "fontes_enriquecimento": [
        { "url": "https://terracasadecor.com.br/vs22", "tipo": "fornecedor" }
      ],
      "variacoes": [
        {
          "sku": "TCD-VS22-CER",
          "cor": "Bege",
          "ean": "7891234001234",
          "preco_venda": 89.90,
          "preco_custo": 38.50,
          "fotos_bucket": ["gs://bucket/tcd-vs22/bege-01.jpg"],
          "fotos_bucket_status": ["200_ok"]
        }
      ],
      "status": "warning",
      "warnings": [
        "peso ausente: nao localizado em site nem em buscas por EAN; Renata pode omitir do bloco de specs",
        "dados_produto.caracteristicas: status pendente — Helena enriquece via concorrentes no step-04"
      ]
    }
  ]
}
```

## Veto Conditions

Rejeitar e refazer se ALGUMA for verdadeira:
1. Algum anúncio elegível ficou sem `nome_base` ou sem `dados_produto`.
2. Mapa `dados_produto` sem os atributos canônicos `material`, `dimensoes_produto`, `caracteristicas` — cada um deve estar presente (mesmo que com `status: "pendente"`).
3. Unidades não normalizadas (ex: dimensões em "mm" ou "polegadas" persistindo no output).
4. `fontes_enriquecimento` vazio para dossiês com confiança `alta` (alta exige pelo menos 1 fonte oficial).
5. Atributo em `dados_produto` com `status: "ok"` mas sem `fonte` declarada.
6. Array `variacoes` vazio em qualquer dossiê (modo simples tem 1 variação, nunca zero).

## Quality Criteria

- [ ] 100% dos anúncios `pronto`/`incompleto` têm dossiê gerado
- [ ] Cada dossiê tem `dados_produto` com atributos canônicos `material`, `dimensoes_produto`, `caracteristicas` — cada um com `valor`, `fonte`, `status`; ausência é veto
- [ ] Atributos vindos de `descricao_complementar` registrados com `fonte: "descricao_complementar"` e `status: "ok"`
- [ ] Atributos não resolvidos com `status: "pendente"` e listados em `pendencias[]`
- [ ] Pelo menos 1 fonte (URL) registrada por dossiê com confiança ≥ media
- [ ] Array `variacoes` com pelo menos 1 item em todo dossiê (modo simples = 1 item)
- [ ] URLs de fotos de todas as variações com status registrado
- [ ] Features identificadas como lista (não como texto corrido)
- [ ] Campos canônicos sempre presentes (mesmo `null`): `modelo`, `publico_genero`, `compatibilidade`
- [ ] Totais do bloco `lote` batem com a contagem real
- [ ] Arquivo salvo em `squads/ml-anuncios/output/curadoria/dossies.json`
