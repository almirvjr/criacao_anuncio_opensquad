# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projeto

Ferramentas de anúncio do Mercado Livre da Terra Casa Decor. **Três frentes:**

1. **Criar anúncio novo** — squad `ml-anuncios` do Opensquad: pipeline de papéis
   (categoria → estrategista → copy → **capas do Almir no Cloudinary** → revisão → publicação) que produz
   título, descrição e ficha. **Desde 07/10/2026 não gera foto** (ver "Fotos" abaixo). Runbook em `PROGRESSO.md`.
2. **Auditar e consertar a ficha dos anúncios JÁ no ar** — `tools/auditoria_ficha/` (ver seção própria abaixo).
3. **Entrar em catálogo sem "Vender um igual"** (catálogo sem oferta ativa) — `tools/catalogo_sem_oferta/Entrar no catalogo.bat`
   (clique duplo; pede link, preço e estoque; confere no ML antes e só publica com "s"; anota em `historico.csv`).
   Receita na memória `ml_catalogo_sem_oferta_criar_pela_api`.

**Idioma:** Responda sempre em portugues (brasileiro), a menos que o usuario mude de idioma.

**Nivel tecnico:** O usuario e leigo em programacao. Ao se comunicar com ele: evite jargoes tecnicos sem explicacao, use analogias do cotidiano para explicar conceitos, prefira frases curtas e diretas. Quando precisar usar termo tecnico inevitavel, explique em parenteses o que significa. Exemplos: em vez de "endpoint", diga "endereco que recebe os dados"; em vez de "deployar", diga "publicar/ativar".

---

## n8n

| Campo | Valor |
|---|---|
| **URL** | Ver `.env` -> `N8N_URL` |
| **API Key** | Ver `.env` -> `N8N_API_KEY` |

---

## MCPs e Infraestrutura

MCPs configurados em `.mcp.json`:

- **mercadolibre**: API ML via token em `access_token_ML` do Supabase. Plugin `ml-kit` atualiza token automaticamente no SessionStart.
- **supabase**: MCP oficial Supabase para queries no banco.
- **n8n** (opcional): MCP para gerenciar workflows n8n via API.
- **olist-docs**: MCP de documentacao da API v3 Tiny (so consulta de doc, nao executor). Operacao real no Tiny continua via HTTP Request no n8n com OAuth2.
- **playwright**: navegacao headless para scraping. Usado em producao pela Helena Estrategista (squad ml-anuncios) para coletar reviews + FAQ + descricao dos 3 anuncios concorrentes top de cada SKU. (A skill `image-overlay` NAO usa mais browser — migrou pra render Python/Pillow; ver abaixo.)

Token ML expira em ~6h. Hook do plugin `ml-kit` puxa token fresco da tabela `access_token_ML` no SessionStart.

### Fotos (fora da esteira desde 07/10/2026)

A squad **não gera foto**: a capa de cada cor é subida pelo Almir no Cloudinary (pasta do fornecedor) com as etiquetas **SKU da cor** (igual ao Tiny) + `capa-anuncio`; o step-07 (`capas.py`) monta o endereço 1200×1200. Trocar cor de produto numa foto = site do ChatGPT (ver `projects/imagens/DECISOES.md` I27). Todo o método de geração (motores, produto travado, cutout, escala, luz, checklist de imagem) foi movido **na íntegra** para `squads/ml-anuncios/_arquivo-fotos/REGRAS-DE-FOTO.md`.

---

## Ficha tecnica dos anuncios no ar — `tools/auditoria_ficha/`

Frente separada do pipeline: mede e conserta a ficha dos ~958 anuncios existentes. Scripts PS 5.1, todos
com backup antes e releitura de conferencia depois. `auditar_ficha_tecnica.ps1` (campo vazio) ·
`auditar_irregularidades.ps1` (valor errado) · `coletar_sugestoes.ps1` (busca o valor certo) ·
`validar_sugestoes.ps1` (peneira) · `aplicar_lote.ps1` / `aplicar_nao_se_aplica.ps1` (grava).

> 🔑 **ANTES de qualquer gravacao em lote, nesta ordem:** (1) filtrar `catalog_listing=false` —
> **anuncio de catalogo responde HTTP 200 e IGNORA a escrita**, sem erro nenhum, entao um lote sem esse
> filtro "corrige" centenas de anuncios e nao corrige nada; (2) rodar `validar_sugestoes.ps1` — valor vindo
> de outra ficha pode nao existir na lista daquela categoria; (3) comparar titulo antes/depois — gravar
> `COLOR` em anuncio **sem variacao** faz o ML anexar a cor no titulo sozinho.

- **Onde cada dado mora:** medida de PRODUTO = ficha do catalogo do ML achada pelo codigo de barras
  (`/products/search?q={EAN}` → `/products/{id}`). **Peso** = Tiny, em `dimensoes.pesoLiquido` (KG) —
  nao existe na raiz do JSON. **Medida do Tiny e da CAIXA**, nao serve. `knowledge_base` = 2a opiniao, tem erro dentro.
- **`value_id = "-1"` = "nao se aplica"** — campo assim esta preenchido, nao vazio. E e assim que se marca.
- **So `variation_attribute` grava na variacao.** `allow_variations` NAO basta (400). `COLOR` e do anuncio
  na maioria das categorias; `MAIN_COLOR` e da variacao. Campo do anuncio com valor diferente por variacao: **nao gravar**.
- Nao existe API de qualidade do anuncio (`/health`, `/performance` = 404). Anuncio de catalogo **nao tem nota**.

---

## Regras Criticas

- **Arquivos temporarios: PROIBIDO criar fora do projeto.** Sempre dentro do diretorio do projeto. Hook global `check-write-path.ps1` bloqueia violacoes.
- **HTTP em Code nodes (n8n): PROIBIDO.** Task runner bloqueia `$helpers`, `fetch()`, `require('https')`. Sempre usar HTTP Request nodes nativos. Code nodes: apenas transformacao.
- **AI Agent tools (n8n):** Sempre configurar `neverError: true` em HTTP Request Tools usadas por AI Agents. Sem isso, qualquer erro HTTP crasha o workflow.
- **Supabase nativo n8n nao suporta arrays.** Campos ARRAY falham no no `n8n-nodes-base.supabase`. Usar HTTP Request node com body JSON para inserts que incluam arrays.
- **Tabelas novas por schema de dominio.** `public` e legado; preferir schemas como `ml_tools`, `tiny`, `integracao`.
- **Validacao obrigatoria:** `validate_workflow` antes de todo `create_workflow` ou `update_workflow`.
- **Expressoes n8n:** Sempre `{{ $json.fieldName }}` - nunca omitir as chaves duplas.
- **Metodo StorySelling na squad ml-anuncios:** a copy (titulo, descricao, ficha) e baseada em diagnostico psicologico das reviews de concorrentes ML (feito pela Helena Estrategista no step-04). Helena precisa de `permalink` valido de pelo menos 2 concorrentes top da Cibele para funcionar. Frameworks de referencia em `squads/ml-anuncios/pipeline/data/storyselling-framework.md` (MECLABS, escada E dai) e `objection-patterns.md` (10 familias). Os templates de foto foram para `_arquivo-fotos/`.
- **SEM MARCA em NENHUMA parte do anuncio (Almir 19/06, DEFINITIVA).** A marca — nome "Terra Casa Decor" e slogan "O seu melhor lugar e a sua casa" — NAO aparece em foto, titulo NEM descricao. Nas fotos: sem logo/slogan e sem se apoiar nas cores da marca (`render_faixa.py` nao desenha marca por padrao, gate `show_brand` off). No titulo/descricao: nao citar o nome da loja nem o slogan/assinatura. Motivo: nao prender o anuncio a um eventual rebrand. O **tom/voz** acolhedor (palavras como "casa", "lar", "dia a dia") PERMANECE — isso e estilo de escrita, nao citacao da marca.
  - **EXCECAO Mundiart (`MDA_`), Almir 07/10/2026:** produto Mundiart e marca propria — campo Marca = `Terra Casa Decor` (so isso) e a **descricao apresenta o produto como da marca Terra Casa Decor**. O **titulo continua sem** o nome da loja. Slogan continua fora.
- **Campos MARCA e MODELO da ficha (Almir 07/10/2026, Marca revista em 08/10).** **Marca = SO o nome do fornecedor** (Viel, Brinox, Bellagio, Passerini...), sem palavra-chave depois — e o padrao da esteira. Quando o Almir quiser, ele troca na mao por **SO `Terra Casa Decor`** (marca propria); nesse caso a descricao pode apresentar o produto como Terra Casa Decor. **Modelo = palavra-chave de busca** que ainda NAO esta no titulo (nada repetido), teto ~30 caracteres. Mundiart: Marca = `Terra Casa Decor` sempre. Conferir no 1o anuncio publicado se o ML aceitou os valores como enviados.

---

## Progresso e Planejamento

- `PROGRESSO.md` - tarefas ativas e proximos passos. Leia apenas quando precisar de contexto historico ou planejar proximos passos. Nao leia proativamente.
- `HISTORICO.md` - tarefas concluidas. Leia apenas para contexto de decisoes passadas.
- `DECISOES.md` - decisoes tecnicas do projeto. Leia apenas ao encontrar problema similar.
- `REFERENCIA.md` - detalhes tecnicos: MCPs, tabelas, RLS, skills, workflows.

---

## Disciplina de Sessao

### Classificacao de tarefas

| Tamanho | Exemplos | Abordagem |
|---------|----------|-----------|
| **Pequena** | Corrigir campo, atualizar expressao, toggle de config | Execucao direta |
| **Media** | Adicionar 1-3 nos, modificar Code node, corrigir bug | Declarar plano em 3 linhas antes de executar |
| **Grande** | Novo workflow, reestruturar cadeia de nos, nova integracao | Usar plan mode antes de executar |

### Regras

- **Uma mudanca por vez:** atualizar -> validar -> confirmar resultado -> proxima mudanca.
- **Ler antes de adivinhar:** quando workflow falhar, verificar `get_executions` antes de qualquer hipotese.
- **Subagentes para contexto grande:** delegar parsing de JSON >30KB, pesquisa em docs ML, scripts complexos de Code nodes.
- **Prompts especificos:** incluir ID do workflow, nome do no e dado disponivel no prompt inicial.
- **`/clear` entre tarefas grandes:** libera contexto apos concluir uma unidade logica.
- **`/save` mid-session:** rodar ao concluir cada unidade logica.
