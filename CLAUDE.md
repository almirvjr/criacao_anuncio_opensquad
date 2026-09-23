# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projeto

Ferramentas de anúncio do Mercado Livre da Terra Casa Decor. **Três frentes:**

1. **Criar anúncio novo** (o grosso deste arquivo) — squad `ml-anuncios` do Opensquad: pipeline de papéis
   (estrategista → categoria → fotos → copy → revisão → publicação) que produz título, descrição, ficha e
   as 10 fotos. Runbook em `PROGRESSO.md`.
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

### Modelo de IA para imagens

A skill `image-ai-generator` da squad ml-anuncios usa Gemini Image via **OpenRouter** (`OPENROUTER_API_KEY` no `.env`). **Motor padrao desde 17/09/2026 = `gpt`** (era `test`). Modos do `generate.py`: `test` (`sourceful/riverflow-v2-fast`, barato p/ layout); `production` (`google/gemini-3.1-flash-image-preview` = Nano Banana 2 Flash); `pro` (`google/gemini-3-pro-image` = Nano Banana Pro); **`gpt` (`openai/gpt-image-2` = GPT Image 2)**.
**Bake-off medido em 17/09/2026 (`tests/motor-bakeoff/`, capa do 8L, alvo de escala 0,38): o `gpt` erra a escala pela METADE do `pro`** (+0,08 contra +0,23) e e o mais estavel entre rodadas. Nenhum motor acerta 0,38 sozinho — a escala ainda precisa de conferencia medida.
**Desde 17/09/2026 o `generate.py` usa a API de imagem do OpenRouter** (`/images/generations`) por padrao, nao o `/chat/completions`: so ela aceita tamanho. Gera em 2048x2048 e REDUZ pra 1200x1200 (o contrato da squad) — antes gerava 1024 e alguem ampliava, o que borrava. `--api chat` volta ao caminho antigo; `--edit` continua sempre no caminho antigo.
🔴 **Armadilha:** a referencia so chega ao modelo pelo parametro `input_references`. Com o nome errado (`image`/`image_urls`) a API **aceita, cobra e ignora a referencia calada**, devolvendo OUTRO produto. O `generate.py` tem trava pra isso (confere `prompt_tokens`); quem mexer nesse trecho confere a IMAGEM, nao o codigo. O texto (headline/selos/CTA) NÃO é gerado pela IA — vem do overlay Pillow (`image-overlay`).

**ARQUITETURA PRODUTO-TRAVADO (2026-06-23, DEFINITIVA) — o produto NÃO é re-renderizado, é COMPOSIÇÃO.** Mata o edit-drift do Nano Banana (`--edit` re-renderiza a cena toda e regride detalhes já aprovados; slot 6 custou 9 iterações). O produto fiel vira PNG travado (recorte BiRefNet do hero + sha256 em `pipeline/data/produtos-travados/{pai_sku}.json` via `lock_product.py`), colado por código (`compose.py`) sobre a cena — a única coisa que a IA gera. Detalhe em `REFERENCIA.md` ("ARQUITETURA PRODUTO-TRAVADO"), `DECISOES.md` (2026-06-23), plano `~/.claude/plans/bubbly-sleeping-ember.md`.
- **Política por slot:** studio/neutro (3,4,9,10) = `compose.py --bg studio` (fundo por código, custo IA 0, fidelidade FORTE por hash/proveniência); lifestyle (capa,2,5,8) = híbrido (compor + `--harmonize warm`; fallback one-shot do hero fiel SEM `--edit`); slot 7 (pedal c/ pé) = one-shot com `generate.py --lock` (gate de produto após gravar; ausente → `_rejeitado/`).
- **`--edit` PROIBIDO p/ corrigir o produto** (edit-drift); só p/ fundo que não toque o produto.
- **Fidelidade é por construção** (composição: hash da camada produto) ou por gate de desastre + olho humano + `inox_cast` (one-shot). NÃO depende da atenção do assistente.
- Heros fiéis (refs mestras p/ travar): `_redesign-overlay/branco-studio-fiel.jpg` (aberto) e `...-fechada.jpg` (fechado).
- `generate.py` tem modo **`faithful`** (recolor/variação idêntica) e anexa **`SCENE_COHERENCE`** automaticamente em geração de cena.

O **overlay de texto é render Python/Pillow** (`skills/image-overlay/scripts/render_faixa.py`), NÃO browser. Decisão de 25/05 sobre FLUX/Nano Pro segue valendo: avaliados em council (17/06) e **descartados** — não comprar (ver `DECISOES.md`).

### Detecção de produto + gate de cor (cutout) — depende de `rembg`

- **`skills/image-overlay/scripts/cutout.py`**: máscara/bbox do produto via **BiRefNet** (`rembg` + `onnxruntime`, modelo `birefnet-general`, roda offline/R$0). Substituiu a heurística frágil do pixel-de-canto em `render_faixa.py` (foto técnica), `fit_scale.py` e `compose_two.py`. **Fallback automático** pra heurística antiga se `rembg` faltar ou `CUTOUT_DISABLE=1`. Modelo configurável por `CUTOUT_MODEL`.
- **`skills/image-overlay/scripts/inox_cast.py`**: quality-gate de cor — reprova foto de inox que ficou "dourada" (calor RGB `w_med>=14`), pra disparar retry. **Não** corrige em pós (achataria reflexos quentes desejados); regenera.
- **Dependência nova:** `pip install rembg onnxruntime` (já instaladas no Windows atual). Sem elas, o pipeline funciona com qualidade antiga (fallback).

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
- **Fotos do anuncio ML: tamanho FIXO 1200x1200 px.** Regra global do projeto. Maior (ex: 1500x1500) ou menor (ex: 1000x1000) e veto automatico — templates de overlay (skill `image-overlay`) assumem canvas 1200x1200 fixo. Felipe redimensiona se Nano Banana retornar dimensao diferente.
- **Foto tecnica de dimensoes: a base precisa nascer com FOLGA.** As cotas sao desenhadas FORA da silhueta do produto — altura a esquerda, largura abaixo e profundidade em diagonal a direita (3a cota, 22/07; so aparece se `dim_profundidade` vier preenchida — produto redondo manda vazio). Exige **~80px livres a esquerda e ~110px abaixo** do produto. Sem essa folga a cota e desenhada fora do canvas e SOME sem erro nenhum: o `render_faixa.py` avisa no log (`[dim] AVISO: so ha Npx de folga...`) mas **nao reposiciona** — mover as cotas mudaria fotos ja aprovadas, entao reenquadrar a base e trabalho de quem gerou.
- **Produto NUNCA e re-renderizado pra corrigir detalhe (arquitetura produto-travado, 2026-06-23).** Composicao (`compose.py` + PNG travado) e o default; `--edit` do Nano Banana e PROIBIDO pra corrigir o produto (re-renderiza a cena toda e regride o que ja estava aprovado = edit-drift). Detalhe na secao "Modelo de IA para imagens" e em `REFERENCIA.md`.
- **Metodo StorySelling na squad ml-anuncios:** copy e fotos sao baseadas em diagnostico psicologico das reviews de concorrentes ML (feito pela Helena Estrategista no step-04). Helena precisa de `permalink` valido de pelo menos 2 concorrentes top da Cibele para funcionar. Frameworks de referencia em `squads/ml-anuncios/pipeline/data/storyselling-framework.md` (MECLABS, escada E dai, hierarquia das 10 fotos), `objection-patterns.md` (10 familias) e `photo-templates.md` (10 templates JSON parametrizados).
- **Capa da variacao = ambientalizada SEM texto.** O overlay de texto vive SO nas 9 fotos StorySelling (compartilhadas entre cores, texto neutro de cor). `picture_ids` = 1 capa + 9 StorySelling = 10.
- **SEM MARCA em NENHUMA parte do anuncio (Almir 19/06, DEFINITIVA).** A marca — nome "Terra Casa Decor" e slogan "O seu melhor lugar e a sua casa" — NAO aparece em foto, titulo NEM descricao. Nas fotos: sem logo/slogan e sem se apoiar nas cores da marca (`render_faixa.py` nao desenha marca por padrao, gate `show_brand` off). No titulo/descricao: nao citar o nome da loja nem o slogan/assinatura. Motivo: nao prender o anuncio a um eventual rebrand. O **tom/voz** acolhedor (palavras como "casa", "lar", "dia a dia") PERMANECE — isso e estilo de escrita, nao citacao da marca.
- **Materiais do produto (lixeiras Viel):** APENAS o corpo cilindrico e aco inox (cool neutral silver, nunca dourado). Tampa + aro/colar do topo + pedal + base sao PLASTICO, **na cor-heroi do anuncio** — branco OU preto (o 8L VIE_1067 e PRETO, escolha do Almir em 26/06). O texto antigo dizia "plastico branco" como se fosse a unica versao. Aba/dobradica da tampa ALINHADA com o pedal (mesmo eixo).
- **CHECKLIST medido antes de pedir aprovacao de imagem** (lista completa em `squads/ml-anuncios/_memory/memories.md`): materiais, alinhamento aba-pedal, inox neutro (`inox_cast`), escala e forma do produto, coerencia dos props, sem marca, sem texto embutido. NUNCA enviar imagem que quebre uma orientacao ja dada.
  - 🔴 **Escala e POR PRODUTO** (corrigido 18/09/2026; antes dizia "≈1/3" pros dois, o que e quase a regua da 5L): razao = altura da lixeira ÷ altura do movel (chao→tampo, 90cm). Verdade fisica: **5L = 0,27 · 8L = 0,38**. Mas o motor entrega 0,42-0,48 e o Almir aceitou (22/09, olhando a imagem) a **faixa 0,36-0,48 no 8L** — o piso fica perto da verdade fisica de proposito: abaixo dele o 8L fica com cara de 5L. Nao confundir com "% do frame".
  - **FORMA do produto** = altura ÷ largura do corpo. **8L = 1,89 (34÷18) · 5L = 1,39 (25÷18)**, tolerancia ±5%. Foi por aqui que se descobriu que a foto-mestre estava esticada 12%. 🔴 **O motor NAO obedece** (entrega ~2,05 em 24 medicoes; nem prompt nem referencia achatada de proposito mudam isso) — corrigir DEPOIS com `skills/image-overlay/scripts/corrigir_forma.py`, que achata a foto inteira ate o produto bater com o real.
  - Desde 18/09/2026 quem mede as duas e o **`pipeline/validators/juiz_escala.py`**, nao o olho. Ele cobre foto ambientada, movel apoiado no chao, produto INTEIRO no quadro e tampa FECHADA; fora disso ele RECUSA medir em vez de chutar.
- **Luz NEUTRA, calor nos MATERIAIS.** Luz quente doura o inox: em 22/09 o gate `inox_cast` reprovou 3 de 5 fotos (14,3 / 20,2 / 24,1; limite 14). Com luz neutra e madeira/terracota/areia segurando o aconchego: 7,4 e 9,1.
- 🔴 **NAO confie cegamente nos templates de `photo-templates.md`.** Em 23/09 o Almir reprovou 5 fotos que obedeciam o template ao pe da letra: o StorySelling escrito aqui **contradiz o prompt original que ele trouxe** (slot 2: o template manda mesma temperatura de cor nos dois lados e "nao exagerar o ANTES"; o prompt dele manda luz fria contra quente, duas paletas e lixeira de plastico barata no lado ruim). Antes de gerar em lote, conferir o template contra a intencao dele. Detalhe em DECISOES 2026-09-17/23.
- **Proporcao do produto nas fotos = ancorada em medidas reais do ambiente** (ex.: bancada de banheiro ~90cm). A IA NAO acerta escala "no olho" — a medida tem que ir explicita no prompt. Quando destaque do produto e escala brigam, gerar a cena ABERTA (movel inteiro no quadro), MEDIR ali, e so entao aproximar com `skills/image-overlay/scripts/enquadrar_capa.py` — aproximar nao muda a relacao de tamanho, entao a medida continua valendo. (A antiga "formula do gabinete cortado" pedia a cena ja fechada, o que tira a regua do quadro e deixa a escala sem como conferir.) Props sempre coerentes com o ambiente (nada de toalha/vaso de mesa no chao). Receita completa em `squads/ml-anuncios/_memory/memories.md`; decisoes em `DECISOES.md` (2026-06-15).

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
