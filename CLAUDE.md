# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projeto

{{DESCRICAO_DO_PROJETO}}

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

A skill `image-ai-generator` da squad ml-anuncios usa Gemini Image via **OpenRouter** (`OPENROUTER_API_KEY` no `.env`). Modos do `generate.py`: `test` (`sourceful/riverflow-v2-fast`, barato p/ layout); `production` (`google/gemini-3.1-flash-image-preview` = Nano Banana 2 Flash); **`pro` (`google/gemini-3-pro-image` = Gemini 3 Pro Image)** — adotado em 19/06 por ser **muito mais fiel e acertar de 1ª**: usar Pro pras cenas/lifestyle/antes-depois. O texto (headline/selos/CTA) NÃO é gerado pela IA — vem do overlay Pillow (`image-overlay`); a IA só preserva o produto.
- **Método 1-tacada:** cenas/lifestyle/antes-depois = gerar a cena inteira numa geração via prompt JSON rico (a IA integra o produto). NÃO compor recorte no Pillow (vira "figurinha"). Macros de detalhe = recorte da foto REAL + modo `faithful` (zero alucinação). Heros fiéis (refs mestras): `_redesign-overlay/branco-studio-fiel.jpg` (aberto) e `...-fechada.jpg` (fechado).
- `generate.py` tem modo **`faithful`** (recolor/variação idêntica) e anexa a cláusula **`SCENE_COHERENCE`** automaticamente em toda geração de cena (props no lugar certo).

O **overlay de texto é render Python/Pillow** (`skills/image-overlay/scripts/render_faixa.py`), NÃO browser. Decisão de 25/05 sobre FLUX/Nano Pro segue valendo: avaliados em council (17/06) e **descartados** — não comprar (ver `DECISOES.md`).

### Detecção de produto + gate de cor (cutout) — depende de `rembg`

- **`skills/image-overlay/scripts/cutout.py`**: máscara/bbox do produto via **BiRefNet** (`rembg` + `onnxruntime`, modelo `birefnet-general`, roda offline/R$0). Substituiu a heurística frágil do pixel-de-canto em `render_faixa.py` (foto técnica), `fit_scale.py` e `compose_two.py`. **Fallback automático** pra heurística antiga se `rembg` faltar ou `CUTOUT_DISABLE=1`. Modelo configurável por `CUTOUT_MODEL`.
- **`skills/image-overlay/scripts/inox_cast.py`**: quality-gate de cor — reprova foto de inox que ficou "dourada" (calor RGB `w_med>=14`), pra disparar retry. **Não** corrige em pós (achataria reflexos quentes desejados); regenera.
- **Dependência nova:** `pip install rembg onnxruntime` (já instaladas no Windows atual). Sem elas, o pipeline funciona com qualidade antiga (fallback).

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
- **Metodo StorySelling na squad ml-anuncios:** copy e fotos sao baseadas em diagnostico psicologico das reviews de concorrentes ML (feito pela Helena Estrategista no step-04). Helena precisa de `permalink` valido de pelo menos 2 concorrentes top da Cibele para funcionar. Frameworks de referencia em `squads/ml-anuncios/pipeline/data/storyselling-framework.md` (MECLABS, escada E dai, hierarquia das 10 fotos), `objection-patterns.md` (10 familias) e `photo-templates.md` (10 templates JSON parametrizados).
- **Capa da variacao = ambientalizada SEM texto.** O overlay de texto vive SO nas 9 fotos StorySelling (compartilhadas entre cores, texto neutro de cor). `picture_ids` = 1 capa + 9 StorySelling = 10.
- **SEM MARCA nas imagens dos anuncios (Almir 19/06, DEFINITIVA).** Nenhuma foto leva logo Terra, slogan, nem se apoia nas cores da marca — pra nao prender a foto a um rebrand. A marca vive no TITULO/DESCRICAO. `render_faixa.py` nao desenha marca por padrao (gate `show_brand`, off).
- **Materiais do produto (lixeiras Viel):** tampa + aro/colar do topo + pedal + base = PLASTICO branco; APENAS o corpo cilindrico e aco inox (cool neutral silver, nunca dourado). Aba/dobradica da tampa ALINHADA com o pedal (mesmo eixo).
- **CHECKLIST medido antes de pedir aprovacao de imagem** (lista completa em `squads/ml-anuncios/_memory/memories.md`): materiais, alinhamento aba-pedal, inox neutro (`inox_cast`), **escala MEDIDA lixeira÷bancada ≈1/3** (nao "% do frame"), coerencia dos props, sem marca, sem texto embutido. NUNCA enviar imagem que quebre uma orientacao ja dada.
- **Proporcao do produto nas fotos = ancorada em medidas reais do ambiente** (ex.: bancada de banheiro ~90cm). A IA NAO acerta escala "no olho" — a medida tem que ir explicita no prompt. Quando destaque do produto e escala 1/3 brigam, usar a **formula do gabinete cortado** (cortar a bancada fora do topo; o gabinete some pra cima e o produto fica no terco de baixo, lendo pequeno mesmo grande no frame). Props sempre coerentes com o ambiente (nada de toalha/vaso de mesa no chao). Receita completa em `squads/ml-anuncios/_memory/memories.md`; decisoes em `DECISOES.md` (2026-06-15).

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
