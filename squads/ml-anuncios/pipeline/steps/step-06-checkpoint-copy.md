---
type: checkpoint
---

# Step 06: Checkpoint A — Aprovação do Conteúdo Textual (Múltiplos Títulos)

## Apresentar ao usuário

Mostrar ao usuário uma tabela resumo do conteúdo textual produzido pela Renata Redatora, lendo `squads/ml-anuncios/output/copywriting/anuncios.yaml`.

**Por SKU**, apresentar:
- As **3-5 alternativas de título** com scores e justificativa.
- A recomendação da Renata destacada.
- Categoria, preço, status_copy.
- Link para descrição completa.

### Formato (por SKU)

```
=== TCD-LXI12 — Lixeira Inox 12L ===

Categoria: Casa > Cozinha > Lixeiras
Preço: R$ 159,90
Status copy: ok
Dor interna do brief: "Minha casa fica com aparência simples e bagunçada por causa dos detalhes."

Títulos propostos:

  [1] Lixeira Inox 12L Pedal Tampa Antiodor Cozinha Banheiro
      56 chars · busca 9/10 · conversão 6/10 · total 15
      "SEO forte; emocionalmente neutro."

  [2] Lixeira Inox 12L Pedal Cozinha Banheiro Moderna Chique
      54 chars · busca 7/10 · conversão 9/10 · total 16
      "Linguagem real do cliente; toca dor interna; perde alguma cobertura SEO."

★ [3] Lixeira Inox 12L Pedal Antiodor Cozinha Banheiro Moderna   ← RECOMENDADO
      56 chars · busca 8/10 · conversão 8/10 · total 16
      "Balanço bom: 'moderna' (linguagem cliente) + SEO base preservado."

Descrição completa: output/copywriting/anuncio-TCD-LXI12.yaml
```

Sempre listar no fim do checkpoint:
- Total de SKUs processados.
- Total `ok` / `warning` / `sem_brief`.
- SKUs bloqueados/ignorados desde o step 01 ou desde o brief da Helena.
- Marca e Modelo propostos (ficha) de cada SKU, com contagem de caracteres.

## Decisão esperada (modo `batch`)

O modo de aprovação do pipeline é `batch` — o usuário aprova o lote inteiro de uma vez, escolhendo qual título usar por SKU.

Opções:

1. **Aprovar tudo com a recomendação da Renata** (default mais rápido):
   - Cada SKU usa o título marcado `recomendado: true`.
   - Pipeline segue para step-07 (buscar as capas no Cloudinary).

2. **Aprovar com seleção manual de títulos**:
   - Para cada SKU, usuário informa qual título escolheu (1, 2, 3, 4 ou 5).
   - Pipeline registra a escolha em `output/copywriting/anuncios.yaml` (campo `titulo_escolhido_numero`) e segue.

3. **Aprovar com edição livre**:
   - Para SKUs específicos, usuário sobrescreve o título com texto livre (ainda dentro de 50-70 chars).
   - Pipeline valida contagem e segue.

4. **Solicitar reformulação de copy** para SKUs específicos:
   - Renata reabre step-05 só para SKUs apontados.
   - Ao terminar, volta para este checkpoint.

5. **Refazer copy do lote inteiro**:
   - Pipeline volta para step-05 com instruções gerais (ex: "todos os títulos com mais palavras emocionais").
   - Pode também voltar para step-04 (Inteligência) se o problema for diagnóstico fraco.

## Registrar decisão

Para cada SKU aprovado, gravar no arquivo de copy:
```yaml
titulo_escolhido_numero: <1-5>   # ou null se foi edição livre
titulo_final: "<string>"
aprovado_em: "<ISO timestamp>"
aprovado_por: "checkpoint humano"
```

Depois de gravar o `titulo_final`, rodar de novo `python squads/ml-anuncios/pipeline/validators/validar_ficha_seo.py squads/ml-anuncios/output/copywriting/anuncio-{pai_sku}.yaml` — se o Almir escolheu outro título, uma palavra de Marca/Modelo pode ter virado repetida. Reprovou → a Renata troca Marca/Modelo, sem mexer no título escolhido.

## Veto Conditions

1. Arquivo `output/copywriting/anuncios.yaml` não existe ou tem zero anúncios — não apresentar checkpoint, voltar para step-05.
2. Qualquer SKU sem `recomendado: true` em algum dos seus títulos — Renata violou a regra; voltar.
3. Qualquer SKU com `status_copy: sem_brief` — sinalizar destacadamente, exigir decisão consciente do usuário (pode aprovar mesmo assim ou voltar para step-04).
4. `validar_ficha_seo.py` com código != 0 depois do título escolhido.
