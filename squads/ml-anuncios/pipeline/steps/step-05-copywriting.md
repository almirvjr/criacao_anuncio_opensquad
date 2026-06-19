---
execution: subagent
agent: renata-redatora
inputFile: squads/ml-anuncios/output/anuncios-entrada.json
outputFile: squads/ml-anuncios/output/copywriting/anuncios.yaml
model_tier: powerful
---

# Step 05: Copywriting (3-5 Títulos com Scoring + Descrição StorySelling + Ficha Técnica)

## Context Loading

Load these files before executing:
- `squads/ml-anuncios/output/anuncios-entrada.json` — `anuncios[]` com `modo`, `pai_sku`, `variacoes[]` (step-01)
- `squads/ml-anuncios/output/curadoria/dossies.json` — specs, features, `publico_genero`, `compatibilidade` (Caio)
- `squads/ml-anuncios/output/categorizacao/categorias.yaml` — categoria, atributos obrigatórios, concorrentes, top_keywords (Cibele)
- `squads/ml-anuncios/output/inteligencia/briefs.yaml` + `squads/ml-anuncios/output/inteligencia/brief-{pai_sku}.yaml` individual — dor_interna, only_factor, linguagem_real_cliente, escada_e_dai (Helena)
- `squads/ml-anuncios/pipeline/data/research-brief.md` — tom Terra Casa Decor
- `squads/ml-anuncios/pipeline/data/storyselling-framework.md` — escada E daí, ONLY FACTOR
- `squads/ml-anuncios/pipeline/data/quality-criteria.md` — regras de título / descrição / ficha
- `squads/ml-anuncios/pipeline/data/anti-patterns.md` — frases proibidas, CAPS LOCK

## Instructions

### Process

A unidade de trabalho e o **anuncio** (nao o SKU). Um anuncio `modo: simples` tem 1 cor; `modo: variacoes` agrupa N cores em 1 publicacao ML. Titulo e descricao sao sempre 1 por anuncio, compartilhados entre as cores.

Para cada **anuncio** em `anuncios-entrada.json` com brief `confianca ≥ media`:

1. Carregar `modo`, `pai_sku`, `variacoes[]` do anuncio; depois dossie + categoria + brief individual (`brief-{pai_sku}.yaml`).

2. **Gerar 3-5 títulos alternativos** seguindo padrão PMME (Produto + Marca + Modelo + Especificação), 50-70 caracteres cada:
   - **Se `modo: variacoes`**: o título NÃO deve mencionar cor específica em nenhuma das alternativas — usar o `nome_base` como âncora, preencher o slot de especificação com material, capacidade ou feature principal.
   - **Se `modo: simples`**: comportamento legado; a cor pode aparecer normalmente no título.
   - Título 1 — **SEO Forte**: máximo de top_keywords da Cibele, ordem otimizada para busca, emocionalmente neutro.
   - Título 2 — **Storyselling Forte**: incorpora 1-2 palavras da `linguagem_real_cliente` do brief.
   - Título 3 — **Balanço**: meio-termo, SEO + 1 palavra emocional.
   - Títulos 4-5 (opcionais): variações de ordem ou substituição de feature secundária.
   
   Para cada título, computar:
   - `length`: contagem de caracteres (50-70 obrigatório).
   - `score_busca` (0-10): aderência SEO. Critérios: cobertura de top_keywords (peso 4), tipo+material+capacidade nas primeiras palavras (peso 3), presença de ambientes (peso 2), comprimento ótimo 55-62 (peso 1).
   - `score_conversao` (0-10): aderência StorySelling. Critérios: uso de linguagem real do cliente (peso 5), conexão com only_factor (peso 3), tom Terra Casa Decor preservado (peso 2).
   - `justificativa`: 1-2 linhas explicando o trade-off.
   
   Marcar `recomendado: true` em UM título (aquele com maior soma `score_busca + score_conversao`; em empate, prioriza `score_conversao`).

3. **Escrever descrição em 3 blocos delimitados por linha em branco** (1 descrição por anuncio, compartilhada entre todas as cores):
   - **Bloco 1 (3-5 linhas, abertura lifestyle)**: tocar a `dor_interna` do brief; integrar 1-2 frases da `linguagem_real_cliente` naturalmente; sem repetir título; tom acolhedor Terra Casa Decor. Se `modo: variacoes`, pode mencionar levemente a variedade de opções se enriquecer a narrativa.
   - **Bloco 2 (bullets `- ` de specs)**: material, capacidade, dimensões, peso, marca, modelo, garantia. Incluir `publico_genero` e `compatibilidade` quando o dossiê tiver valor (não-`null`). Padronizar unidades (cm/kg/L). **Se `modo: variacoes`**: incluir linha `- Cores disponíveis: [lista das cores das variacoes, ex: Branco, Preto, Cinza]`.
   - **Bloco 3 (bullets `- ` features + fechamento)**: para cada feature da `escada_e_dai` do brief, montar `Feature: Benefício emocional` (camada 3 da escada). Fechar com frase acolhedora generica, **SEM citar marca ("Terra Casa Decor") nem slogan** (regra SEM MARCA, Almir 19/06).

4. **Validar totais**:
   - Descrição 200-350 palavras.
   - Sem promessas exageradas ("melhor do mercado", "imbatível", "premium").
   - Sem CAPS LOCK (exceto siglas como LED, USB).
   - Sem HTML, markdown ou emojis (plain text estrito).

5. **Preencher ficha técnica** (`attributes`) cobrindo 100% dos atributos obrigatórios da categoria mapeados para valores do dossie. Padronizar unidades.

6. **Marcar `status_copy`**:
   - `ok`: todos os checks passam.
   - `warning`: algum critério no limite (ex: 1 atributo opcional ausente do dossie).
   - `sem_brief`: brief da Helena indisponível — Renata caiu no modo legado (1 título); requer revisão humana.

7. **Salvar YAML** em `squads/ml-anuncios/output/copywriting/anuncios.yaml` consolidado + `squads/ml-anuncios/output/copywriting/anuncio-{pai_sku}.yaml` individual (1 arquivo por anuncio, independente do numero de cores).

## Output Format

```yaml
lote:
  total_anuncios: <int>
  ok: <int>
  warning: <int>
  sem_brief: <int>

anuncios:
  - nome_base: "<string>"
    modo: "variacoes|simples"
    variacoes: [{ cor: "<string>" }, ...]   # lista presente se modo: variacoes; null se simples
    sku: "<string>"                          # SKU de referência (primeiro SKU ou o único)
    category_id: "MLB<int>"
    status_copy: "ok|warning|sem_brief"
    brief_utilizado: "<path|null>"
    dor_interna_referenciada: "<string|null>"
    only_factor_referenciado: "<string>"
    titles:
      - texto: "<string>"
        length: <int>
        score_busca: <0-10>
        score_conversao: <0-10>
        justificativa: "<string>"
        recomendado: <bool>
    description:
      plain_text: |
        <bloco 1>
        
        <bloco 2 com bullets>
        
        <bloco 3 com bullets e assinatura>
      word_count: <int>
    attributes:
      - { id: "<string>", name: "<string>", value_name: "<string>" }
    keywords_seo_aplicadas: ["<string>", ...]
    preco_venda: <num>
```

## Output Example

```yaml
lote:
  total_anuncios: 1
  ok: 1
  warning: 0
  sem_brief: 0

anuncios:
  - nome_base: "lixeira-inox-12l"
    modo: "simples"
    variacoes: null
    sku: "TCD-LXI12"
    category_id: "MLB264586"
    status_copy: "ok"
    brief_utilizado: "squads/ml-anuncios/output/inteligencia/brief-TCD-LXI12.yaml"
    dor_interna_referenciada: "Minha casa fica com aparência simples e bagunçada por causa dos detalhes."
    only_factor_referenciado: "Visual sofisticado de banheiro/cozinha moderna por preço acessível."
    titles:
      - texto: "Lixeira Inox 12L Pedal Tampa Antiodor Cozinha Banheiro"
        length: 56
        score_busca: 9
        score_conversao: 6
        justificativa: "SEO forte; emocionalmente neutro."
        recomendado: false
      - texto: "Lixeira Inox 12L Pedal Cozinha Banheiro Moderna Chique"
        length: 54
        score_busca: 7
        score_conversao: 9
        justificativa: "Linguagem real do cliente; toca dor interna; perde alguma cobertura SEO."
        recomendado: false
      - texto: "Lixeira Inox 12L Pedal Antiodor Cozinha Banheiro Moderna"
        length: 56
        score_busca: 8
        score_conversao: 8
        justificativa: "Balanço bom: 'moderna' (linguagem cliente) + SEO base preservado."
        recomendado: true
    description:
      plain_text: |
        Tem detalhes que mudam completamente a sensação da casa. Uma lixeira comum pode deixar o banheiro ou a cozinha com aparência desorganizada, mesmo quando tudo está limpo. Essa lixeira de inox foi pensada pra quem quer praticidade no dia a dia sem abrir mão de um ambiente bonito, moderno e aconchegante. Aquela sensação de casa cuidada que vem dos detalhes.

        - Material: aço inox AISI 430 (corpo) + plástico polipropileno reforçado (pedal e tampa)
        - Capacidade: 12 litros
        - Dimensões: 31 x 24 x 24 cm (Altura x Largura x Profundidade)
        - Peso: 1,1 kg
        - Acionamento: pedal silencioso
        - Sistema de tampa: abertura por haste interna (fio reforçado)
        - Marca: Terra Casa Decor
        - Modelo: TCD-LXI12
        - Garantia: 30 dias

        - Capacidade de 12 litros: menos uma preocupação na rotina
        - Corpo em aço inox: banheiro ou cozinha com aparência sofisticada
        - Pedal silencioso: abre sem usar as mãos, mais higiene no dia a dia
        - Base antiderrapante: tranquilidade no uso, fica firme onde voce coloca

        Pode usar na cozinha, no banheiro, no escritorio ou no consultorio. Importante: este modelo nao vem com balde interno removivel e e compativel com sacolas de mercado comuns. Praticidade que combina com o seu dia a dia.
      word_count: 224
    attributes:
      - { id: "BRAND", name: "Marca", value_name: "Terra Casa Decor" }
      - { id: "MODEL", name: "Modelo", value_name: "TCD-LXI12" }
      - { id: "CAPACITY", name: "Capacidade", value_name: "12 L" }
      - { id: "MAIN_MATERIAL", name: "Material principal", value_name: "Aço inox" }
      - { id: "COLOR", name: "Cor", value_name: "Prateado escovado" }
      - { id: "HEIGHT", name: "Altura", value_name: "31 cm" }
      - { id: "WIDTH", name: "Largura", value_name: "24 cm" }
      - { id: "DEPTH", name: "Profundidade", value_name: "24 cm" }
      - { id: "WEIGHT", name: "Peso", value_name: "1.1 kg" }
      - { id: "ACTUATION_TYPE", name: "Acionamento", value_name: "Pedal" }
    keywords_seo_aplicadas: ["lixeira inox", "lixeira pedal", "lixeira 12 litros", "lixeira cozinha", "lixeira moderna"]
    preco_venda: 159.90
```

## Veto Conditions

Rejeitar e refazer se ALGUMA for verdadeira:
1. Algum anuncio com brief `confianca ≥ media` ficou sem copy.
2. Algum anuncio com menos de 3 títulos propostos OU mais de 5.
3. Algum título fora do range 50-70 caracteres.
4. Nenhum título marcado como `recomendado` (ou mais de um marcado).
5. Anuncio `modo: variacoes` com cor específica mencionada em qualquer título.
6. Anuncio `modo: variacoes` sem linha "Cores disponíveis" no bloco 2 da descrição.
7. Descrição sem os 3 blocos claramente separados por linha em branco.
8. Descrição com word_count fora do range 200-350.
9. Ficha técnica não cobre 100% dos atributos obrigatórios.
10. Presença de termos proibidos ("melhor do mercado", "imbatível", "adquira", "produto premium").
11. CAPS LOCK fora de siglas, emojis em qualquer lugar, HTML ou markdown na descrição.
12. Bloco 1 sem âncora na dor_interna do brief (quando brief tem `diagnostico_neutro: false`).

## Quality Criteria

- [ ] 100% dos anuncios com brief válido receberam copy (1 título + 1 descrição por anuncio)
- [ ] Cada anuncio tem 3-5 títulos com scoring (busca + conversão + justificativa)
- [ ] Exatamente 1 título marcado como `recomendado`
- [ ] Cada título passa o range 50-70 chars
- [ ] `modo: variacoes`: nenhum título menciona cor específica
- [ ] `modo: variacoes`: bloco 2 contém linha "Cores disponíveis: [lista]"
- [ ] Descrição tem 3 blocos e 200-350 palavras em plain text estrito
- [ ] Bloco 1 ancora na `dor_interna` (ou registra `diagnostico_neutro` se aplicável)
- [ ] Bloco 3 segue a `escada_e_dai` do brief
- [ ] `publico_genero` e `compatibilidade` aparecem no bloco 2 quando preenchidos no dossie
- [ ] Fechamento acolhedor presente, **SEM citar marca ("Terra Casa Decor") nem slogan** (regra SEM MARCA, Almir 19/06)
- [ ] Ficha técnica cobre todos os atributos obrigatórios
- [ ] `brief_utilizado` registrado em todos os anúncios
- [ ] Arquivo consolidado salvo em `squads/ml-anuncios/output/copywriting/anuncios.yaml`
