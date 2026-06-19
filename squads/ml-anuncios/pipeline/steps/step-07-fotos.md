---
execution: subagent
agent: felipe-fotos
inputFile: squads/ml-anuncios/output/anuncios-entrada.json
outputFile: squads/ml-anuncios/output/fotos/metadata-fotos.yaml
model_tier: powerful
---

# Step 07: Pacote de Fotos por Anúncio (StorySelling + Ambientalizada por Cor)

## Context Loading

Load these files before executing:
- `squads/ml-anuncios/output/anuncios-entrada.json` — `modo`, `pai_sku`, `variacoes[]` com `sku`, `cor`, `fotos_bucket[]` (Caio/re-hosting)
- `squads/ml-anuncios/output/curadoria/dossies.json` — specs e features por `pai_sku` (Caio)
- `squads/ml-anuncios/output/inteligencia/briefs.yaml` — briefing das 10 fotos + `cor_heroi` por anúncio (Helena)
- `squads/ml-anuncios/output/copywriting/anuncios.yaml` — título aprovado (insumo opcional para reforçar coerência)
- `squads/ml-anuncios/pipeline/data/photo-templates.md` — 11 templates JSON parametrizados (10 StorySelling + 1 foto técnica `FICHA_TECNICA_DIMENSOES`)
- `squads/ml-anuncios/pipeline/data/research-brief.md` — paleta e ambientação Terra Casa Decor
- `squads/ml-anuncios/pipeline/data/storyselling-framework.md` — códigos MECLABS e hierarquia
- `squads/ml-anuncios/pipeline/data/quality-criteria.md` — regras de mídia visual
- `squads/ml-anuncios/pipeline/data/anti-patterns.md` — vícios visuais a evitar

## Instructions

### Visão Geral

O step opera em dois modos determinados pelo campo `modo` de cada anúncio em `anuncios-entrada.json`:

| `modo`       | O que Felipe gera                                                              | `picture_ids` por variação              |
|--------------|--------------------------------------------------------------------------------|-----------------------------------------|
| `simples`    | 10 fotos StorySelling + 1 foto técnica `FICHA_TECNICA_DIMENSOES`               | StorySelling + foto técnica             |
| `variacoes`  | 10 fotos StorySelling + 1 foto técnica (cor herói) + 1 ambientalizada/cor      | 1 ambientalizada + StorySelling + técnica |

### Process

Para cada **anúncio** em `anuncios-entrada.json` cujo `pai_sku` conste em `briefs.yaml` com `confianca ∈ {alta, media}`:

**PRÉ-GATE — Validar dados obrigatórios antes de gerar qualquer foto**

0. **Gate de dimensões (VETO)**:
   - Ler `dados_produto.dimensoes_produto` do dossiê do Caio para o `pai_sku` corrente.
   - Se o campo estiver **ausente** ou `dimensoes_produto.altura.status != "ok"` ou `dimensoes_produto.largura.status != "ok"`: **parar imediatamente** com erro:
     ```
     VETO step-07 [{pai_sku}]: altura e/ou largura do produto não resolvidas — deveria ter passado pelo checkpoint step-04b.
     dados_produto.dimensoes_produto.altura.status = "{valor_atual|ausente}"
     dados_produto.dimensoes_produto.largura.status = "{valor_atual|ausente}"
     Nenhuma foto será gerada até que altura e largura (obrigatórias) estejam com status = "ok".
     NOTA: profundidade é opcional — status "nao_aplicavel" ou ausente não bloqueia.
     ```
   - Marcar anúncio como `bloqueado_dimensoes_nao_resolvidas`. Os demais anúncios do lote seguem normalmente.

**FASE A — StorySelling + foto técnica (compartilhadas, 1× por anúncio)**

1. **Identificar cor herói**: usar `brief.cor_heroi` se presente; senão usar a primeira variação em `variacoes[]`.

2. **Validar `fotos_bucket[0]` da cor herói**: HEAD request na URL. Se 4xx/5xx, marcar anúncio como `bloqueado_sem_foto_base` e pular.

3. **Criar estrutura de pasta**: `squads/ml-anuncios/output/fotos/{pai_sku}/`, com subpastas `prompts/`, `_overlay_html/`, `ambientalizadas/`.

4. **Para cada foto** do `briefing_fotos` (slots 1 a 10):

   a. **Selecionar template JSON** correspondente ao `funcao` do slot (ver `photo-templates.md`).

   b. **Preencher placeholders** do template usando:
      - Headline, subheadline, badge, CTA, selos do `briefing_fotos[N]`.
      - Cor da variação herói, material, dimensões do dossiê.
      - Ambiente/cenário inferido da categoria + paleta Terra Casa Decor.
      - **Slot `FICHA_TECNICA_DIMENSOES` (foto técnica)**:
        - `{{dim_altura}}` ← `dados_produto.dimensoes_produto.altura`
        - `{{dim_largura}}` ← `dados_produto.dimensoes_produto.largura`
        - `{{dim_profundidade}}` ← `dados_produto.dimensoes_produto.profundidade` (omitir/deixar vazio se `status: "nao_aplicavel"` — linha some do template HTML)
        - `{{headline_dimensoes}}` ← `briefing_fotos[N].headline` (padrão: "Dimensões")
      - **Slots cor-neutros** (DETALHE_TECNICO_*, FICHA_TECNICA_DIMENSOES): usar descrição de material/dimensão — campo `{{cor_produto}}` não se aplica, omitir ou deixar genérico.
      - **Slots CAPA e LIFESTYLE**: referenciar a cor herói explicitamente.

   c. **Salvar JSON** em `squads/ml-anuncios/output/fotos/{pai_sku}/prompts/foto-{NN}.json`.

   d. **Chamar `image-ai-generator`** (modo `production`, Nano Banana 2 via OpenRouter):
      - `base_image`: `fotos_bucket[0]` da cor herói (baixar localmente se necessário).
      - `prompt`: JSON do passo c.
      - `output_format`: PNG 1200×1200.

   e. **Validar imagem gerada**:
      - Dimensão **exata 1200×1200 px**. Se diferente, redimensionar/recortar com produto centralizado.
      - Produto preservado. Se distorção: retry 1 vez. Se ainda distorcido: marcar `falha_distorceu_produto`.

   f. **Aplicar overlay** com `image-overlay` (slot, headline, subheadline, badge, selos, cta) → salvar em `squads/ml-anuncios/output/fotos/{pai_sku}/foto-{NN}.jpg`. **SEM MARCA (Almir 19/06, DEFINITIVA):** não aplicar logo, slogan, `brand_signature` nem cores da marca em nenhuma foto — evita retrabalho num eventual rebrand. A marca não aparece em nenhuma parte do anúncio (foto, título nem descrição).

   g. **Registrar no metadata**: `funcao`, `objetivo_meclabs`, `objecao_alvo`, `headline_aplicada`, `prompt_json`, `resolucao`, `retries`.

**FASE B — Ambientalizada por cor (`modo: variacoes` apenas)**

5. Para cada variação em `variacoes[]`:

   a. **Validar `fotos_bucket[0]` da variação**: HEAD request. Se falhar: marcar `ambientalizada_bloqueada`, `fotos_cor` fica vazio para essa variação. Continuar com as demais.

   b. **Montar prompt de ambientalização** e salvar em `squads/ml-anuncios/output/fotos/{pai_sku}/prompts/ambientalizada-{sku_variacao}.json`:
      - Objetivo: inserir o produto num cenário residencial harmonioso, preservando EXATAMENTE o produto (forma, cor, acabamento).
      - Cenário coerente com a categoria (sala, cozinha, banheiro, etc.) usando a paleta Terra Casa Decor.
      - Instrução explícita de cor: "O produto é [cor]; mantenha essa cor com fidelidade."

   c. **Chamar `image-ai-generator`** (modo `production`):
      - `base_image`: `fotos_bucket[0]` da variação.
      - `prompt`: JSON do passo b.
      - Saída esperada: imagem 1200×1200 sem texto, produto com cor correta no cenário.

   d. **Validar**:
      - Dimensão **exata 1200×1200 px**.
      - Cor do produto corresponde à variação. Se errada: retry 1 vez. Se ainda errada: marcar `falha_cor_incorreta`.

   e. **NÃO aplicar overlay** — imagem de capa deve ser limpa.

   f. **Salvar localmente** em `squads/ml-anuncios/output/fotos/{pai_sku}/ambientalizadas/{sku_variacao}.jpg`.

   g. **Subir ao bucket `tcd-produtos`** (Supabase Storage):
      - Path: `{sku_variacao}/ambientalizada.jpg` (x-upsert).
      - Usar lógica de upload de `tools/rehost_fotos.py` como referência (lê `SUPABASE_SERVICE_ROLE` e `SUPABASE_PROJECT_ID` do env).

   h. **Preencher `variacoes[].fotos_cor`** na entrada correspondente de `anuncios-entrada.json`:
      ```
      https://{PROJECT_REF}.supabase.co/storage/v1/object/public/tcd-produtos/{sku_variacao}/ambientalizada.jpg
      ```

**FASE C — Montar `picture_ids` e fechar metadata**

6. Para cada variação:
   - `modo: variacoes`: `picture_ids = fotos_cor + [foto-01..foto-10]` (11 itens; ambientalizada obrigatoriamente primeira).
   - `modo: simples`: `picture_ids = [foto-01..foto-10]` (10 itens).

7. **Marcar `status_fotos` do anúncio**:
   - `pronto`: todas as fotos (StorySelling + foto técnica + ambientalizadas) geradas com sucesso.
   - `pronto_neutro`: OK mas brief tinha `diagnostico_neutro: true`.
   - `incompleto`: 2+ falhas (somando StorySelling e ambientalizadas) após retry.
   - `bloqueado_sem_foto_base`: foto base da cor herói indisponível.
   - `bloqueado_dimensoes_nao_resolvidas`: `dados_produto.dimensoes_produto.altura` ou `.largura` sem `status: "ok"` — gate pré-geração ativado (checkpoint step-04b não foi concluído). `profundidade` com `status: "nao_aplicavel"` não bloqueia.

8. **Escrever `metadata.yaml` por anúncio** em `squads/ml-anuncios/output/fotos/{pai_sku}/metadata.yaml` + **resumo do lote** em `squads/ml-anuncios/output/fotos/metadata-fotos.yaml`.

## Output Format (resumo do lote)

```yaml
lote:
  total_anuncios: <int>
  prontos: <int>
  prontos_neutros: <int>
  incompletos: <int>
  bloqueados: <int>
  custo_total_estimado_usd: <num>
  modelo_ia: "google/gemini-3.1-flash-image-preview"  # Nano Banana 2

anuncios:
  - pai_sku: "<string>"
    modo: "variacoes|simples"
    status_fotos: "pronto|pronto_neutro|incompleto|bloqueado_sem_foto_base|bloqueado_dimensoes_nao_resolvidas"
    total_storyselling_geradas: <int>          # sempre 10 se pronto
    total_ambientalizadas_geradas: <int>       # N variações se variacoes, 0 se simples
    total_ambientalizadas_bloqueadas: <int>
    falhas: <int>
    retries_total: <int>
    pasta: "squads/ml-anuncios/output/fotos/<pai_sku>/"
    custo_estimado_usd: <num>
```

## Output Example (resumo do lote)

```yaml
lote:
  total_anuncios: 2
  prontos: 2
  prontos_neutros: 0
  incompletos: 0
  bloqueados: 0
  custo_total_estimado_usd: 1.33
  modelo_ia: "google/gemini-3.1-flash-image-preview"

anuncios:
  - pai_sku: "VIE_1066-PAI"
    modo: "variacoes"
    status_fotos: "pronto"
    total_storyselling_geradas: 10
    total_ambientalizadas_geradas: 3
    total_ambientalizadas_bloqueadas: 0
    falhas: 0
    retries_total: 1
    pasta: "squads/ml-anuncios/output/fotos/VIE_1066-PAI/"
    custo_estimado_usd: 0.91

  - pai_sku: "TCD-LXI12"
    modo: "simples"
    status_fotos: "pronto"
    total_storyselling_geradas: 10
    total_ambientalizadas_geradas: 0
    total_ambientalizadas_bloqueadas: 0
    falhas: 0
    retries_total: 0
    pasta: "squads/ml-anuncios/output/fotos/TCD-LXI12/"
    custo_estimado_usd: 0.42
```

## Veto Conditions

Rejeitar e refazer se ALGUMA for verdadeira:
0. **`dados_produto.dimensoes_produto.altura` ou `.largura` sem `status: "ok"` (ou campo ausente) ao iniciar step-07** — anúncio deve ser marcado `bloqueado_dimensoes_nao_resolvidas` e nenhuma foto gerada. `profundidade` com `status: "nao_aplicavel"` ou ausente não é motivo de veto. A esteira não deveria ter chegado aqui sem passar pelo checkpoint step-04b.
1. Algum anúncio com `confianca ≥ media` no brief ficou sem StorySelling gerada.
2. Algum anúncio com menos de 10 StorySelling válidas (slots faltantes).
3. Algum anúncio com `falhas ≥ 2` (StorySelling + ambientalizadas) sem ser marcado como `incompleto`.
4. Foto 1 (CAPA) sem image-to-image (produto não preservado da foto base).
5. Slot 9 (SOBRECORRECAO) sem selos visuais aplicados.
6. Slot 10 (MACRO_YES) sem CTA. (NÃO exigir brand_signature — regra SEM MARCA, Almir 19/06.)
6b. **Qualquer foto com logo, slogan, brand_signature ou cores da marca aplicados** (viola a regra SEM MARCA).
7. Faltam JSONs em `prompts/` (auditoria quebrada).
8. Anúncio `modo: variacoes` sem ambientalizada para alguma variação onde `fotos_bucket[0]` estava acessível.
9. `picture_ids` de alguma variação com ordem incorreta (ambientalizada não está na 1ª posição em `modo: variacoes`).
10. Overlay aplicado em foto ambientalizada — ambientalizada deve ser imagem limpa.

## Quality Criteria

- [ ] Gate de dimensões executado para cada anúncio antes de gerar qualquer foto — anúncios com `altura` ou `largura` de `dimensoes_produto` sem `status: "ok"` marcados como `bloqueado_dimensoes_nao_resolvidas` sem gerar fotos; `profundidade` ausente/`nao_aplicavel` não bloqueia
- [ ] 100% dos anúncios com brief `confianca ≥ media` (e dimensões obrigatórias ok) têm pasta `squads/ml-anuncios/output/fotos/{pai_sku}/` populada
- [ ] Foto técnica `FICHA_TECNICA_DIMENSOES` gerada com overlay contendo `DIM_ALTURA` e `DIM_LARGURA` de `dados_produto.dimensoes_produto`; `DIM_PROFUNDIDADE` omitido (linha some do template) quando `status: "nao_aplicavel"`
- [ ] Cada anúncio pronto tem StorySelling completas (incluindo a foto técnica)
- [ ] Cada anúncio `modo: variacoes` tem 1 ambientalizada por variação (exceto variações com `fotos_bucket[0]` inacessível)
- [ ] `fotos_cor` de cada variação preenchido com URL pública no `anuncios-entrada.json` atualizado
- [ ] Cada foto com dimensão **exata 1200×1200 px** (padrão fixo do projeto — não mínimo)
- [ ] Cada foto (StorySelling + ambientalizada) tem JSON correspondente em `prompts/`
- [ ] Hierarquia respeitada: slot N → função canônica
- [ ] Headlines/badges/CTA aplicados via overlay nas StorySelling; ambientalizada sem overlay
- [ ] Slot 9 com 4-6 selos visuais
- [ ] Nenhuma foto com logo/slogan/brand_signature ou cores da marca (regra SEM MARCA, Almir 19/06)
- [ ] `picture_ids` montados: fotos_cor (se variacoes) + StorySelling
- [ ] `metadata.yaml` por anúncio em `squads/ml-anuncios/output/fotos/{pai_sku}/metadata.yaml` + `squads/ml-anuncios/output/fotos/metadata-fotos.yaml` consolidado salvos
- [ ] Custo total reportado (StorySelling + ambientalizadas separados)
