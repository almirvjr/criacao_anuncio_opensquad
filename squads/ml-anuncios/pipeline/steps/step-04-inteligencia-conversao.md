---
execution: subagent
agent: helena-estrategista
inputFile: squads/ml-anuncios/output/categorizacao/categorias.yaml
outputFile: squads/ml-anuncios/output/inteligencia/briefs.yaml
model_tier: powerful
---

# Step 04: Inteligência de Conversão (Diagnóstico StorySelling)

## Context Loading

Load these files before executing:
- `squads/ml-anuncios/output/curadoria/dossies.json` — specs, features e mapa `dados_produto` de cada SKU (Caio); Helena lê o `dados_produto` já construído pelo Caio e enriquece apenas os atributos com `status: "pendente"`
- `squads/ml-anuncios/output/categorizacao/categorias.yaml` — concorrentes_top com permalinks (Cibele); pode estar vazio (caso `sem_concorrente`)
- `squads/ml-anuncios/pipeline/data/storyselling-framework.md` — equação MECLABS, códigos psicológicos, escada E daí (a hierarquia das fotos não se aplica desde 07/10/2026)
- `squads/ml-anuncios/pipeline/data/objection-patterns.md` — 10 famílias de objeção típicas (F1-F10) com gatilhos
- `squads/ml-anuncios/pipeline/data/research-brief.md` — tom e paleta Terra Casa Decor
- `squads/ml-anuncios/pipeline/data/quality-criteria.md` — critérios de aceitação do brief
- `squads/ml-anuncios/pipeline/data/anti-patterns.md` — armadilhas do diagnóstico

## Instructions

### Process

1. Para cada SKU com `status: ok` em `categorizacao/categorias.yaml`:
   - Ler os 3 `permalink` dos `concorrentes_top` (Cibele).
   - **Ler o mapa `dados_produto` do dossiê do Caio** (já presente em `dossies.json`): o Caio já parseou `descricao_complementar` e marcou atributos encontrados como `status: "ok"` e não encontrados como `status: "pendente"`. Helena não remonta esse mapa do zero — parte dele e enriquece apenas os atributos com `status: "pendente"`. Mínimos obrigatórios que devem estar presentes: `material`, `dimensoes_produto` (sub-atributos: `altura_cm`, `largura_cm`, `profundidade_cm` do PRODUTO — não da embalagem), `caracteristicas`.
   - **Se `concorrentes_top` estiver vazio/ausente**: marcar `sem_concorrente: true`, pular passos 2-3, gerar brief com `confianca: baixa` sem diagnóstico MECLABS. Ir direto ao passo 8.

2. **Scraping dos concorrentes** (via Playwright MCP, headless):
   - Para cada `permalink`, acessar a página e coletar **4 blocos**:
     - **Reviews / Opiniões**: até 50 reviews por concorrente (texto + estrelas + data + tem_foto + util_count). Paginar até esgotar ou bater limite.
     - **Perguntas e Respostas**: até 30 perguntas (pergunta + resposta do vendedor + data).
     - **Descrição completa do anúncio** (texto integral).
     - **Ficha Técnica / Especificações**: todos os atributos listados (material, dimensões, peso, capacidade, etc.).
   - Salvar tudo cru em `output/inteligencia/_raw/{mlb_id}.json` para auditoria e cache.
   - Se um permalink retornar 404 / página vazia / bloqueio anti-bot, tentar o 4º concorrente da lista da Cibele (se houver). Se sobrarem só 2, prosseguir com `confianca: media`.

3. **Consolidar amostra agregada por SKU**: juntar reviews + perguntas dos 3 concorrentes mantendo o `mlb_id` de origem em cada trecho.

3a. **Enriquecer `dados_produto` a partir das fichas dos concorrentes**:
   - Para cada atributo com `status: "pendente"` no mapa inicial, buscar valor na ficha técnica + descrição de cada concorrente scraped.
   - **`dimensoes_produto` é prioritário**: sempre buscar `altura_cm` e `largura_cm` do PRODUTO (não da caixa) nas fichas — servem à ficha e à descrição (desde 07/10/2026 não há foto técnica; se não achar, ficam `pendente` e não bloqueiam). `profundidade_cm` é opcional: buscar também, mas se nenhum concorrente a trouxer, manter `status: "nao_aplicavel"` (não `pendente`). Anotar `permalink` do concorrente de origem em cada dimensão encontrada.
   - **Regra de preenchimento**: 1 concorrente com o atributo → `status: "ok"`, `fonte: "concorrente"`, `permalink` do concorrente de origem.
   - **Regra de divergência**: 2+ concorrentes com valores diferentes (tolerância ±10% para numéricos) → `status: "divergente"`, `valores_divergentes: [{ valor, permalink }, ...]`. Helena NÃO escolhe — registra tudo e deixa para o checkpoint (step-04b).
   - **Sem resolução**: atributo obrigatório permanece `status: "pendente"`; `profundidade` sem resolução permanece `status: "nao_aplicavel"` (não bloqueia).
   - Consolidar `pendencias[]`: nomes dos atributos obrigatórios ainda `pendente`. Atributos com `status: "nao_aplicavel"` NÃO entram em `pendencias[]`.
   - Consolidar `divergencias[]`: nomes dos atributos `divergente`.

4. **Diagnóstico MECLABS (Modo Busca)**, seguindo `storyselling-framework.md`:
   - **Dor interna mais forte**: identificar frase emocional recorrente nos reviews 5-estrelas. Citar 2-3 trechos textuais como evidência.
   - **ONLY FACTOR**: formular frase única que descreva o diferencial real do produto na percepção do comprador.
   - **Ansiedades**: top 3-5 medos recorrentes nos reviews 1-2 estrelas e nas perguntas do FAQ. Para cada uma: mapear contra família F1-F10 do `objection-patterns.md`, declarar impacto (alto/médio/baixo) e citar trecho.
   - **Linguagem real do cliente**: 5-10 frases textuais (entre aspas) extraídas dos reviews — esse é o vocabulário que Renata vai reaproveitar.
   - **Persona**: gênero predominante, faixa etária, contexto, inferidos das pistas nos reviews.

5. **Avaliar `diagnostico_neutro`**: se nem reviews 5-estrelas trazem carga emocional, marcar `diagnostico_neutro: true` (produto puramente utilitário). Brief usa apenas escada lógica.

6. **Escada "E Daí?"**: para 3-5 features relevantes do dossiê, montar feature → benefício lógico → benefício emocional. Benefício emocional sempre alinhado com a dor interna.

6b. **Limitações do produto (`limitacoes[]`) — OBRIGATÓRIO**: a partir de `dados_produto` + reviews dos concorrentes, listar o que o produto **NÃO tem** ou seu ponto fraco real (ex.: `sem balde interno`, `haste do pedal em nylon`, `garantia curta`). Cada item: `{texto, fonte}`. A limitação é declarada **na descrição** (a Renata cobre; a trava `validar_claims --sem-fotos` bloqueia se faltar). Princípio: **transparência > esconder** (confiança vende mais que perfeição); limitação dita com naturalidade, nunca buraco escondido. Se de fato não houver limitação relevante, `limitacoes: []` **e** preencher `limitacoes_nota` justificando (decisão consciente, não silêncio). **Nunca** afirmar feature que o produto não tem (ver [[feedback_referencia_so_metodo_nao_feature]]).

7. **Palavras-chave para a ficha (`keywords_busca`)**: levantar, nos títulos dos concorrentes e no autocompletar da busca do ML, as 8–12 palavras mais buscadas do produto e gravar em `keywords_busca: [..]` no brief, da mais para a menos buscada. A Renata usa no campo Modelo (regra do Almir, 07/10/2026: palavra-chave que não está no título).

8. **Validar âncoras**: conferir que cada afirmação do diagnóstico tem trecho de review como evidência. Se algum item ficou sem âncora, rebaixar `confianca` ou ajustar.

9. **Marcar `confianca`**:
   - `alta`: ≥ 100 reviews + 3 concorrentes válidos.
   - `media`: 50-99 reviews OU 2 concorrentes válidos.
   - `baixa`: < 50 reviews (escalar para revisão humana).

10. **Salvar brief e artefatos**: 
    - Escrever `squads/ml-anuncios/output/inteligencia/brief-{pai_sku}.yaml` por anúncio. O brief deve incluir: `dados_produto` completo (Caio + enriquecimento Helena nos atributos antes `pendente`), **`limitacoes[]`** (ou `limitacoes: []` + `limitacoes_nota`), `keywords_busca`, `pendencias[]`, `divergencias[]`, `sem_concorrente`. O step-04b lê esse brief e grava o `dados_produto` final consolidado de volta em `dossies.json` (fonte única de verdade). **Não** salvar artefato separado `_enriquecido/`.
    - Consolidar resumo em `squads/ml-anuncios/output/inteligencia/briefs.yaml`.

11. **TRAVA OBRIGATÓRIA — rodar o validador antes de concluir o step**: para CADA brief gerado, executar
    ```
    python squads/ml-anuncios/pipeline/validators/validar_brief.py squads/ml-anuncios/output/inteligencia/brief-{pai_sku}.yaml --sem-fotos
    ```
    Ele (auto-descobre o `_raw/`) confere estrutura + `limitacoes[]` + âncoras de review. **O step-04 só está concluído quando ele sai com código 0.** Se reprovar, corrigir o brief e rodar de novo. O `validar_claims` não roda mais aqui: sem foto, a limitação só pode ser conferida no texto, então ele roda no step-05 com a copy da Renata.

## Output Format (resumo do lote)

```yaml
lote:
  total_briefs: <int>
  confianca_alta: <int>
  confianca_media: <int>
  confianca_baixa: <int>
  diagnostico_neutro: <int>
  risco_produto: <int>
  sem_concorrente: <int>
  total_pendencias: <int>   # soma de todos os atributos pendentes no lote
  total_divergencias: <int> # soma de todos os atributos divergentes no lote

briefs:
  - pai_sku: "<string>"
    confianca: "alta|media|baixa"
    diagnostico_neutro: <bool>
    risco_produto: <bool>
    sem_concorrente: <bool>
    keywords_busca: ["<palavra mais buscada>", "..."]   # 8-12, usadas no Modelo
    pendencias: ["<string>", "..."]      # atributos de dados_produto ainda pendentes
    divergencias: ["<string>", "..."]    # atributos de dados_produto com divergência
    arquivo: "squads/ml-anuncios/output/inteligencia/brief-<pai_sku>.yaml"
    resumo:
      dor_interna: "<string|null>"
      only_factor: "<string>"
      total_reviews_analisadas: <int>
      ansiedades_top: ["<F1|F2|...>", "..."]
```

## Output Example (resumo do lote)

```yaml
lote:
  total_briefs: 2
  confianca_alta: 1
  confianca_media: 1
  confianca_baixa: 0
  diagnostico_neutro: 0
  risco_produto: 0
  sem_concorrente: 0
  total_pendencias: 1
  total_divergencias: 0

briefs:
  - pai_sku: "TCD-LXI12"
    confianca: "alta"
    diagnostico_neutro: false
    risco_produto: false
    sem_concorrente: false
    pendencias: []
    divergencias: []
    arquivo: "squads/ml-anuncios/output/inteligencia/brief-TCD-LXI12.yaml"
    resumo:
      dor_interna: "Minha casa fica com aparência simples e bagunçada por causa dos detalhes."
      only_factor: "Visual sofisticado de banheiro/cozinha moderna por preço acessível."
      total_reviews_analisadas: 147
      ansiedades_top: ["F1 fragilidade", "F2 inclusão de balde", "F3 dúvida material"]

  - pai_sku: "TCD-PNT80"
    confianca: "media"
    diagnostico_neutro: false
    risco_produto: false
    sem_concorrente: false
    pendencias:
      - "dimensoes_produto.altura_cm"  # concorrentes não trouxeram (não bloqueia)
    # NOTA: profundidade_cm ausente nos concorrentes → status "nao_aplicavel", NÃO entra em pendencias[]
    divergencias: []
    arquivo: "squads/ml-anuncios/output/inteligencia/brief-TCD-PNT80.yaml"
    resumo:
      dor_interna: "Cozinhar do dia a dia precisa ser leve e sem grude."
      only_factor: "Solta a comida sem grudar e dura mais que o teflon comum."
      total_reviews_analisadas: 72
      ansiedades_top: ["F10 limpeza", "F1 fragilidade do revestimento"]
```

## Veto Conditions

Rejeitar e refazer (ou escalar) se ALGUMA for verdadeira:
1. Algum SKU com `status: ok` da Cibele ficou sem brief gerado.
2. Algum brief com `confianca: alta` declarada mas com < 100 reviews coletadas (inconsistência).
3. Algum item do diagnóstico sem trecho de review como evidência.
4. Brief sem `keywords_busca` (lista com pelo menos 5 palavras).
7. Dados brutos de scraping não salvos em `_raw/`.
8. Brief sem `dados_produto` (mapa de atributos) — mesmo que todos os campos sejam `pendente`.
9. Brief sem `pendencias[]` ou `divergencias[]` (mesmo que sejam arrays vazios).
10. Brief sem `sem_concorrente` declarado (bool obrigatório).
11. `dados_produto.dimensoes_produto` ausente do brief (`altura` e `largura` devem estar presentes, mesmo que `pendente`; `profundidade` deve estar presente com `status: "nao_aplicavel"` quando o produto não a possui — nunca ausente).
12. **Brief sem `limitacoes[]` declaradas** (ou, quando vazia, sem `limitacoes_nota` justificando) — limitação esquecida vira claim falso / devolução.
13. **`validar_brief.py` não foi rodado, ou foi rodado e saiu com código != 0** para qualquer brief do lote (a trava é a condição de conclusão do step, não opcional).

## Quality Criteria

- [ ] Brief gerado para 100% dos SKUs com `status: ok` em categorias.yaml
- [ ] `dados_produto` presente em cada brief com mínimos obrigatórios (`material`, `dimensoes_produto`, `caracteristicas`) e `status` em cada atributo
- [ ] `dimensoes_produto.altura` e `dimensoes_produto.largura` resolvidas dos concorrentes ou em `pendencias[]`; `profundidade` resolvida se disponível ou com `status: "nao_aplicavel"` (nunca em `pendencias[]`)
- [ ] `keywords_busca` com 8–12 palavras mais buscadas, da mais para a menos buscada
- [ ] `sem_concorrente` declarado como bool em cada brief
- [ ] `pendencias[]` e `divergencias[]` presentes em cada brief (mesmo que vazios)
- [ ] Cada brief tem diagnóstico completo (dor interna, only factor, ansiedades, linguagem real do cliente, persona) — exceto quando `sem_concorrente: true`
- [ ] Cada item do diagnóstico tem citação de review como evidência
- [ ] Escada "E Daí?" com 3-5 features
- [ ] `confianca` declarada coerente com volume de reviews; `baixa` quando `sem_concorrente: true`
- [ ] Dados brutos de scraping em `_raw/`
- [ ] Arquivo de resumo salvo em `squads/ml-anuncios/output/inteligencia/briefs.yaml` + brief individual `brief-{pai_sku}.yaml` por anúncio
